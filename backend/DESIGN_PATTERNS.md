# 后端设计模式文档

本文档描述后端框架中实际使用的设计模式及其实现。

## 已实现的设计模式

### 1. 单例模式 (Singleton Pattern)

**位置**: `backend/utils/logger.py` 中的 `GameLogger` 类

**用途**: 确保整个游戏只有一个日志实例，统一管理日志记录

**实现特点**:
- 使用线程安全的双重检查锁定机制
- 支持多线程环境
- 延迟初始化，首次使用时才创建实例

**代码位置**:
```python
class GameLogger:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**使用方式**:
```python
from backend.utils.logger import game_logger

game_logger.log_info("游戏开始")
game_logger.log_debug("调试信息")
```

**优点**: 
- 避免重复创建日志实例，节省内存
- 统一日志管理，便于日志文件管理
- 线程安全，支持并发访问

---

### 2. 工厂模式 (Factory Pattern)

#### 2.1 玩家工厂 (`PlayerFactory`)

**位置**: `backend/player_controller/player_factory.py`

**用途**: 根据武将名枚举创建对应的玩家实例

**实现特点**:
- 静态工厂方法 `create_player()`
- 根据 `CharacterName` 枚举选择对应的玩家子类
- 支持扩展新武将，只需添加新的判断分支

**代码位置**:
```python
class PlayerFactory:
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
        if character_name == CharacterName.ZHANG_FEI:
            return ZhangFeiPlayer(...)
        elif character_name == CharacterName.LV_MENG:
            return LvmengPlayer(...)
        elif character_name == CharacterName.LING_CAO:
            return LingcaoPlayer(...)
        else:
            return Player(...)  # 默认白板武将
```

**使用方式**:
```python
from backend.player_controller.player_factory import PlayerFactory

player = PlayerFactory.create_player(
    player_id=0,
    name="张飞",
    control_type=ControlType.AI,
    deck=deck,
    character_name=CharacterName.ZHANG_FEI,
    identity=PlayerIdentity.REBEL
)
```

**优点**:
- 集中管理对象创建逻辑
- 隐藏具体子类的创建细节
- 易于添加新武将，符合开闭原则

#### 2.2 牌效果处理器工厂 (`CardEffectHandlerFactory`)

**位置**: `backend/game_controller/card_effect_handler.py`

**用途**: 根据牌的类型和名称创建对应的牌效果处理器

**实现特点**:
- 静态工厂方法 `create_handler()`
- 根据 `CardName` 枚举或 `CardType` 创建处理器
- 支持基本牌、锦囊牌、装备牌的统一处理

**代码位置**:
```python
class CardEffectHandlerFactory:
    @staticmethod
    def create_handler(card: Card, game_controller) -> CardEffectHandler:
        if card.name_enum == CardName.SHA:
            return ShaCardHandler(game_controller)
        elif card.name_enum == CardName.TAO:
            return TaoCardHandler(game_controller)
        elif card.card_type == CardType.EQUIPMENT:
            return EquipmentCardHandler(game_controller)
        # ...
```

**使用方式**:
```python
from backend.game_controller.card_effect_handler import CardEffectHandlerFactory

handler = CardEffectHandlerFactory.create_handler(card, game_controller)
if handler:
    handler.handle(card, targets)
```

**优点**:
- 解耦牌效果处理逻辑
- 易于添加新牌类型
- 统一处理接口

---

### 3. 策略模式 (Strategy Pattern)

#### 3.1 牌效果处理策略 (`CardEffectHandler`)

**位置**: `backend/game_controller/card_effect_handler.py`

**用途**: 将不同牌的效果处理封装为不同的策略类

**实现特点**:
- 抽象基类 `CardEffectHandler` 定义统一接口
- 具体策略类实现不同牌的效果（`ShaCardHandler`、`TaoCardHandler`、`JueDouCardHandler` 等）
- 通过工厂模式选择具体策略

**代码结构**:
```python
class CardEffectHandler(ABC):
    """牌效果处理器基类（策略模式）"""
    
    @abstractmethod
    def handle(self, card: Card, targets: List[int]) -> None:
        """处理牌效果"""
        pass

class ShaCardHandler(CardEffectHandler):
    """杀牌效果处理器"""
    def handle(self, card: Card, targets: List[int]) -> None:
        # 实现杀的效果
        pass

class TaoCardHandler(CardEffectHandler):
    """桃牌效果处理器"""
    def handle(self, card: Card, targets: List[int]) -> None:
        # 实现桃的效果
        pass
```

**使用方式**:
```python
handler = CardEffectHandlerFactory.create_handler(card, game_controller)
handler.handle(card, targets)
```

**优点**:
- 每种牌的效果独立封装，易于维护
- 符合开闭原则，添加新牌只需新增策略类
- 消除大量 if-else 判断，代码更清晰

#### 3.2 阶段技能处理策略 (`PhaseSkillHandler`)

**位置**: `backend/player/phase_skill_handler.py`

**用途**: 将不同阶段的技能处理封装为不同的策略类

**实现特点**:
- 抽象基类 `PhaseSkillHandler` 定义统一接口
- 具体策略类处理不同阶段的技能（`DrawCardPhaseSkillHandler`、`PlayCardPhaseSkillHandler` 等）
- 每个策略类负责构建上下文、执行技能版本和默认版本的操作

**代码结构**:
```python
class PhaseSkillHandler(ABC):
    """阶段技能处理器基类（策略模式）"""
    
    @abstractmethod
    def build_context(self, player, **kwargs) -> dict:
        """构建技能询问上下文"""
        pass
    
    @abstractmethod
    def execute_with_skill(self, player, **kwargs):
        """执行技能版本的操作"""
        pass
    
    @abstractmethod
    def execute_default(self, player, **kwargs):
        """执行默认版本的操作"""
        pass

class DrawCardPhaseSkillHandler(PhaseSkillHandler):
    """摸牌阶段技能处理器"""
    def build_context(self, player, count=2, **kwargs) -> dict:
        # 构建上下文
        pass
    
    def execute_with_skill(self, player, count=2, **kwargs) -> List[Card]:
        return player.draw_card_phase_with_skill(count)
    
    def execute_default(self, player, count=2, **kwargs) -> List[Card]:
        return player.draw_card_phase_default(count)
```

**使用方式**:
```python
from backend.player.phase_skill_handler import PhaseSkillManager

manager = PhaseSkillManager()
result = manager.execute_phase(player, GameEvent.DRAW_CARD, count=2)
```

**优点**:
- 统一技能激活流程
- 各阶段技能处理逻辑独立，易于扩展
- 支持技能询问和默认流程的统一管理

---

### 4. 模板方法模式 (Template Method Pattern)

**位置**: `backend/player/phase_skill_handler.py` 中的 `PhaseSkillManager`

**用途**: 定义阶段技能执行的统一流程模板，具体步骤由子类实现

**实现特点**:
- `PhaseSkillManager.execute_phase()` 定义模板方法
- 固定流程：检查技能 → 构建上下文 → 询问技能 → 执行对应版本
- 具体步骤由 `PhaseSkillHandler` 子类实现

**代码结构**:
```python
class PhaseSkillManager:
    """阶段技能管理器（统一管理技能激活流程）"""
    
    def execute_phase(self, player, event_type: GameEvent, **kwargs):
        """统一的阶段执行流程（模板方法）"""
        # 1. 获取技能名
        skill_name = player.skill_activate_time_with_skill.get(event_type)
        
        # 2. 如果没有技能，执行默认流程
        if not skill_name:
            handler = self.handlers.get(event_type)
            return handler.execute_default(player, **kwargs)
        
        # 3. 获取处理器
        handler = self.handlers.get(event_type)
        
        # 4. 构建上下文
        context = handler.build_context(player, **kwargs)
        
        # 5. 询问是否发动技能
        activate = player.ask_activate_skill(skill_name, context)
        
        # 6. 根据结果执行对应流程
        if activate:
            return handler.execute_with_skill(player, **kwargs)
        else:
            return handler.execute_default(player, **kwargs)
```

**使用方式**:
```python
# Player 类中调用
def draw_card_phase(self, count: int = 2) -> List[Card]:
    return self.phase_skill_manager.execute_phase(self, GameEvent.DRAW_CARD, count=count)
```

**优点**:
- 统一技能激活流程，避免代码重复
- 流程固定，易于理解和维护
- 子类只需实现具体步骤，无需关心整体流程

---

### 5. 封装/管理器模式 (Encapsulation/Manager Pattern)

**位置**: `backend/player/equipment_manager.py` 中的 `EquipmentManager`

**用途**: 封装装备管理逻辑，统一管理所有装备槽位

**实现特点**:
- 集中管理武器、防具、+1马、-1马四个装备槽位
- 提供统一的装备/卸下接口
- 封装装备相关的业务逻辑（如旧装备处理、事件发送等）

**代码结构**:
```python
class EquipmentManager:
    """装备管理器（统一管理所有装备槽位）"""
    
    def __init__(self, player_id: int, player_name: str, deck: Deck):
        self.weapon: Optional[Card] = None
        self.armor: Optional[Card] = None
        self.horse_plus: Optional[Card] = None
        self.horse_minus: Optional[Card] = None
        # ...
    
    def equip(self, card: Card) -> bool:
        """装备牌"""
        # 1. 确定槽位类型
        # 2. 处理旧装备
        # 3. 装备新牌
        # 4. 发送事件
        pass
    
    def unequip_all(self) -> List[tuple]:
        """卸下所有装备"""
        pass
```

**使用方式**:
```python
# Player 类中使用
self.equipment_manager = EquipmentManager(player_id, name, deck)
self.equipment_manager.equip(card)

# 通过属性访问（只读）
weapon = player.weapon  # 委托到 equipment_manager.weapon
```

**优点**:
- 封装装备管理逻辑，职责单一
- 简化 Player 类代码，提高可维护性
- 统一装备处理流程，避免代码重复

---

## 设计模式应用总结

### 模式组合使用

后端框架中多个设计模式经常组合使用：

1. **工厂模式 + 策略模式**: 
   - `CardEffectHandlerFactory` 使用工厂模式创建策略对象
   - `CardEffectHandler` 使用策略模式封装不同牌的效果

2. **策略模式 + 模板方法模式**:
   - `PhaseSkillHandler` 使用策略模式封装不同阶段的处理
   - `PhaseSkillManager` 使用模板方法模式定义统一流程

3. **封装模式 + 属性委托**:
   - `EquipmentManager` 封装装备管理逻辑
   - `Player` 通过属性委托提供向后兼容的接口

### 设计原则体现

- **单一职责原则**: 每个类只负责一个功能（如 `EquipmentManager` 只管理装备）
- **开闭原则**: 通过策略模式和工厂模式，易于扩展新功能而无需修改现有代码
- **依赖倒置原则**: 高层模块依赖抽象（如 `CardEffectHandler`），而非具体实现
- **封装原则**: 通过管理器模式封装复杂逻辑，提供简洁接口

### 代码质量提升

通过应用这些设计模式，后端代码实现了：
- **可维护性**: 代码结构清晰，职责明确
- **可扩展性**: 易于添加新武将、新牌、新技能
- **可测试性**: 模块化设计便于单元测试
- **可读性**: 代码组织合理，易于理解
