# 后端模块

后端模块是猪国杀游戏的核心逻辑实现，采用面向对象设计模式，分为多个功能模块，各模块职责明确，便于维护和扩展。

> 📊 **架构图文档**: 本文档提供了模块的职责说明和开发指南。如需查看详细的模块关系图、数据流图、游戏主循环流程图等可视化图表，请参考 [ARCHITECTURE.md](ARCHITECTURE.md)。架构图文档包含 Mermaid 格式的图表，可在支持 Mermaid 的 Markdown 查看器中查看（如 GitHub、GitLab、VS Code 等）。内容仅供参考。

> 💡 **代码示例**: 如需查看具体的代码执行流程示例，请参考 [EXAMPLES.md](EXAMPLES.md)。示例文档通过"一个角色如何出一张杀"的完整流程，详细说明了各模块之间的交互过程。

## 模块架构

### 核心模块

#### 1. 主控制盘模块 (`main_controller/`)
- **职责**: 游戏入口点，负责配置管理和游戏启动
- 读取配置文件（支持JSON格式）
- 创建游戏控制盘模块
- 管理游戏日志会话

#### 2. 游戏控制盘模块 (`game_controller/`)
- **职责**: 游戏主循环控制，协调各模块交互
- 游戏初始化（创建牌堆、玩家控制器）
- 主游戏循环（摸牌→出牌→弃牌）
- 牌效果处理（通过策略模式实现）
- 游戏结束判断和濒死状态处理

#### 3. 玩家控制模块 (`player_controller/`)
- **职责**: 管理所有玩家，处理玩家相关操作
- 玩家列表管理
- 玩家事件分发（摸牌、出牌、弃牌等）
- 目标选择功能（攻击距离、全体、距离1等）
- 游戏结束判断

#### 4. 玩家模块 (`player/`)
- **职责**: 玩家基类，定义玩家行为和状态
- 玩家状态管理（血量、手牌、装备）
- 默认行为实现（摸牌、出牌、弃牌、受伤、死亡、回复、装备）
- 可继承设计，支持不同武将技能
- 装备管理（通过 `EquipmentManager`）
- 阶段技能处理（通过 `PhaseSkillManager`）

#### 5. 牌模块 (`card/`)
- **职责**: 定义牌的基本属性和行为
- 牌的基本信息（花色、点数、牌名）
- 牌类型分类（基本牌、锦囊牌、装备牌）
- 目标类型定义

#### 6. 牌堆模块 (`deck/`)
- **职责**: 管理游戏牌堆和弃牌堆
- 牌堆初始化（根据配置创建）
- 抽牌和弃牌功能
- 牌堆洗牌和弃牌堆回收

#### 7. 操控模块 (`control/`)
- **职责**: 玩家决策接口，支持多种操控方式
- **核心功能**:
  - 牌选择接口（`select_card`）：正常出牌阶段选择要出的牌
  - 响应牌选择接口（`ask_use_card_response`）：响应类查询（如响应决斗、响应南蛮入侵等）
  - 目标选择接口（`select_targets`）：为牌选择目标
  - 攻击范围过滤接口（`filter_attackable_targets`）：过滤攻击范围内的目标
  - 弃牌选择接口（`select_cards_to_discard`）：选择要弃的牌
- **事件处理**: 使用策略模式处理游戏事件（摸牌、出牌、受伤、死亡等），通过事件处理器更新内部状态
- **状态同步**: 通过 `sync_state()` 方法同步游戏状态，支持基于状态的决策
- **实现类型**:
  - `Control`：基类，提供默认实现
  - `SimpleControl`：规则操控实现，符合猪国杀规则，包含身份标记系统（跳忠、跳反、类反）和逆时针距离计算
- **支持操控方式**: 玩家操控（HUMAN）、AI操控（AI）、规则操控（SIMPLE_AI）

#### 8. 工具模块 (`utils/`)
- **职责**: 提供通用工具和日志系统
- 游戏日志系统（单例模式）
- 事件发送（前后端通信）

### 子模块

#### 玩家模块子模块
- **`equipment_manager.py`**: 装备管理器，负责装备的装备、卸下和状态管理
- **`phase_skill_handler.py`**: 阶段技能处理器，统一管理各阶段的技能激活逻辑

#### 游戏控制模块子模块
- **`card_effect_handler.py`**: 牌效果处理器，使用策略模式处理不同牌的效果

#### 操控模块子模块
- **`control.py`**: Control基类，定义决策接口和事件处理框架
- **`simple_control.py`**: SimpleControl实现，符合猪国杀规则的AI策略，包含身份识别、目标选择等逻辑
- **`control_factory.py`**: Control工厂类，根据操控类型创建对应的Control实例
- **`control_manager.py`**: Control管理器，统一管理所有Control实例，负责事件分发和状态同步
- **`event_handler.py`**: 事件处理器基类和默认实现
- **`simple_event_handler.py`**: SimpleControl专用的事件处理器，能够识别跳忠、跳反等行为
- **`zhuguosha_event_handler.py`**: 猪国杀专用事件处理器，处理身份标记和距离计算

## 核心流程

### 游戏启动流程
```
MainController.load_config() 
→ MainController.start_game() 
→ GameController.initialize() 
→ GameController.start_game()
```

### 游戏主循环
```
1. 摸牌阶段: player.draw_card()
2. 出牌阶段: 
   - player.play_card() 
   - 处理牌效果
   - 重复直到玩家选择结束
3. 弃牌阶段: player.discard_card()
4. 检查游戏结束
5. 切换到下一个玩家
```

## 开发指南

### 添加新武将

1. 在 `config/enums.py` 的 `CharacterName` 枚举中添加武将名枚举
2. 在 `backend/player/player.py` 中创建新的 Player 子类，继承 `Player` 并实现武将技能
3. 在 `backend/player_controller/player_factory.py` 中导入新武将类，并在 `PlayerFactory.create_player()` 方法中添加对应的判断逻辑

**可重写的基础方法**:
- `get_base_max_hp()`: 定义武将基础血量上限

**可重写的阶段技能方法**（当有技能时）:
在 `__init__` 中通过 `self.skill_activate_time_with_skill[GameEvent.XXX] = "技能名"` 注册技能后，可重写对应的 `_with_skill` 方法：
- `draw_card_phase_with_skill(count)`: 摸牌阶段技能
- `play_card_with_skill(available_targets)`: 出牌阶段技能
- `discard_card_with_skill()`: 弃牌阶段技能
- `take_damage_with_skill(damage, source_player_id)`: 受伤阶段技能

**其他可重写的方法**:
- `recover_hp()`: 回复血量逻辑

### 添加新牌

1. 在 `config/enums.py` 中添加牌名枚举
2. 在 `config/card_properties.py` 中配置牌属性（类型、目标类型等）
3. 在 `backend/game_controller/card_effect_handler.py` 中实现牌效果处理器：
4. 在 `CardEffectHandlerFactory` 中注册新处理器

### 修改游戏规则

在 `GameController.start_game()` 中修改主循环逻辑，或在 `GameController` 中添加新的游戏阶段处理。

### 添加新装备

装备牌作为普通牌处理，装备效果在 `EquipmentManager` 中实现。如需特殊装备效果，可在 `Player` 子类中重写相关方法。

### 添加新AI策略

1. 在 `backend/control/` 目录下创建新的 Control 子类，继承 `Control` 基类
2. 实现以下核心方法：
   - `select_card(available_cards, context, available_targets)`: 正常出牌阶段选择要出的牌
   - `ask_use_card_response(card_name, available_cards, context)`: 响应类查询（如响应决斗、响应南蛮入侵、受到杀的攻击等）
   - `select_targets(available_targets, card)`: 为牌选择目标
   - `filter_attackable_targets(targets, available_targets_dict)`: 过滤攻击范围内的目标（可选，用于特殊距离计算）
   - `select_cards_to_discard(hand_cards, count)`: 选择要弃的牌
3. 可选：重写 `sync_state(state)` 方法，自定义状态同步逻辑
4. 可选：注册自定义事件处理器，通过 `register_handler()` 方法处理特定事件
5. 在 `backend/control/control_factory.py` 的 `ControlFactory.create_control()` 方法中添加新策略的创建逻辑
6. 在配置文件中使用对应的 `ControlType` 枚举值

**参考实现**: `backend/control/simple_control.py` 实现了符合猪国杀规则的AI策略，包含：
- 身份标记系统（跳忠、跳反、类反）
- 逆时针距离计算
- 基于身份的目标选择逻辑
- 事件驱动的状态更新

### 调试问题

1. 查看 `logs/` 目录下的游戏日志文件
2. 使用日志系统记录关键状态：
   ```python
   from backend.utils.logger import game_logger
   game_logger.log_info("调试信息")
   game_logger.log_debug("详细调试信息")
   ```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_player.py

# 运行特定测试
pytest tests/test_player.py::test_specific_function
```

## 依赖关系

- **标准库**: `typing`, `logging`, `threading`, `json`, `os`, `sys`, `random`, `abc`
- **项目内部**: `config/`, `communicator/`

## 注意事项

1. **线程安全**: 日志系统使用单例模式，支持多线程
2. **内存管理**: 游戏结束时自动回收资源
3. **错误处理**: 各模块包含异常处理机制
4. **扩展性**: 设计时考虑了功能扩展需求
5. **事件通信**: 使用 `event_sender` 模块向前端发送事件，确保前后端状态同步
