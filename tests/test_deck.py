# 牌堆测试
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.deck.deck import Deck
from backend.card.card import Card
from config.simple_card_config import SimpleGameConfig, SimpleCardConfig, SimplePlayerConfig
from config.enums import CardSuit, CardName, ControlType, PlayerIdentity, CharacterName


class TestDeck(unittest.TestCase):
    """牌堆测试"""
    
    def setUp(self):
        """测试前准备"""
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=5),
            SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 2, count=3),
            SimpleCardConfig(CardName.TAO, CardSuit.HEARTS, 1, count=2),
        ]
        players_config = [
            SimplePlayerConfig("测试玩家", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI)
        ]
        self.config = SimpleGameConfig(deck_config=deck_config, players_config=players_config, shuffle_deck=True)
    
    def test_deck_shuffle(self):
        """测试牌堆洗牌"""
        # 创建两个牌堆，应该顺序不同（由于随机性）
        deck1 = Deck(self.config)
        deck2 = Deck(self.config)
        
        # 验证牌堆大小相同
        self.assertEqual(len(deck1.cards), len(deck2.cards))
        self.assertEqual(len(deck1.cards), 10)  # 5+3+2=10
        
        # 由于洗牌是随机的，两个牌堆的顺序很可能不同
        # 但至少应该包含相同的牌
        deck1_names = [card.name_enum for card in deck1.cards]
        deck2_names = [card.name_enum for card in deck2.cards]
        
        # 统计每种牌的数量
        from collections import Counter
        count1 = Counter(deck1_names)
        count2 = Counter(deck2_names)
        
        self.assertEqual(count1, count2)
    
    def test_deck_draw_card(self):
        """测试抽牌"""
        deck = Deck(self.config)
        initial_size = len(deck.cards)
        
        card = deck.draw_card()
        
        self.assertIsNotNone(card)
        self.assertEqual(len(deck.cards), initial_size - 1)
        self.assertIsInstance(card, Card)
    
    def test_deck_discard_card(self):
        """测试弃牌"""
        deck = Deck(self.config)
        card = deck.draw_card()
        initial_discard_size = len(deck.discard_pile)
        
        deck.discard_card(card)
        
        self.assertEqual(len(deck.discard_pile), initial_discard_size + 1)
        self.assertIn(card, deck.discard_pile)
    
    def test_deck_empty_and_reset(self):
        """测试牌堆抽空后利用弃牌堆重新洗牌"""
        # 创建不打乱的牌堆以便测试
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=3),
        ]
        players_config = [
            SimplePlayerConfig("测试玩家", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI)
        ]
        config = SimpleGameConfig(deck_config=deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        
        # 抽完所有牌
        drawn_cards = []
        while not deck.is_empty():
            card = deck.draw_card()
            if card:
                drawn_cards.append(card)
        
        self.assertTrue(deck.is_empty())
        self.assertEqual(len(drawn_cards), 3)
        
        # 将所有牌放入弃牌堆
        for card in drawn_cards:
            deck.discard_card(card)
        
        self.assertEqual(len(deck.discard_pile), 3)
        self.assertEqual(len(deck.cards), 0)
        
        # 再次抽牌，应该自动从弃牌堆重新洗牌
        card = deck.draw_card()
        self.assertIsNotNone(card)
        self.assertEqual(len(deck.cards), 2)  # 3-1=2
        self.assertEqual(len(deck.discard_pile), 0)  # 弃牌堆应该被清空
    
    def test_deck_multiple_resets(self):
        """测试多次重置牌堆"""
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=2),
        ]
        players_config = [
            SimplePlayerConfig("测试玩家", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI)
        ]
        config = SimpleGameConfig(deck_config=deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        
        # 第一次抽完并重置
        card1 = deck.draw_card()
        card2 = deck.draw_card()
        deck.discard_card(card1)
        deck.discard_card(card2)
        
        # 再次抽牌
        card3 = deck.draw_card()
        self.assertIsNotNone(card3)
        
        # 再次抽牌
        card4 = deck.draw_card()
        self.assertIsNotNone(card4)
        
        # 验证可以持续抽牌
        self.assertTrue(card3.name_enum == CardName.SHA or card4.name_enum == CardName.SHA)
    
    def test_deck_get_size(self):
        """测试获取牌堆大小"""
        deck = Deck(self.config)
        
        size = deck.get_deck_size()
        self.assertEqual(size, len(deck.cards))
        self.assertEqual(size, 10)
        
        # 抽一张牌后
        deck.draw_card()
        self.assertEqual(deck.get_deck_size(), 9)
    
    def test_deck_get_discard_size(self):
        """测试获取弃牌堆大小"""
        deck = Deck(self.config)
        
        initial_discard_size = deck.get_discard_size()
        self.assertEqual(initial_discard_size, 0)
        
        card = deck.draw_card()
        deck.discard_card(card)
        
        self.assertEqual(deck.get_discard_size(), 1)


if __name__ == '__main__':
    unittest.main()
