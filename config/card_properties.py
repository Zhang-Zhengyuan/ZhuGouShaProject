# 牌属性配置文件
from .enums import CardType, TargetType, CardName

# 每张牌的固定属性配置
CARD_PROPERTIES = {
    # 基本牌
    CardName.SHA: {
        "display_name": "杀",
        "card_type": CardType.BASIC,
        "target_type": TargetType.ATTACKABLE,
        "attack_range": 1
    },
    CardName.SHAN: {
        "display_name": "闪",
        "card_type": CardType.BASIC,
        "target_type": TargetType.SELF,
        "attack_range": 1
    },
    CardName.TAO: {
        "display_name": "桃",
        "card_type": CardType.BASIC,
        "target_type": TargetType.SELF,
        "attack_range": 1
    },
    
    # 锦囊牌
    CardName.WU_XIE_KE_JI: {
        "display_name": "无懈可击",
        "card_type": CardType.TRICK,
        "target_type": TargetType.SELF,
        "attack_range": 1
    },
    CardName.NAN_MAN_RU_QIN: {
        "display_name": "南蛮入侵",
        "card_type": CardType.TRICK,
        "target_type": TargetType.ALL,
        "attack_range": 1
    },
    CardName.WAN_JIAN_QI_FA: {
        "display_name": "万箭齐发",
        "card_type": CardType.TRICK,
        "target_type": TargetType.ALL,
        "attack_range": 1
    },
    CardName.JUE_DOU: {
        "display_name": "决斗",
        "card_type": CardType.TRICK,
        "target_type": TargetType.ALL,  # 决斗可以对除自己以外任意1名角色使用（不受攻击范围限制）
        "attack_range": 1
    },
    
    # 装备牌 - 武器
    CardName.QING_GANG_JIAN: {
        "display_name": "青釭剑",
        "card_type": CardType.EQUIPMENT,
        "target_type": TargetType.SELF,
        "attack_range": 2
    },
    CardName.ZHU_GE_LIAN_NU: {
        "display_name": "诸葛连弩",
        "card_type": CardType.EQUIPMENT,
        "target_type": TargetType.SELF,
        "attack_range": 1
    },
    
    # 装备牌 - 防具
    CardName.REN_WANG_DUN: {
        "display_name": "仁王盾",
        "card_type": CardType.EQUIPMENT,
        "target_type": TargetType.SELF,
        "attack_range": 1
    },
    
    # 装备牌 - 坐骑
    CardName.JIN_GONG_MA: {
        "display_name": "进攻马",
        "card_type": CardType.EQUIPMENT,
        "target_type": TargetType.SELF,
        "attack_range": 1
    },
    CardName.FANG_YU_MA: {
        "display_name": "防御马",
        "card_type": CardType.EQUIPMENT,
        "target_type": TargetType.SELF,
        "attack_range": 1
    }
}


def get_card_properties(card_name: CardName) -> dict:
    """获取指定牌名的属性
    
    Args:
        card_name: 牌名枚举
        
    Returns:
        包含display_name, card_type, target_type, attack_range的字典
    """
    return CARD_PROPERTIES.get(card_name, {
        "display_name": card_name.value,
        "card_type": CardType.BASIC,
        "target_type": TargetType.ATTACKABLE,
        "attack_range": 1
    })