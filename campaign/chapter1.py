"""
第一章：公孙瓒旧部 - 围剿模式初始化脚手架

功能：
- create_chapter_one_players(deck, human_control=True, ai_count=4)
  返回玩家实例列表：赵云（human_control 为 True 则为人控，否则为简单AI）
  其余 ai_count 个敌方（反贼）为白板、1血、无技能

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
from backend.player.player import ZhangFeiPlayer
from config.simple_card_config import SimplePlayerConfig

# SimpleAI is provided by ControlFactory via ControlType.SIMPLE_AI


def create_chapter_one_players(deck: Deck, human_control: bool = True, ai_count: int = 4) -> List[BasePlayer]:
    """创建第一章的玩家列表。

    参数:
        deck: 牌堆，用于发手牌
        human_control: 是否把赵云设为真人控制（True -> 人类/窗口控制）
        ai_count: 敌方AI数量（建议 3~4）

    返回:
        players: 按游戏顺序的 Player 实例列表
    """
    players = []

    # 1) 创建赵云（主角，主公/忠臣设定这里采用 PlayerIdentity.LOYALIST 可能不适用，将其设为 LORD）
    control_type = ControlType.HUMAN if human_control else ControlType.SIMPLE_AI
    zhao = ZhaoyunPlayer(player_id=0, name="赵云", control_type=control_type, deck=deck, identity=PlayerIdentity.LORD, character_name=CharacterName.ZHAO_YUN_1, player_controller=None)
    # 初始只解锁龙胆（已经是默认）
    players.append(zhao)

    # 2) 创建若干1血白板AI敌人（反贼）
    for i in range(ai_count):
        pid = i + 1
        # 使用简单 Player 基类实例化白板敌人
        # 这里直接用 Player，默认血量为4，需要把max/current 设置为1
        ai = BasePlayer(player_id=pid, name=f"残兵{i+1}", control_type=ControlType.SIMPLE_AI, deck=deck, identity=PlayerIdentity.REBEL, character_name=CharacterName.BAI_BAN_WU_JIANG, player_controller=None)
        # 设置为1血并清空技能/装备
        # 设置为2血，保持默认手牌抽取流程（不要手动清空 hand_cards）
        ai.max_hp = 2
        ai.current_hp = 2
        # 取消默认装备/技能等（白板无技能）
        players.append(ai)

    return players


def get_chapter_one_config() -> List[SimplePlayerConfig]:
    """生成第一章前端配置（SimplePlayerConfig列表）
    
    返回:
        players_config: 包含赵云（忠臣，人类）和4个残兵（反贼，残兵AI）
    """
    players_cfg = []
    # 赵云（忠臣，人类控制）
    players_cfg.append(SimplePlayerConfig(
        name="赵云",
        character_name=CharacterName.ZHAO_YUN_1,
        identity=PlayerIdentity.LOYALIST,
        control_type=ControlType.HUMAN
    ))
    # 4个残兵（反贼，使用专用残兵AI）
    for i in range(4):
        players_cfg.append(SimplePlayerConfig(
            name=f"残兵{i+1}",
            character_name=CharacterName.CAN_BING,
            identity=PlayerIdentity.REBEL,
            control_type=ControlType.CANBING_AI  # 使用专用残兵AI
        ))
    return players_cfg


def apply_reward_choice(player: BasePlayer, choice: str) -> bool:
    """将章节奖励（选择的技能）应用到玩家（临时生效）。

    支持的 choice 示例：
      - "涯角" (示例技能名)
      - "绝境" (赵云已有的技能名)

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
