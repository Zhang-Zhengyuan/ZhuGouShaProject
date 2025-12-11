from enum import Enum

class GameStateEnum(Enum):
    """游戏状态枚举"""
    WAITING = 0
    ANIMATING = 1
    SELECTING = 2
    PAUSED = 3
    ENDED = 4
    SELECTING_TARGET = 5

class GameState:
    def __init__(self, start_state):
        self.state = start_state  # 当前游戏状态
    def set_state(self, new_state: GameStateEnum):
        self.state = new_state

game_state = GameState(GameStateEnum.WAITING)