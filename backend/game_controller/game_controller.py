# 游戏控制盘模块
from typing import Dict, Any, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.player_controller.player_controller import PlayerController
from backend.deck.deck import Deck
from backend.card.card import Card
from backend.utils.logger import game_logger
from backend.game_controller.card_effect_handler import CardEffectHandlerFactory
from config.enums import CardName, CardType, GameEvent, CardSuit
from config.simple_card_config import SimpleGameConfig
from backend.utils.event_sender import send_draw_card_event, send_game_over_event
from communicator.communicator import communicator
from communicator.comm_event import DebugEvent
from config.enums import PlayerIdentity
import random


class GameController:
    """游戏控制盘模块
    
    负责游戏的主循环和牌效果处理
    """
    
    def __init__(self, config: SimpleGameConfig):
        """初始化函数
        
        Args:
            config: GameConfig配置对象
        """
        self.config = config
        self.player_controller = None
        self.deck = None
        self.current_player_id = None
        self.game_ended = False
    
    def initialize(self) -> None:
        """初始化游戏
        
        根据配置文件调用玩家控制模块生成玩家、调用牌堆模块生成牌堆
        """
        game_logger.log_info("开始初始化游戏...")
        
        # 创建牌堆
        self.deck = Deck(self.config)
        game_logger.log_info(f"牌堆创建完成，总牌数: {len(self.deck.cards)}")
        
        # 创建玩家控制器
        self.player_controller = PlayerController(self.config, self.deck)
        game_logger.log_info(f"玩家控制器创建完成，玩家数量: {len(self.player_controller.players)}")
        
        # 获取初始玩家
        self.current_player_id = self.player_controller.get_initial_player()
        game_logger.log_info(f"初始玩家ID: {self.current_player_id}")
        
        game_logger.log_info("游戏初始化完成")
    
    def _check_debug_events(self):
        """检查调试事件（一键胜利/失败）"""
        if not communicator:
            return
        
        # 尝试获取所有待处理的调试事件
        # 注意：为了避免无限循环（取出非Debug事件又放回去），我们只处理当前队列长度的次数
        q_size = communicator.ftb_queue.qsize()
        other_events = []
        
        for _ in range(q_size):
            try:
                event = communicator.ftb_queue.get_nowait()
                if isinstance(event, DebugEvent):
                    print(f"[Backend] 收到调试指令: {event.command}")
                    if event.command == "win":
                        self._force_win()
                    elif event.command == "lose":
                        self._force_lose()
                else:
                    # 如果不是DebugEvent，暂存
                    other_events.append(event)
            except Exception:
                break
        
        # 将非Debug事件放回队列
        for e in other_events:
            communicator.ftb_queue.put(e)

    def _force_win(self):
        """强制胜利：杀死所有敌人"""
        # 假设当前玩家是主角（赵云），或者找到主角
        # 简单逻辑：杀死所有反贼和内奸
        print("[Debug] 执行一键胜利...")
        for p in self.player_controller.players:
            if p.identity in [PlayerIdentity.REBEL, PlayerIdentity.TRAITOR]:
                if p.is_alive():
                    print(f"[Debug] 处决 {p.name}")
                    p.current_hp = 0
                    p.die()
                    # 触发死亡结算
                    if self.player_controller.game_over():
                        winner = self.player_controller.get_winner()
                        if winner:
                            game_logger.log_info(f" 游戏结束！{winner}")
                            print(f" 游戏结束！{winner}")
                            send_game_over_event(winner)
                        self.game_ended = True
                        return

    def _force_lose(self):
        """强制失败：杀死主角（主公/忠臣）"""
        print("[Debug] 执行一键失败...")
        for p in self.player_controller.players:
            if p.identity in [PlayerIdentity.LORD, PlayerIdentity.LOYALIST]:
                if p.is_alive():
                    print(f"[Debug] 处决 {p.name}")
                    p.current_hp = 0
                    p.die()
                    if self.player_controller.game_over():
                        winner = self.player_controller.get_winner()
                        if winner:
                            game_logger.log_info(f" 游戏结束！{winner}")
                            print(f" 游戏结束！{winner}")
                            send_game_over_event(winner)
                        self.game_ended = True
                        return

    def start_game(self) -> None:
        """开始游戏主循环"""
        # 如果还没有初始化，则初始化
        if self.player_controller is None:
            self.initialize()
        
        # 检查所有玩家是否已有初始手牌，如果没有则发牌（确保只发一次）
        for player in self.player_controller.players:
            if player.deck is not None and len(player.hand_cards) == 0:
                player._draw_initial_cards()
        
        game_logger.log_info("游戏主循环开始")
        
        # 主循环
        turn_number = 1
        max_turns = 1000  # 防止无限循环
        while not self.game_ended and turn_number <= max_turns:
            # 检查调试事件
            self._check_debug_events()
            if self.game_ended:
                break

            current_player = self.player_controller.get_player(self.current_player_id)
            
            # 检查当前玩家是否有效
            if current_player is None:
                game_logger.log_error(f"当前玩家ID {self.current_player_id} 无效，强制结束游戏")
                self.game_ended = True
                break
            
            # 检查当前玩家是否存活
            if not current_player.is_alive():
                # 如果当前玩家已死亡，跳到下一个玩家
                self.current_player_id = self.player_controller.next_player(self.current_player_id)
                continue
            
            # 记录回合开始
            game_logger.log_turn_start(current_player.name, turn_number)
            
            # 记录所有玩家状态
            game_logger.log_all_players_status(self.player_controller.players)
            
            # 记录牌堆状态
            game_logger.log_deck_status(self.deck)
            
            # 准备阶段
            game_logger.log_phase_start(current_player.name, "准备")
            self.player_controller.event(self.current_player_id, GameEvent.PREPARE)
            # 同步状态
            self.player_controller.control_manager.sync_game_state()
            
            # 摸牌阶段
            game_logger.log_phase_start(current_player.name, "摸牌")
            self.player_controller.event(self.current_player_id, GameEvent.DRAW_CARD)
            # 同步状态（摸牌后状态变化）
            self.player_controller.control_manager.sync_player_state(self.current_player_id)
            
            # 出牌阶段
            game_logger.log_phase_start(current_player.name, "出牌")
            play_card_count = 0
            max_play_cards = 100  # 防止无限出牌
            while play_card_count < max_play_cards:
                card, targets = self.player_controller.event(
                    self.current_player_id, GameEvent.PLAY_CARD
                )
                if card is None:
                    break
                play_card_count += 1
                game_logger.log_info(f"玩家 {current_player.name} 打出牌: {card.name}")
                # 处理牌效果（预留接口）
                self._handle_card_effect(card, targets)
                # 同步状态（出牌后状态变化）
                self.player_controller.control_manager.sync_game_state()
                
                # 检查游戏是否在出牌过程中结束
                if self.player_controller.game_over():
                    self.game_ended = True
                    break
            
            # 弃牌阶段
            self.player_controller.event(self.current_player_id, GameEvent.DISCARD_CARD)
            # 同步状态（弃牌后状态变化）
            self.player_controller.control_manager.sync_player_state(self.current_player_id)
            
            # 记录回合结束
            game_logger.log_turn_end(current_player.name)
            
            # 检查游戏是否结束
            if self.player_controller.game_over():
                # 输出胜利方
                winner = self.player_controller.get_winner()
                if winner:
                    game_logger.log_info(f" 游戏结束！{winner}")
                    print(f" 游戏结束！{winner}")
                    send_game_over_event(winner)
                break
            
            # 检查调试事件（回合结束时也检查一次）
            self._check_debug_events()
            if self.game_ended:
                break

            # 检查是否还有存活玩家
            alive_players = [p for p in self.player_controller.players if p.is_alive()]
            if not alive_players:
                self.game_ended = True
                break
            
            # 下一个玩家
            next_player_id = self.player_controller.next_player(self.current_player_id)
            if next_player_id == self.current_player_id and len(alive_players) > 1:
                # 如果下一个玩家还是自己，说明有问题，强制结束
                game_logger.log_warning(f"next_player返回了相同的玩家ID: {next_player_id}，强制结束游戏")
                self.game_ended = True
                break
            self.current_player_id = next_player_id
            turn_number += 1
        
        if turn_number > max_turns:
            game_logger.log_error(f"游戏超过最大回合数 {max_turns}，强制结束")
            self.game_ended = True
        
        # 善后工作
        self._cleanup()
    
    def _handle_card_effect(self, card: Card, targets: list) -> None:
        """处理牌效果（使用策略模式）
        
        Args:
            card: 出的牌
            targets: 目标列表
        """
        # 使用工厂模式创建对应的处理器
        handler = CardEffectHandlerFactory.create_handler(card, self)
        if handler:
            handler.handle(card, targets)
            # 处理赵云的“冲阵”技能：如果出牌是通过龙胆转换（闪转杀/杀转闪）而来，且使用者为赵云2（第二章的赵云）
            try:
                from config.enums import CharacterName
                attacker = self.player_controller.get_player(self.current_player_id)
                if attacker and getattr(attacker, 'character_name', None) == CharacterName.ZHAO_YUN_2:
                    # card.converted_from 表示该卡是被龙胆转换过来的（如闪->杀或杀->闪）
                    if hasattr(card, 'converted_from') and card.converted_from is not None:
                        # 只对主要目标进行夺牌（如杀的目标或锦囊的指定目标）——使用 targets[0] 作为主目标
                        try:
                            if not targets:
                                return
                            primary_tid = targets[0]
                            target_player = self.player_controller.get_player(primary_tid)
                            if target_player and hasattr(target_player, 'hand_cards') and target_player.hand_cards:
                                # 询问操控者要夺取目标的哪张手牌（传入询问时的手牌数量快照）。
                                try:
                                    snapshot_count = len(target_player.hand_cards)
                                    idx = attacker.control.ask_steal_from_target(primary_tid, snapshot_count, context=f"通过冲阵从 玩家{primary_tid} 夺牌")
                                except Exception:
                                    idx = None
                                if idx is None:
                                    # 玩家选择不夺或发生错误，跳过夺牌但不中断后续流程
                                    pass
                                else:
                                    # 在询问期间目标手牌可能已变化，重新获取当前手牌数并调整索引
                                    current_count = len(target_player.hand_cards)
                                    if current_count <= 0:
                                        # 目标已无手牌，无法夺取
                                        pass
                                    else:
                                        # 如果索引超出当前范围，则使用当前最后一张
                                        if idx < 0:
                                            idx = 0
                                        if idx >= current_count:
                                            idx = current_count - 1
                                        stolen = target_player.hand_cards.pop(idx)
                                        attacker.hand_cards.append(stolen)
                                # 发送夺牌事件以便前端做动画（从目标玩家到攻击者）
                                try:
                                    from backend.utils.event_sender import send_steal_card_event
                                    send_steal_card_event(stolen, primary_tid, attacker.player_id)
                                except Exception:
                                    # 如果事件发送失败，也不阻塞游戏逻辑
                                    pass
                                game_logger.log_info(f"{attacker.name} 通过冲阵从 {target_player.name} 获得一张手牌 (index {idx})")
                        except Exception:
                            pass
            except Exception:
                # 不应阻塞游戏流程
                pass
        else:
            game_logger.log_warning(f"未知的牌类型或牌名: {card.name}")
    
    def _cleanup(self) -> None:
        """善后工作（回收内存等）"""
        # 预留接口，具体实现待补充
        pass
