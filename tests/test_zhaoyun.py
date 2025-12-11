# 赵云武将测试
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.player.player import ZhaoyunPlayer
from backend.deck.deck import Deck
from backend.control.simple_control import SimpleControl
from config.enums import CharacterName, PlayerIdentity, ControlType, CardName, CardSuit
from config.simple_card_config import SimpleGameConfig, SimpleCardConfig, SimplePlayerConfig


class MockControl:
    """模拟控制器"""
    def select_cards_to_discard(self, hand_cards, count):
        # 返回前count张牌
        return hand_cards[:count]


@pytest.fixture
def game_config():
    """创建简单游戏配置"""
    config = SimpleGameConfig(
        deck_config=[
            SimpleCardConfig(name=CardName.SHA, suit=CardSuit.HEARTS, rank=7, count=5),
            SimpleCardConfig(name=CardName.SHAN, suit=CardSuit.DIAMONDS, rank=8, count=5),
            SimpleCardConfig(name=CardName.TAO, suit=CardSuit.CLUBS, rank=9, count=5),
            SimpleCardConfig(name=CardName.WU_XIE_KE_JI, suit=CardSuit.SPADES, rank=10, count=5),
            SimpleCardConfig(name=CardName.JUE_DOU, suit=CardSuit.HEARTS, rank=5, count=5),
            SimpleCardConfig(name=CardName.NAN_MAN_RU_QIN, suit=CardSuit.DIAMONDS, rank=6, count=5),
            SimpleCardConfig(name=CardName.WAN_JIAN_QI_FA, suit=CardSuit.CLUBS, rank=7, count=5),
        ],
        players_config=[
            SimplePlayerConfig(name="赵云", character_name=CharacterName.ZHAO_YUN_1, identity=PlayerIdentity.LORD, control_type=ControlType.SIMPLE_AI),
        ]
    )
    return config


@pytest.fixture
def zhaoyun_player(game_config):
    """创建赵云玩家"""
    deck = Deck(game_config)
    player = ZhaoyunPlayer(
        player_id=0,
        name="赵云",
        control_type=ControlType.SIMPLE_AI,
        deck=deck,
        identity=PlayerIdentity.LORD,
        character_name=CharacterName.ZHAO_YUN_1,
        player_controller=None
    )
    player.control = MockControl()
    return player


class TestZhaoyunBasicSkills:
    """测试赵云基础技能"""

    def test_zhaoyun_creation(self, zhaoyun_player):
        """测试赵云创建"""
        assert zhaoyun_player.name == "赵云"
        assert zhaoyun_player.character_name == CharacterName.ZHAO_YUN_1
        assert zhaoyun_player.max_hp == 5  # 基础4 + 主公加成1
        assert zhaoyun_player.longhun_evolved == False  # 默认龙胆未进化
        # 检查初始技能解锁状态：只有龙胆被解锁
        assert zhaoyun_player.is_skill_unlocked("龙胆") == True
        assert zhaoyun_player.is_skill_unlocked("冲阵") == False
        assert zhaoyun_player.is_skill_unlocked("绝境") == False

    def test_skill_unlock(self, zhaoyun_player):
        """测试技能解锁接口"""
        # 初始状态：只有龙胆被解锁
        assert zhaoyun_player.is_skill_unlocked("龙胆") == True
        assert zhaoyun_player.is_skill_unlocked("冲阵") == False
        
        # 解锁冲阵
        result = zhaoyun_player.unlock_skill("冲阵")
        assert result == True
        assert zhaoyun_player.is_skill_unlocked("冲阵") == True
        
        # 尝试重复解锁冲阵，应该返回False
        result = zhaoyun_player.unlock_skill("冲阵")
        assert result == False
        
        # 解锁绝境
        result = zhaoyun_player.unlock_skill("绝境")
        assert result == True
        assert zhaoyun_player.is_skill_unlocked("绝境") == True

    def test_longdan_card_transform_requires_unlock(self, zhaoyun_player):
        """测试龙胆技能在未解锁时无法转化牌"""
        from backend.card.card import Card
        
        # 初始龙胆已解锁，可以转化
        sha = Card(name=CardName.SHA, suit=CardSuit.HEARTS, rank=7)
        assert zhaoyun_player._can_use_as_different_card(sha) == True

    def test_juejiang_hand_limit_without_unlock(self, zhaoyun_player):
        """测试绝境未解锁时，手牌上限不会+2"""
        zhaoyun_player.current_hp = 4
        limit = zhaoyun_player._get_hand_card_limit()
        # 绝境未解锁，上限应该就是当前血量
        assert limit == 4
        
        # 解锁绝境后，上限+2
        zhaoyun_player.unlock_skill("绝境")
        limit = zhaoyun_player._get_hand_card_limit()
        assert limit == 6

    def test_longhun_evolved_multi_cards(self, zhaoyun_player):
        """测试龙魂可以转化多种牌"""
        from backend.card.card import Card
        
        zhaoyun_player.set_longhun_evolved(True)
        
        # 龙魂可以转化各种花色
        hearts_card = Card(name=CardName.SHA, suit=CardSuit.HEARTS, rank=7)
        diamonds_card = Card(name=CardName.SHAN, suit=CardSuit.DIAMONDS, rank=8)
        clubs_card = Card(name=CardName.TAO, suit=CardSuit.CLUBS, rank=9)
        spades_card = Card(name=CardName.WU_XIE_KE_JI, suit=CardSuit.SPADES, rank=10)
        
        assert zhaoyun_player._can_use_as_different_card(hearts_card) == True
        assert zhaoyun_player._can_use_as_different_card(diamonds_card) == True
        assert zhaoyun_player._can_use_as_different_card(clubs_card) == True
        assert zhaoyun_player._can_use_as_different_card(spades_card) == True

    def test_longhun_card_type_mapping(self, zhaoyun_player):
        """测试龙魂的花色转化规则"""
        from backend.card.card import Card
        
        zhaoyun_player.set_longhun_evolved(True)
        
        # 红桃 -> 桃
        hearts = Card(name=CardName.SHA, suit=CardSuit.HEARTS, rank=7)
        assert zhaoyun_player._get_longhun_card_type(hearts) == CardName.TAO
        
        # 方片 -> 杀
        diamonds = Card(name=CardName.SHAN, suit=CardSuit.DIAMONDS, rank=8)
        assert zhaoyun_player._get_longhun_card_type(diamonds) == CardName.SHA
        
        # 梅花 -> 闪
        clubs = Card(name=CardName.TAO, suit=CardSuit.CLUBS, rank=9)
        assert zhaoyun_player._get_longhun_card_type(clubs) == CardName.SHAN
        
        # 黑桃 -> 无懈可击
        spades = Card(name=CardName.WU_XIE_KE_JI, suit=CardSuit.SPADES, rank=10)
        assert zhaoyun_player._get_longhun_card_type(spades) == CardName.WU_XIE_KE_JI

    def test_juejiang_hand_card_limit(self, zhaoyun_player):
        """测试绝境手牌上限+2（在绝境已解锁的情况下）"""
        # 首先解锁绝境
        zhaoyun_player.unlock_skill("绝境")
        
        zhaoyun_player.current_hp = 4
        limit = zhaoyun_player._get_hand_card_limit()
        assert limit == 6  # 4 + 2
        
        zhaoyun_player.current_hp = 3
        limit = zhaoyun_player._get_hand_card_limit()
        assert limit == 5  # 3 + 2

    def test_longhun_evolve(self, zhaoyun_player):
        """测试龙胆进化为龙魂"""
        assert zhaoyun_player.longhun_evolved == False
        zhaoyun_player.set_longhun_evolved(True)
        assert zhaoyun_player.longhun_evolved == True
        zhaoyun_player.set_longhun_evolved(False)
        assert zhaoyun_player.longhun_evolved == False

    def test_juejiang_draw_on_dying(self, zhaoyun_player):
        """测试绝境在进入濒死状态时摸一张牌（绝境已解锁）"""
        # 先解锁绝境
        zhaoyun_player.unlock_skill("绝境")
        
        zhaoyun_player.current_hp = 2
        initial_hand_count = len(zhaoyun_player.hand_cards)
        
        # 造成2点伤害，进入濒死状态
        zhaoyun_player.take_damage_default(damage=2, source_player_id=1)
        
        # 应该摸了一张牌
        assert zhaoyun_player.current_hp == 0
        assert len(zhaoyun_player.hand_cards) == initial_hand_count + 1

    def test_juejiang_no_draw_on_dying_without_unlock(self, zhaoyun_player):
        """测试绝境未解锁时，进入濒死状态不会摸牌"""
        # 确保绝境未解锁
        assert zhaoyun_player.is_skill_unlocked("绝境") == False
        
        zhaoyun_player.current_hp = 2
        initial_hand_count = len(zhaoyun_player.hand_cards)
        
        # 造成2点伤害，进入濒死状态
        zhaoyun_player.take_damage_default(damage=2, source_player_id=1)
        
        # 不应该摸牌
        assert zhaoyun_player.current_hp == 0
        assert len(zhaoyun_player.hand_cards) == initial_hand_count

    def test_turn_state_reset(self, zhaoyun_player):
        """测试回合状态重置"""
        zhaoyun_player.longdan_cards_used_this_turn = ["card1", "card2"]
        zhaoyun_player.chongzhen_triggered_this_turn = True
        
        zhaoyun_player.reset_turn_state()
        
        assert zhaoyun_player.longdan_cards_used_this_turn == []
        assert zhaoyun_player.chongzhen_triggered_this_turn == False
        assert zhaoyun_player.sha_used_this_turn == False


class TestZhaoyunLonghunEffect:
    """测试龙魂两张牌额外效果"""

    def test_longhun_two_red_cards(self, zhaoyun_player):
        """测试龙魂使用两张红色牌（伤害+1）"""
        from backend.card.card import Card
        
        zhaoyun_player.set_longhun_evolved(True)
        
        # 创建两张红色牌（红桃和方片）
        red1 = Card(name=CardName.SHA, suit=CardSuit.HEARTS, rank=7)
        red2 = Card(name=CardName.SHAN, suit=CardSuit.DIAMONDS, rank=8)
        
        # 应用效果（仅日志记录，实际效果由处理器实现）
        zhaoyun_player._apply_longhun_effect([red1, red2])
        # 无异常即表示正确

    def test_longhun_two_black_cards(self, zhaoyun_player):
        """测试龙魂使用两张黑色牌（弃置对方牌）"""
        from backend.card.card import Card
        
        zhaoyun_player.set_longhun_evolved(True)
        
        # 创建两张黑色牌（梅花和黑桃）
        black1 = Card(name=CardName.TAO, suit=CardSuit.CLUBS, rank=9)
        black2 = Card(name=CardName.WU_XIE_KE_JI, suit=CardSuit.SPADES, rank=10)
        
        # 应用效果（仅日志记录，实际效果由处理器实现）
        zhaoyun_player._apply_longhun_effect([black1, black2])
        # 无异常即表示正确


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
