# Control工厂模块
"""根据操控类型创建对应的Control实例"""
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.control import Control
from backend.control.simple_control import SimpleControl
from backend.control.human_control import HumanControl
from backend.control.campaign_ai import CanBingAI, AdouAI, CaoJunAI
from config.enums import ControlType


class ControlFactory:
    """Control工厂类
    
    根据操控类型创建对应的Control实例
    """
    
    @staticmethod
    def create_control(control_type: ControlType, player_id: Optional[int] = None) -> Control:
        """创建Control实例
        
        Args:
            control_type: 操控类型
            player_id: 关联的玩家ID
            
        Returns:
            Control实例
        """
        if control_type == ControlType.SIMPLE_AI:
            # 规则操控：使用SimpleControl
            return SimpleControl(player_id)
        elif control_type == ControlType.CANBING_AI:
            # 残兵AI：第一章专用
            return CanBingAI(player_id)
        elif control_type == ControlType.ADOU_AI:
            # 阿斗AI：第二章专用
            return AdouAI(player_id)
        elif control_type == ControlType.CAOJUN_AI:
            # 曹军AI：第二章专用
            return CaoJunAI(player_id)
        elif control_type == ControlType.AI:
            # AI操控：暂时使用基类Control（后续可以实现AIControl）
            return Control(control_type, player_id)
        elif control_type == ControlType.HUMAN:
            # 玩家操控：返回 HumanControl（命令行/前端交互）
            return HumanControl(player_id)
        else:
            # 默认使用基类Control
            return Control(control_type, player_id)

