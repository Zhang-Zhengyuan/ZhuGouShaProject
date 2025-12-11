# 阶段技能处理器模块
"""使用策略模式统一处理各阶段的技能激活逻辑"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.card.card import Card
from backend.utils.logger import game_logger
from config.enums import GameEvent


class PhaseSkillHandler(ABC):
    """阶段技能处理器基类（策略模式）"""
    
    @abstractmethod
    def build_context(self, player, **kwargs) -> dict:
        """构建技能询问上下文
        
        Args:
            player: 玩家对象
            **kwargs: 阶段特定的参数
            
        Returns:
            上下文字典
        """
        pass
    
    @abstractmethod
    def execute_with_skill(self, player, **kwargs):
        """执行技能版本的操作
        
        Args:
            player: 玩家对象
            **kwargs: 阶段特定的参数
            
        Returns:
            操作结果
        """
        pass
    
    @abstractmethod
    def execute_default(self, player, **kwargs):
        """执行默认版本的操作
        
        Args:
            player: 玩家对象
            **kwargs: 阶段特定的参数
            
        Returns:
            操作结果
        """
        pass


class DrawCardPhaseSkillHandler(PhaseSkillHandler):
    """摸牌阶段技能处理器"""
    
    def build_context(self, player, **kwargs) -> dict:
        """构建摸牌阶段的上下文"""
        return {
            "player_id": player.player_id,
            "name": player.name,
            "current_hp": player.current_hp,
            "max_hp": player.max_hp,
            "hand_size": len(player.hand_cards),
        }
    
    def execute_with_skill(self, player, **kwargs) -> List[Card]:
        """执行技能版本的摸牌"""
        return player.draw_card_phase_with_skill()
    
    def execute_default(self, player, **kwargs) -> List[Card]:
        """执行默认版本的摸牌"""
        return player.draw_card_phase_default()


class PlayCardPhaseSkillHandler(PhaseSkillHandler):
    """出牌阶段技能处理器"""
    
    def build_context(self, player, available_targets=None, **kwargs) -> dict:
        """构建出牌阶段的上下文"""
        return {
            "player_id": player.player_id,
            "name": player.name,
            "current_hp": player.current_hp,
            "max_hp": player.max_hp,
            "hand_size": len(player.hand_cards),
            "available_targets": available_targets or {},
        }
    
    def execute_with_skill(self, player, available_targets=None, **kwargs) -> Tuple[Optional[Card], List[int]]:
        """执行技能版本的出牌"""
        return player.play_card_with_skill(available_targets)
    
    def execute_default(self, player, available_targets=None, **kwargs) -> Tuple[Optional[Card], List[int]]:
        """执行默认版本的出牌"""
        return player.play_card_default(available_targets)


class DiscardCardPhaseSkillHandler(PhaseSkillHandler):
    """弃牌阶段技能处理器"""
    
    def build_context(self, player, **kwargs) -> dict:
        """构建弃牌阶段的上下文"""
        return {
            "player_id": player.player_id,
            "name": player.name,
            "current_hp": player.current_hp,
            "max_hp": player.max_hp,
            "hand_size": len(player.hand_cards),
        }
    
    def execute_with_skill(self, player, **kwargs) -> List[Card]:
        """执行技能版本的弃牌"""
        return player.discard_card_with_skill()
    
    def execute_default(self, player, **kwargs) -> List[Card]:
        """执行默认版本的弃牌"""
        return player.discard_card_default()


class DamagePhaseSkillHandler(PhaseSkillHandler):
    """受伤阶段技能处理器"""
    
    def build_context(self, player, damage=1, source_player_id=None, 
                     damage_type=None, original_card_name=None, **kwargs) -> dict:
        """构建受伤阶段的上下文"""
        return {
            "player_id": player.player_id,
            "name": player.name,
            "current_hp": player.current_hp,
            "max_hp": player.max_hp,
            "hand_size": len(player.hand_cards),
            "damage": damage,
            "source_player_id": source_player_id,
            "damage_type": damage_type,
            "original_card_name": original_card_name,
        }
    
    def execute_with_skill(self, player, damage=1, source_player_id=None,
                          damage_type=None, original_card_name=None, **kwargs) -> None:
        """执行技能版本的受伤"""
        player.take_damage_with_skill(damage, source_player_id, damage_type, original_card_name)
    
    def execute_default(self, player, damage=1, source_player_id=None,
                       damage_type=None, original_card_name=None, **kwargs) -> None:
        """执行默认版本的受伤"""
        player.take_damage_default(damage, source_player_id, damage_type, original_card_name)


class PhaseSkillManager:
    """阶段技能管理器（统一管理技能激活流程）"""
    
    def __init__(self):
        """初始化管理器，注册各阶段的处理器"""
        self.handlers = {
            GameEvent.DRAW_CARD: DrawCardPhaseSkillHandler(),
            GameEvent.PLAY_CARD: PlayCardPhaseSkillHandler(),
            GameEvent.DISCARD_CARD: DiscardCardPhaseSkillHandler(),
            GameEvent.DAMAGE: DamagePhaseSkillHandler(),
        }
    
    def execute_phase(self, player, event_type: GameEvent, **kwargs):
        """统一的阶段执行流程（模板方法）
        
        Args:
            player: 玩家对象
            event_type: 游戏事件类型
            **kwargs: 阶段特定的参数
            
        Returns:
            阶段执行结果
        """
        # 获取该阶段的技能名
        skill_name = player.skill_activate_time_with_skill.get(event_type)
        
        # 如果没有技能，直接执行默认流程
        if not skill_name:
            handler = self.handlers.get(event_type)
            if handler:
                return handler.execute_default(player, **kwargs)
            return None
        
        # 获取该阶段的处理器
        handler = self.handlers.get(event_type)
        if not handler:
            return None
        
        # 构建上下文
        context = handler.build_context(player, **kwargs)
        
        # 询问是否发动技能
        activate = player.ask_activate_skill(skill_name, context)
        
        # 根据是否发动技能执行对应流程
        if activate:
            game_logger.log_info(f"{player.name}发动技能[{skill_name}]")
            return handler.execute_with_skill(player, **kwargs)
        else:
            return handler.execute_default(player, **kwargs)

