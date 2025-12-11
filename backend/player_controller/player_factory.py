# 玩家工厂模块
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.player.player import Player, ZhangFeiPlayer, LvmengPlayer, LingcaoPlayer, ZhuguoShaPlayer, ZhaoyunPlayer
from backend.deck.deck import Deck
from config.enums import ControlType, PlayerIdentity, CharacterName


class PlayerFactory:
    """玩家工厂类
    
    根据武将名枚举创建对应的玩家实例
    """
    
    @staticmethod
    def create_player(
        player_id: int,
        name: str,
        control_type: ControlType,
        deck: Deck,
        character_name: CharacterName,
        identity: PlayerIdentity = None,
        player_controller = None
    ) -> Player:
        """创建玩家实例
        
        Args:
            player_id: 玩家ID
            name: 玩家名称
            control_type: 操控类型
            deck: 牌堆
            character_name: 武将名枚举
            identity: 玩家身份
            player_controller: 玩家控制器引用
            
        Returns:
            玩家实例（max_hp 默认为 4）
        """
        # 根据武将名创建对应的玩家子类
        if character_name == CharacterName.ZHANG_FEI:
            return ZhangFeiPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
        elif character_name == CharacterName.LV_MENG:
            return LvmengPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
        elif character_name == CharacterName.LING_CAO:
            return LingcaoPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
        elif character_name == CharacterName.ZHU_GUO_SHA:
            return ZhuguoShaPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
        elif character_name == CharacterName.ZHAO_YUN_1:
            return ZhaoyunPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
        elif character_name == CharacterName.ZHAO_YUN_2:
            p = ZhaoyunPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
            p.unlock_skill("冲阵")
            return p
        elif character_name == CharacterName.ZHAO_YUN_3:
            p = ZhaoyunPlayer(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )
            p.unlock_skill("冲阵")
            p.unlock_skill("绝境")
            return p
        else:
            # 默认创建白板武将（Player基类）
            return Player(
                player_id=player_id,
                name=name,
                control_type=control_type,
                deck=deck,
                identity=identity,
                character_name=character_name,
                player_controller=player_controller
            )

