"""
第二章：长坂坡之战 - 突围模式初始化脚手架

功能：
- create_chapter_two_players(deck, human_control=True, ai_count=4)
  返回玩家实例列表：赵云（ZHAO_YUN_2，human_control 为 True 则为人控，否则为简单AI）

- apply_reward_choice(player, choice)
  将选择的奖励技能临时加入玩家（仅在本章会使用）

注意：本模块尽量只做组装与配置，不直接启动游戏主循环。
"""
from typing import List
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.player.player import ZhaoyunPlayer, Player
from backend.deck.deck import Deck
from backend.control.control_factory import ControlFactory
from config.enums import CharacterName, ControlType, PlayerIdentity
from backend.player.player import Player as BasePlayer
from config.simple_card_config import SimplePlayerConfig


def create_chapter_two_players(deck: Deck, human_control: bool = True, ai_count: int = 4) -> List[BasePlayer]:
    """创建第二章的玩家列表。

    参数:
        deck: 牌堆，用于发手牌
        human_control: 是否把赵云设为真人控制（True -> 人类/窗口控制）
        ai_count: 敌方AI数量（固定为4：1个阿斗 + 3个曹军）

    返回:
        players: 按游戏顺序的 Player 实例列表
                [0] 赵云（忠臣，人类控制）
                [1] 阿斗（主公，2血，AI）
                [2-4] 曹军（反贼，3血，AI）
    """
    players = []

    # 1) 创建赵云2（ZHAO_YUN_2，拥有龙胆和冲阵技能，忠臣）
    control_type = ControlType.HUMAN if human_control else ControlType.SIMPLE_AI
    zhao = ZhaoyunPlayer(
        player_id=0, 
        name="赵云", 
        control_type=control_type, 
        deck=deck, 
        identity=PlayerIdentity.LOYALIST,  # 忠臣
        character_name=CharacterName.ZHAO_YUN_2, 
        player_controller=None
    )
    # 第二章：赵云已解锁龙胆和冲阵技能
    zhao.unlock_skill("冲阵")
    players.append(zhao)

    # 2) 创建阿斗（主公，2血，AI）
    adou = BasePlayer(
        player_id=1, 
        name="阿斗", 
        control_type=ControlType.SIMPLE_AI, 
        deck=deck, 
        identity=PlayerIdentity.LORD,  # 主公
        character_name=CharacterName.ADOU, 
        player_controller=None
    )
    # 阿斗：主公身份基础血量4+1=5，但这里特殊设定为2血（剧情需要）
    adou.max_hp = 2
    adou.current_hp = 2
    players.append(adou)

    # 3) 创建三个曹军（反贼，3血，AI）
    for i in range(3):
        pid = i + 2  # player_id: 2, 3, 4
        cao = BasePlayer(
            player_id=pid, 
            name=f"曹军{i+1}", 
            control_type=ControlType.SIMPLE_AI, 
            deck=deck, 
            identity=PlayerIdentity.REBEL,  # 反贼
            character_name=CharacterName.CAO_JUN, 
            player_controller=None
        )
        # 曹军：3血
        cao.max_hp = 3
        cao.current_hp = 3
        players.append(cao)

    return players


def get_chapter_two_config() -> List[SimplePlayerConfig]:
    """生成第二章前端配置（SimplePlayerConfig列表）
    
    返回:
        players_config: 包含赵云（忠臣，人类）、阿斗（主公，阿斗AI）和3个曹军（反贼，曹军AI）
    """
    players_cfg = []
    # 赵云（忠臣，人类控制）
    players_cfg.append(SimplePlayerConfig(
        name="赵云",
        character_name=CharacterName.ZHAO_YUN_2,
        identity=PlayerIdentity.LOYALIST,
        control_type=ControlType.HUMAN
    ))
    # 阿斗（主公，使用专用阿斗AI）
    players_cfg.append(SimplePlayerConfig(
        name="阿斗",
        character_name=CharacterName.ADOU,
        identity=PlayerIdentity.LORD,
        control_type=ControlType.ADOU_AI  # 使用专用阿斗AI
    ))
    # 3个曹军（反贼，使用专用曹军AI）
    for i in range(3):
        players_cfg.append(SimplePlayerConfig(
            name=f"曹军{i+1}",
            character_name=CharacterName.CAO_JUN,
            identity=PlayerIdentity.REBEL,
            control_type=ControlType.CAOJUN_AI  # 使用专用曹军AI
        ))
    return players_cfg


def apply_reward_choice(player: BasePlayer, choice: str) -> bool:
    """将章节奖励（选择的技能）应用到玩家（临时生效）。

    支持的 choice 示例：
      - "绝境" (赵云的第三个技能)
      - 其他自定义技能名

    返回 True 表示成功应用，False 表示不支持该选择。
    """
    if not player:
        return False
    # 这里只做非常轻量的处理：将技能名标记为已解锁（若字段存在）
    try:
        if hasattr(player, 'skill_unlock_status'):
            player.skill_unlock_status[choice] = True
            return True
        else:
            # 如果player没有skill_unlock_status（白板），我们可以在player上动态添加一个字段
            setattr(player, 'skill_unlock_status', {choice: True})
            return True
    except Exception:
        return False
