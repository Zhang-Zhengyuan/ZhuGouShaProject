"""
第三章：长坂坡突围 - 绝境求生

功能：
- get_chapter_three_config()
  返回第三章的前端配置列表

"""
from typing import List
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.simple_card_config import SimplePlayerConfig
from config.enums import CharacterName, PlayerIdentity, ControlType

def get_chapter_three_config() -> List[SimplePlayerConfig]:
    """生成第三章前端配置（SimplePlayerConfig列表）
    
    配置：
    - 赵云（忠臣，人类）：赵云3（龙胆+冲阵+绝境）
    - 3个曹军（反贼，曹军AI）
    - 1个张郃（反贼，曹军AI）
    """
    players_cfg = []
    
    # 赵云（忠臣，人类控制）- 赵云3 (龙胆+冲阵+绝境)
    players_cfg.append(SimplePlayerConfig(
        name="赵云",
        character_name=CharacterName.ZHAO_YUN_3,
        identity=PlayerIdentity.LOYALIST,
        control_type=ControlType.HUMAN
    ))
    
    # 3个曹军（反贼，曹军AI）
    for i in range(3):
        players_cfg.append(SimplePlayerConfig(
            name=f"曹军{i+1}",
            character_name=CharacterName.CAO_JUN,
            identity=PlayerIdentity.REBEL,
            control_type=ControlType.CAOJUN_AI
        ))
        
    # 1个张郃（反贼，曹军AI）
    players_cfg.append(SimplePlayerConfig(
        name="张郃",
        character_name=CharacterName.ZHANG_HE,
        identity=PlayerIdentity.REBEL,
        control_type=ControlType.CAOJUN_AI
    ))
    
    return players_cfg
