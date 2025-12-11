# Player类测试
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.player.player import Player
from backend.deck.deck import Deck
from backend.card.card import Card
from config.simple_card_config import SimpleGameConfig, SimpleCardConfig, SimplePlayerConfig
from config.enums import CardSuit, CardName, ControlType, PlayerIdentity, CharacterName


class TestPlayer(unittest.TestCase):
    """Player类测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建简单的牌堆配置
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=10),
            SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 2, count=10),
            SimpleCardConfig(CardName.TAO, CardSuit.HEARTS, 1, count=5),
        ]
        players_config = [
            SimplePlayerConfig("测试玩家", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI)
        ]
        self.config = SimpleGameConfig(deck_config=deck_config, players_config=players_config, shuffle_deck=False)
        self.deck = Deck(self.config)
    
    def test_player_draw_card(self):
        """测试玩家摸牌"""
        player = Player(1, "测试玩家", ControlType.AI, self.deck, PlayerIdentity.REBEL, CharacterName.BAI_BAN_WU_JIANG)
        initial_hand_size = len(player.hand_cards)
        initial_deck_size = len(self.deck.cards)
        
        # 摸2张牌
        drawn_cards = player.draw_card(2)
        
        self.assertEqual(len(drawn_cards), 2)
        self.assertEqual(len(player.hand_cards), initial_hand_size + 2)
        self.assertEqual(len(self.deck.cards), initial_deck_size - 2)
        self.assertTrue(all(card in player.hand_cards for card in drawn_cards))
    
    def test_player_draw_card_phase(self):
        """测试玩家摸牌阶段"""
        player = Player(1, "测试玩家", ControlType.AI, self.deck, PlayerIdentity.REBEL, CharacterName.BAI_BAN_WU_JIANG)
        initial_hand_size = len(player.hand_cards)
        
        # 摸牌阶段（默认摸2张）
        drawn_cards = player.draw_card_phase()
        
        self.assertEqual(len(drawn_cards), 2)
        self.assertEqual(len(player.hand_cards), initial_hand_size + 2)
    
    def test_player_discard_card(self):
        """测试玩家弃牌"""
        player = Player(1, "测试玩家", ControlType.AI, self.deck, PlayerIdentity.REBEL, CharacterName.BAI_BAN_WU_JIANG)
        
        # 给玩家超过血量上限的手牌
        for i in range(6):
            card = Card(CardSuit.HEARTS, i + 1, CardName.SHA)
            player.hand_cards.append(card)
        
        initial_hand_size = len(player.hand_cards)
        initial_discard_size = len(self.deck.discard_pile)
        
        # 弃牌（应该弃掉超过血量上限的部分）
        discarded_cards = player.discard_card()
        
        # 验证弃牌数量
        expected_discard_count = initial_hand_size - player.current_hp
        self.assertEqual(len(discarded_cards), expected_discard_count)
        self.assertEqual(len(player.hand_cards), player.current_hp)
        self.assertEqual(len(self.deck.discard_pile), initial_discard_size + expected_discard_count)
    
    def test_player_discard_card_no_excess(self):
        """测试玩家手牌未超限时不弃牌"""
        player = Player(1, "测试玩家", ControlType.AI, self.deck, PlayerIdentity.REBEL, CharacterName.BAI_BAN_WU_JIANG)
        
        # 手牌数量等于血量上限
        player.hand_cards = [Card(CardSuit.HEARTS, i + 1, CardName.SHA) for i in range(4)]
        
        discarded_cards = player.discard_card()
        
        self.assertEqual(len(discarded_cards), 0)
        self.assertEqual(len(player.hand_cards), 4)


if __name__ == '__main__':
    unittest.main()

