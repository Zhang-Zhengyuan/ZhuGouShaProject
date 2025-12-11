"""
章节流程管理 (轻量版)
- 提供章节开始画面（终端交互）用于选择奖励
- 负责组装第一章、第二章并启动游戏（调用 GameController）
- 负责关卡内规则（例如限制敌人技能）、胜利判定与过关回调

注意：UI层仍使用现有前端/后端系统；本模块以终端交互为主，用于快速验证章节流程。
"""
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game_controller.game_controller import GameController
from config.simple_card_config import SimpleGameConfig
from config.simple_detailed_config import create_simple_default_game_config
from campaign.chapter1 import create_chapter_one_players, apply_reward_choice
from campaign.chapter2 import create_chapter_two_players
from campaign.chapter2 import apply_reward_choice as apply_reward_choice_chapter2
from backend.control.control_manager import ControlManager
from backend.utils.event_sender import set_control_manager


def chapter_start_ui() -> Optional[str]:
    """简单的终端开始界面，返回玩家选择的奖励技能名（字符串）"""
    print("=== 第一章：公孙瓒旧部 ===")
    print("模式：围剿模式（你是赵云，其他为反贼）")
    print("请选择关卡奖励（输入序号并回车）：")
    print("1) 岁角（示例技能）")
    print("2) 绝境（解锁赵云绝境技能）")
    print("0) 不选择")
    return None


def start_chapter_one(human_control: bool = True, ai_count: int = 4):
    """启动第一章章节：
    - 构建基础游戏配置
    - 初始化 GameController（创建牌堆/玩家控制器）
    - 使用 `create_chapter_one_players` 替换玩家列表（并重建 ControlManager）
    - 应用奖励选择
    - 启动游戏主循环
    """
    # 加载默认游戏配置（用于牌堆）
    game_config: SimpleGameConfig = create_simple_default_game_config()

    # 创建GameController并初始化（将会创建默认PlayerController）
    gc = GameController(game_config)
    gc.initialize()

    # 构建章节玩家（赵云 + 敌人），player_id 从0开始连续
    players = create_chapter_one_players(gc.deck, human_control=human_control, ai_count=ai_count)

    # 替换 PlayerController 的 players 列表
    pc = gc.player_controller
    # 设置玩家引用player_controller与player_id一致性
    for i, p in enumerate(players):
        p.player_id = i
        # 确保player knows its player_controller
        p.player_controller = pc
    pc.players = players

    # 重新创建 ControlManager，使其包含新的玩家的 Control 实例
    pc.control_manager = ControlManager(pc)
    set_control_manager(pc.control_manager)
    # 同步一次状态
    pc.control_manager.sync_game_state()

    # 章节开始界面（选择奖励）
    reward = chapter_start_ui()
    if reward:
        # 将奖励应用到赵云（假设玩家0为赵云）
        apply_reward_choice(pc.get_player(0), reward)
        print(f"已为赵云应用奖励：{reward}")

    print("章节准备就绪，开始游戏...")
    # 开始游戏（start_game 中会自动为玩家发初始手牌）
    gc.start_game()

    # 关卡结束，判断胜利/失败
    winner = pc.get_winner()
    if winner and '主公' in winner:
        print("你通关了第一章！")
        return True
    else:
        print("你未能通关第一章。")
        return False


def start_chapter_one_headless(human_control: bool = True, ai_count: int = 4, auto_unlock_skill: str = '冲阵'):
    """无交互版本的第一章启动，用于从前端 UI 直接触发。
    - 自动为赵云解锁指定技能（默认 '冲阵'）
    - 不弹出终端奖励选择
    - 启动后端游戏主循环（阻塞直到游戏结束）
    返回 True/False 表示通关结果
    """
    # 加载默认游戏配置（用于前端展示/牌堆）
    game_config: SimpleGameConfig = create_simple_default_game_config()

    # 创建GameController并初始化（将会创建默认PlayerController）
    gc = GameController(game_config)
    gc.initialize()

    # 构建章节玩家（赵云 + 敌人）
    players = create_chapter_one_players(gc.deck, human_control=human_control, ai_count=ai_count)

    # 替换 PlayerController 的 players 列表
    pc = gc.player_controller
    for i, p in enumerate(players):
        p.player_id = i
        p.player_controller = pc
    pc.players = players

    # 重新创建 ControlManager 并设置
    pc.control_manager = ControlManager(pc)
    set_control_manager(pc.control_manager)
    pc.control_manager.sync_game_state()

    # 自动解锁技能到赵云（玩家0）
    if auto_unlock_skill:
        try:
            apply_reward_choice(pc.get_player(0), auto_unlock_skill)
        except Exception:
            pass

    # 启动游戏（start_game 中会自动为玩家发初始手牌）
    gc.start_game()

    # 关卡结束判定
    winner = pc.get_winner()
    if winner and '主公' in winner:
        return True
    return False


def chapter_two_start_ui() -> Optional[str]:
    """第二章简单的终端开始界面，返回玩家选择的奖励技能名（字符串）"""
    print("=== 第二章：长坂坡之战 ===")
    print("模式：突围模式（你是赵云，其他为反贼）")
    print("请选择关卡奖励（输入序号并回车）：")
    print("1) 绝境（解锁赵云绝境技能）")
    print("2) 龙魂（龙胆进化为龙魂）")
    print("0) 不选择")
    return None


def start_chapter_two(human_control: bool = True, ai_count: int = 4):
    """启动第二章章节：
    - 构建基础游戏配置
    - 初始化 GameController（创建牌堆/玩家控制器）
    - 使用 `create_chapter_two_players` 替换玩家列表（并重建 ControlManager）
    - 应用奖励选择
    - 启动游戏主循环
    """
    # 加载默认游戏配置（用于牌堆）
    game_config: SimpleGameConfig = create_simple_default_game_config()

    # 创建GameController并初始化（将会创建默认PlayerController）
    gc = GameController(game_config)
    gc.initialize()

    # 构建章节玩家（赵云2 + 敌人），player_id 从0开始连续
    players = create_chapter_two_players(gc.deck, human_control=human_control, ai_count=ai_count)

    # 替换 PlayerController 的 players 列表
    pc = gc.player_controller
    # 设置玩家引用player_controller与player_id一致性
    for i, p in enumerate(players):
        p.player_id = i
        # 确保player knows its player_controller
        p.player_controller = pc
    pc.players = players

    # 重新创建 ControlManager，使其包含新的玩家的 Control 实例
    pc.control_manager = ControlManager(pc)
    set_control_manager(pc.control_manager)
    # 同步一次状态
    pc.control_manager.sync_game_state()

    # 章节开始界面（选择奖励）
    reward = chapter_two_start_ui()
    if reward:
        # 将奖励应用到赵云（假设玩家0为赵云）
        apply_reward_choice_chapter2(pc.get_player(0), reward)
        print(f"已为赵云应用奖励：{reward}")

    print("第二章准备就绪，开始游戏...")
    # 开始游戏（start_game 中会自动为玩家发初始手牌）
    gc.start_game()

    # 关卡结束，判断胜利/失败
    winner = pc.get_winner()
    if winner and '主公' in winner:
        print("你通关了第二章！")
        return True
    else:
        print("你未能通关第二章。")
        return False


def start_chapter_two_headless(human_control: bool = True, ai_count: int = 4, auto_unlock_skill: str = '绝境'):
    """无交互版本的第二章启动，用于从前端 UI 直接触发。
    - 自动为赵云解锁指定技能（默认 '绝境'）
    - 不弹出终端奖励选择
    - 启动后端游戏主循环（阻塞直到游戏结束）
    返回 True/False 表示通关结果
    """
    # 加载默认游戏配置（用于前端展示/牌堆）
    game_config: SimpleGameConfig = create_simple_default_game_config()

    # 创建GameController并初始化（将会创建默认PlayerController）
    gc = GameController(game_config)
    gc.initialize()

    # 构建章节玩家（赵云2 + 敌人）
    players = create_chapter_two_players(gc.deck, human_control=human_control, ai_count=ai_count)

    # 替换 PlayerController 的 players 列表
    pc = gc.player_controller
    for i, p in enumerate(players):
        p.player_id = i
        p.player_controller = pc
    pc.players = players

    # 重新创建 ControlManager 并设置
    pc.control_manager = ControlManager(pc)
    set_control_manager(pc.control_manager)
    pc.control_manager.sync_game_state()

    # 自动解锁技能到赵云（玩家0）
    if auto_unlock_skill:
        try:
            apply_reward_choice_chapter2(pc.get_player(0), auto_unlock_skill)
        except Exception:
            pass

    # 启动游戏（start_game 中会自动为玩家发初始手牌）
    gc.start_game()

    # 关卡结束判定
    winner = pc.get_winner()
    if winner and '主公' in winner:
        return True
    return False

