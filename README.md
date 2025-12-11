# 猪国杀

一个基于 Python 的卡牌游戏项目，规则与"三国杀"大体一致并进行简化。本项目旨在锻炼 Python 编程能力、面向对象编程思路和设计模式的应用。

## 项目简介

猪国杀是一款回合制卡牌游戏，基于省选原题 [SDOI2010] 猪国杀（详见 [ZHUGUOSHA.md](ZHUGUOSHA.md)）实现。玩家扮演不同身份（主公、忠臣、反贼）的武将，通过出牌、使用技能等方式进行游戏。游戏支持多种操控方式（玩家操控、AI操控），并提供了完整的游戏逻辑和可视化界面。

本项目框架在完全兼容原题规则、能够通过原题测试用例的基础上，提供了良好的可扩展性和可玩性。通过前后端分离的架构设计、模块化的代码结构以及丰富的配置选项，开发者可以轻松扩展新武将、新牌型和新AI策略，同时玩家也可以通过图形界面体验完整的游戏流程。

## 项目架构

项目采用前后端分离的架构设计，分为以下三个主要部分：

### 前端 (`frontend/`)
- 使用 **pygame** 实现游戏界面
- 负责用户交互和视觉呈现
- 与后端通过通信模块进行数据交换
- 详细文档请参考 [frontend/README.md](frontend/README.md)

### 后端 (`backend/`)
- 游戏核心逻辑实现
- 采用面向对象设计，模块化架构
- 包含玩家模块、牌堆模块、游戏控制模块等
- 支持配置驱动，便于扩展和测试
- 详细文档请参考 [backend/README.md](backend/README.md)

### 测试 (`tests/`)
- 单元测试
- 使用 pytest 框架
- 覆盖核心游戏逻辑

## 技术栈

- **Python 3.x**
- **pygame** - 游戏界面框架
- **pytest** - 单元测试框架

## 项目结构

```
legends-of-the-pig-kingdoms/
├── backend/              # 后端模块（游戏逻辑）
├── frontend/             # 前端模块（游戏界面）
├── config/               # 配置文件模块
├── config_file/          # JSON 配置文件目录
├── communicator/         # 前后端通信模块
├── tests/                # 测试文件
├── logs/                 # 日志文件目录
├── main_back.py          # 后端启动入口
├── main_front.py         # 前端启动入口
├── main_integrated.py    # 前后端整合启动入口
├── requirements.txt      # 项目依赖
└── README.md             # 项目说明文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行游戏

#### 方式一：前后端整合运行
```bash
python main_integrated.py
```

#### 方式二：仅运行后端
```bash
# 终端1：启动后端
python main_back.py

```

### 3. 使用配置文件

游戏支持通过 JSON 配置文件自定义游戏参数：

- 配置文件位置：`config_file/` 目录
- 默认配置文件：`config_file/default_game_config.json`
- 可通过启动界面选择配置文件，或使用命令行参数指定

```bash
# 使用命令行指定配置文件
python main_back.py --config my_config
```

## 配置说明

游戏配置通过 JSON 文件定义，包括：

- **玩家配置**：玩家身份、武将、操控方式等
- **牌堆配置**：牌的种类、数量、属性等
- **游戏规则**：洗牌、初始手牌数等

配置文件示例和详细说明请参考 `config_file/` 目录下的示例文件。

## 设计特点

- **模块化设计**：各模块职责明确，便于维护和扩展
- **面向对象编程**：使用继承、多态等特性实现武将技能扩展
- **设计模式应用**：策略模式、工厂模式、单例模式等
- **配置驱动**：游戏参数通过配置文件控制，便于调试和平衡性调整
- **完整的日志系统**：记录游戏事件，便于调试和回放

## 开发指南

### 添加新武将
继承 `Player` 类，重写相关方法实现武将技能。

### 添加新牌
在配置文件中添加牌的定义，并在相关模块中实现牌的效果处理。

### 添加新AI策略
继承 `Control` 类，实现 `select_card`、`select_targets`、`ask_use_card_response` 等方法。可以参考 `backend/control/simple_control.py` 的实现，该文件实现了符合猪国杀规则的AI策略。

### 运行测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_batch_game.py

# 查看详细输出
pytest tests/ -v
```

## 文档

- [后端文档](backend/README.md) - 后端模块详细文档
- [前端文档](frontend/README.md) - 前端模块详细文档
- [猪国杀规则文档](ZHUGUOSHA.md) - 省选原题（SDOI2010）规则说明
- [作业说明](HOMEWORK.md) - Git 小作业任务说明

## 注意事项

- 确保 Python 版本 >= 3.7
- 首次运行前请安装所有依赖
- 配置文件需符合 JSON 格式规范
- 游戏日志保存在 `logs/` 目录下

## 许可证

本项目为课程作业项目。

