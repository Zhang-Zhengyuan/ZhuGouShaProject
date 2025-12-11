第一章：公孙瓒旧部（围剿模式）

目标：玩家扮演赵云，击败场上所有反贼。其余敌人为白板、1血、无技能。

如何使用：
- 在游戏启动前，调用 `campaign.create_chapter_one_players(deck, human_control=True, ai_count=4)`
  以获取玩家列表（列表顺序用于游戏中的玩家顺序）。

- 可调用 `campaign.apply_reward_choice(player, choice)` 将奖励技能临时赋予玩家（例如 "绝境"）。

设计说明：
- 本模块仅提供章节配置与玩家组装，保持与原有游戏主循环解耦。
- 推荐在 `main_zhuguosha.py` 中添加一个入口来选择“章节模式”并使用本脚手架构建玩家列表。
