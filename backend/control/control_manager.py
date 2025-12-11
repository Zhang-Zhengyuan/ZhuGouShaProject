# Control管理器模块
"""统一管理所有Control实例，负责事件分发和状态同步"""
from typing import Dict, List, Optional, TYPE_CHECKING
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.control import Control
from backend.utils.logger import game_logger
from communicator.comm_event import CommEvent, DrawCardEvent, PlayCardEvent, HPChangeEvent, DiscardCardEvent, EquipChangeEvent, DeathEvent

if TYPE_CHECKING:
    from backend.player.player import Player
    from backend.player_controller.player_controller import PlayerController


class ControlManager:
    """Control管理器
    
    统一管理所有Control实例，负责：
    1. 事件分发：将游戏事件分发给各个Control（根据可见性）
    2. 状态同步：定期同步场上状态给各个Control
    """
    
    def __init__(self, player_controller):
        """初始化ControlManager
        
        Args:
            player_controller: 玩家控制器引用（PlayerController类型）
        """
        self.player_controller = player_controller
        self.controls: Dict[int, Control] = {}  # player_id -> Control
        self._initialize_controls()
    
    def _initialize_controls(self) -> None:
        """初始化所有Control实例"""
        if not self.player_controller:
            return
        
        for player in self.player_controller.players:
            self.controls[player.player_id] = player.control
        game_logger.log_info(f"ControlManager初始化完成，管理 {len(self.controls)} 个Control实例")
    
    def notify_event(self, event: CommEvent) -> None:
        """通知所有Control关于游戏事件
        
        根据事件类型和可见性规则，将事件分发给相应的Control
        
        Args:
            event: 游戏事件
        """
        if not self.controls:
            return
        
        # 根据事件类型决定如何分发
        if isinstance(event, DrawCardEvent):
            # 摸牌事件：只有摸牌的玩家能看到牌面，其他玩家只能看到摸牌动作
            self._notify_draw_card(event)
        elif isinstance(event, PlayCardEvent):
            # 出牌事件：所有玩家都能看到（公开信息）
            self._notify_play_card(event)
        elif isinstance(event, HPChangeEvent):
            # 血量变化：所有玩家都能看到（公开信息）
            self._notify_hp_change(event)
        elif isinstance(event, DiscardCardEvent):
            # 弃牌事件：所有玩家都能看到（公开信息）
            self._notify_discard_card(event)
        elif isinstance(event, EquipChangeEvent):
            # 装备变化：所有玩家都能看到（公开信息）
            self._notify_equip_change(event)
        elif isinstance(event, DeathEvent):
            # 死亡事件：所有玩家都能看到（公开信息）
            self._notify_death(event)
    
    def _notify_draw_card(self, event: DrawCardEvent) -> None:
        """通知摸牌事件
        
        摸牌事件的可见性处理：只有摸牌的玩家能看到牌面，其他玩家看不到牌面
        
        Args:
            event: 摸牌事件
        """
        for player_id, control in self.controls.items():
            if player_id == event.to_player:
                # 摸牌的玩家能看到完整事件（包含牌面信息）
                control.on_event(event)
            else:
                # 其他玩家只能看到摸牌动作（不包含牌面信息）
                # 创建一个不包含牌面信息的事件副本
                hidden_event = DrawCardEvent(
                    card_config=None,  # 牌面信息设为None，表示不可见
                    to_player=event.to_player
                )
                control.on_event(hidden_event)
    
    def _notify_play_card(self, event: PlayCardEvent) -> None:
        """通知出牌事件
        
        Args:
            event: 出牌事件
        """
        # 出牌是公开信息，所有Control都能看到
        for control in self.controls.values():
            control.on_event(event)
    
    def _notify_hp_change(self, event: HPChangeEvent) -> None:
        """通知血量变化事件
        
        Args:
            event: 血量变化事件
        """
        # 血量是公开信息，所有Control都能看到
        for control in self.controls.values():
            control.on_event(event)
    
    def _notify_discard_card(self, event: DiscardCardEvent) -> None:
        """通知弃牌事件
        
        Args:
            event: 弃牌事件
        """
        # 弃牌是公开信息，所有Control都能看到
        for control in self.controls.values():
            control.on_event(event)
    
    def _notify_equip_change(self, event: EquipChangeEvent) -> None:
        """通知装备变化事件
        
        Args:
            event: 装备变化事件
        """
        # 装备是公开信息，所有Control都能看到
        for control in self.controls.values():
            control.on_event(event)
    
    def _notify_death(self, event: DeathEvent) -> None:
        """通知死亡事件
        
        Args:
            event: 死亡事件
        """
        # 死亡是公开信息，所有Control都能看到
        for control in self.controls.values():
            control.on_event(event)
    
    def sync_game_state(self) -> None:
        """同步场上状态给所有Control
        
        定期调用此方法，将当前游戏状态同步给所有Control
        每个Control只能看到自己玩家的完整信息和场上公开信息
        """
        if not self.player_controller:
            return
        
        for player_id, control in self.controls.items():
            # 获取该玩家能看到的状态
            visible_state = self._get_visible_state(player_id)
            control.sync_state(visible_state)
    
    def sync_player_state(self, player_id: int) -> None:
        """同步单个玩家的状态给其Control
        
        Args:
            player_id: 玩家ID
        """
        if player_id not in self.controls:
            return
        
        control = self.controls[player_id]
        visible_state = self._get_visible_state(player_id)
        control.sync_state(visible_state)
    
    def _get_visible_state(self, player_id: int) -> Dict:
        """获取指定玩家能看到的状态
        
        Args:
            player_id: 玩家ID
            
        Returns:
            可见状态字典，包含：
            - self: 自己的完整信息（手牌、装备等）
            - players: 其他玩家的公开信息（血量、装备、手牌数量等）
            - deck_size: 牌堆剩余数量
            - discard_pile_size: 弃牌堆数量
        """
        if not self.player_controller:
            return {}
        
        player = self.player_controller.get_player(player_id)
        if not player:
            return {}
        
        # 自己的完整信息
        self_info = {
            "player_id": player.player_id,
            "name": player.name,
            "identity": player.identity.value if player.identity else None,
            "character": player.character_name.value if player.character_name else None,
            "max_hp": player.max_hp,
            "current_hp": player.current_hp,
            "status": player.status.value if player.status else None,
            "hand_cards": [self._card_to_dict(card) for card in player.hand_cards],  # 完整手牌信息
            "hand_count": len(player.hand_cards),
            "weapon": self._card_to_dict(player.weapon) if player.weapon else None,
            "armor": self._card_to_dict(player.armor) if player.armor else None,
            "horse_plus": self._card_to_dict(player.horse_plus) if player.horse_plus else None,
            "horse_minus": self._card_to_dict(player.horse_minus) if player.horse_minus else None,
        }
        
        # 其他玩家的公开信息
        players_info = []
        for other_player in self.player_controller.players:
            if other_player.player_id == player_id:
                continue
            
            # 其他玩家只能看到公开信息
            players_info.append({
                "player_id": other_player.player_id,
                "name": other_player.name,
                "identity": other_player.identity.value if other_player.identity else None,
                "character": other_player.character_name.value if other_player.character_name else None,
                "max_hp": other_player.max_hp,
                "current_hp": other_player.current_hp,
                "status": other_player.status.value if other_player.status else None,
                "hand_count": len(other_player.hand_cards),  # 只能看到手牌数量，不能看到具体牌
                "weapon": self._card_to_dict(other_player.weapon) if other_player.weapon else None,
                "armor": self._card_to_dict(other_player.armor) if other_player.armor else None,
                "horse_plus": self._card_to_dict(other_player.horse_plus) if other_player.horse_plus else None,
                "horse_minus": self._card_to_dict(other_player.horse_minus) if other_player.horse_minus else None,
            })
        
        # 牌堆信息
        deck = self.player_controller.deck
        deck_info = {
            "deck_size": len(deck.cards) if deck else 0,
            "discard_pile_size": len(deck.discard_pile) if deck else 0,
        }
        
        return {
            "self": self_info,
            "players": players_info,
            "deck": deck_info,
        }
    
    def _card_to_dict(self, card) -> Optional[Dict]:
        """将Card对象转换为字典（用于状态同步）
        
        Args:
            card: Card对象
            
        Returns:
            字典表示，如果card为None则返回None
        """
        if card is None:
            return None
        
        return {
            "name": card.name_enum.value if hasattr(card.name_enum, 'value') else str(card.name_enum),
            "suit": card.suit.value if hasattr(card.suit, 'value') else str(card.suit),
            "rank": card.rank,
        }

