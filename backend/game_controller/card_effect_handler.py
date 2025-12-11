# 牌效果处理器模块
"""使用策略模式处理各种牌的效果"""
from abc import ABC, abstractmethod
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.card.card import Card
from backend.player_controller.player_controller import PlayerController
from backend.deck.deck import Deck
from backend.utils.logger import game_logger
from backend.utils.event_sender import send_play_card_event
from config.enums import CardName, CardType, GameEvent, CardSuit, CharacterName


class CardEffectHandler(ABC):
    """牌效果处理器基类（策略模式）"""
    
    def __init__(self, game_controller):
        """初始化处理器
        
        Args:
            game_controller: 游戏控制器引用
        """
        self.game_controller = game_controller
        self.player_controller = game_controller.player_controller
        self.deck = game_controller.deck
        self.current_player_id = game_controller.current_player_id
    
    @abstractmethod
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理牌效果
        
        Args:
            card: 出的牌
            targets: 目标列表
        """
        pass
    
    def _handle_dying_process(self, dying_player_id: int) -> None:
        """处理濒死状态（辅助方法）
        
        规则：
        - 如果濒死的是自己，且有桃，应该使用桃（自救）
        - 别人濒死一定不救
        
        Args:
            dying_player_id: 濒死玩家ID
        """
        dying_player = self.player_controller.get_player(dying_player_id)
        if dying_player is None or dying_player.current_hp > 0:
            return
        
        # 先检查濒死玩家自己是否有桃（自救）
        tao_card = dying_player.ask_use_tao(f"自救（濒死状态）")
        
        if tao_card is not None:
            # 濒死玩家自己使用桃自救
            game_logger.log_info(f"{dying_player.name} 使用 桃 自救")
            # 发送出牌事件：濒死玩家对自己使用桃
            send_play_card_event(tao_card, dying_player_id, [dying_player_id])
            # 使用桃，濒死玩家回复1点血量
            self.player_controller.event(dying_player_id, GameEvent.HEAL, heal=1)
            # 桃进入弃牌堆
            self.deck.discard_card(tao_card)
            return
        
        # 如果濒死玩家自己没有桃，别人濒死一定不救，直接死亡
        # 不再询问其他玩家
        self.player_controller.event(dying_player_id, GameEvent.DEATH)
        
        # 玩家死亡后立即检查游戏是否结束
        if self.player_controller.game_over():
            self.game_controller.game_ended = True
    
    def _ask_wu_xie_ke_ji(self, original_card: Card, target_player_id: int, 
                          user_player_id: int, is_effective: bool = True) -> bool:
        """询问无懈可击（辅助方法）
        
        规则：
        - 从使用锦囊的玩家（user_player_id）开始按顺时针顺序询问
        - 无懈别人的无懈时，从使用那张无懈的玩家开始查询
        
        Args:
            original_card: 原始锦囊牌
            target_player_id: 目标玩家ID（需要使用无懈可击的玩家）
            user_player_id: 使用锦囊牌的玩家ID（或使用无懈的玩家ID）
            is_effective: 当前是否生效
            
        Returns:
            bool: 最终是否生效
        """
        # 获取所有存活玩家，从使用锦囊的玩家（或使用无懈的玩家）开始按顺时针顺序询问
        alive_players = [p for p in self.player_controller.players if p.is_alive()]
        if not alive_players:
            return is_effective
        
        # 找到使用锦囊的玩家（或使用无懈的玩家）在存活玩家中的位置
        user_index = -1
        for i, player in enumerate(alive_players):
            if player.player_id == user_player_id:
                user_index = i
                break
        
        if user_index == -1:
            return is_effective
        
        # 从使用锦囊的玩家（或使用无懈的玩家）开始按顺时针顺序询问无懈可击
        for i in range(len(alive_players)):
            player_index = (user_index + i) % len(alive_players)
            player = alive_players[player_index]
            
            # 询问是否使用无懈可击
            user_player = self.player_controller.get_player(user_player_id)
            target_player = self.player_controller.get_player(target_player_id)
            context = f"{user_player.name if user_player else '玩家' + str(user_player_id)}使用的{original_card.name}对{target_player.name if target_player else '玩家' + str(target_player_id)}即将{'生效' if is_effective else '失效'}，是否使用无懈可击"
            wu_xie_card = player.ask_use_wu_xie_ke_ji(context)
            
            if wu_xie_card is not None:
                # 使用无懈可击，反转效果并递归询问
                # 递归时，从使用这张无懈的玩家（player.player_id）开始查询
                game_logger.log_player_use_card(player.name, "无懈可击")
                # 发送出牌事件：玩家对目标使用无懈可击（标注响应类型和是否生效）
                send_play_card_event(
                    wu_xie_card, player.player_id, [target_player_id],
                    response_type="响应无懈可击",
                    response_target=target_player_id,
                    original_card_name=original_card.name,
                    is_effective=is_effective
                )
                self.deck.discard_card(wu_xie_card)
                # 递归询问：从使用这张无懈的玩家（player.player_id）开始查询
                return self._ask_wu_xie_ke_ji(original_card, target_player_id, player.player_id, not is_effective)
        
        # 没有人使用无懈可击，返回当前效果
        return is_effective


class ShaCardHandler(CardEffectHandler):
    """杀牌效果处理器"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理杀牌效果"""
        if not targets:
            return
        
        target_id = targets[0]  # 杀只能指定一个目标
        target_player = self.player_controller.get_player(target_id)
        
        if target_player is None or not target_player.is_alive():
            return
        
        # 检查攻击者是否装备了青釭剑（无视防具）
        attacker_player = self.player_controller.get_player(self.current_player_id)
        ignore_armor = (attacker_player and 
                       attacker_player.weapon and 
                       attacker_player.weapon.name_enum == CardName.QING_GANG_JIAN)
        
        # 检查仁王盾效果：黑色杀直接无效（除非青釭剑无视防具）
        if (not ignore_armor and
            target_player.armor and 
            target_player.armor.name_enum == CardName.REN_WANG_DUN and 
            card.suit in [CardSuit.SPADES, CardSuit.CLUBS]):  # 黑色花色
            # 黑色杀对仁王盾无效，杀进入弃牌堆
            game_logger.log_card_effect("仁王盾", f"黑色杀对 {target_player.name} 无效")
            self.deck.discard_card(card)
            return
        
        # 询问目标是否使用闪（青釭剑仍然可以闪）
        attacker_player = self.player_controller.get_player(self.current_player_id)
        context = f"受到{attacker_player.name if attacker_player else '玩家' + str(self.current_player_id)}的杀攻击，是否使用闪"
        shan_card = target_player.ask_use_shan(context)
        
        if shan_card is not None:
            # 使用闪，将杀和闪都进入弃牌堆
            game_logger.log_player_use_card(target_player.name, "闪")
            # 发送出牌事件：目标玩家对自己使用闪（标注响应类型）
            # 如果目标是赵云并且使用的牌实际上是杀（龙胆将杀当闪响应），告诉前端用特殊展示牌
            conversion_display = None
            try:
                if target_player and getattr(target_player, 'character_name', None) == CharacterName.ZHAO_YUN_1 and getattr(shan_card, 'name_enum', None) == CardName.SHA:
                    # 用一个与杀/闪不同的卡牌来展示
                    conversion_display = CardName.SHA_TO_SHAN
            except Exception:
                conversion_display = None

            send_play_card_event(
                shan_card, target_player.player_id, [target_player.player_id],
                response_type="响应杀",
                response_target=self.current_player_id,
                original_card_name=card.name,
                conversion_display=conversion_display
            )
            self.deck.discard_card(card)
            self.deck.discard_card(shan_card)
            return
        
        # 不使用闪或青釭剑无视防具，目标受到1点伤害
        self.deck.discard_card(card)
        self.player_controller.event(
            target_id, GameEvent.DAMAGE, 
            damage=1, 
            source_player_id=self.current_player_id,
            damage_type="杀",
            original_card_name=card.name
        )
        
        # 检查目标是否进入濒死状态
        target_player = self.player_controller.get_player(target_id)
        if target_player and target_player.current_hp == 0:
            self._handle_dying_process(target_id)
            # 检查游戏是否结束
            if self.game_controller.game_ended:
                return


class TaoCardHandler(CardEffectHandler):
    """桃牌效果处理器"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理桃牌效果"""
        if not targets:
            return
        
        target_id = targets[0]  # 桃只能指定一个目标
        target_player = self.player_controller.get_player(target_id)
        
        if target_player is None or not target_player.is_alive():
            return
        
        # 桃只能对自己使用
        if target_id != self.current_player_id:
            return
        
        # 回复1点血量
        self.player_controller.event(target_id, GameEvent.HEAL, heal=1)
        # 桃进入弃牌堆
        self.deck.discard_card(card)


class EquipmentCardHandler(CardEffectHandler):
    """装备牌效果处理器"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理装备牌效果"""
        if not targets:
            return
        
        target_id = targets[0]  # 装备只能指定一个目标
        target_player = self.player_controller.get_player(target_id)
        
        if target_player is None or not target_player.is_alive():
            return
        
        # 装备牌只能对自己使用
        if target_id != self.current_player_id:
            return
        
        # 装备牌
        self.player_controller.event(target_id, GameEvent.EQUIP, card=card)


class JueDouCardHandler(CardEffectHandler):
    """决斗牌效果处理器"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理决斗效果"""
        if not targets:
            return
        
        target_id = targets[0]  # 决斗只能指定一个目标
        target_player = self.player_controller.get_player(target_id)
        attacker_player = self.player_controller.get_player(self.current_player_id)
        
        if target_player is None or not target_player.is_alive() or attacker_player is None:
            return
        
        # 注意：决斗事件已经在player.py的play_card_default中发送了，这里不需要重复发送
        # 决斗本身不是响应类事件，使用log_player_play_card记录日志
        game_logger.log_player_play_card(attacker_player.name, "决斗", [target_player.player_id], [target_player.name])
        
        # 询问无懈可击（决斗可以被无懈可击抵消）
        is_effective = self._ask_wu_xie_ke_ji(card, target_id, attacker_player.player_id, is_effective=True)
        if not is_effective:
            # 被无懈可击抵消，决斗无效并弃置
            game_logger.log_info(f"决斗被无懈可击抵消")
            self.deck.discard_card(card)
            return
        
        # 从目标开始，交替询问是否使用杀
        current_attacker = target_player
        current_defender = attacker_player
        round_count = 0
        
        while True:
            round_count += 1
            game_logger.log_info(f"决斗第{round_count}轮：{current_attacker.name} 对 {current_defender.name}")
            
            # 询问当前攻击者是否使用杀（传递决斗上下文）
            context = f"响应决斗：{current_defender.name}对您使用决斗，决斗目标：{current_defender.player_id}，是否使用杀"
            sha_card = current_attacker.ask_use_sha(context)
            
            if sha_card is None:
                # 不使用杀，当前攻击者受到1点伤害
                self.player_controller.event(
                    current_attacker.player_id, GameEvent.DAMAGE, 
                    damage=1, 
                    source_player_id=current_defender.player_id,
                    damage_type="决斗",
                    original_card_name="决斗"
                )
                self.deck.discard_card(card)
                
                # 检查是否进入濒死状态
                if current_attacker.current_hp == 0:
                    self._handle_dying_process(current_attacker.player_id)
                    # 检查游戏是否结束
                    if self.game_controller.game_ended:
                        return
                return
            
            # 使用杀，将杀进入弃牌堆
            # 响应决斗的杀不指定目标，所以不传targets
            game_logger.log_player_use_card(current_attacker.name, "杀", None, None)
            # 发送出牌事件：攻击者对防御者使用杀（标注响应决斗，不指定目标）
            conversion_display = None
            try:
                if current_attacker and getattr(current_attacker, 'character_name', None) == CharacterName.ZHAO_YUN_1 and getattr(sha_card, 'name_enum', None) == CardName.SHAN:
                    # 赵云用闪当杀响应决斗，展示应为“闪转杀”
                    conversion_display = CardName.SHAN_TO_SHA
            except Exception:
                conversion_display = None

            send_play_card_event(
                sha_card, current_attacker.player_id, [],  # 响应决斗的杀不指定目标
                response_type="响应决斗",
                response_target=current_defender.player_id,
                original_card_name="决斗",
                conversion_display=conversion_display
            )
            self.deck.discard_card(sha_card)
            
            # 交换攻击者和防御者
            current_attacker, current_defender = current_defender, current_attacker


class NanManRuQinCardHandler(CardEffectHandler):
    """南蛮入侵牌效果处理器"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理南蛮入侵效果"""
        attacker_player = self.player_controller.get_player(self.current_player_id)
        if attacker_player is None:
            return
        
        game_logger.log_player_use_card(attacker_player.name, "南蛮入侵")
        
        # 获取所有存活玩家，从使用锦囊牌的玩家开始按顺时针顺序（不包括使用者）
        alive_players = [p for p in self.player_controller.players 
                        if p.is_alive() and p.player_id != self.current_player_id]
        if not alive_players:
            self.deck.discard_card(card)
            return
        
        # 找到使用锦囊牌的玩家在存活玩家中的位置
        user_index = -1
        for i, player in enumerate(self.player_controller.players):
            if player.player_id == self.current_player_id:
                user_index = i
                break
        
        if user_index == -1:
            user_index = 0
        
        # 从使用锦囊牌的玩家开始按顺时针顺序处理每个目标
        for i in range(len(self.player_controller.players)):
            player_index = (user_index + i) % len(self.player_controller.players)
            player = self.player_controller.players[player_index]
            
            # 跳过使用者和已死亡的玩家
            if player.player_id == self.current_player_id or not player.is_alive():
                continue
            
            # 进行无懈可击判定
            is_effective = self._ask_wu_xie_ke_ji(card, player.player_id, self.current_player_id, True)
            
            if not is_effective:
                game_logger.log_info(f"南蛮入侵对 {player.name} 被无懈可击")
                continue
            
            # 询问是否使用杀（传递南蛮入侵上下文）
            context = f"响应南蛮入侵：{attacker_player.name if attacker_player else '玩家' + str(self.current_player_id)}使用南蛮入侵，是否使用杀"
            sha_card = player.ask_use_sha(context)
            
            if sha_card is None:
                # 不使用杀，受到1点伤害
                self.player_controller.event(
                    player.player_id, GameEvent.DAMAGE, 
                    damage=1, 
                    source_player_id=self.current_player_id,
                    damage_type="南蛮入侵",
                    original_card_name="南蛮入侵"
                )
                
                # 检查是否进入濒死状态
                if player.current_hp == 0:
                    self._handle_dying_process(player.player_id)
                    
                    # 检查游戏是否结束
                    if self.player_controller.game_over():
                        self.game_controller.game_ended = True
                        return
            else:
                # 使用杀，将杀进入弃牌堆
                game_logger.log_player_use_card(player.name, "杀")
                # 发送出牌事件：玩家响应南蛮入侵使用杀（不指定目标）
                conversion_display = None
                original_card_name = None
                try:
                    # 检查是否是赵云的龙胆转化：闪转杀
                    if player and getattr(player, 'character_name', None) in [CharacterName.ZHAO_YUN_1, CharacterName.ZHAO_YUN_2]:
                        if hasattr(sha_card, 'converted_from') and sha_card.converted_from == CardName.SHAN:
                            # 赵云用闪当杀响应，展示应为"闪转杀"
                            conversion_display = CardName.SHAN_TO_SHA
                            original_card_name = CardName.SHAN
                except Exception:
                    conversion_display = None

                send_play_card_event(
                    sha_card, player.player_id, [],  # 响应南蛮入侵的杀不指定目标
                    response_type="响应南蛮入侵",
                    response_target=self.current_player_id,
                    original_card_name=original_card_name,
                    conversion_display=conversion_display
                )
                self.deck.discard_card(sha_card)
        
        # 南蛮入侵进入弃牌堆
        self.deck.discard_card(card)


class WanJianQiFaCardHandler(CardEffectHandler):
    """万箭齐发牌效果处理器"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理万箭齐发效果"""
        attacker_player = self.player_controller.get_player(self.current_player_id)
        if attacker_player is None:
            return
        
        game_logger.log_player_use_card(attacker_player.name, "万箭齐发")
        
        # 获取所有存活玩家，从使用锦囊牌的玩家开始按顺时针顺序（不包括使用者）
        alive_players = [p for p in self.player_controller.players 
                        if p.is_alive() and p.player_id != self.current_player_id]
        if not alive_players:
            self.deck.discard_card(card)
            return
        
        # 找到使用锦囊牌的玩家在存活玩家中的位置
        user_index = -1
        for i, player in enumerate(self.player_controller.players):
            if player.player_id == self.current_player_id:
                user_index = i
                break
        
        if user_index == -1:
            user_index = 0
        
        # 从使用锦囊牌的玩家开始按顺时针顺序处理每个目标
        for i in range(len(self.player_controller.players)):
            player_index = (user_index + i) % len(self.player_controller.players)
            player = self.player_controller.players[player_index]
            
            # 跳过使用者和已死亡的玩家
            if player.player_id == self.current_player_id or not player.is_alive():
                continue
            
            # 进行无懈可击判定
            is_effective = self._ask_wu_xie_ke_ji(card, player.player_id, self.current_player_id, True)
            
            if not is_effective:
                game_logger.log_info(f"万箭齐发对 {player.name} 被无懈可击")
                continue
            
            # 询问是否使用闪（传递万箭齐发上下文）
            context = f"响应万箭齐发：{attacker_player.name if attacker_player else '玩家' + str(self.current_player_id)}使用万箭齐发，是否使用闪"
            shan_card = player.ask_use_shan(context)
            
            if shan_card is None:
                # 不使用闪，受到1点伤害
                self.player_controller.event(
                    player.player_id, GameEvent.DAMAGE, 
                    damage=1, 
                    source_player_id=self.current_player_id,
                    damage_type="万箭齐发",
                    original_card_name="万箭齐发"
                )
                
                # 检查是否进入濒死状态
                if player.current_hp == 0:
                    self._handle_dying_process(player.player_id)
                    
                    # 检查游戏是否结束
                    if self.player_controller.game_over():
                        self.game_controller.game_ended = True
                        return
            else:
                # 使用闪，将闪进入弃牌堆
                game_logger.log_player_use_card(player.name, "闪")
                # 发送出牌事件：玩家响应万箭齐发使用闪（发送到[-1]表示在中心显示）
                conversion_display = None
                original_card_name = None
                try:
                    # 检查是否是赵云的龙胆转化：杀转闪
                    if player and getattr(player, 'character_name', None) in [CharacterName.ZHAO_YUN_1, CharacterName.ZHAO_YUN_2]:
                        if hasattr(shan_card, 'converted_from') and shan_card.converted_from == CardName.SHA:
                            # 赵云用杀当闪响应，展示应为"杀转闪"
                            conversion_display = CardName.SHA_TO_SHAN
                            original_card_name = CardName.SHA
                except Exception:
                    conversion_display = None

                send_play_card_event(
                    shan_card, player.player_id, [],  # 响应万箭齐发的闪发送到[-1]（在event_sender中自动处理）
                    response_type="响应万箭齐发",
                    response_target=self.current_player_id,
                    original_card_name=original_card_name,
                    conversion_display=conversion_display
                )
                self.deck.discard_card(shan_card)
        
        # 万箭齐发进入弃牌堆
        self.deck.discard_card(card)


class WuXieKeJiCardHandler(CardEffectHandler):
    """无懈可击牌效果处理器（不应该通过这里处理）"""
    
    def handle(self, card: Card, targets: List[int]) -> None:
        """无懈可击不应该通过这里处理，应该通过无懈可击询问机制处理"""
        return


class CardEffectHandlerFactory:
    """牌效果处理器工厂（工厂模式）"""
    
    @staticmethod
    def create_handler(card: Card, game_controller) -> CardEffectHandler:
        """根据牌类型创建对应的处理器
        
        Args:
            card: 牌对象
            game_controller: 游戏控制器
            
        Returns:
            对应的牌效果处理器
        """
        # 根据牌名创建处理器
        if card.name_enum == CardName.SHA:
            return ShaCardHandler(game_controller)
        elif card.name_enum == CardName.TAO:
            return TaoCardHandler(game_controller)
        elif card.name_enum == CardName.JUE_DOU:
            return JueDouCardHandler(game_controller)
        elif card.name_enum == CardName.NAN_MAN_RU_QIN:
            return NanManRuQinCardHandler(game_controller)
        elif card.name_enum == CardName.WAN_JIAN_QI_FA:
            return WanJianQiFaCardHandler(game_controller)
        elif card.name_enum == CardName.WU_XIE_KE_JI:
            return WuXieKeJiCardHandler(game_controller)
        # 根据牌类型创建处理器
        elif card.card_type == CardType.EQUIPMENT:
            return EquipmentCardHandler(game_controller)
        elif card.card_type == CardType.TRICK:
            # 如果是不认识的锦囊牌，返回None（不应该发生）
            return None
        else:
            # 未知牌类型，返回None
            return None

