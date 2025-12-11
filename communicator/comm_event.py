from config.simple_card_config import SimpleGameConfig, SimpleCardConfig
from config.enums import EquipmentType, CardName
class CommEvent:
    """Base class for communication events."""
    pass

class DrawCardEvent(CommEvent):
    def __init__(self, card_config: SimpleCardConfig = None, to_player: int = None):
        self.card_config = card_config  # None表示牌面信息不可见
        self.to_player = to_player
class PlayCardEvent(CommEvent):
    def __init__(self, card_config: SimpleCardConfig, from_player: int, to_player: int, 
                 response_type: str = None, response_target: int = None, 
                 original_card_name: str = None, conversion_display: str = None, is_effective: bool = None):
        """
        出牌事件
        
        Args:
            card_config: 牌配置
            from_player: 出牌玩家ID
            to_player: 目标玩家ID
            response_type: 响应类型（"响应决斗"、"响应南蛮入侵"、"响应万箭齐发"、"响应杀"等）
            response_target: 响应目标（对于响应类事件，表示响应的目标玩家ID）
            original_card_name: 原始牌名（对于响应类事件，表示响应的原始牌）
            is_effective: 是否生效（对于无懈可击，表示目标是否生效）
        """
        self.card_config = card_config
        self.from_player = from_player
        self.to_player = to_player
        self.response_type = response_type  # 响应类型
        self.response_target = response_target  # 响应目标
        self.original_card_name = original_card_name  # 原始牌名
        self.conversion_display = conversion_display  # 如果本次出牌是由转化（龙胆等）产生，前端可以用此字段展示特殊卡面
        self.is_effective = is_effective  # 是否生效（无懈可击用）
class DiscardCardEvent(CommEvent):
    def __init__(self, card_config: SimpleCardConfig, player: int):
        self.card_config = card_config
        self.player = player
class HPChangeEvent(CommEvent):
    def __init__(self, player_id: int, new_hp: int, source_player_id: int = None, 
                 damage_type: str = None, original_card_name: str = None):
        """
        血量变化事件
        
        Args:
            player_id: 玩家ID
            new_hp: 新的血量值
            source_player_id: 伤害来源玩家ID（如果是伤害）
            damage_type: 伤害类型（"杀"、"决斗"、"南蛮入侵"、"万箭齐发"等）
            original_card_name: 原始牌名（造成伤害的牌）
        """
        self.player_id = player_id
        self.new_hp = new_hp
        self.source_player_id = source_player_id  # 伤害来源
        self.damage_type = damage_type  # 伤害类型
        self.original_card_name = original_card_name  # 原始牌名
class EquipChangeEvent(CommEvent):
    def __init__(self, player_id: int, equip_name: CardName, equip_type: EquipmentType):
        self.player_id = player_id
        self.equip_name = equip_name
        self.equip_type = equip_type
class DeathEvent(CommEvent):
    def __init__(self, player_id: int):
        self.player_id = player_id
class GameOverEvent(CommEvent):
    def __init__(self, winner_id: int = None, winner_info: str = None):
        self.winner_id = winner_id
        self.winner_info = winner_info

class AckEvent(CommEvent):
    """ACK确认事件"""
    def __init__(self, original_event_id: int, success: bool = True, message: str = ""):
        self.original_event_id = original_event_id
        self.success = success
        self.message = message
class StealCardEvent(CommEvent):
    def __init__(self, card_config: SimpleCardConfig, from_player: int, to_player: int):
        self.card_config = card_config
        self.from_player = from_player
        self.to_player = to_player

class DebugEvent(CommEvent):
    def __init__(self, command: str):
        self.command = command  # "win" or "lose"

class AskPlayCardEvent(CommEvent):
    """后端请求前端出牌"""
    def __init__(self, available_cards: list = None):
        self.available_cards = available_cards # List of SimpleCardConfig

class PlayCardResponseEvent(CommEvent):
    """前端响应出牌请求"""
    def __init__(self, card_index: int):
        self.card_index = card_index # Index in the available_cards list, or -1 for cancel/skip

class AskTargetEvent(CommEvent):
    """后端请求前端选择目标"""
    def __init__(self, available_targets: list):
        self.available_targets = available_targets # List of player_ids

class TargetResponseEvent(CommEvent):
    """前端响应目标选择"""
    def __init__(self, target_ids: list):
        self.target_ids = target_ids # List of player_ids, or None/empty for cancel