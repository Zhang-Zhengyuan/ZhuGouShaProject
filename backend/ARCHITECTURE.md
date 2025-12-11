# 后端架构图

本文档包含后端模块的架构图和运行逻辑图，用于可视化理解模块间的关系和数据流。

## 模块间联系示意图

```mermaid
graph TB
    %% 外部依赖
    Config[config/] --> MainController
    Frontend[frontend/] -.-> MainController
    
    %% 核心模块层次
    MainController[主控制盘模块<br/>main_controller/] --> GameController[游戏控制盘模块<br/>game_controller/]
    GameController --> PlayerController[玩家控制模块<br/>player_controller/]
    GameController --> Deck[牌堆模块<br/>deck/]
    
    %% 玩家相关模块
    PlayerController --> Player[玩家模块<br/>player/]
    Player --> Control[操控模块<br/>control/]
    Player --> Card[牌模块<br/>card/]
    Player --> Deck
    
    %% 牌相关模块
    Deck --> Card
    Control --> Card
    
    %% 工具模块（被所有模块使用）
    Utils[工具模块<br/>utils/] -.-> MainController
    Utils -.-> GameController
    Utils -.-> PlayerController
    Utils -.-> Player
    Utils -.-> Deck
    Utils -.-> Control
    Utils -.-> Card
    
    %% 子模块
    Player --> EquipmentManager[装备管理器<br/>equipment_manager.py]
    Player --> PhaseSkillManager[阶段技能处理器<br/>phase_skill_handler.py]
    GameController --> CardEffectHandler[牌效果处理器<br/>card_effect_handler.py]
    Control --> ControlManager[Control管理器<br/>control_manager.py]
    Control --> EventHandler[事件处理器<br/>event_handler.py]
    
    %% 样式定义
    classDef coreModule fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef dataModule fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef utilModule fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef externalModule fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef subModule fill:#fce4ec,stroke:#880e4f,stroke-width:1px
    
    class MainController,GameController,PlayerController coreModule
    class Player,Card,Deck,Control dataModule
    class Utils utilModule
    class Config,Frontend externalModule
    class EquipmentManager,PhaseSkillManager,CardEffectHandler,ControlManager,EventHandler subModule
```

### 模块依赖关系说明

- **实线箭头**: 直接依赖关系，表示模块A直接使用模块B
- **虚线箭头**: 间接依赖关系，表示模块A通过其他模块间接使用模块B
- **核心模块**: 控制游戏流程的主要模块（蓝色）
- **数据模块**: 管理游戏数据和状态的基础模块（紫色）
- **工具模块**: 提供通用功能的支持模块（绿色）
- **外部模块**: 项目外部依赖（橙色）
- **子模块**: 模块内部的辅助类（粉色）

## 游戏运行时数据流图

```mermaid
sequenceDiagram
    participant MC as MainController
    participant GC as GameController
    participant PC as PlayerController
    participant P as Player
    participant Ctrl as Control
    participant EM as EquipmentManager
    participant PSM as PhaseSkillManager
    participant D as Deck
    participant C as Card
    participant CEH as CardEffectHandler
    participant U as Utils
    
    Note over MC: 游戏启动
    MC->>GC: 创建游戏控制器
    GC->>PC: 创建玩家控制器
    GC->>D: 创建牌堆
    PC->>P: 创建玩家实例
    P->>Ctrl: 创建Control实例
    P->>EM: 初始化装备管理器
    P->>PSM: 初始化阶段技能管理器
    P->>D: 抽取初始手牌
    D->>C: 返回牌对象
    PC->>Ctrl: 同步游戏状态
    
    Note over GC: 游戏主循环
    loop 每个回合
        GC->>PC: 获取当前玩家
        GC->>U: 记录玩家状态
        GC->>U: 记录牌堆状态
        PC->>Ctrl: 同步游戏状态
        
        Note over P: 摸牌阶段
        PC->>P: 摸牌事件
        P->>PSM: 执行摸牌阶段技能
        PSM->>Ctrl: 询问是否发动技能
        Ctrl->>PSM: 返回技能发动结果
        PSM->>P: 返回技能处理结果
        P->>D: 抽取手牌
        D->>C: 返回牌对象
        P->>U: 发送摸牌事件
        U->>Ctrl: 通知摸牌事件
        
        Note over P: 出牌阶段
        loop 出牌循环
            PC->>P: 出牌事件
            P->>PSM: 执行出牌阶段技能
            PSM->>Ctrl: 询问是否发动技能
            Ctrl->>PSM: 返回技能发动结果
            P->>Ctrl: 查询可选牌和目标
            Ctrl->>P: 返回选择的牌
            P->>Ctrl: 查询选择的目标
            Ctrl->>P: 返回选择的目标
            P->>PC: 返回牌和目标
            GC->>CEH: 处理牌效果
            CEH->>P: 执行牌效果
            P->>EM: 更新装备状态（如需要）
            P->>U: 发送出牌事件
            U->>Ctrl: 通知出牌事件
        end
        
        Note over P: 弃牌阶段
        PC->>P: 弃牌事件
        P->>PSM: 执行弃牌阶段技能
        PSM->>Ctrl: 询问是否发动技能
        Ctrl->>PSM: 返回技能发动结果
        P->>Ctrl: 查询要弃的牌
        Ctrl->>P: 返回选择的牌
        P->>D: 弃牌到弃牌堆
        P->>U: 发送弃牌事件
        U->>Ctrl: 通知弃牌事件
        
        GC->>PC: 检查游戏结束
    end
    
    Note over MC: 游戏结束
    MC->>U: 结束游戏会话
```

## 游戏主循环详细流程

```mermaid
flowchart TD
    Start([游戏开始]) --> Init[初始化游戏]
    Init --> CreateDeck[创建牌堆]
    CreateDeck --> CreatePlayers[创建玩家]
    CreatePlayers --> GetInitialPlayer[获取初始玩家]
    GetInitialPlayer --> GameLoop{游戏主循环}
    
    GameLoop --> SyncState[同步游戏状态到Control]
    SyncState --> DrawPhase[摸牌阶段]
    DrawPhase --> AskSkill1{询问Control<br/>是否发动技能?}
    AskSkill1 -->|是| DrawCardSkill[执行技能摸牌]
    AskSkill1 -->|否| DrawCard[默认摸牌]
    DrawCardSkill --> PlayPhase[出牌阶段]
    DrawCard --> PlayPhase
    
    PlayPhase --> SelectCard{询问Control<br/>选择出牌?}
    SelectCard -->|是| AskTargets[询问Control<br/>选择目标]
    AskTargets --> PlayCard[玩家出牌]
    PlayCard --> HandleEffect[处理牌效果]
    HandleEffect --> CheckDeath{有玩家死亡?}
    CheckDeath -->|是| HandleDeath[处理死亡逻辑]
    CheckDeath -->|否| SelectCard
    HandleDeath --> CheckGameEnd1{游戏结束?}
    CheckGameEnd1 -->|是| EndGame([游戏结束])
    CheckGameEnd1 -->|否| SelectCard
    SelectCard -->|否| DiscardPhase[弃牌阶段]
    
    DiscardPhase --> AskSkill2{询问Control<br/>是否发动技能?}
    AskSkill2 -->|是| DiscardSkill[执行技能弃牌]
    AskSkill2 -->|否| AskDiscard[询问Control<br/>选择要弃的牌]
    AskDiscard --> DiscardCard[玩家弃牌]
    DiscardSkill --> CheckGameEnd2{游戏结束?}
    DiscardCard --> CheckGameEnd2
    CheckGameEnd2 -->|是| EndGame
    CheckGameEnd2 -->|否| NextPlayer[切换到下一个玩家]
    NextPlayer --> GameLoop
    
    EndGame --> Cleanup[清理资源]
    Cleanup --> Finish([结束])
```

