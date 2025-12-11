# 事件发送工具模块
"""后端向前端发送事件的工具函数"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.card.card import Card
from communicator.communicator import communicator
from communicator.comm_event import DrawCardEvent, PlayCardEvent, HPChangeEvent, DiscardCardEvent, EquipChangeEvent, DeathEvent, GameOverEvent
from config.simple_card_config import SimpleCardConfig
from config.enums import CardName, EquipmentType

# 全局配置：是否等待ACK确认（类似环境变量）
# 可以通过 set_wait_for_ack() 函数修改
_wait_for_ack: bool = False

# 全局ControlManager引用（由PlayerController设置）
_control_manager = None


def set_wait_for_ack(wait_for_ack: bool) -> None:
    """设置全局的 wait_for_ack 配置
    
    Args:
        wait_for_ack: 是否等待ACK确认，默认为True
    """
    global _wait_for_ack
    _wait_for_ack = wait_for_ack


def get_wait_for_ack() -> bool:
    """获取全局的 wait_for_ack 配置
    
    Returns:
        当前的 wait_for_ack 配置值
    """
    return _wait_for_ack


def set_control_manager(control_manager) -> None:
    """设置全局的ControlManager引用
    
    Args:
        control_manager: ControlManager实例
    """
    global _control_manager
    _control_manager = control_manager


def get_control_manager():
    """获取全局的ControlManager引用
    
    Returns:
        ControlManager实例或None
    """
    return _control_manager


def card_to_simple_config(card: Card) -> SimpleCardConfig:
    """将Card对象转换为SimpleCardConfig
    
    Args:
        card: Card对象
        
    Returns:
        SimpleCardConfig对象
    """
    return SimpleCardConfig(
        name=card.name_enum,
        suit=card.suit,
        rank=card.rank
    )


def send_draw_card_event(card: Card, to_player_id: int) -> tuple:
    """发送摸牌事件到前端

    Args:
        card: 摸到的牌
        to_player_id: 接收牌的玩家ID

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        event = None
        if communicator:
            card_config = card_to_simple_config(card)
            event = DrawCardEvent(card_config, to_player_id)
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)
        
        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)
        
        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def send_steal_card_event(card: Card, from_player_id: int, to_player_id: int) -> tuple:
    """发送夺牌事件到前端（用于动画表现：从目标玩家到赵云）

    Args:
        card: 被夺取的牌对象（可以为 None 表示牌面不可见）
        from_player_id: 被夺取的玩家ID
        to_player_id: 夺取者玩家ID

    Returns: (success, message) or (None,None)
    """
    try:
        event = None
        if communicator:
            card_config = card_to_simple_config(card) if card else None
            event = None
            from communicator.comm_event import StealCardEvent
            event = StealCardEvent(card_config, from_player_id, to_player_id)
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)

        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)

        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def send_play_card_event(card: Card, from_player_id: int, to_player_ids: list, 
                         response_type: str = None, response_target: int = None,
                         original_card_name: str = None, conversion_display: str = None, is_effective: bool = None) -> tuple:
    """发送出牌事件到前端

    Args:
        card: 使用的牌
        from_player_id: 出牌玩家ID
        to_player_ids: 目标玩家ID列表（可以是空列表或None）
        response_type: 响应类型（"响应决斗"、"响应南蛮入侵"、"响应万箭齐发"、"响应杀"等）
        response_target: 响应目标（对于响应类事件，表示响应的目标玩家ID）
        original_card_name: 原始牌名（对于响应类事件，表示响应的原始牌）
        is_effective: 是否生效（对于无懈可击，表示目标是否生效）

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        events = []
        if communicator:
            card_config = card_to_simple_config(card)
            # 确保to_player_ids是列表
            if to_player_ids is None:
                to_player_ids = []
            # 如果没有目标且不是响应类事件，发送给自己（某些牌可能没有目标）
            # 对于响应类事件（如响应决斗的杀、响应南蛮入侵的杀），发送给[-1]表示在中心显示
            if not to_player_ids:
                if response_type is None:
                    # 非响应类事件，发送给自己
                    to_player_ids = [from_player_id]
                else:
                    # 响应类事件，发送给[-1]表示在中心显示（前端会处理）
                    to_player_ids = [-1]

            # 对每个目标发送事件，只等待最后一个事件的ACK
            success = True
            message = ""
            for i, to_player_id in enumerate(to_player_ids):
                event = PlayCardEvent(
                    card_config, from_player_id, to_player_id,
                    response_type=response_type,
                    response_target=response_target,
                    original_card_name=original_card_name,
                    conversion_display=conversion_display,
                    is_effective=is_effective
                )
                events.append(event)
                result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack and i == len(to_player_ids) - 1)
                if _wait_for_ack and i == len(to_player_ids) - 1:
                    success, message = result

            # 通知ControlManager（只通知一次，因为所有Control都能看到）
            if _control_manager and events:
                _control_manager.notify_event(events[0])

            if _wait_for_ack:
                return success, message
            return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def send_hp_change_event(player_id: int, new_hp: int, source_player_id: int = None,
                         damage_type: str = None, original_card_name: str = None) -> tuple:
    """发送血量变化事件到前端

    Args:
        player_id: 玩家ID
        new_hp: 新的血量值
        source_player_id: 伤害来源玩家ID（如果是伤害）
        damage_type: 伤害类型（"杀"、"决斗"、"南蛮入侵"、"万箭齐发"等）
        original_card_name: 原始牌名（造成伤害的牌）

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        event = None
        if communicator:
            event = HPChangeEvent(
                player_id, new_hp,
                source_player_id=source_player_id,
                damage_type=damage_type,
                original_card_name=original_card_name
            )
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)
        
        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)
        
        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def send_discard_card_event(card: Card, player_id: int) -> tuple:
    """发送弃牌事件到前端

    Args:
        card: 弃掉的牌
        player_id: 弃牌的玩家ID

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        event = None
        if communicator:
            card_config = card_to_simple_config(card)
            event = DiscardCardEvent(card_config, player_id)
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)
        
        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)
        
        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def _get_equipment_type(card_name: CardName) -> EquipmentType:
    """根据牌名获取装备类型
    
    Args:
        card_name: 装备牌名称
        
    Returns:
        装备类型枚举
    """
    if card_name in [CardName.QING_GANG_JIAN, CardName.ZHU_GE_LIAN_NU]:
        return EquipmentType.WEAPON
    elif card_name == CardName.REN_WANG_DUN:
        return EquipmentType.ARMOR
    elif card_name == CardName.JIN_GONG_MA:
        return EquipmentType.HORSE_MINUS
    elif card_name == CardName.FANG_YU_MA:
        return EquipmentType.HORSE_PLUS
    else:
        # 默认返回武器类型
        return EquipmentType.WEAPON


def send_equip_change_event(player_id: int, equip_name: CardName, equip_type: EquipmentType) -> tuple:
    """发送装备变化事件到前端

    Args:
        player_id: 玩家ID
        equip_name: 装备牌名称
        equip_type: 装备类型

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        event = None
        if communicator:
            event = EquipChangeEvent(player_id, equip_name, equip_type)
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)
        
        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)
        
        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def send_death_event(player_id: int) -> tuple:
    """发送死亡事件到前端

    Args:
        player_id: 死亡的玩家ID

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        event = None
        if communicator:
            event = DeathEvent(player_id)
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)
        
        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)
        
        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None


def send_game_over_event(winner_info: str) -> tuple:
    """发送游戏结束事件到前端

    Args:
        winner_info: 胜利者信息

    Returns:
        (success: bool, message: str) - 如果全局wait_for_ack为False，返回(None, None)
    """
    try:
        event = None
        if communicator:
            event = GameOverEvent(winner_info=winner_info)
            result = communicator.send_to_frontend(event, wait_for_ack=_wait_for_ack)
        
        # 通知ControlManager
        if _control_manager and event:
            _control_manager.notify_event(event)
        
        if communicator and event:
            return result if _wait_for_ack else (None, None)
        return None, None
    except Exception as e:
        # 如果通信失败，不影响游戏逻辑
        if _wait_for_ack:
            return False, f"Communication error: {str(e)}"
        return None, None

