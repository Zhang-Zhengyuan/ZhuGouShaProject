"""
章节战役专用AI实现

提供三种针对特定章节的AI：
1. CanBingAI - 第一章残兵AI（目标：杀死赵云）
2. AdouAI - 第二章阿斗AI（目标：保护自己，配合赵云）
3. CaoJunAI - 第二章曹军AI（目标：杀死阿斗和赵云）

这些AI有明确的阵营意识，不依赖跳忠/跳反机制。
"""
from typing import List, Optional, Dict, Any
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.control import Control
from config.enums import ControlType, CardName, CardType, CharacterName
from backend.card.card import Card
from backend.utils.logger import game_logger


class CanBingAI(Control):
    """第一章残兵AI
    
    特点：
    - 明确知道目标是杀死赵云（ZHAO_YUN_1）
    - 残兵之间互相配合，不会互相攻击
    - 优先使用杀/决斗攻击赵云
    - 当赵云不在攻击范围内时，使用AOE锦囊（南蛮/万箭）
    """
    
    def __init__(self, player_id: Optional[int] = None):
        super().__init__(ControlType.SIMPLE_AI, player_id)
        self.target_character = CharacterName.ZHAO_YUN_1  # 明确的击杀目标
        
    def _find_target_by_character(self, character: CharacterName) -> Optional[int]:
        """根据武将枚举查找玩家ID"""
        if not self.game_state:
            return None
            
        # 检查所有玩家
        if "players" in self.game_state:
            for player_info in self.game_state["players"]:
                if player_info.get("character_name") == character and player_info.get("status") != "死亡":
                    return player_info.get("player_id")
        return None
    
    def _is_ally(self, player_id: int) -> bool:
        """判断是否是己方（其他残兵）"""
        if not self.game_state or "players" not in self.game_state:
            return False
        for player_info in self.game_state["players"]:
            if player_info.get("player_id") == player_id:
                character = player_info.get("character_name")
                # 残兵之间是盟友
                return character == CharacterName.CAN_BING
        return False
    
    def select_targets(self, available_targets: List[int], card: Optional[Card] = None) -> List[int]:
        """选择目标：优先攻击赵云，绝不攻击残兵盟友"""
        if not available_targets:
            return []
        
        # 找到赵云的ID
        zhaoyun_id = self._find_target_by_character(self.target_character)
        
        # 如果赵云在可选目标中，直接选择赵云
        if zhaoyun_id and zhaoyun_id in available_targets:
            return [zhaoyun_id]
        
        # 如果赵云不在范围内，过滤掉盟友，选择剩余目标
        non_ally_targets = [tid for tid in available_targets if not self._is_ally(tid)]
        
        if non_ally_targets:
            # 优先选择血量最少的非盟友
            return self._select_weakest(non_ally_targets)
        
        # 没有合适目标，返回空（不攻击盟友）
        return []
    
    def _select_weakest(self, targets: List[int]) -> List[int]:
        """选择血量最少的目标"""
        if not targets or not self.game_state:
            return []
        
        target_hp = {}
        for player_info in self.game_state.get("players", []):
            pid = player_info.get("player_id")
            if pid in targets:
                target_hp[pid] = player_info.get("current_hp", 999)
        
        if not target_hp:
            return [random.choice(targets)]
        
        min_hp = min(target_hp.values())
        weakest = [pid for pid, hp in target_hp.items() if hp == min_hp]
        return [random.choice(weakest)]
    
    def select_cards_for_use(self, available_cards: List[Card], available_targets_dict: Dict[str, List[int]]) -> tuple[Optional[Card], List[int]]:
        """选择出牌：优先使用攻击性卡牌"""
        if not available_cards:
            return None, []
        
        zhaoyun_id = self._find_target_by_character(self.target_character)
        
        # 优先级1: 如果有杀且赵云在攻击范围内，出杀
        sha_cards = [c for c in available_cards if c.name == CardName.SHA]
        if sha_cards and zhaoyun_id:
            attackable = available_targets_dict.get("杀", [])
            if zhaoyun_id in attackable:
                return sha_cards[0], [zhaoyun_id]
        
        # 优先级2: 如果有决斗，对赵云使用
        juedou_cards = [c for c in available_cards if c.name == CardName.JUE_DOU]
        if juedou_cards and zhaoyun_id:
            all_targets = available_targets_dict.get("决斗", [])
            if zhaoyun_id in all_targets:
                return juedou_cards[0], [zhaoyun_id]
        
        # 优先级3: AOE锦囊（南蛮/万箭），无差别攻击
        nanman_cards = [c for c in available_cards if c.name == CardName.NAN_MAN_RU_QIN]
        if nanman_cards:
            return nanman_cards[0], [-1]  # AOE目标为-1
        
        wanjian_cards = [c for c in available_cards if c.name == CardName.WAN_JIAN_QI_FA]
        if wanjian_cards:
            return wanjian_cards[0], [-1]
        
        # 优先级4: 如果自己血量低，使用桃
        if self.game_state and "self" in self.game_state:
            my_hp = self.game_state["self"].get("current_hp", 4)
            my_max_hp = self.game_state["self"].get("max_hp", 4)
            if my_hp < my_max_hp:
                tao_cards = [c for c in available_cards if c.name == CardName.TAO]
                if tao_cards:
                    return tao_cards[0], [self.player_id]
        
        # 优先级5: 使用任何可用的攻击牌
        if sha_cards:
            attackable = available_targets_dict.get("杀", [])
            targets = self.select_targets(attackable, sha_cards[0])
            if targets:
                return sha_cards[0], targets
        
        if juedou_cards:
            all_targets = available_targets_dict.get("决斗", [])
            targets = self.select_targets(all_targets, juedou_cards[0])
            if targets:
                return juedou_cards[0], targets
        
        # 没有合适的牌，不出牌
        return None, []
    
    def ask_use_card_response(self, card_name: CardName, available_cards: List[Card], context: str = "") -> Optional[Card]:
        """响应卡牌请求（出闪/杀等）"""
        # 简单策略：如果有就出
        matching_cards = [c for c in available_cards if c.name == card_name]
        return matching_cards[0] if matching_cards else None


class AdouAI(Control):
    """第二章阿斗AI（主公）
    
    特点：
    - 知道赵云（ZHAO_YUN_2）是盟友（忠臣），曹军是敌人
    - 保守策略：优先自保（使用桃回血）
    - 攻击优先级：曹军 > 不明身份
    - 不会攻击赵云
    """
    
    def __init__(self, player_id: Optional[int] = None):
        super().__init__(ControlType.SIMPLE_AI, player_id)
        self.ally_character = CharacterName.ZHAO_YUN_2
        self.enemy_character = CharacterName.CAO_JUN
    
    def _find_player_by_character(self, character: CharacterName) -> Optional[int]:
        """根据武将枚举查找玩家ID"""
        if not self.game_state or "players" not in self.game_state:
            return None
        for player_info in self.game_state["players"]:
            if player_info.get("character_name") == character and player_info.get("status") != "死亡":
                return player_info.get("player_id")
        return None
    
    def _is_ally(self, player_id: int) -> bool:
        """判断是否是盟友（赵云ZHAO_YUN_2）"""
        if not self.game_state or "players" not in self.game_state:
            return False
        for player_info in self.game_state["players"]:
            if player_info.get("player_id") == player_id:
                return player_info.get("character_name") == self.ally_character
        return False
    
    def _is_enemy(self, player_id: int) -> bool:
        """判断是否是敌人（曹军CAO_JUN）"""
        if not self.game_state or "players" not in self.game_state:
            return False
        for player_info in self.game_state["players"]:
            if player_info.get("player_id") == player_id:
                character = player_info.get("character_name")
                return character == self.enemy_character
        return False
    
    def select_targets(self, available_targets: List[int], card: Optional[Card] = None) -> List[int]:
        """选择目标：优先攻击曹军，绝不攻击赵云"""
        if not available_targets:
            return []
        
        # 过滤掉盟友
        non_ally_targets = [tid for tid in available_targets if not self._is_ally(tid)]
        if not non_ally_targets:
            return []
        
        # 优先选择敌人（曹军）
        enemy_targets = [tid for tid in non_ally_targets if self._is_enemy(tid)]
        if enemy_targets:
            return self._select_weakest(enemy_targets)
        
        # 如果没有明确的敌人，选择血量最少的非盟友
        return self._select_weakest(non_ally_targets)
    
    def _select_weakest(self, targets: List[int]) -> List[int]:
        """选择血量最少的目标"""
        if not targets or not self.game_state:
            return []
        
        target_hp = {}
        for player_info in self.game_state.get("players", []):
            pid = player_info.get("player_id")
            if pid in targets:
                target_hp[pid] = player_info.get("current_hp", 999)
        
        if not target_hp:
            return [random.choice(targets)]
        
        min_hp = min(target_hp.values())
        weakest = [pid for pid, hp in target_hp.items() if hp == min_hp]
        return [random.choice(weakest)]
    
    def select_cards_for_use(self, available_cards: List[Card], available_targets_dict: Dict[str, List[int]]) -> tuple[Optional[Card], List[int]]:
        """选择出牌：优先自保，其次攻击敌人"""
        if not available_cards:
            return None, []
        
        # 优先级1: 如果血量低于最大值，优先使用桃
        if self.game_state and "self" in self.game_state:
            my_hp = self.game_state["self"].get("current_hp", 2)
            my_max_hp = self.game_state["self"].get("max_hp", 2)
            if my_hp < my_max_hp:
                tao_cards = [c for c in available_cards if c.name == CardName.TAO]
                if tao_cards:
                    return tao_cards[0], [self.player_id]
        
        # 优先级2: 如果有杀且曹军在攻击范围内，出杀
        sha_cards = [c for c in available_cards if c.name == CardName.SHA]
        if sha_cards:
            attackable = available_targets_dict.get("杀", [])
            targets = self.select_targets(attackable, sha_cards[0])
            if targets:
                return sha_cards[0], targets
        
        # 优先级3: 决斗攻击曹军
        juedou_cards = [c for c in available_cards if c.name == CardName.JUE_DOU]
        if juedou_cards:
            all_targets = available_targets_dict.get("决斗", [])
            targets = self.select_targets(all_targets, juedou_cards[0])
            if targets:
                return juedou_cards[0], targets
        
        # 优先级4: AOE（慎用，因为会伤到赵云）
        # 只有在曹军数量 >= 2时才使用AOE
        enemy_count = 0
        if self.game_state and "players" in self.game_state:
            for p in self.game_state["players"]:
                if self._is_enemy(p.get("player_id")) and p.get("status") != "死亡":
                    enemy_count += 1
        
        if enemy_count >= 2:
            nanman_cards = [c for c in available_cards if c.name == CardName.NAN_MAN_RU_QIN]
            if nanman_cards:
                return nanman_cards[0], [-1]
            
            wanjian_cards = [c for c in available_cards if c.name == CardName.WAN_JIAN_QI_FA]
            if wanjian_cards:
                return wanjian_cards[0], [-1]
        
        # 没有合适的牌
        return None, []
    
    def ask_use_card_response(self, card_name: CardName, available_cards: List[Card], context: str = "") -> Optional[Card]:
        """响应卡牌请求"""
        matching_cards = [c for c in available_cards if c.name == card_name]
        return matching_cards[0] if matching_cards else None


class CaoJunAI(Control):
    """第二章曹军AI（反贼）
    
    特点：
    - 知道阿斗（ADOU）和赵云（ZHAO_YUN_2）是敌人
    - 曹军之间互相配合，不会互相攻击
    - 攻击优先级：阿斗（主公）> 赵云 > 其他
    - 激进策略：优先输出而非自保
    """
    
    def __init__(self, player_id: Optional[int] = None):
        super().__init__(ControlType.SIMPLE_AI, player_id)
        self.primary_target = CharacterName.ADOU  # 首要目标
        self.secondary_target = CharacterName.ZHAO_YUN_2  # 次要目标
        self.ally_character = CharacterName.CAO_JUN
    
    def _find_player_by_character(self, character: CharacterName) -> Optional[int]:
        """根据武将枚举查找玩家ID"""
        if not self.game_state or "players" not in self.game_state:
            return None
        for player_info in self.game_state["players"]:
            if player_info.get("character_name") == character and player_info.get("status") != "死亡":
                return player_info.get("player_id")
        return None
    
    def _is_ally(self, player_id: int) -> bool:
        """判断是否是盟友（其他曹军CAO_JUN）"""
        if not self.game_state or "players" not in self.game_state:
            return False
        for player_info in self.game_state["players"]:
            if player_info.get("player_id") == player_id:
                character = player_info.get("character_name")
                return character == self.ally_character
        return False
    
    def select_targets(self, available_targets: List[int], card: Optional[Card] = None) -> List[int]:
        """选择目标：阿斗 > 赵云 > 其他，不攻击曹军"""
        if not available_targets:
            return []
        
        # 过滤掉盟友
        non_ally_targets = [tid for tid in available_targets if not self._is_ally(tid)]
        if not non_ally_targets:
            return []
        
        # 优先级1: 阿斗
        adou_id = self._find_player_by_character(self.primary_target)
        if adou_id and adou_id in non_ally_targets:
            return [adou_id]
        
        # 优先级2: 赵云
        zhaoyun_id = self._find_player_by_character(self.secondary_target)
        if zhaoyun_id and zhaoyun_id in non_ally_targets:
            return [zhaoyun_id]
        
        # 优先级3: 其他非盟友，选血量最少的
        return self._select_weakest(non_ally_targets)
    
    def _select_weakest(self, targets: List[int]) -> List[int]:
        """选择血量最少的目标"""
        if not targets or not self.game_state:
            return []
        
        target_hp = {}
        for player_info in self.game_state.get("players", []):
            pid = player_info.get("player_id")
            if pid in targets:
                target_hp[pid] = player_info.get("current_hp", 999)
        
        if not target_hp:
            return [random.choice(targets)]
        
        min_hp = min(target_hp.values())
        weakest = [pid for pid, hp in target_hp.items() if hp == min_hp]
        return [random.choice(weakest)]
    
    def select_cards_for_use(self, available_cards: List[Card], available_targets_dict: Dict[str, List[int]]) -> tuple[Optional[Card], List[int]]:
        """选择出牌：激进策略，优先输出"""
        if not available_cards:
            return None, []
        
        adou_id = self._find_player_by_character(self.primary_target)
        zhaoyun_id = self._find_player_by_character(self.secondary_target)
        
        # 优先级1: 杀攻击阿斗
        sha_cards = [c for c in available_cards if c.name == CardName.SHA]
        if sha_cards and adou_id:
            attackable = available_targets_dict.get("杀", [])
            if adou_id in attackable:
                return sha_cards[0], [adou_id]
        
        # 优先级2: 杀攻击赵云
        if sha_cards and zhaoyun_id:
            attackable = available_targets_dict.get("杀", [])
            if zhaoyun_id in attackable:
                return sha_cards[0], [zhaoyun_id]
        
        # 优先级3: 决斗攻击阿斗
        juedou_cards = [c for c in available_cards if c.name == CardName.JUE_DOU]
        if juedou_cards and adou_id:
            all_targets = available_targets_dict.get("决斗", [])
            if adou_id in all_targets:
                return juedou_cards[0], [adou_id]
        
        # 优先级4: 决斗攻击赵云
        if juedou_cards and zhaoyun_id:
            all_targets = available_targets_dict.get("决斗", [])
            if zhaoyun_id in all_targets:
                return juedou_cards[0], [zhaoyun_id]
        
        # 优先级5: AOE锦囊
        nanman_cards = [c for c in available_cards if c.name == CardName.NAN_MAN_RU_QIN]
        if nanman_cards:
            return nanman_cards[0], [-1]
        
        wanjian_cards = [c for c in available_cards if c.name == CardName.WAN_JIAN_QI_FA]
        if wanjian_cards:
            return wanjian_cards[0], [-1]
        
        # 优先级6: 使用任何可用的杀/决斗
        if sha_cards:
            attackable = available_targets_dict.get("杀", [])
            targets = self.select_targets(attackable, sha_cards[0])
            if targets:
                return sha_cards[0], targets
        
        if juedou_cards:
            all_targets = available_targets_dict.get("决斗", [])
            targets = self.select_targets(all_targets, juedou_cards[0])
            if targets:
                return juedou_cards[0], targets
        
        # 优先级7: 如果血量危险（<=1），使用桃
        if self.game_state and "self" in self.game_state:
            my_hp = self.game_state["self"].get("current_hp", 3)
            if my_hp <= 1:
                tao_cards = [c for c in available_cards if c.name == CardName.TAO]
                if tao_cards:
                    return tao_cards[0], [self.player_id]
        
        # 没有合适的牌
        return None, []
    
    def ask_use_card_response(self, card_name: CardName, available_cards: List[Card], context: str = "") -> Optional[Card]:
        """响应卡牌请求"""
        matching_cards = [c for c in available_cards if c.name == card_name]
        return matching_cards[0] if matching_cards else None
