from config.enums import CardName, CardType, ControlType, PlayerStatus, PlayerIdentity, CharacterName, TargetType
class PlayerConfig:
    name: str  # 玩家名称
    character_name: CharacterName  # 武将名
    identity: PlayerIdentity  # 身份
    control_type: ControlType  # 控制类型
    max_hp: int  # 血量上限