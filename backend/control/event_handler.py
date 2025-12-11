# 事件处理器模块（策略模式）
"""定义各种事件处理器的接口和实现"""
from abc import ABC, abstractmethod
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from communicator.comm_event import CommEvent, DrawCardEvent, PlayCardEvent, HPChangeEvent, DiscardCardEvent, EquipChangeEvent, DeathEvent
from backend.utils.logger import game_logger


class EventHandler(ABC):
    """事件处理器基类（策略接口）"""
    
    @abstractmethod
    def handle(self, event: CommEvent, player_id: Optional[int] = None) -> None:
        """处理事件
        
        Args:
            event: 游戏事件
            player_id: 关联的玩家ID（可选）
        """
        pass


class DrawCardEventHandler(EventHandler):
    """摸牌事件处理器"""
    
    def handle(self, event: DrawCardEvent, player_id: Optional[int] = None) -> None:
        """处理摸牌事件
        
        Args:
            event: 摸牌事件
            player_id: 关联的玩家ID
        """
        if player_id == event.to_player:
            # 摸牌的玩家能看到牌面信息
            game_logger.log_debug(f"Control (玩家{player_id}) 收到摸牌事件: 牌={event.card_config.name if event.card_config else None}")
        else:
            # 其他玩家只能看到摸牌动作（看不到牌面）
            game_logger.log_debug(f"Control (玩家{player_id}) 收到摸牌事件: 玩家{event.to_player}摸牌（看不到牌面）")


class PlayCardEventHandler(EventHandler):
    """出牌事件处理器"""
    
    def handle(self, event: PlayCardEvent, player_id: Optional[int] = None) -> None:
        """处理出牌事件
        
        Args:
            event: 出牌事件
            player_id: 关联的玩家ID
        """
        game_logger.log_debug(f"Control (玩家{player_id}) 收到出牌事件: 玩家{event.from_player}对玩家{event.to_player}使用{event.card_config.name if event.card_config else None}")


class HPChangeEventHandler(EventHandler):
    """血量变化事件处理器"""
    
    def handle(self, event: HPChangeEvent, player_id: Optional[int] = None) -> None:
        """处理血量变化事件
        
        Args:
            event: 血量变化事件
            player_id: 关联的玩家ID
        """
        game_logger.log_debug(f"Control (玩家{player_id}) 收到血量变化事件: 玩家{event.player_id}血量变为{event.new_hp}")


class DiscardCardEventHandler(EventHandler):
    """弃牌事件处理器"""
    
    def handle(self, event: DiscardCardEvent, player_id: Optional[int] = None) -> None:
        """处理弃牌事件
        
        Args:
            event: 弃牌事件
            player_id: 关联的玩家ID
        """
        game_logger.log_debug(f"Control (玩家{player_id}) 收到弃牌事件: 玩家{event.player}弃掉{event.card_config.name if event.card_config else None}")


class EquipChangeEventHandler(EventHandler):
    """装备变化事件处理器"""
    
    def handle(self, event: EquipChangeEvent, player_id: Optional[int] = None) -> None:
        """处理装备变化事件
        
        Args:
            event: 装备变化事件
            player_id: 关联的玩家ID
        """
        game_logger.log_debug(f"Control (玩家{player_id}) 收到装备变化事件: 玩家{event.player_id}装备变化 - {event.equip_name.value if hasattr(event.equip_name, 'value') else event.equip_name}")


class DeathEventHandler(EventHandler):
    """死亡事件处理器"""
    
    def handle(self, event: DeathEvent, player_id: Optional[int] = None) -> None:
        """处理死亡事件
        
        Args:
            event: 死亡事件
            player_id: 关联的玩家ID
        """
        game_logger.log_debug(f"Control (玩家{player_id}) 收到死亡事件: 玩家{event.player_id}死亡")


class DefaultEventHandler(EventHandler):
    """默认事件处理器（处理未知类型的事件）"""
    
    def handle(self, event: CommEvent, player_id: Optional[int] = None) -> None:
        """处理未知类型的事件
        
        Args:
            event: 游戏事件
            player_id: 关联的玩家ID
        """
        event_type = type(event).__name__
        game_logger.log_debug(f"Control (玩家{player_id}) 收到未知事件: {event_type}")

