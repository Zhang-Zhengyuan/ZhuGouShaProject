# 游戏结束逻辑测试
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.player_controller.player_controller import PlayerController
from backend.deck.deck import Deck
from config.simple_card_config import SimpleGameConfig, SimpleCardConfig, SimplePlayerConfig
from config.enums import CardSuit, CardName, ControlType, PlayerIdentity, CharacterName, PlayerStatus


class TestGameEnd(unittest.TestCase):
    """游戏结束逻辑测试"""
    
    def setUp(self):
        """测试前准备"""
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=20),
            SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 2, count=10),
        ]
        self.deck_config = deck_config
    
    def test_game_over_lord_dead_rebel_win(self):
        """测试主公死亡，反贼胜利"""
        players_config = [
            SimplePlayerConfig("主公", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LORD, ControlType.AI),
            SimplePlayerConfig("反贼1", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI),
            SimplePlayerConfig("反贼2", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI),
        ]
        config = SimpleGameConfig(deck_config=self.deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        player_controller = PlayerController(config, deck)
        
        # 主公死亡
        lord = player_controller.get_lord()
        lord.die()
        
        # 验证游戏结束
        self.assertTrue(player_controller.game_over())
        
        # 验证反贼胜利
        winner = player_controller.get_winner()
        self.assertIsNotNone(winner)
        self.assertIn("反贼胜利", winner)
    
    def test_game_over_lord_and_loyalist_win(self):
        """测试主公和忠臣胜利（反贼和内奸全部死亡）"""
        players_config = [
            SimplePlayerConfig("主公", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LORD, ControlType.AI),
            SimplePlayerConfig("忠臣", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LOYALIST, ControlType.AI),
            SimplePlayerConfig("反贼", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI),
            SimplePlayerConfig("内奸", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.TRAITOR, ControlType.AI),
        ]
        config = SimpleGameConfig(deck_config=self.deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        player_controller = PlayerController(config, deck)
        
        # 反贼和内奸死亡
        rebels = [p for p in player_controller.players if p.identity == PlayerIdentity.REBEL]
        traitors = [p for p in player_controller.players if p.identity == PlayerIdentity.TRAITOR]
        
        for rebel in rebels:
            rebel.die()
        for traitor in traitors:
            traitor.die()
        
        # 验证游戏结束
        self.assertTrue(player_controller.game_over())
        
        # 验证主公和忠臣胜利
        winner = player_controller.get_winner()
        self.assertIsNotNone(winner)
        self.assertIn("主公，忠臣胜利", winner)
    
    def test_game_over_traitor_alone_win(self):
        """测试内奸单独胜利（只剩内奸一人）"""
        players_config = [
            SimplePlayerConfig("主公", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LORD, ControlType.AI),
            SimplePlayerConfig("忠臣", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LOYALIST, ControlType.AI),
            SimplePlayerConfig("反贼", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI),
            SimplePlayerConfig("内奸", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.TRAITOR, ControlType.AI),
        ]
        config = SimpleGameConfig(deck_config=self.deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        player_controller = PlayerController(config, deck)
        
        # 除了内奸外，其他人都死亡
        traitor = [p for p in player_controller.players if p.identity == PlayerIdentity.TRAITOR][0]
        others = [p for p in player_controller.players if p != traitor]
        
        for player in others:
            player.die()
        
        # 验证游戏结束
        self.assertTrue(player_controller.game_over())
        
        # 验证内奸胜利
        winner = player_controller.get_winner()
        self.assertIsNotNone(winner)
        self.assertIn("内奸胜利", winner)
        self.assertIn(traitor.name, winner)
    
    def test_game_not_over(self):
        """测试游戏未结束的情况"""
        players_config = [
            SimplePlayerConfig("主公", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LORD, ControlType.AI),
            SimplePlayerConfig("忠臣", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.LOYALIST, ControlType.AI),
            SimplePlayerConfig("反贼", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI),
        ]
        config = SimpleGameConfig(deck_config=self.deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        player_controller = PlayerController(config, deck)
        
        # 所有人存活
        self.assertFalse(player_controller.game_over())
        
        winner = player_controller.get_winner()
        self.assertIsNone(winner)


if __name__ == '__main__':
    unittest.main()

