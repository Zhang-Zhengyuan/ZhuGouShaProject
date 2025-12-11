# 猪国杀规则事件处理器模块
"""为SimpleControl提供能够识别跳忠、跳反等行为的事件处理器"""
from typing import Optional, TYPE_CHECKING
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.event_handler import EventHandler
from communicator.comm_event import PlayCardEvent, HPChangeEvent
from backend.utils.logger import game_logger
from config.enums import CardName

if TYPE_CHECKING:
    from backend.control.simple_control import SimpleControl


class ZhuguoShaPlayCardEventHandler(EventHandler):
    """猪国杀规则出牌事件处理器
    
    识别跳忠、跳反等行为
    """
    
    def __init__(self, control: 'SimpleControl'):
        """初始化处理器
        
        Args:
            control: SimpleControl实例
        """
        self.control = control
    
    def handle(self, event: PlayCardEvent, player_id: Optional[int] = None) -> None:
        """处理出牌事件
        
        识别跳忠、跳反行为：
        - 跳忠：对主猪或已跳忠的猪献殷勤，或对已跳反的猪表敌意
        - 跳反：对主猪或已跳忠的猪表敌意，或对已跳反的猪献殷勤
        
        Args:
            event: 出牌事件
            player_id: 关联的玩家ID（观察者）
        """
        from_player_id = event.from_player
        to_player_id = event.to_player
        
        # 更新手牌数量
        if player_id == from_player_id:
            # 自己出牌：更新自己的手牌数量（-1）
            if "self" not in self.control.internal_state:
                self.control.internal_state["self"] = {}
            self.control.internal_state["self"]["hand_count"] = \
                max(0, self.control.internal_state["self"].get("hand_count", 0) - 1)
        else:
            # 其他玩家出牌：更新其他玩家的手牌数量（-1）
            if "players" not in self.control.internal_state:
                self.control.internal_state["players"] = {}
            if from_player_id not in self.control.internal_state["players"]:
                self.control.internal_state["players"][from_player_id] = {}
            self.control.internal_state["players"][from_player_id]["hand_count"] = \
                max(0, self.control.internal_state["players"][from_player_id].get("hand_count", 0) - 1)
        
        # 识别跳忠、跳反行为（使用完整的事件信息）
        if event.card_config:
            card_name_str = event.card_config.name.value if hasattr(event.card_config.name, 'value') else str(event.card_config.name)
            
            # 判断是否是表敌意（杀、决斗，但响应决斗的杀不算表敌意）
            # 响应类事件不算表敌意或献殷勤，但无懈可击响应需要特殊处理
            is_response = event.response_type is not None
            
            # 无懈可击响应需要特殊处理（可以献殷勤或表敌意）
            is_wu_xie_response = (card_name_str == "无懈可击" and 
                                  is_response and 
                                  event.response_type == "响应无懈可击")
            
            if not is_response or is_wu_xie_response:
                # 非响应类事件或无懈可击响应才判断跳忠、跳反
                is_hostility = False
                is_loyalty = False
                
                if is_wu_xie_response:
                    # 无懈可击响应：is_effective=True表示保护目标（献殷勤），False表示抵消献殷勤（表敌意）
                    # to_player_id是被保护的目标（response_target）
                    if event.is_effective is True:
                        is_loyalty = True  # 保护目标，献殷勤
                        from_player_name = self.control._get_player_name(from_player_id)
                        target_player_name = self.control._get_player_name(to_player_id)
                        game_logger.log_info(f"{from_player_name}对{target_player_name}献殷勤（无懈可击）")
                    elif event.is_effective is False:
                        is_hostility = True  # 抵消献殷勤，表敌意
                        from_player_name = self.control._get_player_name(from_player_id)
                        target_player_name = self.control._get_player_name(to_player_id)
                        game_logger.log_info(f"{from_player_name}对{target_player_name}表敌意（无懈可击抵消）")
                else:
                    # 非响应类事件：杀、决斗表敌意
                    is_hostility = card_name_str in ["杀", "决斗"]
                    if is_hostility:
                        from_player_name = self.control._get_player_name(from_player_id)
                        target_player_name = self.control._get_player_name(to_player_id)
                        game_logger.log_info(f"{from_player_name}对{target_player_name}表敌意（{card_name_str}）")
                
                if is_hostility:
                    # 表敌意
                    if self.control._is_lord(to_player_id):
                        # 对主猪表敌意 -> 跳反
                        self.control._mark_jumped_rebel(from_player_id)
                    elif to_player_id in self.control.jumped_loyal:
                        # 对已跳忠的猪表敌意 -> 跳反
                        self.control._mark_jumped_rebel(from_player_id)
                    elif to_player_id in self.control.jumped_rebel:
                        # 对已跳反的猪表敌意 -> 跳忠
                        self.control._mark_jumped_loyal(from_player_id)
                
                if is_loyalty:
                    # 献殷勤（无懈可击保护目标）
                    if self.control._is_lord(to_player_id):
                        # 对主猪献殷勤 -> 跳忠
                        self.control._mark_jumped_loyal(from_player_id)
                    elif to_player_id in self.control.jumped_loyal:
                        # 对已跳忠的猪献殷勤 -> 跳忠
                        self.control._mark_jumped_loyal(from_player_id)
                    elif to_player_id in self.control.jumped_rebel:
                        # 对已跳反的猪献殷勤 -> 跳反
                        self.control._mark_jumped_rebel(from_player_id)


class ZhuguoShaHPChangeEventHandler(EventHandler):
    """猪国杀规则血量变化事件处理器
    
    识别类反猪（主猪认为）
    """
    
    def __init__(self, control: 'SimpleControl'):
        """初始化处理器
        
        Args:
            control: SimpleControl实例
        """
        self.control = control
    
    def handle(self, event: HPChangeEvent, player_id: Optional[int] = None) -> None:
        """处理血量变化事件
        
        如果主猪受到伤害，且伤害来源没有跳身份，且是通过南猪入侵/万箭齐发造成的，
        则标记为类反猪
        
        Args:
            event: 血量变化事件
            player_id: 关联的玩家ID（观察者）
        """
        # 更新血量
        if player_id == event.player_id:
            # 自己血量变化：更新自己的血量
            if "self" not in self.control.internal_state:
                self.control.internal_state["self"] = {}
            self.control.internal_state["self"]["current_hp"] = event.new_hp
        else:
            # 其他玩家血量变化：更新其他玩家的血量
            if "players" not in self.control.internal_state:
                self.control.internal_state["players"] = {}
            if event.player_id not in self.control.internal_state["players"]:
                self.control.internal_state["players"][event.player_id] = {}
            self.control.internal_state["players"][event.player_id]["current_hp"] = event.new_hp
        
        # 如果主猪受到伤害，且伤害来源没有跳身份，且是通过南猪入侵/万箭齐发造成的，标记为类反猪
        if (event.player_id == self.control.player_id and 
            self.control._get_my_identity() == "主公" and
            event.source_player_id is not None and
            event.damage_type in ["南蛮入侵", "万箭齐发"]):
            # 主猪受到南蛮入侵/万箭齐发的伤害
            source_id = event.source_player_id
            # 如果伤害来源没有跳身份，标记为类反猪
            if (source_id not in self.control.jumped_rebel and 
                source_id not in self.control.jumped_loyal):
                self.control._mark_class_rebel(source_id)

