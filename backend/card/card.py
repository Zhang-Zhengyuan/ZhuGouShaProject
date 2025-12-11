# 牌模块
from typing import List, Union
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.utils.logger import game_logger
from config.enums import CardSuit, CardType, EquipmentType, CardName, TargetType
from config.card_properties import get_card_properties


class Card:
    """牌类
    
    只有data，包含牌的基本信息
    """
    
    def __init__(self, suit: CardSuit, rank: int, name: CardName):
        """初始化牌
        
        Args:
            suit: 花色
            rank: 点数
            name: 牌名枚举
        """
        self.suit = suit  # 花色
        self.rank = rank  # 点数
        self.name_enum = name  # 牌名枚举（用于代码判断）
        
        # 从牌属性配置中获取其他属性
        properties = get_card_properties(name)
        self.name = properties["display_name"]  # 中文显示名称
        self.card_type = properties["card_type"]  # 牌类型（基本/锦囊/装备）
        self.target_type = properties["target_type"]  # 牌指定目标：攻击距离目标/所有目标/距离为1的目标/自己
        self.attack_range = properties["attack_range"]  # 攻击距离（仅对装备牌有效）
        
        # 视为属性，初始化时与牌名一致
        self.regarded_as = self.name  # 当前被视为的牌名
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}({self.suit.value}{self.rank})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"Card(suit={self.suit}, rank={self.rank}, name='{self.name}', type={self.card_type})"
    
    def is_equipment(self) -> bool:
        """是否为装备牌"""
        return self.card_type == CardType.EQUIPMENT
    
    def is_basic(self) -> bool:
        """是否为基本牌"""
        return self.card_type == CardType.BASIC
    
    def is_trick(self) -> bool:
        """是否为锦囊牌"""
        return self.card_type == CardType.TRICK
    
    def set_regarded_as(self, regarded_as: Union[str, CardName]) -> None:
        """设置视为属性
        
        Args:
            regarded_as: 要视为的牌名（可以是字符串或CardName枚举）
        """
        self.regarded_as = regarded_as.value if isinstance(regarded_as, CardName) else regarded_as
    
    def reset_regarded_as(self) -> None:
        """重置视为属性为原始牌名"""
        self.regarded_as = self.name
    
    def get_regarded_as(self) -> str:
        """获取当前视为的牌名
        
        Returns:
            当前被视为的牌名
        """
        return self.regarded_as
