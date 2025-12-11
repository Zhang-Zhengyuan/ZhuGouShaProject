"""命令行交互的 Human 控制器实现

该实现继承自 `Control`，在命令行中提示用户选择牌、目标和响应。
用于快速原型和手动对战测试。后续可替换为基于 `communicator` 的前端实现。
"""
from typing import List, Optional, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.control.control import Control
from backend.card.card import Card
from config.enums import ControlType, CardName, TargetType
from communicator.communicator import communicator
from communicator.comm_event import AskPlayCardEvent, PlayCardResponseEvent, AskTargetEvent, TargetResponseEvent
from config.simple_card_config import SimpleCardConfig


class HumanControl(Control):
    """基于命令行交互的 Control 实现。"""

    def __init__(self, player_id: Optional[int] = None):
        super().__init__(ControlType.HUMAN, player_id)

    def _ask_frontend_for_targets(self, available_targets: List[int]) -> List[int]:
        """请求前端选择目标"""
        communicator.send_to_frontend(AskTargetEvent(available_targets=available_targets))
        
        print("[后端] 等待前端选目标...")
        while True:
            event = communicator.get_from_frontend(timeout=None)
            if isinstance(event, TargetResponseEvent):
                if event.target_ids is None:
                    return []
                # 验证目标有效性
                valid_targets = [pid for pid in event.target_ids if pid in available_targets]
                return valid_targets
            # 忽略其他事件

    def _ask_frontend_for_card(self, available_cards: List[Card]) -> Optional[Card]:
        """请求前端选择卡牌"""
        # 转换卡牌配置
        simple_cards = []
        for c in available_cards:
            simple_cards.append(SimpleCardConfig(c.name_enum, c.suit, c.rank))
        
        # 发送请求
        communicator.send_to_frontend(AskPlayCardEvent(available_cards=simple_cards))
        
        # 等待响应
        print("[后端] 等待前端选牌...")
        while True:
            event = communicator.get_from_frontend(timeout=None)
            if isinstance(event, PlayCardResponseEvent):
                idx = event.card_index
                if idx == -1:
                    return None
                if 0 <= idx < len(available_cards):
                    return available_cards[idx]
            # 忽略其他事件（或者应该处理？）
            # 实际上这里可能会丢弃其他重要事件，但在同步模型下暂时只能这样
            
    def _print_cards(self, cards: List[Card]) -> None:
        for i, c in enumerate(cards):
            try:
                display = str(c)
            except Exception:
                display = getattr(c, 'name', repr(c))
            print(f"  [{i}] {display}")

    def _prompt_index(self, prompt: str, max_index: int, allow_empty: bool = True) -> Optional[int]:
        """提示用户输入单个索引，返回 None 表示跳过。"""
        while True:
            s = input(prompt).strip()
            if s == "" and allow_empty:
                return None
            if s.lower() in ("q", "quit", "exit"):
                print("退出交互，使用默认行为")
                return None
            try:
                idx = int(s)
                if 0 <= idx <= max_index:
                    return idx
            except Exception:
                pass
            print(f"输入无效，请输入 0 - {max_index} 的整数，或直接回车跳过")

    def _prompt_indices(self, prompt: str, max_index: int, required_count: int = 1) -> List[int]:
        """提示用户输入多个索引（以逗号分隔），返回索引列表。"""
        while True:
            s = input(prompt).strip()
            if s.lower() in ("q", "quit", "exit"):
                print("退出交互，返回空列表")
                return []
            parts = [p.strip() for p in s.split(",") if p.strip() != ""]
            try:
                idxs = [int(p) for p in parts]
            except Exception:
                print("输入格式错误，请输入逗号分隔的索引，例如: 0,2,3")
                continue
            if any(i < 0 or i > max_index for i in idxs):
                print(f"索引超出范围，请输入 0 - {max_index} 的值")
                continue
            if len(idxs) < required_count:
                print(f"请至少选择 {required_count} 个目标")
                continue
            return idxs

    def select_card(self, available_cards: List[Card], context: str = "", available_targets: Dict[str, List[int]] = None) -> Optional[Card]:
        """让用户选择要出的牌"""
        if not available_cards:
            return None
        
        # 优先尝试使用前端交互
        try:
            return self._ask_frontend_for_card(available_cards)
        except Exception as e:
            print(f"[警告] 前端交互失败，回退到命令行: {e}")
        
        print("请选择要出的牌（从左往右索引），直接回车表示不出：")
        self._print_cards(available_cards)
        idx = self._prompt_index(f"选择牌索引 (0-{len(available_cards)-1}): ", len(available_cards)-1, allow_empty=True)
        if idx is None:
            return None
        return available_cards[idx]

    def select_targets(self, available_targets: List[int], card: Optional[Card] = None) -> List[int]:
        """让用户选择目标列表（返回 player_id 列表）"""
        if not available_targets:
            return []
            
        # 如果卡牌是 SELF，则直接返回自己 (无需前端交互)
        if card is not None and card.target_type == TargetType.SELF:
            return [self.player_id]
            
        # 优先尝试使用前端交互
        try:
            return self._ask_frontend_for_targets(available_targets)
        except Exception as e:
            print(f"[警告] 前端交互失败，回退到命令行: {e}")

        # 打印目标索引及玩家id（这里available_targets就是player ids）
        print("请选择目标（可以输入单个索引或多个索引以逗号分隔）：")
        for i, pid in enumerate(available_targets):
            print(f"  [{i}] 玩家{pid}")
        
        # 决斗只允许一个目标
        required = 1
        idxs = self._prompt_indices(f"输入目标索引（0-{len(available_targets)-1}），逗号分隔: ", len(available_targets)-1, required_count=required)
        if not idxs:
            return []
        return [available_targets[i] for i in idxs[:required]]

    def ask_use_card_response(self, card_name: CardName, available_cards: List[Card], context: str = "") -> Optional[Card]:
        """询问玩家是否使用指定牌（响应类），返回选择的牌或 None"""
        if not available_cards:
            return None
            
        # 优先尝试使用前端交互
        try:
            return self._ask_frontend_for_card(available_cards)
        except Exception as e:
            print(f"[警告] 前端交互失败，回退到命令行: {e}")

        print(f"是否使用 {card_name.value} 响应？")
        self._print_cards(available_cards)
        idx = self._prompt_index(f"选择牌索引 (0-{len(available_cards)-1}): ", len(available_cards)-1, allow_empty=True)
        if idx is None:
            return None
        return available_cards[idx]
        print(f"响应询问: {context}")
        print("你的可用响应牌：")
        self._print_cards(available_cards)
        print("输入要使用的牌索引，或直接回车表示不使用")
        idx = self._prompt_index(f"选择牌索引 (0-{len(available_cards)-1}): ", len(available_cards)-1, allow_empty=True)
        if idx is None:
            return None
        return available_cards[idx]

    def ask_activate_skill(self, skill_name: str, context: dict) -> bool:
        """询问玩家是否发动技能，返回 True/False"""
        print(f"是否发动技能 '{skill_name}'? 上下文: {context}")
        while True:
            s = input("输入 y/n（默认 n）: ").strip().lower()
            if s == "y":
                return True
            if s == "n" or s == "":
                return False
            print("请输入 'y' 或 'n'")

    def ask_steal_from_target(self, target_player_id: int, target_hand_count: int, context: str = "") -> Optional[int]:
        """询问是否从目标手牌中夺取一张（命令行实现）。

        只显示目标手牌数量，不显示牌面内容。返回0-based索引或None表示不夺取。
        """
        if target_hand_count <= 0:
            return None
        # 显示目标手牌数量但不泄露牌面
        print(f"目标 玩家{target_player_id} 有 {target_hand_count} 张手牌（手牌内容保密）。")
        print("手牌编号: ", end="")
        for i in range(1, target_hand_count + 1):
            print(f" 手牌{i}", end="")
        print("")
        prompt = f"输入要夺取的手牌编号 (1-{target_hand_count})，或直接回车表示不夺取: "
        idx = self._prompt_index(prompt, target_hand_count - 1, allow_empty=True)
        if idx is None:
            return None
        return idx

    def select_cards_to_discard(self, hand_cards: List[Card], count: int) -> List[Card]:
        """弃牌阶段提示用户选择要弃的牌（返回 Card 列表）"""
        if count <= 0:
            return []
        if count >= len(hand_cards):
            return hand_cards.copy()
        print(f"需要弃置 {count} 张牌，请选择索引（逗号分隔）：")
        self._print_cards(hand_cards)
        idxs = self._prompt_indices(f"输入 {count} 个索引，例如 0,2: ", len(hand_cards)-1, required_count=count)
        if not idxs:
            # 默认弃置前 count 张
            return hand_cards[:count]
        return [hand_cards[i] for i in idxs[:count]]
