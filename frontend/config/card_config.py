from config.enums import CardSuit, CardName
class CardConfig:
    name: CardName  # 牌名
    suit: CardSuit  # 花色
    rank: int  # 点数
    def __init__(self, card_name: CardName, suit: CardSuit, rank: int):
        self.name = card_name
        self.suit = suit
        self.rank = rank
    def __eq__(self, other):
        if not isinstance(other, CardConfig):
            return False
        return self.name == other.name and self.suit == other.suit and self.rank == other.rank