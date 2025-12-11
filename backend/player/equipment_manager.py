# 装备管理器模块
"""统一管理玩家装备的模块"""
from typing import Optional, List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.card.card import Card
from backend.deck.deck import Deck
from backend.utils.logger import game_logger
from backend.utils.event_sender import send_discard_card_event, send_equip_change_event
from config.enums import CardName, EquipmentType


class EquipmentManager:
    """装备管理器（统一管理所有装备槽位）"""
    
    # 装备名到槽位类型的映射
    CARD_TO_SLOT: Dict[CardName, str] = {
        CardName.QING_GANG_JIAN: "weapon",
        CardName.ZHU_GE_LIAN_NU: "weapon",
        CardName.REN_WANG_DUN: "armor",
        CardName.JIN_GONG_MA: "horse_minus",
        CardName.FANG_YU_MA: "horse_plus",
    }
    
    # 槽位类型到装备类型的映射
    SLOT_TO_EQUIPMENT_TYPE: Dict[str, EquipmentType] = {
        "weapon": EquipmentType.WEAPON,
        "armor": EquipmentType.ARMOR,
        "horse_plus": EquipmentType.HORSE_PLUS,
        "horse_minus": EquipmentType.HORSE_MINUS,
    }
    
    # 槽位类型到中文名称的映射
    SLOT_TO_NAME: Dict[str, str] = {
        "weapon": "武器",
        "armor": "防具",
        "horse_plus": "防御马",
        "horse_minus": "进攻马",
    }
    
    def __init__(self, player_id: int, player_name: str, deck: Deck):
        """初始化装备管理器
        
        Args:
            player_id: 玩家ID
            player_name: 玩家名称
            deck: 牌堆引用
        """
        self.player_id = player_id
        self.player_name = player_name
        self.deck = deck
        
        # 装备槽位
        self.weapon: Optional[Card] = None
        self.armor: Optional[Card] = None
        self.horse_plus: Optional[Card] = None
        self.horse_minus: Optional[Card] = None
    
    def get_slot(self, slot_name: str) -> Optional[Card]:
        """获取指定槽位的装备
        
        Args:
            slot_name: 槽位名称（"weapon", "armor", "horse_plus", "horse_minus"）
            
        Returns:
            装备牌或None
        """
        return getattr(self, slot_name, None)
    
    def set_slot(self, slot_name: str, card: Optional[Card]) -> None:
        """设置指定槽位的装备
        
        Args:
            slot_name: 槽位名称
            card: 装备牌或None（卸下装备）
        """
        setattr(self, slot_name, card)
    
    def get_all_equipment(self) -> List[Card]:
        """获取所有装备
        
        Returns:
            所有装备牌的列表
        """
        equipment = []
        for slot_name in ["weapon", "armor", "horse_plus", "horse_minus"]:
            card = self.get_slot(slot_name)
            if card:
                equipment.append(card)
        return equipment
    
    def get_equipment_count(self) -> int:
        """获取装备数量
        
        Returns:
            装备数量
        """
        return len(self.get_all_equipment())
    
    def equip(self, card: Card) -> bool:
        """装备牌
        
        Args:
            card: 要装备的牌
            
        Returns:
            是否装备成功
        """
        if not card.is_equipment():
            return False
        
        # 获取槽位名称
        slot_name = self.CARD_TO_SLOT.get(card.name_enum)
        if not slot_name:
            return False
        
        # 获取旧装备
        old_equipment = self.get_slot(slot_name)
        
        # 如果有旧装备，进入弃牌堆
        if old_equipment:
            self.deck.discard_card(old_equipment)
            send_discard_card_event(old_equipment, self.player_id)
        
        # 设置新装备
        self.set_slot(slot_name, card)
        
        # 记录装备日志
        slot_name_cn = self.SLOT_TO_NAME[slot_name]
        game_logger.log_player_equip(self.player_name, card.name, slot_name_cn)
        
        # 发送装备事件
        equip_type = self.SLOT_TO_EQUIPMENT_TYPE[slot_name]
        send_equip_change_event(self.player_id, card.name_enum, equip_type)
        
        return True
    
    def unequip_all(self) -> List[tuple]:
        """卸下所有装备
        
        Returns:
            被卸下的装备列表，每个元素为 (slot_name, card) 元组
        """
        unequipped = []
        for slot_name in ["weapon", "armor", "horse_plus", "horse_minus"]:
            card = self.get_slot(slot_name)
            if card:
                self.deck.discard_card(card)
                send_discard_card_event(card, self.player_id)
                unequipped.append((slot_name, card))
                self.set_slot(slot_name, None)
        return unequipped
    
    def discard_all(self) -> None:
        """弃掉所有装备（用于死亡等情况）"""
        for slot_name in ["weapon", "armor", "horse_plus", "horse_minus"]:
            card = self.get_slot(slot_name)
            if card:
                self.deck.discard_card(card)
                send_discard_card_event(card, self.player_id)
                self.set_slot(slot_name, None)
    
    def get_equipment_type(self, card_name: CardName) -> Optional[EquipmentType]:
        """获取装备类型
        
        Args:
            card_name: 装备牌名
            
        Returns:
            装备类型或None
        """
        slot_name = self.CARD_TO_SLOT.get(card_name)
        if slot_name:
            return self.SLOT_TO_EQUIPMENT_TYPE.get(slot_name)
        return None

