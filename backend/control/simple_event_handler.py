# SimpleControl专用事件处理器模块
"""为SimpleControl提供能够更新内部状态的事件处理器"""
from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.event_handler import EventHandler
from communicator.comm_event import CommEvent, DrawCardEvent, PlayCardEvent, HPChangeEvent, DiscardCardEvent, EquipChangeEvent, DeathEvent
from backend.utils.logger import game_logger


class SimpleDrawCardEventHandler(EventHandler):
    """SimpleControl的摸牌事件处理器
    
    更新内部状态：记录玩家手牌数量变化
    """
    
    def __init__(self, state: Dict[str, Any]):
        """初始化处理器
        
        Args:
            state: SimpleControl的内部状态字典
        """
        self.state = state
    
    def handle(self, event: DrawCardEvent, player_id: Optional[int] = None) -> None:
        """处理摸牌事件
        
        Args:
            event: 摸牌事件
            player_id: 关联的玩家ID
        """
        if player_id == event.to_player:
            # 自己摸牌：更新自己的手牌数量（+1）
            if "self" not in self.state:
                self.state["self"] = {}
            self.state["self"]["hand_count"] = self.state["self"].get("hand_count", 0) + 1
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 自己摸牌，手牌数量+1")
        else:
            # 其他玩家摸牌：更新其他玩家的手牌数量（+1）
            if "players" not in self.state:
                self.state["players"] = {}
            if event.to_player not in self.state["players"]:
                self.state["players"][event.to_player] = {}
            self.state["players"][event.to_player]["hand_count"] = \
                self.state["players"][event.to_player].get("hand_count", 0) + 1
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 玩家{event.to_player}摸牌，手牌数量+1")


class SimplePlayCardEventHandler(EventHandler):
    """SimpleControl的出牌事件处理器
    
    更新内部状态：记录玩家出牌信息，更新手牌数量
    """
    
    def __init__(self, state: Dict[str, Any]):
        """初始化处理器
        
        Args:
            state: SimpleControl的内部状态字典
        """
        self.state = state
    
    def handle(self, event: PlayCardEvent, player_id: Optional[int] = None) -> None:
        """处理出牌事件
        
        Args:
            event: 出牌事件
            player_id: 关联的玩家ID
        """
        if player_id == event.from_player:
            # 自己出牌：更新自己的手牌数量（-1）
            if "self" not in self.state:
                self.state["self"] = {}
            self.state["self"]["hand_count"] = max(0, self.state["self"].get("hand_count", 0) - 1)
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 自己出牌，手牌数量-1")
        else:
            # 其他玩家出牌：更新其他玩家的手牌数量（-1）
            if "players" not in self.state:
                self.state["players"] = {}
            if event.from_player not in self.state["players"]:
                self.state["players"][event.from_player] = {}
            self.state["players"][event.from_player]["hand_count"] = \
                max(0, self.state["players"][event.from_player].get("hand_count", 0) - 1)
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 玩家{event.from_player}出牌，手牌数量-1")


class SimpleHPChangeEventHandler(EventHandler):
    """SimpleControl的血量变化事件处理器
    
    更新内部状态：记录玩家血量变化
    """
    
    def __init__(self, state: Dict[str, Any]):
        """初始化处理器
        
        Args:
            state: SimpleControl的内部状态字典
        """
        self.state = state
    
    def handle(self, event: HPChangeEvent, player_id: Optional[int] = None) -> None:
        """处理血量变化事件
        
        Args:
            event: 血量变化事件
            player_id: 关联的玩家ID
        """
        if player_id == event.player_id:
            # 自己血量变化：更新自己的血量
            if "self" not in self.state:
                self.state["self"] = {}
            self.state["self"]["current_hp"] = event.new_hp
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 自己血量变为{event.new_hp}")
        else:
            # 其他玩家血量变化：更新其他玩家的血量
            if "players" not in self.state:
                self.state["players"] = {}
            if event.player_id not in self.state["players"]:
                self.state["players"][event.player_id] = {}
            self.state["players"][event.player_id]["current_hp"] = event.new_hp
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 玩家{event.player_id}血量变为{event.new_hp}")


class SimpleDiscardCardEventHandler(EventHandler):
    """SimpleControl的弃牌事件处理器
    
    更新内部状态：记录玩家弃牌信息，更新手牌数量
    """
    
    def __init__(self, state: Dict[str, Any]):
        """初始化处理器
        
        Args:
            state: SimpleControl的内部状态字典
        """
        self.state = state
    
    def handle(self, event: DiscardCardEvent, player_id: Optional[int] = None) -> None:
        """处理弃牌事件
        
        Args:
            event: 弃牌事件
            player_id: 关联的玩家ID
        """
        if player_id == event.player:
            # 自己弃牌：更新自己的手牌数量（-1）
            if "self" not in self.state:
                self.state["self"] = {}
            self.state["self"]["hand_count"] = max(0, self.state["self"].get("hand_count", 0) - 1)
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 自己弃牌，手牌数量-1")
        else:
            # 其他玩家弃牌：更新其他玩家的手牌数量（-1）
            if "players" not in self.state:
                self.state["players"] = {}
            if event.player not in self.state["players"]:
                self.state["players"][event.player] = {}
            self.state["players"][event.player]["hand_count"] = \
                max(0, self.state["players"][event.player].get("hand_count", 0) - 1)
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 玩家{event.player}弃牌，手牌数量-1")


class SimpleEquipChangeEventHandler(EventHandler):
    """SimpleControl的装备变化事件处理器
    
    更新内部状态：记录玩家装备变化
    """
    
    def __init__(self, state: Dict[str, Any]):
        """初始化处理器
        
        Args:
            state: SimpleControl的内部状态字典
        """
        self.state = state
    
    def handle(self, event: EquipChangeEvent, player_id: Optional[int] = None) -> None:
        """处理装备变化事件
        
        Args:
            event: 装备变化事件
            player_id: 关联的玩家ID
        """
        equip_type_name = event.equip_type.value if hasattr(event.equip_type, 'value') else str(event.equip_type)
        equip_name = event.equip_name.value if hasattr(event.equip_name, 'value') else str(event.equip_name)
        
        if player_id == event.player_id:
            # 自己装备变化：更新自己的装备信息
            if "self" not in self.state:
                self.state["self"] = {}
            if "equipment" not in self.state["self"]:
                self.state["self"]["equipment"] = {}
            self.state["self"]["equipment"][equip_type_name] = equip_name
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 自己装备{equip_type_name}变为{equip_name}")
        else:
            # 其他玩家装备变化：更新其他玩家的装备信息
            if "players" not in self.state:
                self.state["players"] = {}
            if event.player_id not in self.state["players"]:
                self.state["players"][event.player_id] = {}
            if "equipment" not in self.state["players"][event.player_id]:
                self.state["players"][event.player_id]["equipment"] = {}
            self.state["players"][event.player_id]["equipment"][equip_type_name] = equip_name
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 玩家{event.player_id}装备{equip_type_name}变为{equip_name}")


class SimpleDeathEventHandler(EventHandler):
    """SimpleControl的死亡事件处理器
    
    更新内部状态：标记玩家死亡
    """
    
    def __init__(self, state: Dict[str, Any]):
        """初始化处理器
        
        Args:
            state: SimpleControl的内部状态字典
        """
        self.state = state
    
    def handle(self, event: DeathEvent, player_id: Optional[int] = None) -> None:
        """处理死亡事件
        
        Args:
            event: 死亡事件
            player_id: 关联的玩家ID
        """
        if player_id == event.player_id:
            # 自己死亡：更新自己的状态
            if "self" not in self.state:
                self.state["self"] = {}
            self.state["self"]["status"] = "死亡"
            self.state["self"]["current_hp"] = 0
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 自己死亡")
        else:
            # 其他玩家死亡：更新其他玩家的状态
            if "players" not in self.state:
                self.state["players"] = {}
            if event.player_id not in self.state["players"]:
                self.state["players"][event.player_id] = {}
            self.state["players"][event.player_id]["status"] = "死亡"
            self.state["players"][event.player_id]["current_hp"] = 0
            game_logger.log_debug(f"SimpleControl (玩家{player_id}) 更新状态: 玩家{event.player_id}死亡")

