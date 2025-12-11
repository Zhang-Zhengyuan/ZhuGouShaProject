# 简化牌配置
from typing import List, Dict, Any
from dataclasses import dataclass
from .enums import CardSuit, CardName, ControlType, PlayerIdentity, CharacterName


@dataclass
class SimpleCardConfig:
    """简化的牌配置，只包含牌名、花色、点数"""
    name: CardName  # 牌名
    suit: CardSuit  # 花色
    rank: int  # 点数
    count: int = 1  # 该牌的数量


@dataclass
class SimplePlayerConfig:
    """简化的玩家配置"""
    name: str  # 玩家名称
    character_name: CharacterName = CharacterName.BAI_BAN_WU_JIANG  # 武将名
    identity: PlayerIdentity = PlayerIdentity.REBEL  # 身份
    control_type: ControlType = ControlType.AI  # 操控类型


@dataclass
class SimpleGameConfig:
    """简化的游戏配置"""
    # 牌堆配置
    deck_config: List[SimpleCardConfig]
    # 玩家配置
    players_config: List[SimplePlayerConfig]
    # 游戏规则配置
    shuffle_deck: bool = True  # 是否打乱牌堆
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SimpleGameConfig':
        """从字典创建配置对象
        
        Args:
            config_dict: 配置字典（必须由 to_dict() 方法产生）
            
        Returns:
            配置对象
            
        Raises:
            ValueError: 如果配置字典格式不正确或缺少必需字段
            KeyError: 如果枚举值不存在
            TypeError: 如果字段类型不正确
        """
        if not isinstance(config_dict, dict):
            raise TypeError(f"config_dict 必须是字典类型，实际类型: {type(config_dict)}")
        
        # 检查并解析牌堆配置
        if "deck" not in config_dict:
            raise ValueError("配置字典中缺少 'deck' 字段")
        if not isinstance(config_dict["deck"], list):
            raise TypeError(f"'deck' 必须是列表类型，实际类型: {type(config_dict['deck'])}")
        
        deck_config = []
        for idx, card_data in enumerate(config_dict["deck"]):
            if not isinstance(card_data, dict):
                raise TypeError(f"'deck[{idx}]' 必须是字典类型，实际类型: {type(card_data)}")
            
            # 检查必需字段
            if "name" not in card_data:
                raise ValueError(f"'deck[{idx}]' 缺少必需字段 'name'")
            if "suit" not in card_data:
                raise ValueError(f"'deck[{idx}]' 缺少必需字段 'suit'")
            if "rank" not in card_data:
                raise ValueError(f"'deck[{idx}]' 缺少必需字段 'rank'")
            if "count" not in card_data:
                raise ValueError(f"'deck[{idx}]' 缺少必需字段 'count'")
            
            # 检查字段类型并转换枚举
            if not isinstance(card_data["name"], str):
                raise TypeError(f"'deck[{idx}].name' 必须是字符串类型，实际类型: {type(card_data['name'])}")
            try:
                card_name = CardName[card_data["name"]]
            except KeyError:
                raise ValueError(f"'deck[{idx}].name' 无效的枚举值: {card_data['name']}")
            
            if not isinstance(card_data["suit"], str):
                raise TypeError(f"'deck[{idx}].suit' 必须是字符串类型，实际类型: {type(card_data['suit'])}")
            try:
                card_suit = CardSuit[card_data["suit"]]
            except KeyError:
                raise ValueError(f"'deck[{idx}].suit' 无效的枚举值: {card_data['suit']}")
            
            if not isinstance(card_data["rank"], int):
                raise TypeError(f"'deck[{idx}].rank' 必须是整数类型，实际类型: {type(card_data['rank'])}")
            
            if not isinstance(card_data["count"], int):
                raise TypeError(f"'deck[{idx}].count' 必须是整数类型，实际类型: {type(card_data['count'])}")
            
            card_config = SimpleCardConfig(
                name=card_name,
                suit=card_suit,
                rank=card_data["rank"],
                count=card_data["count"]
            )
            deck_config.append(card_config)
        
        # 检查并解析玩家配置
        if "players" not in config_dict:
            raise ValueError("配置字典中缺少 'players' 字段")
        if not isinstance(config_dict["players"], list):
            raise TypeError(f"'players' 必须是列表类型，实际类型: {type(config_dict['players'])}")
        
        players_config = []
        for idx, player_data in enumerate(config_dict["players"]):
            if not isinstance(player_data, dict):
                raise TypeError(f"'players[{idx}]' 必须是字典类型，实际类型: {type(player_data)}")
            
            # 检查必需字段
            if "name" not in player_data:
                raise ValueError(f"'players[{idx}]' 缺少必需字段 'name'")
            if "character_name" not in player_data:
                raise ValueError(f"'players[{idx}]' 缺少必需字段 'character_name'")
            if "identity" not in player_data:
                raise ValueError(f"'players[{idx}]' 缺少必需字段 'identity'")
            if "control_type" not in player_data:
                raise ValueError(f"'players[{idx}]' 缺少必需字段 'control_type'")
            
            # 检查字段类型并转换枚举
            if not isinstance(player_data["name"], str):
                raise TypeError(f"'players[{idx}].name' 必须是字符串类型，实际类型: {type(player_data['name'])}")
            
            if not isinstance(player_data["character_name"], str):
                raise TypeError(f"'players[{idx}].character_name' 必须是字符串类型，实际类型: {type(player_data['character_name'])}")
            try:
                character_name = CharacterName[player_data["character_name"]]
            except KeyError:
                raise ValueError(f"'players[{idx}].character_name' 无效的枚举值: {player_data['character_name']}")
            
            if not isinstance(player_data["identity"], str):
                raise TypeError(f"'players[{idx}].identity' 必须是字符串类型，实际类型: {type(player_data['identity'])}")
            try:
                identity = PlayerIdentity[player_data["identity"]]
            except KeyError:
                raise ValueError(f"'players[{idx}].identity' 无效的枚举值: {player_data['identity']}")
            
            if not isinstance(player_data["control_type"], str):
                raise TypeError(f"'players[{idx}].control_type' 必须是字符串类型，实际类型: {type(player_data['control_type'])}")
            try:
                control_type = ControlType[player_data["control_type"]]
            except KeyError:
                raise ValueError(f"'players[{idx}].control_type' 无效的枚举值: {player_data['control_type']}")
            
            player_config = SimplePlayerConfig(
                name=player_data["name"],
                character_name=character_name,
                identity=identity,
                control_type=control_type
            )
            players_config.append(player_config)
        
        # 解析游戏规则配置（可选，有默认值）
        shuffle_deck = True
        if "game" in config_dict:
            if not isinstance(config_dict["game"], dict):
                raise TypeError(f"'game' 必须是字典类型，实际类型: {type(config_dict['game'])}")
            if "shuffle_deck" in config_dict["game"]:
                if not isinstance(config_dict["game"]["shuffle_deck"], bool):
                    raise TypeError(f"'game.shuffle_deck' 必须是布尔类型，实际类型: {type(config_dict['game']['shuffle_deck'])}")
                shuffle_deck = config_dict["game"]["shuffle_deck"]
        
        return cls(
            deck_config=deck_config,
            players_config=players_config,
            shuffle_deck=shuffle_deck
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            配置字典
        """
        return {
            "deck": [
                {
                    "name": card.name.name,
                    "suit": card.suit.name,
                    "rank": card.rank,
                    "count": card.count
                }
                for card in self.deck_config
            ],
            "players": [
                {
                    "name": player.name,
                    "character_name": player.character_name.name,
                    "identity": player.identity.name,
                    "control_type": player.control_type.name
                }
                for player in self.players_config
            ],
            "game": {
                "shuffle_deck": self.shuffle_deck
            }
        }
