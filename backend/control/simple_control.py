# 简单Control实现（规则操控）
"""基于规则的简单Control实现，符合ZHUGUOSHA.md中的规则"""
from typing import List, Optional, Dict, Any, Set
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.control import Control
from config.enums import ControlType, CardName, CardType, PlayerIdentity
from backend.card.card import Card
from backend.utils.logger import game_logger
from communicator.comm_event import DrawCardEvent, PlayCardEvent, HPChangeEvent, DiscardCardEvent, EquipChangeEvent, DeathEvent
from backend.control.simple_event_handler import (
    SimpleDrawCardEventHandler, SimpleDiscardCardEventHandler, 
    SimpleEquipChangeEventHandler, SimpleDeathEventHandler
)
from backend.control.zhuguosha_event_handler import (
    ZhuguoShaPlayCardEventHandler, ZhuguoShaHPChangeEventHandler
)


class SimpleControl(Control):
    """简单Control实现（规则操控）
    
    基于简单规则的决策逻辑，适用于规则操控类型的玩家
    能够根据事件更新内部状态，并基于状态做出决策
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """初始化简单Control
        
        Args:
            player_id: 关联的玩家ID
        """
        super().__init__(ControlType.SIMPLE_AI, player_id)
        
        # 内部状态字典（用于跟踪场上信息）
        # 结构：
        # {
        #   "self": {
        #       "hand_count": int,
        #       "current_hp": int,
        #       "equipment": {equip_type: equip_name}
        #   },
        #   "players": {
        #       player_id: {
        #           "hand_count": int,
        #           "current_hp": int,
        #           "equipment": {equip_type: equip_name},
        #           "status": str
        #       }
        #   }
        # }
        self.internal_state: Dict[str, Any] = {
            "self": {},
            "players": {}
        }
        
        # 身份标记系统（符合ZHUGUOSHA.md规则）
        # 跳忠：对主猪或已跳忠的猪献殷勤，或对已跳反的猪表敌意
        # 跳反：对主猪或已跳忠的猪表敌意，或对已跳反的猪献殷勤
        # 类反：没有跳身份，且用南猪入侵/万箭齐发对主猪造成伤害的猪（主猪认为）
        self.jumped_loyal: Set[int] = set()  # 已跳忠的玩家ID集合
        self.jumped_rebel: Set[int] = set()  # 已跳反的玩家ID集合
        self.class_rebel: Set[int] = set()  # 类反猪集合（主猪认为）
        
        # 记录玩家顺序（用于距离计算，逆时针方向）
        self.player_order: List[int] = []  # 玩家ID顺序列表（逆时针）
        
        # 记录自己是否已经跳过身份
        self.has_jumped = False
        
        # 注册SimpleControl专用的事件处理器（覆盖默认处理器）
        self._register_simple_handlers()
    
    def _register_simple_handlers(self) -> None:
        """注册SimpleControl专用的事件处理器"""
        # 使用增强的处理器，能够识别跳忠、跳反等行为
        self.register_handler(DrawCardEvent, SimpleDrawCardEventHandler(self.internal_state))
        self.register_handler(PlayCardEvent, ZhuguoShaPlayCardEventHandler(self))
        self.register_handler(HPChangeEvent, ZhuguoShaHPChangeEventHandler(self))
        self.register_handler(DiscardCardEvent, SimpleDiscardCardEventHandler(self.internal_state))
        self.register_handler(EquipChangeEvent, SimpleEquipChangeEventHandler(self.internal_state))
        self.register_handler(DeathEvent, SimpleDeathEventHandler(self.internal_state))
    
    def sync_state(self, state: Dict[str, Any]) -> None:
        """同步游戏状态（覆盖父类方法）
        
        在同步状态时，同时更新内部状态
        
        Args:
            state: 游戏状态字典
        """
        # 调用父类方法同步game_state
        super().sync_state(state)
        
        # 更新内部状态
        if "self" in state:
            self_info = state["self"]
            self.internal_state["self"] = {
                "hand_count": self_info.get("hand_count", 0),
                "current_hp": self_info.get("current_hp", 0),
                "equipment": {}
            }
            # 更新装备信息
            for equip_key in ["weapon", "armor", "horse_plus", "horse_minus"]:
                equip_value = self_info.get(equip_key)
                if equip_value:
                    equip_type = equip_key.replace("horse_plus", "+1马").replace("horse_minus", "-1马")
                    if isinstance(equip_value, dict):
                        self.internal_state["self"]["equipment"][equip_type] = \
                            equip_value.get("name", "")
                    else:
                        self.internal_state["self"]["equipment"][equip_type] = str(equip_value)
        
        if "players" in state:
            for player_info in state["players"]:
                player_id = player_info["player_id"]
                self.internal_state["players"][player_id] = {
                    "hand_count": player_info.get("hand_count", 0),
                    "current_hp": player_info.get("current_hp", 0),
                    "status": player_info.get("status", "存活"),
                    "equipment": {}
                }
                # 更新装备信息
                for equip_key in ["weapon", "armor", "horse_plus", "horse_minus"]:
                    equip_value = player_info.get(equip_key)
                    if equip_value:
                        equip_type = equip_key.replace("horse_plus", "+1马").replace("horse_minus", "-1马")
                        if isinstance(equip_value, dict):
                            self.internal_state["players"][player_id]["equipment"][equip_type] = \
                                equip_value.get("name", "")
                        else:
                            self.internal_state["players"][player_id]["equipment"][equip_type] = str(equip_value)
        
        # 更新玩家顺序（逆时针方向，用于距离计算）
        # 注意：只包含存活的玩家（距离计算时应该跳过死亡的玩家）
        if "self" in state and "players" in state:
            self_info = state["self"]
            players_info = state["players"]
            
            # 构建完整的玩家列表（包括自己），但只包含存活的玩家
            all_players = []
            
            # 检查自己是否存活
            self_status = self_info.get("status", "存活")
            self_hp = self_info.get("current_hp", 0)
            if self_status != "死亡" and self_hp > 0:
                all_players.append(self_info)
            
            # 检查其他玩家是否存活
            for player_info in players_info:
                player_status = player_info.get("status", "存活")
                player_hp = player_info.get("current_hp", 0)
                if player_status != "死亡" and player_hp > 0:
                    all_players.append(player_info)
            
            # 如果没有存活玩家，清空player_order
            if not all_players:
                self.player_order = []
                return
            
            # 按player_id排序
            all_players.sort(key=lambda p: p["player_id"])
            
            my_id = self_info["player_id"]
            # 找到自己在存活玩家列表中的位置
            my_index = next((i for i, p in enumerate(all_players) if p["player_id"] == my_id), 0)
            
            # 逆时针顺序：从自己开始，然后按ID顺序循环（只包含存活玩家）
            self.player_order = [p["player_id"] for p in all_players[my_index:]] + \
                              [p["player_id"] for p in all_players[:my_index]]
    
    def _calculate_distance(self, from_id: int, to_id: int) -> int:
        """计算两个玩家之间的距离（逆时针方向）
        
        根据ZHUGUOSHA.md：两只猪的距离定义为沿着逆时针方向间隔的猪数+1
        间隔的猪数 = 中间跳过的猪数
        
        Args:
            from_id: 起始玩家ID
            to_id: 目标玩家ID
            
        Returns:
            距离（至少为1）
        """
        if from_id == to_id:
            return 1
        
        if not self.player_order:
            return 999  # 无法计算，返回很大的值
        
        # 找到两个玩家在顺序中的位置
        try:
            from_index = self.player_order.index(from_id)
            to_index = self.player_order.index(to_id)
        except ValueError:
            return 999
        
        # 计算逆时针距离
        # 间隔的猪数 = 中间跳过的猪数
        if to_index > from_index:
            # 不需要绕圈：间隔数 = to_index - from_index - 1
            intervals = to_index - from_index - 1
            distance = intervals + 1
        else:
            # 需要绕一圈：间隔数 = (从from_index到末尾的间隔) + (从开头到to_index的间隔)
            # 从from_index到末尾的间隔数 = len(player_order) - from_index - 1
            # 从开头到to_index的间隔数 = to_index
            intervals = (len(self.player_order) - from_index - 1) + to_index
            distance = intervals + 1
        
        return distance
    
    def _is_attackable(self, target_id: int) -> bool:
        """判断目标是否在攻击范围内
        
        根据规则：杀的攻击范围都是1（无论有无武器）
        
        Args:
            target_id: 目标玩家ID
            
        Returns:
            是否在攻击范围内
        """
        if not self.player_id:
            return False
        
        distance = self._calculate_distance(self.player_id, target_id)
        return distance <= 1
    
    def _get_my_identity(self) -> Optional[str]:
        """获取自己的身份
        
        Returns:
            身份字符串（"主公"、"忠臣"、"反贼"、"内奸"）或None
        """
        if not self.game_state or "self" not in self.game_state:
            return None
        return self.game_state["self"].get("identity")
    
    def _is_lord(self, player_id: int) -> bool:
        """判断玩家是否是主猪
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否是主猪
        """
        if player_id == self.player_id:
            return self._get_my_identity() == "主公"
        
        if self.game_state and "players" in self.game_state:
            for p in self.game_state["players"]:
                if p["player_id"] == player_id:
                    return p.get("identity") == "主公"
        return False
    
    def _get_player_name(self, player_id: int) -> str:
        """获取玩家名称
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家名称，如果找不到则返回"玩家{player_id}"
        """
        # 先检查是否是自己的ID
        if self.game_state and "self" in self.game_state:
            if self.game_state["self"].get("player_id") == player_id:
                return self.game_state["self"].get("name", f"玩家{player_id}")
        
        # 检查其他玩家
        if self.game_state and "players" in self.game_state:
            for player_info in self.game_state["players"]:
                if player_info.get("player_id") == player_id:
                    return player_info.get("name", f"玩家{player_id}")
        
        # 如果找不到，返回默认格式
        return f"玩家{player_id}"
    
    def _mark_jumped_loyal(self, player_id: int) -> None:
        """标记玩家跳忠
        
        Args:
            player_id: 玩家ID
        """
        if player_id not in self.jumped_loyal:
            self.jumped_loyal.add(player_id)
            # 如果之前标记为跳反，移除跳反标记
            self.jumped_rebel.discard(player_id)
            player_name = self._get_player_name(player_id)
            game_logger.log_info(f"{player_name}跳忠")
    
    def _mark_jumped_rebel(self, player_id: int) -> None:
        """标记玩家跳反
        
        Args:
            player_id: 玩家ID
        """
        if player_id not in self.jumped_rebel:
            self.jumped_rebel.add(player_id)
            # 如果之前标记为跳忠，移除跳忠标记
            self.jumped_loyal.discard(player_id)
            # 如果之前标记为类反，移除类反标记（因为已经跳反了）
            self.class_rebel.discard(player_id)
            player_name = self._get_player_name(player_id)
            game_logger.log_info(f"{player_name}跳反")
    
    def _mark_class_rebel(self, player_id: int) -> None:
        """标记玩家为类反（仅主猪使用）
        
        Args:
            player_id: 玩家ID
        """
        if self._get_my_identity() != "主公":
            return
        
        if player_id not in self.jumped_rebel and player_id not in self.jumped_loyal:
            if player_id not in self.class_rebel:
                self.class_rebel.add(player_id)
                player_name = self._get_player_name(player_id)
                game_logger.log_info(f"主猪认为{player_name}是类反猪")
    
    def filter_attackable_targets(self, targets: List[int], available_targets_dict: Dict[str, List[int]] = None) -> List[int]:
        """过滤攻击范围内的目标（使用逆时针距离计算）
        
        对于杀，重新使用逆时针距离过滤攻击范围内的目标
        
        Args:
            targets: 目标列表（可能使用了错误的距离计算）
            available_targets_dict: 可用目标字典（可选）
            
        Returns:
            过滤后的目标列表（只包含逆时针距离<=1的目标）
        """
        if not targets:
            return []
        
        # 使用逆时针距离重新过滤攻击范围内的目标（杀的攻击范围是1）
        filtered_targets = []
        for target_id in targets:
            if target_id == self.player_id:
                continue  # 跳过自己
            # 使用自己的_calculate_distance方法（只计算逆时针距离）
            distance = self._calculate_distance(self.player_id, target_id)
            if distance <= 1:  # 杀的攻击范围是1
                filtered_targets.append(target_id)
        
        return filtered_targets
    
    def select_targets(self, available_targets: List[int], card: Optional[Card] = None) -> List[int]:
        """选择目标（符合猪国杀规则）
        
        根据身份和规则选择目标，对不能使用的牌不处理（返回空列表）
        
        Args:
            available_targets: 可选目标列表（已经使用逆时针距离过滤过）
            card: 要为哪张牌选择目标（可选）
            
        Returns:
            选择的目标列表
        """
        if not available_targets:
            return []
        
        my_identity = self._get_my_identity()
        if not my_identity:
            # 如果不知道身份，使用默认逻辑
            return self._select_targets_default(available_targets)
        
        # 根据身份选择目标
        if my_identity == "主公":
            return self._select_targets_as_lord(available_targets)
        elif my_identity == "忠臣":
            return self._select_targets_as_loyalist(available_targets)
        elif my_identity == "反贼":
            return self._select_targets_as_rebel(available_targets)
        else:
            # 内奸或其他，使用默认逻辑
            return self._select_targets_default(available_targets)
    
    def _select_targets_default(self, available_targets: List[int]) -> List[int]:
        """默认选择目标逻辑（优先选择血量最少的）
        
        Args:
            available_targets: 可选目标列表
            
        Returns:
            选择的目标列表
        """
        import random
        
        # 优先使用内部状态
        target_hp_map = {}
        if self.internal_state.get("players"):
            for target_id in available_targets:
                if target_id in self.internal_state["players"]:
                    player_state = self.internal_state["players"][target_id]
                    # 跳过已死亡的玩家
                    if player_state.get("status") == "死亡":
                        continue
                    target_hp_map[target_id] = player_state.get("current_hp", 999)
        
        # 如果内部状态不完整，使用game_state
        if not target_hp_map and self.game_state and self.game_state.get("players"):
            players_info = self.game_state.get("players", [])
            for player_info in players_info:
                if player_info["player_id"] in available_targets:
                    target_hp_map[player_info["player_id"]] = player_info.get("current_hp", 999)
        
        if not target_hp_map:
            return [random.choice(available_targets)] if available_targets else []
        
        # 优先选择名为“赵云”的目标（章节/剧情模式里敌人优先攻击赵云）
        for pid in available_targets:
            # 从game_state中检查名字
            if self.game_state and "players" in self.game_state:
                for pinfo in self.game_state["players"]:
                    if pinfo.get("player_id") == pid and pinfo.get("name") == "赵云":
                        return [pid]

        # 选择血量最少的
        min_hp = min(target_hp_map.values())
        min_hp_targets = [pid for pid, hp in target_hp_map.items() if hp == min_hp]
        
        return [random.choice(min_hp_targets)]
    
    def _select_targets_as_lord(self, available_targets: List[int]) -> List[int]:
        """主猪选择目标
        
        规则：对逆时针方向能够执行到的第一只类反猪或者已跳反猪表敌意
        如果没有，那么就不表敌意
        
        注意：决斗可以对任意目标使用（不受攻击范围限制），杀只能对攻击范围内的目标使用
        
        Args:
            available_targets: 可选目标列表
            
        Returns:
            选择的目标列表
        """
        # 按逆时针顺序查找类反猪或已跳反猪
        for player_id in self.player_order:
            if player_id == self.player_id:
                continue
            if player_id in available_targets:
                # 如果目标在available_targets中，说明这张牌可以对该目标使用
                # 对于决斗（TargetType.ALL），所有存活玩家都在available_targets中
                # 对于杀（TargetType.ATTACKABLE），只有攻击范围内的玩家在available_targets中
                # 所以这里不需要再检查攻击范围，因为available_targets已经过滤过了
                if player_id in self.class_rebel or player_id in self.jumped_rebel:
                    return [player_id]
        
        # 如果没有找到，返回空列表（不表敌意）
        return []
    
    def _select_targets_as_loyalist(self, available_targets: List[int]) -> List[int]:
        """忠猪选择目标
        
        规则：对逆时针方向能够执行到的第一只已经跳反的猪表敌意
        如果没有，那么就不表敌意
        
        注意：available_targets已经根据牌的类型过滤过了：
        - 决斗（TargetType.ALL）：包含所有存活玩家（除了自己）
        - 杀（TargetType.ATTACKABLE）：只包含攻击范围内的玩家
        所以如果目标在available_targets中，说明这张牌可以对该目标使用，直接选择即可
        
        Args:
            available_targets: 可选目标列表
            
        Returns:
            选择的目标列表
        """
        # 按逆时针顺序查找已跳反猪
        # available_targets已经根据牌的类型过滤过了，所以不需要再检查攻击范围
        for player_id in self.player_order:
            if player_id == self.player_id:
                continue
            if player_id in available_targets:
                if player_id in self.jumped_rebel:
                    return [player_id]
        
        # 如果没有找到，返回空列表（不表敌意）
        return []
    
    def _select_targets_as_rebel(self, available_targets: List[int]) -> List[int]:
        """反猪选择目标
        
        规则：如果有机会则对主猪表，否则，对逆时针方向能够执行到的第一只已经跳忠的猪表敌意
        如果没有，那么就不表敌意
        
        注意：available_targets已经根据牌的类型过滤过了：
        - 决斗（TargetType.ALL）：包含所有存活玩家（除了自己）
        - 杀（TargetType.ATTACKABLE）：只包含攻击范围内的玩家
        所以如果目标在available_targets中，说明这张牌可以对该目标使用，直接选择即可
        
        Args:
            available_targets: 可选目标列表
            
        Returns:
            选择的目标列表
        """
        # 优先对主猪表敌意（按逆时针方向找到第一个可以表的主猪）
        # 按逆时针顺序查找主猪
        for player_id in self.player_order:
            if player_id == self.player_id:
                continue  # 跳过自己
            if player_id not in available_targets:
                continue  # 跳过不在可选目标中的玩家
            # 如果目标在available_targets中，说明这张牌可以对该目标使用
            # 反贼只对主猪或已跳忠的猪表敌意，不对反贼表敌意
            if self._is_lord(player_id):
                return [player_id]

        # 如果player_order没有找到主公（或主公在available_targets外），优先寻找名字为赵云的目标
        for pid in available_targets:
            if self.game_state and "players" in self.game_state:
                for pinfo in self.game_state["players"]:
                    if pinfo.get("player_id") == pid and pinfo.get("name") == "赵云":
                        return [pid]
            
        for player_id in self.player_order:
            if player_id == self.player_id:
                continue  # 跳过自己
            if player_id not in available_targets:
                continue  # 跳过不在可选目标中的玩家
            # 如果目标在available_targets中，说明这张牌可以对该目标使用
            # 反贼只对主猪或已跳忠的猪表敌意，不对反贼表敌意
            if player_id in self.jumped_loyal:
                return [player_id]
        # 如果没有找到，返回空列表（不表敌意）
        return []
    
    def select_card(self, available_cards: List[Card], context: str = "", available_targets: Dict[str, List[int]] = None) -> Optional[Card]:
        """选择要出的牌（正常出牌阶段，符合猪国杀规则，覆盖父类方法）
        
        按照从左往右的顺序遍历每张牌，根据对应牌思考是否应该出这张牌
        
        规则优先级（对每张牌按顺序判断）：
        1. 如果是桃且生命值未满，必然吃掉
        2. 如果是南猪入侵、万箭齐发，必然使用
        3. 如果是装备，必然装上
        4. 如果是决斗/杀，根据身份判断是否应该出（检查是否有应该攻击的目标）
        
        Args:
            available_cards: 可选的牌列表（从左往右的顺序）
            context: 使用上下文（正常出牌时通常为空）
            available_targets: 可用目标字典（可选，用于检查是否有合法目标）
            
        Returns:
            选择的牌或None
        """
        if not available_cards:
            return None
        
        # 获取身份和状态信息（只获取一次）
        my_identity = self._get_my_identity()
        my_hp = self.internal_state.get("self", {}).get("current_hp", 0)
        my_max_hp = self.game_state.get("self", {}).get("max_hp", 4) if self.game_state else 4
        
        # 从左往右遍历每张牌，根据对应牌思考是否应该出
        for card in available_cards:
            # 1. 如果是桃且生命值未满，必然吃掉
            if card.name_enum == CardName.TAO:
                if my_hp < my_max_hp:
                    return card
                continue  # 生命值已满，跳过这张牌
            
            # 2. 如果是南猪入侵、万箭齐发，必然使用
            if card.name_enum == CardName.NAN_MAN_RU_QIN or card.name_enum == CardName.WAN_JIAN_QI_FA:
                return card
            
            # 3. 如果是装备，必然装上
            if card.card_type == CardType.EQUIPMENT:
                return card
            
            # 4. 如果是决斗，根据身份判断是否应该出
            if card.name_enum == CardName.JUE_DOU:
                # 决斗可以对任意目标使用（不受攻击范围限制）
                # 需要检查所有存活目标中是否有"应该攻击"的目标
                if available_targets is None:
                    continue  # 没有目标信息，跳过这张牌
                
                # 获取所有存活目标列表（决斗可以对任意目标使用）
                all_targets = available_targets.get("all", [])
                if not all_targets:
                    continue  # 没有目标，跳过这张牌
                
                # 检查目标中是否有应该攻击的目标
                has_valid_target = False
                
                if my_identity == "主公":
                    # 主猪：检查目标中是否有类反猪或已跳反猪
                    for target_id in all_targets:
                        if target_id in self.class_rebel or target_id in self.jumped_rebel:
                            has_valid_target = True
                            break
                elif my_identity == "反贼":
                    # 反贼：检查目标中是否有主猪或已跳忠的猪
                    for target_id in all_targets:
                        if self._is_lord(target_id) or target_id in self.jumped_loyal:
                            has_valid_target = True
                            break
                elif my_identity == "忠臣":
                    # 忠臣：检查目标中是否有已跳反猪
                    for target_id in all_targets:
                        if target_id in self.jumped_rebel:
                            has_valid_target = True
                            break
                
                if has_valid_target:
                    return card
                continue  # 没有应该攻击的目标，跳过这张牌
            
            # 5. 如果是杀，根据身份判断是否应该出
            if card.name_enum == CardName.SHA:
                # 杀只能对攻击范围内的目标使用（使用逆时针距离计算）
                # 需要检查攻击范围内的目标中是否有"应该攻击"的目标
                if available_targets is None:
                    continue  # 没有目标信息，跳过这张牌
                
                # 获取攻击范围内的目标
                all_targets = available_targets.get("attackable", [])
                if not all_targets:
                    continue  # 没有目标，跳过这张牌
                
                # 使用逆时针距离重新过滤攻击范围内的目标（杀的攻击范围是1）
                attackable_targets = []
                for target_id in all_targets:
                    if target_id == self.player_id:
                        continue  # 跳过自己
                    # 使用自己的_calculate_distance方法（只计算逆时针距离）
                    distance = self._calculate_distance(self.player_id, target_id)
                    if distance <= 1:  # 杀的攻击范围是1
                        attackable_targets.append(target_id)
                
                if not attackable_targets:
                    continue  # 没有攻击范围内的目标，跳过这张牌
                
                # 检查攻击范围内的目标中是否有应该攻击的目标
                has_valid_target = False
                
                if my_identity == "主公":
                    # 主猪：检查攻击范围内的目标中是否有类反猪或已跳反猪
                    for target_id in attackable_targets:
                        if target_id in self.class_rebel or target_id in self.jumped_rebel:
                            has_valid_target = True
                            break
                elif my_identity == "反贼":
                    # 反贼：检查攻击范围内的目标中是否有主猪或已跳忠的猪
                    for target_id in attackable_targets:
                        if self._is_lord(target_id) or target_id in self.jumped_loyal:
                            has_valid_target = True
                            break
                elif my_identity == "忠臣":
                    # 忠臣：检查攻击范围内的目标中是否有已跳反猪
                    for target_id in attackable_targets:
                        if target_id in self.jumped_rebel:
                            has_valid_target = True
                            break
                
                if has_valid_target:
                    return card
                continue  # 没有应该攻击的目标，跳过这张牌
        
        # 没有找到应该出的牌
        return None
    
    def ask_use_card_response(self, card_name: CardName, available_cards: List[Card], context: str = "") -> Optional[Card]:
        """询问是否使用指定牌（响应类查询，与正常出牌分开）
        
        按照从左往右的顺序（available_cards的顺序）选择第一张符合条件的牌
        
        规则：
        - 受到杀时，有闪必然使用
        - 响应南猪入侵/万箭齐发时，有杀/闪必然使用
        - 响应决斗时，有杀必然使用
        - 无懈可击：根据献殷勤/表敌意规则判断
        
        Args:
            card_name: 要查询的牌名枚举
            available_cards: 可选的牌列表（从左往右的顺序，只包含指定牌名的牌）
            context: 使用上下文（如"响应决斗"、"响应南蛮入侵"、"受到杀的攻击"等）
            
        Returns:
            选择的牌或None（不使用）
        """
        if not available_cards:
            return None
        
        # 按照从左往右的顺序遍历，选择第一张符合条件的牌
        
        # 1. 濒死状态，有桃必然使用（只有自己濒死才自救，别人濒死不救）
        # 只有在context明确包含"自救"时才使用桃，确保只有自己濒死时才救
        if card_name == CardName.TAO and context and "自救" in context:
            return available_cards[0]  # 从左往右第一张桃
        
        # 2. 受到杀攻击，有闪必然使用
        if card_name == CardName.SHAN and context and "受到" in context and "杀" in context:
            return available_cards[0]  # 从左往右第一张闪
        
        # 3. 响应南蛮入侵，有杀必然使用
        if card_name == CardName.SHA and context and ("响应南蛮入侵" in context or "响应南猪入侵" in context):
            return available_cards[0]  # 从左往右第一张杀
        
        # 4. 响应万箭齐发，有闪必然使用
        if card_name == CardName.SHAN and context and "响应万箭齐发" in context:
            return available_cards[0]  # 从左往右第一张闪
        
        # 5. 响应决斗，有杀必然使用
        if card_name == CardName.SHA and context and "响应决斗" in context:
            return available_cards[0]  # 从左往右第一张杀
        
        # 6. 无懈可击：检查是否需要献殷勤或表敌意
        if card_name == CardName.WU_XIE_KE_JI and context and ("无懈可击" in context or "是否使用无懈可击" in context):
            # 从context中解析is_effective状态
            is_effective = "即将生效" in context or "即将 生效" in context
            
            my_identity = self._get_my_identity()
            
            # 从context中解析目标玩家名称
            # context格式："{user_player.name}使用的{original_card.name}对{target_player.name}即将{'生效' if is_effective else '失效'}，是否使用无懈可击"
            target_name = None
            if "对" in context and "即将" in context:
                # 提取"对"和"即将"之间的内容
                start_idx = context.find("对") + 1
                end_idx = context.find("即将")
                if start_idx > 0 and end_idx > start_idx:
                    target_name = context[start_idx:end_idx].strip()
            
            # 如果找到了目标名称，检查是否需要献殷勤或表敌意
            if target_name:
                # 从game_state中查找目标玩家ID
                target_player_id = None
                if self.game_state and "players" in self.game_state:
                    for player_info in self.game_state["players"]:
                        if player_info.get("name") == target_name:
                            target_player_id = player_info.get("player_id")
                            break
                
                # 如果找不到，检查是否是自己的名称
                if target_player_id is None and self.game_state and "self" in self.game_state:
                    if self.game_state["self"].get("name") == target_name:
                        target_player_id = self.game_state["self"].get("player_id")
                
                if target_player_id is not None:
                    should_use = False
                    
                    if is_effective:
                        # is_effective=True：保护目标（献殷勤）
                        if my_identity == "主公":
                            # 主猪：如果能对自己献殷勤，那么一定献（保护自己）
                            if target_player_id == self.player_id:
                                should_use = True
                            # 如果能对已经跳忠的猪献殷勤，那么一定献
                            elif target_player_id in self.jumped_loyal:
                                should_use = True
                        
                        elif my_identity == "反贼":
                            # 反猪：如果有机会对已经跳反的猪献殷勤，那么一定献
                            if target_player_id in self.jumped_rebel:
                                should_use = True
                        
                        elif my_identity == "忠臣":
                            # 忠猪：如果有机会对主猪或者已经跳忠的猪献殷勤，那么一定献
                            if self._is_lord(target_player_id) or target_player_id in self.jumped_loyal:
                                should_use = True
                    
                    else:
                        # is_effective=False：抵消保护（表敌意）
                        if my_identity == "反贼":
                            # 反猪：如果有机会对主猪或已跳忠的猪表敌意，那么一定表敌意
                            if self._is_lord(target_player_id) or target_player_id in self.jumped_loyal:
                                should_use = True
                        
                        elif my_identity == "忠臣":
                            # 忠猪：如果有机会对已跳反的猪表敌意，那么一定表敌意
                            if target_player_id in self.jumped_rebel:
                                should_use = True
                    
                    if should_use:
                        # 需要献殷勤或表敌意，使用无懈可击（从左往右第一张）
                        return available_cards[0]
        
        # 7. 其他情况，默认不使用
        return None
    
    def select_cards_to_discard(self, hand_cards: List[Card], count: int) -> List[Card]:
        """选择要弃的牌（简单规则：优先弃装备牌，然后弃点数小的）
        
        Args:
            hand_cards: 手牌列表
            count: 要弃的牌数量
            
        Returns:
            选择要弃的牌列表
        """
        if count <= 0:
            return []
        if count >= len(hand_cards):
            return hand_cards.copy()
        
        # 简单规则：优先弃装备牌
        from config.enums import CardType
        equipment_cards = [card for card in hand_cards if card.card_type == CardType.EQUIPMENT]
        non_equipment_cards = [card for card in hand_cards if card.card_type != CardType.EQUIPMENT]
        
        discard_list = []
        
        # 先弃装备牌
        if equipment_cards and len(discard_list) < count:
            discard_list.extend(equipment_cards[:count - len(discard_list)])
        
        # 如果还需要弃牌，按点数从小到大排序后选择
        if len(discard_list) < count:
            remaining_needed = count - len(discard_list)
            sorted_cards = sorted(non_equipment_cards, key=lambda c: c.rank)
            discard_list.extend(sorted_cards[:remaining_needed])
        
        return discard_list[:count]

