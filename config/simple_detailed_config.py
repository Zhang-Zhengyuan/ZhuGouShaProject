# 简化的详细默认配置文件
import json
import os
from typing import Dict, Any
from .simple_card_config import SimpleGameConfig, SimpleCardConfig, SimplePlayerConfig
from .enums import CardSuit, CardName, ControlType, PlayerIdentity, CharacterName


def load_config(config_file_name: str = "default_game_config") -> SimpleGameConfig:
    """加载配置文件
    
    Args:
        config_file_name: 配置文件名（不需要加.json扩展名），默认为 "default_game_config"
                        例如：输入 "my_config" 会查找 "config_file/my_config.json"
        
    Returns:
        SimpleGameConfig配置对象
        
    Raises:
        FileNotFoundError: 如果指定的配置文件不存在
        ValueError: 如果配置文件格式不正确
        TypeError: 如果配置文件类型不正确
    """
    # 计算项目根目录：从 config/ 向上一级到项目根目录
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_file_dir)
    config_file_dir = os.path.join(project_root, 'config_file')
    
    # 处理文件名：自动添加 .json 扩展名（如果用户已经加了，也接受）
    if config_file_name.endswith('.json'):
        file_name = config_file_name
    else:
        file_name = config_file_name + '.json'
    
    # 构建完整路径
    config_path = os.path.join(config_file_dir, file_name)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请确保 config_file/{file_name} 文件存在"
        )
    
    # 从指定文件加载配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)
    config = SimpleGameConfig.from_dict(config_dict)
    
    return config


def create_simple_default_game_config() -> SimpleGameConfig:
    """创建简化的默认游戏配置（从配置文件读取）
    
    从 config_file/default_game_config.json 加载配置
    
    Returns:
        SimpleGameConfig配置对象
    """
    return load_config("default_game_config")


#TODO 可以修改成使用工厂模式
def create_hardcoded_default_game_config() -> SimpleGameConfig:
    """创建简化的默认游戏配置"""
    
    # 牌堆配置 - 只包含指定的牌
    deck_config = [
        # 基本牌 - 杀 (30张，每种花色点数组合1张)
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 1, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 1, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 1, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 1, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 2, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 2, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 2, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 2, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 3, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 3, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 3, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 3, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 4, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 4, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 4, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 4, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 5, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 5, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 5, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 5, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 6, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 6, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 6, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 6, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 7, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 7, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.CLUBS, 7, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.SPADES, 7, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.HEARTS, 8, 1),
        SimpleCardConfig(CardName.SHA, CardSuit.DIAMONDS, 8, 1),
        
        # 基本牌 - 闪 (15张，每种花色点数组合1张)
        SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 2, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.DIAMONDS, 2, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.CLUBS, 2, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.SPADES, 2, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 3, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.DIAMONDS, 3, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.CLUBS, 3, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.SPADES, 3, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 4, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.DIAMONDS, 4, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.CLUBS, 4, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.SPADES, 4, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.HEARTS, 5, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.DIAMONDS, 5, 1),
        SimpleCardConfig(CardName.SHAN, CardSuit.CLUBS, 5, 1),
        
        # 基本牌 - 桃 (8张，每种花色点数组合1张)
        SimpleCardConfig(CardName.TAO, CardSuit.HEARTS, 1, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.DIAMONDS, 1, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.CLUBS, 1, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.SPADES, 1, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.HEARTS, 2, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.DIAMONDS, 2, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.CLUBS, 2, 1),
        SimpleCardConfig(CardName.TAO, CardSuit.SPADES, 2, 1),
        
        # 锦囊牌 - 无懈可击 (4张，每种花色点数组合1张)
        SimpleCardConfig(CardName.WU_XIE_KE_JI, CardSuit.SPADES, 11, 1),
        SimpleCardConfig(CardName.WU_XIE_KE_JI, CardSuit.CLUBS, 11, 1),
        SimpleCardConfig(CardName.WU_XIE_KE_JI, CardSuit.SPADES, 12, 1),
        SimpleCardConfig(CardName.WU_XIE_KE_JI, CardSuit.CLUBS, 12, 1),
        
        # # 锦囊牌 - 南蛮入侵 (3张，每种花色点数组合1张)
        SimpleCardConfig(CardName.NAN_MAN_RU_QIN, CardSuit.SPADES, 7, 1),
        SimpleCardConfig(CardName.NAN_MAN_RU_QIN, CardSuit.CLUBS, 7, 1),
        SimpleCardConfig(CardName.NAN_MAN_RU_QIN, CardSuit.SPADES, 8, 1),
        
        # 锦囊牌 - 万箭齐发 (1张)
        SimpleCardConfig(CardName.WAN_JIAN_QI_FA, CardSuit.HEARTS, 1, 1),
        
        # 锦囊牌 - 决斗 (3张)
        SimpleCardConfig(CardName.JUE_DOU, CardSuit.SPADES, 1, 1),
        SimpleCardConfig(CardName.JUE_DOU, CardSuit.CLUBS, 1, 1),
        SimpleCardConfig(CardName.JUE_DOU, CardSuit.SPADES, 2, 1),
        
        # 装备牌 - 青釭剑 (1张)
        SimpleCardConfig(CardName.QING_GANG_JIAN, CardSuit.SPADES, 6, 1),
        
        # 装备牌 - 诸葛连弩 (1张)
        SimpleCardConfig(CardName.ZHU_GE_LIAN_NU, CardSuit.HEARTS, 7, 1),
        
        # 装备牌 - 仁王盾 (1张)
        SimpleCardConfig(CardName.REN_WANG_DUN, CardSuit.SPADES, 2, 1),
        
        # 装备牌 - 进攻马 (1张)
        SimpleCardConfig(CardName.JIN_GONG_MA, CardSuit.HEARTS, 5, 1),
        
        # 装备牌 - 防御马 (1张)
        SimpleCardConfig(CardName.FANG_YU_MA, CardSuit.SPADES, 5, 1),
    ]
    
    # 玩家配置
    players_config = [
        SimplePlayerConfig(
            name="主公",
            character_name=CharacterName.BAI_BAN_WU_JIANG,
            identity=PlayerIdentity.LORD,
            control_type=ControlType.AI
        ),
        SimplePlayerConfig(
            name="忠臣",
            character_name=CharacterName.GUAN_YU,
            identity=PlayerIdentity.LOYALIST,
            control_type=ControlType.AI
        ),
        SimplePlayerConfig(
            name="反贼1",
            character_name=CharacterName.ZHANG_FEI,
            identity=PlayerIdentity.REBEL,
            control_type=ControlType.AI
        ),
        SimplePlayerConfig(
            name="反贼2",
            character_name=CharacterName.LV_MENG,
            identity=PlayerIdentity.REBEL,
            control_type=ControlType.AI
        ),
        SimplePlayerConfig(
            name="内奸",
            character_name=CharacterName.BAI_BAN_WU_JIANG,
            identity=PlayerIdentity.TRAITOR,
            control_type=ControlType.AI
        )
    ]
    
    return SimpleGameConfig(
        deck_config=deck_config,
        players_config=players_config,
        shuffle_deck=True
    )