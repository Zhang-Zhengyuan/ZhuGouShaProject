# 日志系统测试
import unittest
import sys
import os
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.logger import game_logger
from backend.player.player import Player
from backend.deck.deck import Deck
from backend.card.card import Card
from config.simple_card_config import SimpleGameConfig, SimpleCardConfig, SimplePlayerConfig
from config.enums import CardSuit, CardName, ControlType, PlayerIdentity, CharacterName


class TestLogger(unittest.TestCase):
    """日志系统测试"""
    
    def setUp(self):
        """测试前准备"""
        # 开始测试会话日志
        self.log_path = game_logger.start_game_session(is_test=True)
        self.assertIsNotNone(self.log_path)
    
    def tearDown(self):
        """测试后清理"""
        game_logger.end_game_session()
    
    def test_logger_initialization(self):
        """测试日志系统初始化"""
        self.assertIsNotNone(game_logger.logger)
        self.assertTrue(game_logger.is_test_mode)
    
    def test_log_info(self):
        """测试记录信息日志"""
        game_logger.log_info("测试信息日志")
        # 验证日志记录成功（不抛出异常）
    
    def test_log_warning(self):
        """测试记录警告日志"""
        game_logger.log_warning("测试警告日志")
        # 验证日志记录成功（不抛出异常）
    
    def test_log_error(self):
        """测试记录错误日志"""
        game_logger.log_error("测试错误日志")
        # 验证日志记录成功（不抛出异常）
    
    def test_log_debug(self):
        """测试记录调试日志"""
        game_logger.log_debug("测试调试日志")
        # 验证日志记录成功（不抛出异常）
    
    def test_log_player_draw_cards(self):
        """测试记录玩家摸牌日志"""
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=5),
        ]
        players_config = [
            SimplePlayerConfig("测试玩家", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI)
        ]
        config = SimpleGameConfig(deck_config=deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        player = Player(1, "测试玩家", ControlType.AI, deck, PlayerIdentity.REBEL, CharacterName.BAI_BAN_WU_JIANG)
        
        # 摸牌
        cards = player.draw_card(2)
        
        # 记录摸牌日志
        game_logger.log_player_draw_cards(player.name, cards)
        # 验证日志记录成功（不抛出异常）
    
    def test_log_player_play_card(self):
        """测试记录玩家出牌日志"""
        game_logger.log_player_play_card("测试玩家", "杀", [2], ["目标玩家"])
        # 验证日志记录成功（不抛出异常）
    
    def test_log_player_status(self):
        """测试记录玩家状态日志"""
        deck_config = [
            SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, count=5),
        ]
        players_config = [
            SimplePlayerConfig("测试玩家", CharacterName.BAI_BAN_WU_JIANG, PlayerIdentity.REBEL, ControlType.AI)
        ]
        config = SimpleGameConfig(deck_config=deck_config, players_config=players_config, shuffle_deck=False)
        deck = Deck(config)
        player = Player(1, "测试玩家", ControlType.AI, deck, PlayerIdentity.REBEL, CharacterName.BAI_BAN_WU_JIANG)
        
        # 记录玩家状态
        game_logger.log_player_status(
            player_name=player.name,
            player_id=player.player_id,
            current_hp=player.current_hp,
            max_hp=player.max_hp,
            hand_cards=player.hand_cards,
            weapon=player.weapon,
            armor=player.armor,
            horse_plus=player.horse_plus,
            horse_minus=player.horse_minus,
            identity=player.identity.value if player.identity else None,
        )
        # 验证日志记录成功（不抛出异常）
    
    def test_log_game_start(self):
        """测试记录游戏开始日志"""
        game_logger.log_game_start()
        # 验证日志记录成功（不抛出异常）
    
    def test_log_session_lifecycle(self):
        """测试日志会话生命周期"""
        # 开始会话
        log_path = game_logger.start_game_session(is_test=True)
        self.assertIsNotNone(log_path)
        
        # 记录一些日志
        game_logger.log_info("会话测试日志")
        
        # 结束会话
        game_logger.end_game_session()
        
        # 重新开始会话
        log_path2 = game_logger.start_game_session(is_test=True)
        self.assertIsNotNone(log_path2)


if __name__ == '__main__':
    unittest.main()

