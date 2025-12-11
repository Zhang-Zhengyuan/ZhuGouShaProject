# 牌堆模块
import random
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.card.card import Card
from backend.utils.logger import game_logger
from config.enums import CardSuit, CardType, CardName


class Deck:
    """牌堆类
    
    管理游戏中的牌堆
    """
    
    def __init__(self, config):
        """初始化牌堆
        
        Args:
            config: 游戏配置，必须提供
        """
        if config is None:
            raise ValueError("牌堆必须使用配置创建，不能为None")
        
        self.cards: List[Card] = []
        self.discard_pile: List[Card] = []
        self.config = config
        self._initialize_deck()
        
        # 根据配置决定是否打乱牌堆
        if self.config.shuffle_deck:
            self.shuffle()
    
    def _initialize_deck(self) -> None:
        """初始化牌堆，创建所有牌"""
        game_logger.log_info("开始初始化牌堆...")
        # 使用配置创建牌堆
        self._create_deck_from_config()
        game_logger.log_info(f"牌堆初始化完成，总牌数: {len(self.cards)}")
    
    def _create_deck_from_config(self) -> None:
        """根据配置创建牌堆"""
        for card_config in self.config.deck_config:
            for _ in range(card_config.count):
                card = Card(
                    suit=card_config.suit,
                    rank=card_config.rank,
                    name=card_config.name
                )
                self.cards.append(card)
    
    
    def shuffle(self) -> None:
        """洗牌"""
        random.shuffle(self.cards)
    
    def draw_card(self) -> Optional[Card]:
        """抽一张牌
        
        Returns:
            抽到的牌，如果牌堆为空则返回None
        """
        if not self.cards:
            # 如果牌堆为空，将弃牌堆洗牌后重新使用
            if self.discard_pile:
                self.cards = self.discard_pile.copy()
                self.discard_pile.clear()
                self.shuffle()
            else:
                return None
        
        return self.cards.pop(0)
    
    def draw_cards(self, count: int) -> List[Card]:
        """抽多张牌
        
        Args:
            count: 抽牌数量
            
        Returns:
            抽到的牌列表
        """
        cards = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                cards.append(card)
            else:
                break
        return cards
    
    def discard_card(self, card: Card) -> None:
        """弃牌
        
        Args:
            card: 要弃的牌
        """
        # 进入弃牌堆时刷新视为属性为原始牌名
        card.reset_regarded_as()
        self.discard_pile.append(card)
    
    def discard_cards(self, cards: List[Card]) -> None:
        """弃多张牌
        
        Args:
            cards: 要弃的牌列表
        """
        # 进入弃牌堆时刷新每张牌的视为属性为原始牌名
        for card in cards:
            card.reset_regarded_as()
        self.discard_pile.extend(cards)
    
    def get_deck_size(self) -> int:
        """获取牌堆大小
        
        Returns:
            牌堆中牌的数量
        """
        return len(self.cards)
    
    def get_discard_size(self) -> int:
        """获取弃牌堆大小
        
        Returns:
            弃牌堆中牌的数量
        """
        return len(self.discard_pile)
    
    def is_empty(self) -> bool:
        """检查牌堆是否为空
        
        Returns:
            牌堆是否为空
        """
        return len(self.cards) == 0
