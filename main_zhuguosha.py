#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
猪国杀主程序 - 用于处理输入输出
根据ZHUGUOSHA.md的输入输出格式，运行游戏并输出结果
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.game_controller.game_controller import GameController
from backend.card.card import Card
from config.simple_card_config import SimpleGameConfig, SimplePlayerConfig, SimpleCardConfig
from config.enums import CardName, CardSuit, PlayerIdentity, CharacterName, ControlType
from backend.utils.logger import game_logger
from backend.utils.event_sender import set_wait_for_ack


# 牌名映射：输入的单字母 -> CardName枚举
CARD_NAME_MAP = {
    'P': CardName.TAO,           # 桃
    'K': CardName.SHA,           # 杀
    'D': CardName.SHAN,          # 闪
    'F': CardName.JUE_DOU,       # 决斗
    'N': CardName.NAN_MAN_RU_QIN,  # 南蛮入侵
    'W': CardName.WAN_JIAN_QI_FA,  # 万箭齐发
    'J': CardName.WU_XIE_KE_JI,    # 无懈可击
    'Z': CardName.ZHU_GE_LIAN_NU,  # 诸葛连弩
}

# 身份映射：输入的字符串 -> PlayerIdentity枚举
IDENTITY_MAP = {
    'MP': PlayerIdentity.LORD,      # 主猪
    'ZP': PlayerIdentity.LOYALIST,  # 忠猪
    'FP': PlayerIdentity.REBEL,      # 反猪
}


def parse_input_file(input_file: str) -> tuple:
    """解析输入文件
    
    Args:
        input_file: 输入文件路径
        
    Returns:
        (players_config, initial_hands, deck_order)
        players_config: List[SimplePlayerConfig] - 玩家配置列表
        initial_hands: Dict[int, List[str]] - 初始手牌 {player_id: [card_chars], ...}
        deck_order: List[str] - 牌堆顺序 [card_chars, ...]
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines:
        raise ValueError(f"输入文件为空: {input_file}")
    
    # 第一行：n m
    n, m = map(int, lines[0].split())
    
    # 接下来n行：身份和初始手牌
    players_data = []
    for i in range(1, n + 1):
        parts = lines[i].split()
        identity = parts[0]
        hand_cards = parts[1:5]  # 4张初始手牌
        players_data.append({
            "identity": identity,
            "hand_cards": hand_cards
        })
    
    # 最后一行：牌堆
    deck_cards = lines[n + 1].split()
    
    # 身份映射
    identity_map = {
        'MP': PlayerIdentity.LORD,
        'ZP': PlayerIdentity.LOYALIST,
        'FP': PlayerIdentity.REBEL
    }
    
    # 创建玩家配置
    players_config = []
    initial_hands = {}
    
    for i, player_data in enumerate(players_data):
        identity_str = player_data["identity"]
        identity_enum = identity_map.get(identity_str)
        if identity_enum is None:
            raise ValueError(f"未知的身份: {identity_str}")
        
        # 忠臣使用赵云武将，其他身份使用猪国杀武将
        if identity_enum == PlayerIdentity.LOYALIST:
            character_name = CharacterName.ZHAO_YUN_1
        else:
            character_name = CharacterName.ZHU_GUO_SHA
        
        players_config.append(
            SimplePlayerConfig(
                name=f"玩家{i+1}",
                character_name=character_name,
                identity=identity_enum,
                control_type=ControlType.SIMPLE_AI
            )
        )
        
        # 保存初始手牌
        initial_hands[i] = player_data["hand_cards"]
    
    return players_config, initial_hands, deck_cards


def create_game_config(players_config: list, deck_order: list) -> SimpleGameConfig:
    """根据解析的数据创建游戏配置
    
    Args:
        players_config: 玩家配置列表
        deck_order: 牌堆顺序 [card_chars, ...]
        
    Returns:
        SimpleGameConfig配置对象
    """
    # 统计每种牌的数量（用于deck配置）
    card_count = {}
    for card_char in deck_order:
        card_count[card_char] = card_count.get(card_char, 0) + 1
    
    # 创建牌堆配置
    deck_config = []
    for card_char, count in card_count.items():
        card_name_enum = CARD_NAME_MAP.get(card_char)
        if card_name_enum is None:
            raise ValueError(f"未知的牌名: {card_char}")
        
        deck_config.append(
            SimpleCardConfig(
                name=card_name_enum,
                suit=CardSuit.HEARTS,  # 默认花色
                rank=1,  # 默认点数
                count=count
            )
        )
    
    # 创建游戏配置（不打乱牌堆）
    return SimpleGameConfig(
        deck_config=deck_config,
        players_config=players_config,
        shuffle_deck=False
    )


def create_card_from_name(card_name_char: str, suit: CardSuit = CardSuit.HEARTS, rank: int = 1) -> Card:
    """根据牌名字符创建Card对象
    
    Args:
        card_name_char: 牌名字符（P/K/D/F/N/W/J/Z）
        suit: 花色（默认红桃）
        rank: 点数（默认1）
        
    Returns:
        Card对象
    """
    card_name = CARD_NAME_MAP.get(card_name_char)
    if card_name is None:
        raise ValueError(f"未知的牌名: {card_name_char}")
    return Card(suit=suit, rank=rank, name=card_name)




def set_initial_hand_cards_and_deck_order(game_controller: GameController, 
                                          initial_hands: dict, deck_order: list) -> None:
    """设置初始手牌和牌堆顺序
    
    Args:
        game_controller: 游戏控制器
        initial_hands: {player_id: [card_chars], ...}
        deck_order: [card_chars, ...]
    """
    deck = game_controller.deck
    
    # 清空现有牌堆
    deck.cards.clear()
    
    # 按照输入顺序创建牌堆（从顶部到底部）
    for card_char in deck_order:
        card = create_card_from_name(card_char)
        deck.cards.append(card)
    
    # 将牌堆的最后一张牌复制100遍添加到牌堆末尾
    if deck.cards:
        last_card_char = deck_order[-1] if deck_order else None
        if last_card_char:
            for _ in range(100):
                card = create_card_from_name(last_card_char)
                deck.cards.append(card)
    
    # 设置初始手牌（初始手牌不在牌堆中，是独立的）
    for player_id_str, hand_cards in initial_hands.items():
        player_id = int(player_id_str)
        player = game_controller.player_controller.get_player(player_id)
        if player is None:
            continue
        
        # 清空手牌
        player.hand_cards.clear()
        
        # 添加初始手牌（创建新的Card对象，不引用牌堆中的牌）
        for card_char in hand_cards:
            card = create_card_from_name(card_char)
            player.hand_cards.append(card)


def fix_lord_max_hp_for_zhuguosha(game_controller: GameController) -> None:
    """修正主公的血量上限（猪国杀规则：所有玩家都是4点体力上限）
    
    在正常游戏中，主公的血量上限是基础+1，但在猪国杀程序中，主公也应该是4点。
    这个函数需要在初始化后调用，将主公的max_hp和current_hp都设置为4。
    
    Args:
        game_controller: 游戏控制器
    """
    for player in game_controller.player_controller.players:
        if player.identity == PlayerIdentity.LORD:
            # 将主公的血量上限和当前血量都设置为4（猪国杀规则）
            player.max_hp = 4
            player.current_hp = 4
            break


def unlock_chongzhen_skill(game_controller: GameController) -> None:
    """解锁赵云的冲阵技能
    
    此函数提供了解锁冲阵技能的接口，但默认不被调用。
    可在游戏进程中的特定时刻调用此函数来解锁冲阵技能。
    
    Args:
        game_controller: 游戏控制器
    """
    from backend.player.player import ZhaoyunPlayer
    for player in game_controller.player_controller.players:
        if isinstance(player, ZhaoyunPlayer):
            player.unlock_skill("冲阵")


def unlock_juejiang_skill(game_controller: GameController) -> None:
    """解锁赵云的绝境技能
    
    此函数提供了解锁绝境技能的接口，但默认不被调用。
    可在游戏进程中的特定时刻调用此函数来解锁绝境技能。
    
    Args:
        game_controller: 游戏控制器
    """
    from backend.player.player import ZhaoyunPlayer
    for player in game_controller.player_controller.players:
        if isinstance(player, ZhaoyunPlayer):
            player.unlock_skill("绝境")


def format_output(game_controller: GameController) -> str:
    """格式化输出
    
    Args:
        game_controller: 游戏控制器
        
    Returns:
        输出字符串
    """
    output_lines = []
    
    # 第一行：游戏结果（MP或FP）
    winner = game_controller.player_controller.get_winner()
    if winner is None:
        # 如果游戏未结束，检查当前状态
        lord_alive = False
        all_rebels_dead = True
        for player in game_controller.player_controller.players:
            if player.identity == PlayerIdentity.LORD and player.is_alive():
                lord_alive = True
            if player.identity == PlayerIdentity.REBEL and player.is_alive():
                all_rebels_dead = False
        
        if lord_alive and all_rebels_dead:
            output_lines.append("MP")
        else:
            output_lines.append("FP")
    elif "主公" in winner or "主猪" in winner or "MP" in winner:
        output_lines.append("MP")
    elif "反贼" in winner or "反猪" in winner or "FP" in winner:
        output_lines.append("FP")
    else:
        # 默认：检查主猪是否存活
        lord_alive = False
        all_rebels_dead = True
        for player in game_controller.player_controller.players:
            if player.identity == PlayerIdentity.LORD and player.is_alive():
                lord_alive = True
            if player.identity == PlayerIdentity.REBEL and player.is_alive():
                all_rebels_dead = False
        
        if lord_alive and all_rebels_dead:
            output_lines.append("MP")
        else:
            output_lines.append("FP")
    
    # 接下来n行：每个玩家的手牌或DEAD
    for player in game_controller.player_controller.players:
        if not player.is_alive():
            output_lines.append("DEAD")
        else:
            # 输出手牌（按照从左往右的顺序）
            if not player.hand_cards:
                output_lines.append("")  # 空行
            else:
                # 将Card对象转换为单字母
                card_chars = []
                for card in player.hand_cards:
                    # 反向查找CardName -> 单字母
                    for char, card_name in CARD_NAME_MAP.items():
                        if card.name_enum == card_name:
                            card_chars.append(char)
                            break
                output_lines.append(" ".join(card_chars))
    
    return "\n".join(output_lines)


def main():
    """主函数

    支持两种运行模式：
    - 传统批处理模式：python main_zhuguosha.py <input_file>
    - 章节模式（第一章）：python main_zhuguosha.py chapter1
    """
    if len(sys.argv) < 2:
        print("Usage: python main_zhuguosha.py <input_file> OR python main_zhuguosha.py chapter1")
        sys.exit(1)

    # 章节模式入口
    if sys.argv[1] == 'chapter1':
        # 延迟导入以避免循环依赖
        from campaign.flow import start_chapter_one
        # human_control=True 表示玩家1（赵云）为真人控制
        start_chapter_one(human_control=True, ai_count=4)
        return

    input_file = sys.argv[1]
    
    # 设置 wait_for_ack 为 False（关闭ACK等待）
    set_wait_for_ack(False)
    
    try:
        # 解析输入文件
        players_config, initial_hands, deck_order = parse_input_file(input_file)
        
        # 创建游戏配置
        game_config = create_game_config(players_config, deck_order)
        
        # 开始游戏会话日志
        log_path = game_logger.start_game_session(is_test=False)
        game_logger.log_info(f"开始新游戏（猪国杀模式），玩家数量: {len(players_config)}")
        
        try:
            # 创建游戏控制器
            game_controller = GameController(game_config)
            game_controller.initialize()
            
            # 设置初始手牌和牌堆顺序（必须在initialize之后）
            set_initial_hand_cards_and_deck_order(game_controller, initial_hands, deck_order)
            
            # 修正主公的血量上限（猪国杀规则：所有玩家都是4点体力上限）
            fix_lord_max_hp_for_zhuguosha(game_controller)
            
            # 运行游戏（game_controller已经初始化并设置好初始状态）
            # 注意：start_game中会检查是否已初始化，不会重复初始化
            game_controller.start_game()
        finally:
            # 结束游戏会话日志
            game_logger.end_game_session()
        
        # 格式化输出
        output = format_output(game_controller)
        
        # 输出到文件
        output_dir = os.path.join("HomeWork", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        # 从输入文件名提取编号
        input_basename = os.path.basename(input_file)
        if input_basename.endswith('.in'):
            output_filename = input_basename[:-3] + '.out'
        else:
            output_filename = input_basename + '.out'
        
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        # 不输出到控制台（批处理模式）
        # print(f"输出已保存到: {output_path}")
    except Exception as e:
        # 输出错误信息
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

