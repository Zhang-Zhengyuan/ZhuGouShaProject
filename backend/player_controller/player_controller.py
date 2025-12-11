# 玩家控制模块
from typing import Dict, Any, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.player.player import Player
from backend.deck.deck import Deck
from backend.utils.logger import game_logger
from backend.player_controller.player_factory import PlayerFactory
from backend.control.control_manager import ControlManager
from backend.utils.event_sender import set_control_manager
from config.enums import GameEvent, ControlType, PlayerIdentity, CharacterName, TargetType


class PlayerController:
    """玩家控制模块
    
    管理所有玩家和玩家相关操作
    """
    
    def __init__(self, config, deck: Deck):
        """初始化函数
        
        Args:
            config: 配置信息（可以是字典或GameConfig对象）
            deck: 牌堆
        """
        self.config = config
        self.deck = deck
        self.players: List[Player] = []
        self._initialize_players()
        
        # 创建ControlManager并注册到event_sender
        self.control_manager = ControlManager(self)
        set_control_manager(self.control_manager)
        
        # 初始化时同步一次状态
        self.control_manager.sync_game_state()
    
    def _initialize_players(self) -> None:
        """根据配置信息生成玩家列表"""
        game_logger.log_info("开始初始化玩家...")
        players_config = self.config.players_config
        for player_id, player_config in enumerate(players_config):
            # 使用工厂模式创建玩家实例
            # player_config 是 SimplePlayerConfig 对象，直接使用其属性
            player = PlayerFactory.create_player(
                player_id=player_id,
                name=player_config.name,
                control_type=player_config.control_type,
                deck=self.deck,
                character_name=player_config.character_name,
                identity=player_config.identity,
                player_controller=self
            )
            game_logger.log_info(
                f"创建玩家 {player_id}: {player_config.name} "
                f"(身份: {player_config.identity.value}, "
                f"武将: {player_config.character_name.value}, "
                f"血量: {player.max_hp})"
            )
            self.players.append(player)
    
    def event(self, player_id: int, event: GameEvent, **kwargs) -> Any:
        """处理玩家事件
        
        Args:
            player_id: 玩家ID
            event: 事件类型
            **kwargs: 事件参数
            
        Returns:
            事件处理结果
        """
        player = self.get_player(player_id)
        if player is None:
            return None
        
        if event == GameEvent.PREPARE:
            return player.reset_turn_state()
        elif event == GameEvent.DRAW_CARD:
            return player.draw_card_phase()
        elif event == GameEvent.PLAY_CARD:
            # 出牌时先获取目标信息
            targets = self.get_targets(player_id)
            return player.play_card(targets)
        elif event == GameEvent.DISCARD_CARD:
            return player.discard_card()
        elif event == GameEvent.DAMAGE:
            return player.take_damage(
                kwargs.get("damage", 1), 
                kwargs.get("source_player_id"),
                kwargs.get("damage_type"),
                kwargs.get("original_card_name")
            )
        elif event == GameEvent.HEAL:
            return player.heal(kwargs.get("heal", 1))
        elif event == GameEvent.DEATH:
            return player.die()
        elif event == GameEvent.EQUIP:
            return player.equip(kwargs.get("card"))
        
        return None
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """获取指定ID的玩家
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家对象或None
        """
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None
    
    def next_player(self, current_player_id: int) -> int:
        """获取下一个玩家
        
        Args:
            current_player_id: 当前玩家ID
            
        Returns:
            下一个玩家ID
        """
        alive_players = [p for p in self.players if p.is_alive()]
        if not alive_players:
            return current_player_id
        
        current_index = -1
        for i, player in enumerate(alive_players):
            if player.player_id == current_player_id:
                current_index = i
                break
        
        if current_index == -1:
            return alive_players[0].player_id
        
        next_index = (current_index + 1) % len(alive_players)
        return alive_players[next_index].player_id
    
    def game_over(self) -> bool:
        """判断游戏是否结束
        
        Returns:
            游戏是否结束
        """
        alive_players = [p for p in self.players if p.is_alive()]
        
        # 如果只剩一个玩家，游戏结束
        if len(alive_players) <= 1:
            return True
        
        # 检查主公是否死亡（反贼胜利条件）
        lord = self.get_lord()
        if lord and not lord.is_alive():
            return True
        
        # 检查主公是否存活，且反贼和内奸都全部死亡（主公胜利条件）
        if lord and lord.is_alive():
            alive_rebels = [p for p in self.players if p.identity == PlayerIdentity.REBEL and p.is_alive()]
            alive_traitors = [p for p in self.players if p.identity == PlayerIdentity.TRAITOR and p.is_alive()]
            if not alive_rebels and not alive_traitors:
                return True
        
        return False
    
    def get_lord(self) -> Optional[Player]:
        """获取主公玩家
        
        Returns:
            主公玩家对象，如果没有则返回None
        """
        for player in self.players:
            if player.identity == PlayerIdentity.LORD:
                return player
        return None
    
    def _check_lord_victory(self) -> bool:
        """检查主公胜利条件
        
        Returns:
            是否满足主公胜利条件
        """
        lord = self.get_lord()
        if not lord or not lord.is_alive():
            return False
        
        # 检查忠臣是否全部存活
        loyalists = [p for p in self.players if p.identity == PlayerIdentity.LOYALIST and p.is_alive()]
        if not loyalists:
            return False
        
        # 检查反贼是否全部死亡
        rebels = [p for p in self.players if p.identity == PlayerIdentity.REBEL and p.is_alive()]
        if rebels:
            return False
        
        # 检查内奸是否全部死亡
        traitors = [p for p in self.players if p.identity == PlayerIdentity.TRAITOR and p.is_alive()]
        if traitors:
            return False
        
        return True
    
    def get_winner(self) -> Optional[str]:
        """获取胜利方
        
        Returns:
            胜利方名称，如果游戏未结束则返回None
        """
        if not self.game_over():
            return None
        
        alive_players = [p for p in self.players if p.is_alive()]
        
        # 1. 如果最后只剩一个人且为内奸，则该内奸获胜
        if len(alive_players) == 1:
            winner = alive_players[0]
            if winner.identity == PlayerIdentity.TRAITOR:
                return f"内奸胜利 - {winner.name}"
        
        # 2. 如果主公死亡，则所有反贼获胜
        lord = self.get_lord()
        if lord and not lord.is_alive():
            rebels = [p for p in self.players if p.identity == PlayerIdentity.REBEL]
            return f"反贼胜利 - {', '.join([p.name for p in rebels])}"
        
        # 3. 如果只剩主公或主公和忠臣（反贼和内奸都死了），则主公和所有忠臣获胜
        # 检查主公是否存活
        if lord and lord.is_alive():
            # 检查反贼是否全部死亡
            alive_rebels = [p for p in self.players if p.identity == PlayerIdentity.REBEL and p.is_alive()]
            # 检查内奸是否全部死亡
            alive_traitors = [p for p in self.players if p.identity == PlayerIdentity.TRAITOR and p.is_alive()]
            
            # 如果反贼和内奸都死了，则主公和所有忠臣获胜
            if not alive_rebels and not alive_traitors:
                loyalists = [p for p in self.players if p.identity == PlayerIdentity.LOYALIST]
                all_winners = [lord] + loyalists
                return f"主公，忠臣胜利 - {', '.join([p.name for p in all_winners])}"
        
        return "平局"
    
    def get_initial_player(self) -> int:
        """获取初始玩家ID
        
        Returns:
            初始玩家ID
        """
        if self.players:
            return self.players[0].player_id
        return 0
    
    def calculate_distance(self, from_player_id: int, to_player_id: int) -> int:
        """计算两个玩家之间的距离
        
        Args:
            from_player_id: 起始玩家ID
            to_player_id: 目标玩家ID
            
        Returns:
            两个玩家之间的距离
        """
        if from_player_id == to_player_id:
            return 1
        
        alive_players = [p for p in self.players if p.is_alive()]
        if len(alive_players) <= 1:
            return 0
        
        # 找到两个玩家在存活玩家列表中的位置
        from_index = -1
        to_index = -1
        for i, player in enumerate(alive_players):
            if player.player_id == from_player_id:
                from_index = i
            elif player.player_id == to_player_id:
                to_index = i
        
        if from_index == -1 or to_index == -1:
            return 0
        
        # 计算顺时针和逆时针距离，取较小值
        total_players = len(alive_players)
        clockwise_distance = (to_index - from_index) % total_players
        counterclockwise_distance = (from_index - to_index) % total_players
        
        base_distance = min(clockwise_distance, counterclockwise_distance)
        
        # 应用马的效果
        from_player = self.get_player(from_player_id)
        to_player = self.get_player(to_player_id)
        
        if from_player and to_player:
            # 攻击马（-1马）使距离-1
            if from_player.horse_minus:
                base_distance = max(1, base_distance - 1)
            
            # 防御马（+1马）使距离+1
            if to_player.horse_plus:
                base_distance += 1
        
        # 距离最小是1
        return max(1, base_distance)
    
    def get_attack_range(self, player_id: int) -> int:
        """获取玩家的攻击距离
        
        Args:
            player_id: 玩家ID
            
        Returns:
            攻击距离
        """
        player = self.get_player(player_id)
        if not player:
            return 1
        
        # 基础攻击距离为1
        attack_range = 1
        
        # 如果有武器，增加攻击距离
        if player.weapon:
            attack_range = player.weapon.attack_range
        
        return attack_range
    
    def get_targets(self, player_id: int) -> Dict[str, List[int]]:
        """获取目标列表
        
        Args:
            player_id: 玩家ID
            
        Returns:
            目标字典，包含attackable、all、dis1等键
        """
        alive_players = [p for p in self.players if p.is_alive() and p.player_id != player_id]
        player_ids = [p.player_id for p in alive_players]
        
        # 获取攻击距离
        attack_range = self.get_attack_range(player_id)
        
        # 计算攻击距离内的目标（确保不包含自己）
        attackable_targets = []
        for target_id in player_ids:
            if target_id == player_id:  # 确保不包含自己
                continue
            distance = self.calculate_distance(player_id, target_id)
            if distance <= attack_range:
                attackable_targets.append(target_id)
        
        # 计算距离为1的目标（确保不包含自己）
        distance_1_targets = []
        for target_id in player_ids:
            if target_id == player_id:  # 确保不包含自己
                continue
            distance = self.calculate_distance(player_id, target_id)
            if distance == 1:
                distance_1_targets.append(target_id)
        
        # WARNING: 现在的ALL是不包含自己的
        return {
            "attackable": attackable_targets,  # 攻击距离内的目标
            "all": player_ids,  # 所有活着的目标
            "dis1": distance_1_targets,  # 距离为1的目标
            "self": [player_id]  # 自己
        }
    
    def generate_briefing(self, player_id: int) -> Dict[str, Any]:
        """生成简报（预留接口）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            简报字典
        """
        # 预留接口，暂时不实现
        return {}
    
    def get_player_identity(self, player_id: int) -> Optional[PlayerIdentity]:
        """获取玩家身份
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家身份或None
        """
        player = self.get_player(player_id)
        return player.identity if player else None
    
    def get_players_by_identity(self, identity: PlayerIdentity) -> List[Player]:
        """根据身份获取玩家列表
        
        Args:
            identity: 身份类型
            
        Returns:
            该身份的所有玩家列表
        """
        return [player for player in self.players if player.identity == identity and player.is_alive()]
    
    
    def get_loyalists(self) -> List[Player]:
        """获取所有忠臣
        
        Returns:
            忠臣玩家列表
        """
        return self.get_players_by_identity(PlayerIdentity.LOYALIST)
    
    def get_rebels(self) -> List[Player]:
        """获取所有反贼
        
        Returns:
            反贼玩家列表
        """
        return self.get_players_by_identity(PlayerIdentity.REBEL)
    
    def get_traitor(self) -> Optional[Player]:
        """获取内奸
        
        Returns:
            内奸玩家或None
        """
        traitors = self.get_players_by_identity(PlayerIdentity.TRAITOR)
        return traitors[0] if traitors else None
