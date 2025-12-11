# 玩家模块
from typing import List, Optional, Tuple, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.card.card import Card
from backend.deck.deck import Deck
from config.card_properties import get_card_properties
from backend.control.control import Control
from backend.control.control_factory import ControlFactory
from backend.player.equipment_manager import EquipmentManager
from backend.player.phase_skill_handler import PhaseSkillManager
from backend.utils.logger import game_logger
from backend.utils.event_sender import send_draw_card_event, send_play_card_event, send_hp_change_event, send_discard_card_event, send_equip_change_event, send_death_event
from config.enums import CardName, CardType, ControlType, PlayerStatus, PlayerIdentity, CharacterName, TargetType, GameEvent, EquipmentType, CardSuit


class Player:
    """玩家基类
    
    这个模块要继承，其中每一个函数都包含一个默认函数。
    所有都为子类的为白板武将，在实现其他武将时，应继承默认函数，并修改外接口。
    """
    
    # 武将基础血量上限映射（子类可以覆盖 get_base_max_hp 方法来自定义）
    
    def get_base_max_hp(self) -> int:
        """获取武将的基础血量上限（子类可以覆盖此方法来自定义）
        
        Returns:
            基础血量上限
        """
        return 4
    
    def __init__(self, player_id: int, name: str, control_type: ControlType, deck: Deck, identity: PlayerIdentity = None, character_name: CharacterName = None, player_controller = None):
        """初始化函数
        
        Args:
            player_id: 玩家ID
            name: 玩家名称
            control_type: 操控类型
            deck: 牌堆
            identity: 玩家身份
            character_name: 武将名
            player_controller: 玩家控制器引用
        """
        self.player_id = player_id
        self.name = name
        self.character_name = character_name or CharacterName.BAI_BAN_WU_JIANG  # 武将名，默认为白板武将
        self.identity = identity or PlayerIdentity.REBEL  # 玩家身份，默认为反贼
        self.status = PlayerStatus.ALIVE  # 存活状态
        
        # 计算血量上限：基础血量上限 + 主公加成（+1）
        base_max_hp = self.get_base_max_hp()
        if self.identity == PlayerIdentity.LORD:
            self.max_hp = base_max_hp + 1  # 主公血量上限+1
        else:
            self.max_hp = base_max_hp
        
        self.current_hp = self.max_hp  # 当前血量等于血量上限
        self.initial_hand_size = 4  # 初始手牌数量
        
        self.deck = deck
        
        # 手牌
        self.hand_cards: List[Card] = []
        
        # 装备管理器
        self.equipment_manager = EquipmentManager(player_id, name, deck)
        
        # 阶段技能管理器
        self.phase_skill_manager = PhaseSkillManager()
        
        # 操控模块（使用工厂模式创建）
        self.control = ControlFactory.create_control(control_type, player_id)
        
        # 回合状态跟踪
        self.sha_used_this_turn = False  # 当前回合是否已使用杀
        self.player_controller = player_controller  # 玩家控制器引用
        
        # 伤害来源追踪
        self.last_damage_source: Optional[int] = None  # 最后一次伤害的来源玩家ID
        
        self.skill_activate_time_with_skill = { # 技能发动时间
            GameEvent.DRAW_CARD: None,
            GameEvent.PLAY_CARD: None,
            GameEvent.DISCARD_CARD: None,
            GameEvent.DAMAGE: None,
            GameEvent.HEAL: None,
            GameEvent.DEATH: None,
            GameEvent.EQUIP: None,
        }
    
    # 装备属性（只读，向后兼容，从 EquipmentManager 获取）
    # 注意：只能通过 equipment_manager.equip() 来装备，不能直接修改这些属性
    @property
    def weapon(self) -> Optional[Card]:
        """武器牌"""
        return self.equipment_manager.weapon
    
    @property
    def armor(self) -> Optional[Card]:
        """防具牌"""
        return self.equipment_manager.armor
    
    @property
    def horse_plus(self) -> Optional[Card]:
        """+1马"""
        return self.equipment_manager.horse_plus
    
    @property
    def horse_minus(self) -> Optional[Card]:
        """-1马"""
        return self.equipment_manager.horse_minus
    
    def _draw_initial_cards(self) -> None:
        """抽取初始手牌"""
        for _ in range(self.initial_hand_size):
            card = self.deck.draw_card()
            if card:
                self.hand_cards.append(card)
                
                # 发送摸牌事件到前端
                send_draw_card_event(card, self.player_id)
        
        # 记录初始手牌
        if self.hand_cards:
            card_names = [card.name for card in self.hand_cards]
            game_logger.log_info(f"{self.name} 初始手牌: {', '.join(card_names)}")
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.status == PlayerStatus.ALIVE
    
    def draw_card(self, count: int = 2) -> List[Card]:
        """一般摸牌（直接摸牌，不触发技能询问）
        
        Args:
            count: 摸牌数量
            
        Returns:
            摸到的牌列表
        """
        drawn_cards = []
        for _ in range(count):
            card = self.deck.draw_card()
            if card:
                self.hand_cards.append(card)
                drawn_cards.append(card)
                
                # 发送摸牌事件到前端
                send_draw_card_event(card, self.player_id)
        
        # 记录摸牌日志
        if drawn_cards:
            game_logger.log_player_draw_cards(self.name, drawn_cards)
        
        return drawn_cards
    
    def draw_card_phase(self, count: int = 2) -> List[Card]:
        """摸牌阶段（使用阶段技能管理器）

        用于回合中的摸牌阶段，会触发技能询问

        Args:
            count: 基本摸牌数量（默认2张），可以被技能修改

        Returns:
            摸到的牌列表
        """
        return self.phase_skill_manager.execute_phase(self, GameEvent.DRAW_CARD, count=count)

    def draw_card_phase_default(self, count: int = 2) -> List[Card]:
        """默认摸牌流程（原有实现）"""
        return self.draw_card(count)

    def draw_card_phase_with_skill(self, count: int = 2) -> List[Card]:
        """发动技能后的摸牌阶段（子类可覆盖），默认等同于默认摸牌流程"""
        return self.draw_card_phase_default(count)
    
    def play_card(self, available_targets: Dict[str, List[int]] = None) -> Tuple[Optional[Card], List[int]]:
        """出牌（使用阶段技能管理器）
        
        Args:
            available_targets: 可用目标字典，包含attackable、all、dis1等键
            
        Returns:
            (选择的牌, 目标列表)
        """
        return self.phase_skill_manager.execute_phase(self, GameEvent.PLAY_CARD, available_targets=available_targets)

    def play_card_with_skill(self, available_targets: Dict[str, List[int]] = None) -> Tuple[Optional[Card], List[int]]:
        """发动技能后的出牌阶段（子类可覆盖），默认等同于默认出牌流程"""
        return self.play_card_default(available_targets)

    def play_card_default(self, available_targets: Dict[str, List[int]] = None) -> Tuple[Optional[Card], List[int]]:
        """未发动技能时的默认出牌流程（原有实现）"""
        # 获取可选牌（传入available_targets以检查是否有合法目标）
        playable_cards = self._get_playable_cards(available_targets)
        if not playable_cards:
            return None, []
        
        # 让操控模块选择牌（传入available_targets以便检查是否有合法目标）
        selected_card = self.control.select_card(playable_cards, "", available_targets)
        if selected_card is None:
            return None, []
        
        # 根据牌的类型和可用目标确定可选目标
        targets = self._get_targets_for_card(selected_card, available_targets)
        
        # 确保目标列表中不包含自己（除了SELF类型的牌）
        if selected_card.target_type != TargetType.SELF:
            targets = [t for t in targets if t != self.player_id]
        
        # 如果是杀，需要在Control中重新过滤攻击范围内的目标（使用逆时针距离）
        # 因为player_controller的get_targets使用的是最小距离，而猪国杀应该只使用逆时针距离
        if selected_card.name_enum == CardName.SHA and selected_card.target_type == TargetType.ATTACKABLE:
            # 对于杀，让Control重新过滤攻击范围内的目标
            if hasattr(self.control, 'filter_attackable_targets'):
                targets = self.control.filter_attackable_targets(targets, available_targets)
        
        # 如果是自己类型的牌，直接使用自己
        if selected_card.target_type == TargetType.SELF:
            selected_targets = [self.player_id]
        elif selected_card.target_type == TargetType.ALL:
            # 对于ALL类型的牌，需要区分：
            # - 南蛮入侵、万箭齐发：使用所有目标
            # - 决斗：只选择一个目标
            if selected_card.name_enum == CardName.JUE_DOU:
                # 决斗只选择一个目标
                selected_targets = self.control.select_targets(targets, selected_card)
                # 确保只选择一个目标
                if selected_targets:
                    selected_targets = [selected_targets[0]]
                else:
                    selected_targets = []
            else:
                # 其他ALL类型牌（南蛮入侵、万箭齐发）使用所有目标
                selected_targets = targets
        else:
            # 让操控模块选择目标
            selected_targets = self.control.select_targets(targets, selected_card)
        
        # 从手牌中移除已出的牌
        if selected_card in self.hand_cards:
            self.hand_cards.remove(selected_card)
        
        # 记录出牌日志
        # 获取目标玩家名称
        target_names = []
        if hasattr(self, 'player_controller') and self.player_controller:
            for target_id in selected_targets:
                target_player = self.player_controller.get_player(target_id)
                if target_player:
                    target_names.append(target_player.name)
        else:
            # 如果没有player_controller引用，使用ID
            target_names = [f"玩家{target_id}" for target_id in selected_targets]
        
        game_logger.log_player_play_card(self.name, selected_card.name, selected_targets, target_names)
        
        # 发送出牌事件到前端
        # 对于多目标牌（TargetType.ALL），需要区分：
        # - 决斗：虽然目标类型是ALL，但实际只选择一个目标，应该发送给实际目标
        # - 南蛮入侵、万箭齐发：真正的多目标牌，发送给[-1]表示对所有目标生效
        if selected_card.target_type == TargetType.ALL:
            if selected_card.name_enum == CardName.JUE_DOU:
                # 决斗只选择一个目标，发送给实际目标
                send_play_card_event(selected_card, self.player_id, selected_targets)
            else:
                # 真正的多目标牌（南蛮入侵、万箭齐发）只发送一个事件给[-1]
                # 避免发送多个重复的事件
                if selected_targets:
                    send_play_card_event(selected_card, self.player_id, [-1])
                else:
                    send_play_card_event(selected_card, self.player_id, [self.player_id])
        else:
            # 单目标牌正常发送
            send_play_card_event(selected_card, self.player_id, selected_targets)
        
        # 如果出的是杀牌，标记当前回合已使用杀（除非装备了诸葛连弩）
        if selected_card.name_enum == CardName.SHA:
            # 如果装备了诸葛连弩，出杀次数不受限制
            if not (self.weapon and self.weapon.name_enum == CardName.ZHU_GE_LIAN_NU):
                self.sha_used_this_turn = True
        
        return selected_card, selected_targets
    
    def discard_card(self) -> List[Card]:
        """弃牌（使用阶段技能管理器）"""
        return self.phase_skill_manager.execute_phase(self, GameEvent.DISCARD_CARD)

    def discard_card_with_skill(self) -> List[Card]:
        """发动技能后的弃牌阶段（子类可覆盖），默认等同于默认弃牌流程"""
        return self.discard_card_default()
    
    def discard_card_default(self) -> List[Card]:
        """默认弃牌流程（原有实现）"""
        # 检查手牌数量是否超过上限
        if len(self.hand_cards) <= self.current_hp:
            return []
        
        # 让操控模块选择要弃的牌
        discard_count = len(self.hand_cards) - self.current_hp
        selected_cards = self.control.select_cards_to_discard(self.hand_cards, discard_count)
        
        # 确保selected_cards不为None
        if selected_cards is None:
            selected_cards = []
        
        # 从手牌中移除并放入弃牌堆
        discarded_cards = []
        for card in selected_cards:
            if card in self.hand_cards:
                self.hand_cards.remove(card)
                # 将牌放入弃牌堆
                self.deck.discard_card(card)
                # 发送弃牌事件
                send_discard_card_event(card, self.player_id)
                discarded_cards.append(card)
        
        # 记录弃牌日志
        if discarded_cards:
            card_names = [card.name for card in discarded_cards]
            game_logger.log_info(f"{self.name} 弃牌: {', '.join(card_names)}")
        
        return discarded_cards
    
    def take_damage(self, damage: int, source_player_id: Optional[int] = None, 
                    damage_type: str = None, original_card_name: str = None) -> None:
        """受伤（使用阶段技能管理器）"""
        self.phase_skill_manager.execute_phase(
            self, GameEvent.DAMAGE, 
            damage=damage, 
            source_player_id=source_player_id,
            damage_type=damage_type,
            original_card_name=original_card_name
        )

    def take_damage_default(self, damage: int, source_player_id: Optional[int] = None,
                           damage_type: str = None, original_card_name: str = None) -> None:
        """默认受伤流程（原有实现）"""
        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - damage)
        
        # 记录伤害来源
        if source_player_id is not None:
            self.last_damage_source = source_player_id
        
        # 记录受伤日志
        game_logger.log_player_damage(self.name, damage, self.current_hp, self.max_hp)
        
        # 发送血量变化事件到前端（传递伤害来源和伤害类型信息）
        if self.current_hp != old_hp:
            send_hp_change_event(
                self.player_id, self.current_hp,
                source_player_id=source_player_id,
                damage_type=damage_type,
                original_card_name=original_card_name
            )
        
        if self.current_hp == 0 and old_hp > 0:
            # 血量降到0时进入濒死状态，不直接死亡
            game_logger.log_player_dying(self.name)
            # 濒死处理由GameController负责

    def take_damage_with_skill(self, damage: int, source_player_id: Optional[int] = None,
                               damage_type: str = None, original_card_name: str = None) -> None:
        """发动技能后的受伤流程（子类可覆盖），默认等同于默认受伤流程"""
        self.take_damage_default(damage, source_player_id, damage_type, original_card_name)
    
    def die(self) -> None:
        """死亡（默认实现）"""
        self.status = PlayerStatus.DEAD
        self.current_hp = 0
        
        # 记录死亡日志
        identity_name = self.identity.value if self.identity else None
        game_logger.log_player_death(self.name, identity_name)
        
        # 发送死亡事件到前端
        send_death_event(self.player_id)
        
        # 处理死亡时的特殊逻辑
        self._handle_death_consequences()
        
        # 死亡时将所有手牌和装备牌进入弃牌堆
        if hasattr(self, 'deck') and self.deck:
            # 将所有手牌进入弃牌堆
            for card in self.hand_cards:
                self.deck.discard_card(card)
                # 发送弃牌事件
                send_discard_card_event(card, self.player_id)
            self.hand_cards.clear()
            
            # 将装备牌进入弃牌堆（使用装备管理器）
            self.equipment_manager.discard_all()
        else:
            # 如果没有牌堆引用，直接清空
            self.hand_cards.clear()
            self.equipment_manager.unequip_all()
    
    def _handle_death_consequences(self) -> None:
        """处理死亡时的特殊逻辑"""
        if not hasattr(self, 'player_controller') or not self.player_controller:
            return
        
        # 获取伤害来源
        killer_id = self.last_damage_source
        if killer_id is None:
            return
        
        killer = self.player_controller.get_player(killer_id)
        if killer is None or not killer.is_alive():
            return
        
        # 主公杀死忠臣的惩罚
        if (self.identity == PlayerIdentity.LOYALIST and 
            killer.identity == PlayerIdentity.LORD):
            self._handle_lord_kill_loyalist(killer)
        
        # 杀死反贼的奖励
        elif self.identity == PlayerIdentity.REBEL:
            self._handle_kill_rebel_reward(killer)
    
    def _handle_lord_kill_loyalist(self, killer) -> None:
        """处理主公杀死忠臣的惩罚"""
        game_logger.log_info(f"{killer.name} 杀死了忠臣 {self.name}，需要弃掉所有牌！")
        
        # 弃掉所有手牌
        if killer.hand_cards:
            for card in killer.hand_cards.copy():
                killer.hand_cards.remove(card)
                killer.deck.discard_card(card)
                # 发送弃牌事件
                send_discard_card_event(card, killer.player_id)
            game_logger.log_info(f"{killer.name} 弃掉了所有手牌")
        
        # 弃掉所有装备牌（使用装备管理器）
        unequipped = killer.equipment_manager.unequip_all()
        if unequipped:
            slot_names = {
                "weapon": "武器",
                "armor": "防具",
                "horse_plus": "防御马",
                "horse_minus": "进攻马",
            }
            for slot_name, card in unequipped:
                game_logger.log_info(f"{killer.name} 弃掉了{slot_names.get(slot_name, '装备')}")
    
    def _handle_kill_rebel_reward(self, killer) -> None:
        """处理杀死反贼的奖励"""
        # 先检查游戏是否结束，如果结束则不执行奖励
        if hasattr(self, 'player_controller') and self.player_controller:
            if self.player_controller.game_over():
                return
        
        game_logger.log_info(f"{killer.name} 杀死了反贼 {self.name}，摸三张牌！")
        
        # 摸三张牌
        drawn_cards = killer.draw_card(3)
        if drawn_cards:
            card_names = [card.name for card in drawn_cards]
            game_logger.log_info(f"{killer.name} 摸到了: {', '.join(card_names)}")
    
    def heal(self, heal_amount: int) -> None:
        """回复（默认实现）
        
        Args:
            heal_amount: 回复量
        """
        old_hp = self.current_hp
        
        # 记录是否脱离濒死状态
        leaving_dying = (old_hp <= 0 and old_hp + heal_amount > 0)
        
        self.current_hp = min(self.max_hp, self.current_hp + heal_amount)
        actual_heal = self.current_hp - old_hp
        
        # 记录治疗日志
        if actual_heal > 0:
            game_logger.log_player_heal(self.name, actual_heal, self.current_hp, self.max_hp)
            
            # 发送血量变化事件到前端
            send_hp_change_event(self.player_id, self.current_hp)
    
    def equip(self, card: Card) -> bool:
        """装备（使用装备管理器）
        
        Args:
            card: 要装备的牌
            
        Returns:
            是否装备成功
        """
        return self.equipment_manager.equip(card)
    
    def _get_playable_cards(self, available_targets: Dict[str, List[int]] = None) -> List[Card]:
        """获取可出的牌
        
        Args:
            available_targets: 可用目标字典，用于检查是否有合法目标
        """
        playable_cards = []
        
        for card in self.hand_cards:
            if self._can_play_card(card, available_targets):
                playable_cards.append(card)
        
        return playable_cards
    
    def _can_play_card(self, card: Card, available_targets: Dict[str, List[int]] = None) -> bool:
        """判断是否可以出指定牌
        
        Args:
            card: 要判断的牌
            available_targets: 可用目标字典，用于检查是否有合法目标
            
        Returns:
            是否可以出牌
        """
        # 杀牌判断
        if card.name_enum == CardName.SHA:
            # 如果装备了诸葛连弩，出杀次数不受限制
            if self.weapon and self.weapon.name_enum == CardName.ZHU_GE_LIAN_NU:
                # 仍需检查是否有合法目标
                targets = self._get_targets_for_card(card, available_targets)
                return len(targets) > 0
            # 否则杀必须当前回合没有出过且攻击范围内有人才能使用
            if self.sha_used_this_turn:
                return False
            # 检查是否有合法目标
            targets = self._get_targets_for_card(card, available_targets)
            return len(targets) > 0
        
        # 闪牌判断
        elif card.name_enum == CardName.SHAN:
            # 闪无论如何不能使用
            return False
        
        # 桃牌判断
        elif card.name_enum == CardName.TAO:
            # 桃只有在不是满血时可以使用
            return self.current_hp < self.max_hp
        
        # 装备牌判断
        elif card.card_type == CardType.EQUIPMENT:
            # 装备一定可以使用
            return True
        
        # 锦囊牌判断
        elif card.card_type == CardType.TRICK:
            # 无懈可击不能使用
            if card.name_enum == CardName.WU_XIE_KE_JI:
                return False
            # 其他锦囊牌需要检查是否有合法目标
            # 对于TargetType.SELF类型的锦囊牌，目标总是自己，不需要检查
            if card.target_type == TargetType.SELF:
                return True
            # 其他类型的锦囊牌需要检查目标
            targets = self._get_targets_for_card(card, available_targets)
            return len(targets) > 0
        
        # 其他牌默认可以使用（如果没有目标类型要求）
        # 但为了安全起见，如果available_targets不为None，也检查一下目标
        if available_targets is not None:
            # 对于TargetType.SELF类型的牌，目标总是自己，不需要检查
            if card.target_type == TargetType.SELF:
                return True
            # 对于需要目标的牌，检查是否有合法目标
            targets = self._get_targets_for_card(card, available_targets)
            # 如果牌的目标类型不是SELF，则需要有合法目标
            if card.target_type != TargetType.SELF:
                return len(targets) > 0
        
        return True
    
    def _get_targets_for_card(self, card: Card, available_targets: Dict[str, List[int]] = None) -> List[int]:
        """获取牌的目标列表
        
        Args:
            card: 要出的牌
            available_targets: 可用目标字典
            
        Returns:
            该牌可选的目标列表
        """
        if available_targets is None:
            return []
        
        # 根据牌的目标类型选择合适的目标列表
        if card.target_type == TargetType.ATTACKABLE:
            targets = available_targets.get("attackable", [])
        elif card.target_type == TargetType.ALL:
            targets = available_targets.get("all", [])
        elif card.target_type == TargetType.DIS1:
            targets = available_targets.get("dis1", [])
        elif card.target_type == TargetType.SELF:
            return [self.player_id]
        else:
            # 默认返回攻击距离内的目标
            targets = available_targets.get("attackable", [])
        
        # 确保目标列表中不包含自己（除了SELF类型的牌）
        if card.target_type != TargetType.ALL:
            targets = [t for t in targets if t != self.player_id]
        return targets
    
    def ask_use_card(self, card_name: CardName, context: str = "") -> Optional[Card]:
        """询问玩家是否使用指定牌（响应类查询，与正常出牌分开）
        
        Args:
            card_name: 牌名枚举
            context: 使用上下文描述（如"响应决斗"、"响应南蛮入侵"、"受到杀的攻击"等）
            
        Returns:
            选择的牌或None（不使用）
        """
        # 查找手牌中是否有指定牌名的牌（使用枚举匹配，保持从左往右的顺序）
        available_cards = [card for card in self.hand_cards if card.name_enum == card_name]
        
        if not available_cards:
            return None
        
        # 使用专门的响应类查询方法（与正常出牌分开）
        selected_card = self.control.ask_use_card_response(card_name, available_cards, context)
        
        if selected_card is not None:
            # 如果选择了使用牌，从手牌中移除
            if selected_card in self.hand_cards:
                self.hand_cards.remove(selected_card)
        
        return selected_card
    
    def ask_use_tao(self, context: str = "") -> Optional[Card]:
        """询问玩家是否使用桃
        
        Args:
            context: 使用上下文描述
            
        Returns:
            选择的桃或None（不使用）
        """
        return self.ask_use_card(CardName.TAO, context)
    
    def ask_use_shan(self, context: str = "") -> Optional[Card]:
        """询问玩家是否使用闪
        
        Args:
            context: 使用上下文描述
            
        Returns:
            选择的闪或None（不使用）
        """
        return self.ask_use_card(CardName.SHAN, context)
    
    def ask_use_sha(self, context: str = "") -> Optional[Card]:
        """询问玩家是否使用杀
        
        Args:
            context: 使用上下文描述
            
        Returns:
            选择的杀或None（不使用）
        """
        return self.ask_use_card(CardName.SHA, context)
    
    def ask_use_wu_xie_ke_ji(self, context: str = "") -> Optional[Card]:
        """询问玩家是否使用无懈可击
        
        Args:
            context: 使用上下文描述
            
        Returns:
            选择的无懈可击或None（不使用）
        """
        return self.ask_use_card(CardName.WU_XIE_KE_JI, context)
    
    def reset_turn_state(self) -> None:
        """重置回合状态"""
        self.sha_used_this_turn = False

    def ask_activate_skill(self, skill_name: str, context: dict) -> bool:
        """统一武将技能发动询问，直接委托Control，true为发动。"""
        if hasattr(self.control, 'ask_activate_skill') and callable(self.control.ask_activate_skill):
            try:
                return bool(self.control.ask_activate_skill(skill_name, context))
            except Exception:
                return False
        return False


class ZhangFeiPlayer(Player):
    """张飞武将：出的杀不限次数，技能咆哮"""
    
    def __init__(self, player_id: int, name: str, control_type: ControlType, deck: Deck, identity: PlayerIdentity = None, character_name: CharacterName = None, player_controller = None):
        super().__init__(player_id, name, control_type, deck, identity, character_name, player_controller)
        # 设置出牌阶段技能名
        self.skill_activate_time_with_skill[GameEvent.PLAY_CARD] = "咆哮"

    def play_card_with_skill(self, available_targets: Dict[str, List[int]] = None) -> Tuple[Optional[Card], List[int]]:
        """发动咆哮技能后的出牌阶段：直接执行技能效果"""
        selected_card, selected_targets = self.play_card_default(available_targets)
        # “杀”判定重置sha_used_this_turn，无限杀
        if selected_card is not None and selected_card.name_enum == CardName.SHA:
            self.sha_used_this_turn = False
        return selected_card, selected_targets

    def _can_play_card(self, card: Card, available_targets: Dict[str, List[int]] = None) -> bool:
        if card.name_enum == CardName.SHA:
            # 张飞的咆哮技能：杀不限次数，但仍需检查是否有合法目标
            targets = self._get_targets_for_card(card, available_targets)
            return len(targets) > 0
        return super()._can_play_card(card, available_targets)


class LvmengPlayer(Player):
    """吕蒙武将：弃牌阶段可选择发动技能"克己"，只有在本回合没有使用过杀的时候才可以不用弃牌"""
    
    def __init__(self, player_id: int, name: str, control_type: ControlType, deck: Deck, identity: PlayerIdentity = None, character_name: CharacterName = None, player_controller = None):
        super().__init__(player_id, name, control_type, deck, identity, character_name, player_controller)
        # 设置弃牌阶段技能名
        self.skill_activate_time_with_skill[GameEvent.DISCARD_CARD] = "克己"

    def discard_card_with_skill(self) -> List[Card]:
        """发动克己技能后的弃牌阶段：只有在本回合没有使用过杀的时候才可以不用弃牌"""
        # 检查本回合是否使用过杀
        if self.sha_used_this_turn:
            # 本回合使用过杀，技能无效，执行默认弃牌流程
            game_logger.log_info(f"{self.name} 技能[克己]失效：本回合已使用过杀，需要弃牌")
            return self.discard_card_default()
        else:
            # 本回合没有使用过杀，技能生效，不弃牌
            if len(self.hand_cards) > self.current_hp:
                game_logger.log_info(f"{self.name} 技能[克己]生效：本回合未使用杀，不弃任何手牌")
            else:
                game_logger.log_info(f"{self.name} 技能[克己]生效：本回合未使用杀，手牌未超限，无需弃牌")
            return []


class ZhuguoShaPlayer(Player):
    """猪国杀武将：专供猪国杀规则使用，没有弃牌阶段"""
    
    def __init__(self, player_id: int, name: str, control_type: ControlType, deck: Deck, identity: PlayerIdentity = None, character_name: CharacterName = None, player_controller = None):
        super().__init__(player_id, name, control_type, deck, identity, character_name, player_controller)
        # 设置弃牌阶段技能名（虽然不会执行弃牌，但设置技能名以便识别）
        self.skill_activate_time_with_skill[GameEvent.DISCARD_CARD] = "无弃牌阶段"
    
    def discard_card_with_skill(self) -> List[Card]:
        """猪国杀规则：没有弃牌阶段，直接返回空列表"""
        game_logger.log_info(f"{self.name} 猪国杀规则：跳过弃牌阶段")
        return []


class LingcaoPlayer(Player):
    """凌操武将：摸牌阶段摸牌数量 = 3 + 装备牌数量/2下取整"""
    
    def __init__(self, player_id: int, name: str, control_type: ControlType, deck: Deck, identity: PlayerIdentity = None, character_name: CharacterName = None, player_controller = None):
        super().__init__(player_id, name, control_type, deck, identity, character_name, player_controller)
        self.skill_activate_time_with_skill[GameEvent.DRAW_CARD] = "凌操"

    def draw_card_phase_with_skill(self, count: int = 2) -> List[Card]:
        """凌操的摸牌阶段技能实现：摸牌数量 = 3 + floor(装备数量/2)"""
        equipment_count = 0
        try:
            equipment_count = self.equipment_manager.get_equipment_count()
        except Exception:
            equipment_count = 0
        new_count = 3 + (equipment_count // 2)
        return self.draw_card_phase_default(new_count)


class ZhaoyunPlayer(Player):
    """赵云武将：三个技能（龙胆/龙魂可进化、冲阵、绝境）"""
    
    def __init__(self, player_id: int, name: str, control_type: ControlType, deck: Deck, identity: PlayerIdentity = None, character_name: CharacterName = None, player_controller = None):
        super().__init__(player_id, name, control_type, deck, identity, character_name, player_controller)
        # 赵云技能标记 - 渐进式解锁
        # 初始只有龙胆，冲阵和绝境需要通过 unlock_skill() 来开放
        self.skill_unlock_status = {
            "龙胆": True,      # 一开始就拥有龙胆技能
            "冲阵": False,     # 二技能，初始未解锁
            "绝境": False      # 三技能，初始未解锁
        }
        self.longhun_evolved = False  # 龙胆是否进化为龙魂（false时为龙胆，true时为龙魂）
        self.longdan_cards_used_this_turn = []  # 本回合通过龙胆/龙魂使用过的卡牌列表
        self.chongzhen_triggered_this_turn = False  # 本回合冲阵是否已触发过

    def get_base_max_hp(self) -> int:
        """赵云血量上限为4（与白板相同）"""
        return 4

    def unlock_skill(self, skill_name: str) -> bool:
        """解锁赵云的指定技能
        
        Args:
            skill_name: 技能名称（"龙胆", "冲阵", "绝境"）
            
        Returns:
            是否成功解锁（如果已解锁或技能名无效则返回False）
        """
        if skill_name not in self.skill_unlock_status:
            game_logger.log_warning(f"技能 {skill_name} 不存在于赵云的技能集合中")
            return False
        
        if self.skill_unlock_status[skill_name]:
            game_logger.log_warning(f"{self.name} 的技能 {skill_name} 已经被解锁")
            return False
        
        self.skill_unlock_status[skill_name] = True
        
        # 绝境是锁定技，不需要在技能激活时间映射中注册（不需要询问）
        
        game_logger.log_info(f"{self.name} 的技能 {skill_name} 已解锁！")
        return True

    def is_skill_unlocked(self, skill_name: str) -> bool:
        """检查指定技能是否已解锁
        
        Args:
            skill_name: 技能名称（"龙胆", "冲阵", "绝境"）
            
        Returns:
            技能是否已解锁
        """
        return self.skill_unlock_status.get(skill_name, False)

    def unlock_all_skills(self) -> None:
        """解锁赵云的所有技能（便捷方法）"""
        for skill_name in ["龙胆", "冲阵", "绝境"]:
            self.unlock_skill(skill_name)

    def set_longhun_evolved(self, evolved: bool) -> None:
        """设置龙胆是否进化为龙魂
        
        Args:
            evolved: True表示龙胆进化为龙魂，False表示使用龙胆
        """
        self.longhun_evolved = evolved
        if evolved:
            game_logger.log_info(f"{self.name} 的技能龙胆已进化为龙魂！")
        else:
            game_logger.log_info(f"{self.name} 正在使用技能龙胆")

    def _can_use_as_different_card(self, card: Card) -> bool:
        """检查是否可以将此卡牌转化为其它卡牌使用（龙胆/龙魂）
        
        仅在龙胆技能已解锁时才允许转化
        
        龙胆规则：可将杀当闪、闪当杀使用或打出
        龙魂规则：可将至多两张花色相同的牌按以下规则使用或打出：
          - 红桃当【桃】
          - 方片当火【杀】
          - 梅花当【闪】
          - 黑桃当【无懈可击】
        
        Args:
            card: 要检查的卡牌
            
        Returns:
            是否可以进行转化
        """
        # 龙胆技能未解锁，不能转化任何牌
        if not self.is_skill_unlocked("龙胆"):
            return False
        
        if card is None:
            return False

        if self.longhun_evolved:
            # 龙魂：支持所有牌的转化（仅受花色和数量2限制）
            return card.suit is not None and card.name_enum in [
                CardName.SHA, CardName.SHAN, CardName.TAO,
                CardName.WU_XIE_KE_JI, CardName.JUE_DOU,
                CardName.NAN_MAN_RU_QIN, CardName.WAN_JIAN_QI_FA
            ]
        else:
            # 龙胆：仅支持杀↔闪转化
            return card.name_enum in [CardName.SHA, CardName.SHAN]

    def _get_longhun_card_type(self, card: Card) -> Optional[CardName]:
        """根据龙魂规则，获取卡牌转化后的卡牌名
        
        Args:
            card: 要转化的卡牌
            
        Returns:
            转化后的卡牌名（CardName），如果不符合龙魂规则则返回None
        """
        if not self.longhun_evolved or card is None:
            return None

        suit = card.suit
        # 红桃 → 桃
        if suit == CardSuit.HEARTS:
            return CardName.TAO
        # 方片 → 杀（火杀视作普通杀）
        elif suit == CardSuit.DIAMONDS:
            return CardName.SHA
        # 梅花 → 闪
        elif suit == CardSuit.CLUBS:
            return CardName.SHAN
        # 黑桃 → 无懈可击
        elif suit == CardSuit.SPADES:
            return CardName.WU_XIE_KE_JI
        return None

    def _apply_longhun_effect(self, cards_used: List[Card]) -> None:
        """应用龙魂使用两张卡牌的额外效果
        
        若使用了两张红色牌（红桃/方片），此牌的回复值或伤害值+1
        若使用了两张黑色牌（梅花/黑桃），你弃置当前回合角色一张牌
        
        Args:
            cards_used: 使用的卡牌列表（应为最多两张）
        """
        if not self.longhun_evolved or len(cards_used) != 2:
            return

        card1, card2 = cards_used[0], cards_used[1]

        # 检查两张牌是否都是红色
        red_cards = [CardSuit.HEARTS, CardSuit.DIAMONDS]
        black_cards = [CardSuit.CLUBS, CardSuit.SPADES]

        if card1.suit in red_cards and card2.suit in red_cards:
            # 红色效果：此牌的回复值或伤害值+1（由使用的牌效果处理器处理）
            game_logger.log_info(f"{self.name} 通过龙魂使用了两张红色牌，伤害值或回复值+1")
            # 标记在卡牌使用时传递给处理器处理
        elif card1.suit in black_cards and card2.suit in black_cards:
            # 黑色效果：弃置当前回合角色（出牌者）一张牌
            game_logger.log_info(f"{self.name} 通过龙魂使用了两张黑色牌，需要弃置出牌角色一张牌")
            # 这应该由出牌者（当前回合角色）选择执行
            if self.player_controller:
                current_player = self.player_controller.get_player(self.player_id)
                if current_player and len(current_player.hand_cards) > 0:
                    # 出牌者（当前角色）需要弃一张牌
                    # 这里可以调用control的选择接口
                    pass

    def take_damage_default(self, damage: int, source_player_id: Optional[int] = None,
                               damage_type: str = None, original_card_name: str = None) -> None:
        old_hp = self.current_hp
        super().take_damage_default(damage, source_player_id, damage_type, original_card_name)
        
        # 绝境：进入濒死状态时摸一张牌
        entering_dying = (old_hp > 0 and self.current_hp <= 0)
        if self.is_skill_unlocked("绝境") and entering_dying:
             game_logger.log_info(f"{self.name} 进入濒死状态，触发绝境技能，摸一张牌")
             self.draw_card(1)

    def heal(self, heal_amount: int) -> None:
        old_hp = self.current_hp
        super().heal(heal_amount)
        
        # 绝境：脱离濒死状态时摸一张牌
        leaving_dying = (old_hp <= 0 and self.current_hp > 0)
        if self.is_skill_unlocked("绝境") and leaving_dying:
             game_logger.log_info(f"{self.name} 脱离濒死状态，触发绝境技能，摸一张牌")
             self.draw_card(1)

    def draw_card_phase_with_skill(self, count: int = 2) -> List[Card]:
        """发动绝境技能后的摸牌阶段
        
        绝境（锁定技）：你的手牌上限+2
        （由 Player.current_hp 实现手牌上限，弃牌阶段在此处无法直接改变，需在discard_card_default中修改逻辑）
        
        当你进入或脱离濒死状态时，你摸一张牌
        （这部分需要与 take_damage 流程集成）
        
        仅在绝境技能已解锁时才应用效果
        """
        if not self.is_skill_unlocked("绝境"):
            # 绝境未解锁，返回基础摸牌
            return self.draw_card_phase_default(count)
        
        # 绝境已解锁，应用技能效果
        drawn = self.draw_card_phase_default(count)
        game_logger.log_info(f"{self.name} 发动技能[绝境]：手牌上限+2，当进入/脱离濒死时摸一张牌")
        return drawn

    def _get_hand_card_limit(self) -> int:
        """获取手牌上限（绝境锁定技效果）
        
        只有当绝境技能已解锁时，才会应用+2的加成
        
        Returns:
            手牌上限
        """
        # 基础上限 = 当前血量
        base_limit = self.current_hp
        
        # 如果绝境已解锁，手牌上限+2
        if self.is_skill_unlocked("绝境"):
            return base_limit + 2
        else:
            return base_limit

    def discard_card_default(self) -> List[Card]:
        """弃牌阶段，考虑绝境的手牌上限+2"""
        # 检查手牌数量是否超过上限（上限 = 血量+2，绝境效果）
        hand_limit = self._get_hand_card_limit()
        if len(self.hand_cards) <= hand_limit:
            return []

        # 让操控模块选择要弃的牌
        discard_count = len(self.hand_cards) - hand_limit
        selected_cards = self.control.select_cards_to_discard(self.hand_cards, discard_count)

        # 确保selected_cards不为None
        if selected_cards is None:
            selected_cards = []

        # 从手牌中移除并放入弃牌堆
        discarded_cards = []
        for card in selected_cards:
            if card in self.hand_cards:
                self.hand_cards.remove(card)
                # 将牌放入弃牌堆
                self.deck.discard_card(card)
                # 发送弃牌事件
                send_discard_card_event(card, self.player_id)
                discarded_cards.append(card)

        # 记录弃牌日志
        if discarded_cards:
            card_names = [card.name for card in discarded_cards]
            game_logger.log_info(f"{self.name} 弃牌: {', '.join(card_names)}")

        return discarded_cards

    def take_damage_default(self, damage: int, source_player_id: Optional[int] = None,
                           damage_type: str = None, original_card_name: str = None) -> None:
        """受伤流程，考虑绝境的濒死时摸牌效果"""
        old_hp = self.current_hp
        
        # 记录是否进入濒死状态
        entering_dying = (old_hp > 0 and self.current_hp - damage <= 0)

        self.current_hp = max(0, self.current_hp - damage)

        # 记录伤害来源
        if source_player_id is not None:
            self.last_damage_source = source_player_id

        # 记录受伤日志
        game_logger.log_player_damage(self.name, damage, self.current_hp, self.max_hp)

        # 发送血量变化事件到前端
        if self.current_hp != old_hp:
            send_hp_change_event(
                self.player_id, self.current_hp,
                source_player_id=source_player_id,
                damage_type=damage_type,
                original_card_name=original_card_name
            )

        # 绝境效果：进入濒死状态时摸一张牌（仅在绝境已解锁时）
        if self.is_skill_unlocked("绝境") and entering_dying and self.current_hp == 0:
            game_logger.log_info(f"{self.name} 进入濒死状态，触发绝境技能，摸一张牌")
            self.draw_card(1)

    def reset_turn_state(self) -> None:
        """重置回合状态"""
        super().reset_turn_state()
        self.longdan_cards_used_this_turn = []
        self.chongzhen_triggered_this_turn = False

    def ask_use_card(self, card_name: CardName, context: str = "") -> Optional[Card]:
        """询问玩家是否使用指定牌（考虑龙胆转化）
        
        赵云的龙胆技能可以将杀当闪或闪当杀使用。
        
        Args:
            card_name: 牌名枚举
            context: 使用上下文描述
            
        Returns:
            选择的牌或None（不使用）
        """
        # 查找手牌中是否有指定牌名的牌
        available_cards = [card for card in self.hand_cards if card.name_enum == card_name]
        
        # 记录是否使用龙胆转化
        is_longdan_conversion = False
        original_card_name = None
        
        # 如果龙胆已解锁，还可以寻找可以转化的牌
        if self.is_skill_unlocked("龙胆"):
            if card_name == CardName.SHAN:
                # 如果要求闪，但没有闪，可以用杀代替（龙胆）
                if not available_cards:
                    available_cards = [card for card in self.hand_cards if card.name_enum == CardName.SHA]
                    is_longdan_conversion = True
                    original_card_name = CardName.SHA  # 原始牌是杀
            elif card_name == CardName.SHA:
                # 如果要求杀，但没有杀，可以用闪代替（龙胆）
                if not available_cards:
                    available_cards = [card for card in self.hand_cards if card.name_enum == CardName.SHAN]
                    is_longdan_conversion = True
                    original_card_name = CardName.SHAN  # 原始牌是闪
        
        if not available_cards:
            return None
        
        # 使用专门的响应类查询方法
        selected_card = self.control.ask_use_card_response(card_name, available_cards, context)
        
        if selected_card is not None:
            # 如果选择了使用牌，从手牌中移除
            if selected_card in self.hand_cards:
                self.hand_cards.remove(selected_card)
            
            # 如果是龙胆转化，标记converted_from字段以便冲阵技能触发
            if is_longdan_conversion:
                try:
                    selected_card.converted_from = original_card_name
                except Exception:
                    pass
        
        return selected_card

    def take_damage_with_skill(self, damage: int, source_player_id: Optional[int] = None,
                               damage_type: str = None, original_card_name: str = None) -> None:
        """赵云受伤流程（考虑绝境技能）"""
        # 调用默认受伤流程（包括绝境摸牌）
        self.take_damage_default(damage, source_player_id, damage_type, original_card_name)

    def play_card_default(self, available_targets: Dict[str, List[int]] = None) -> Tuple[Optional[Card], List[int]]:
        """出牌流程（考虑龙胆技能，闪当作杀使用）"""
        # 获取可选牌
        playable_cards = self._get_playable_cards(available_targets)
        if not playable_cards:
            return None, []
        
        # 让操控模块选择牌
        selected_card = self.control.select_card(playable_cards, "", available_targets)
        if selected_card is None:
            return None, []
        
        # 处理龙胆：闪当作杀时，使用杀的目标逻辑
        is_longdan_conversion = (selected_card.name_enum == CardName.SHAN and self.is_skill_unlocked("龙胆"))
        original_card_name = None
        if is_longdan_conversion:
            # 记录原始牌名（使用枚举CardName），随后把这张闪临时视作杀来处理（包括目标选择和效果处理）
            original_card_name = selected_card.name_enum
            # 标记该卡是通过龙胆转换而来，供后续效果（如冲阵）检测
            try:
                selected_card.converted_from = original_card_name
            except Exception:
                pass
            # 将selected_card临时修改为杀的属性，以便后续的效果处理使用ShaCardHandler
            sha_props = get_card_properties(CardName.SHA)
            try:
                selected_card.name_enum = CardName.SHA
                selected_card.name = sha_props.get("display_name", selected_card.name)
                selected_card.card_type = sha_props.get("card_type", selected_card.card_type)
                selected_card.target_type = sha_props.get("target_type", selected_card.target_type)
            except Exception:
                # 如果修改失败，不阻塞游戏流程，仍然按原逻辑处理目标
                pass
            # 闪当作杀，使用杀的目标逻辑
            targets = self._get_targets_for_card_with_longdan(selected_card, available_targets)
        else:
            # 其他情况使用基类逻辑
            targets = self._get_targets_for_card(selected_card, available_targets)
        
        # 确保目标列表中不包含自己
        if selected_card.target_type != TargetType.SELF:
            targets = [t for t in targets if t != self.player_id]
        
        # 对于龙胆转化的杀，进行目标过滤
        if is_longdan_conversion:
            if hasattr(self.control, 'filter_attackable_targets'):
                targets = self.control.filter_attackable_targets(targets, available_targets)
        elif selected_card.name_enum == CardName.SHA and selected_card.target_type == TargetType.ATTACKABLE:
            if hasattr(self.control, 'filter_attackable_targets'):
                targets = self.control.filter_attackable_targets(targets, available_targets)
        
        # 处理目标选择逻辑
        if selected_card.target_type == TargetType.SELF and not is_longdan_conversion:
            # 普通的SELF类型牌（非龙胆转换）直接指定自己
            selected_targets = [self.player_id]
        elif selected_card.target_type == TargetType.ALL:
            if selected_card.name_enum == CardName.JUE_DOU:
                selected_targets = self.control.select_targets(targets, selected_card)
                if selected_targets:
                    selected_targets = [selected_targets[0]]
                else:
                    selected_targets = []
            else:
                selected_targets = targets
        else:
            # 对于龙胆转化的闪，也需要选择目标
            selected_targets = self.control.select_targets(targets, selected_card)
        
        # 从手牌中移除已出的牌
        if selected_card in self.hand_cards:
            # 注意：如果进行了龙胆转换，selected_card.name_enum 已被修改为 SHA，
            # 这里移除的是手牌对象本身，后续效果处理会对该对象进行弃牌。
            self.hand_cards.remove(selected_card)
        
        # 记录出牌日志
        target_names = []
        if hasattr(self, 'player_controller') and self.player_controller:
            for target_id in selected_targets:
                target_player = self.player_controller.get_player(target_id)
                if target_player:
                    target_names.append(target_player.name)
        else:
            target_names = [f"玩家{target_id}" for target_id in selected_targets]
        
        game_logger.log_player_play_card(self.name, selected_card.name, selected_targets, target_names)
        
        # 发送出牌事件到前端（如果是龙胆转换，可带上 conversion_display 让前端展示特殊卡面）
        conversion_display = None
        if is_longdan_conversion:
            # 当闪被当作杀打出时，展示一张“闪转杀”专用卡面
            # 前端应使用 CardName.SHAN_TO_SHA 对应的图片（例如“闪转杀”）进行展示
            try:
                conversion_display = CardName.SHAN_TO_SHA
            except Exception:
                conversion_display = CardName.JUE_DOU

        if selected_card.target_type == TargetType.ALL:
            if selected_card.name_enum == CardName.JUE_DOU:
                send_play_card_event(selected_card, self.player_id, selected_targets, original_card_name=original_card_name, conversion_display=conversion_display)
            else:
                send_play_card_event(selected_card, self.player_id, [-1], original_card_name=original_card_name, conversion_display=conversion_display)
        else:
            send_play_card_event(selected_card, self.player_id, selected_targets, original_card_name=original_card_name, conversion_display=conversion_display)

        # 标记出杀（如果本次出的是杀）
        if selected_card.name_enum == CardName.SHA:
            # 如果装备了诸葛连弩，出杀次数不受限制
            if not (self.weapon and self.weapon.name_enum == CardName.ZHU_GE_LIAN_NU):
                self.sha_used_this_turn = True
        
        return selected_card, selected_targets

    def _can_play_card(self, card: Card, available_targets: Dict[str, List[int]] = None) -> bool:
        """判断是否可以出指定牌（考虑龙胆技能）
        
        赵云的龙胆技能使其可以在出牌阶段出闪（视作杀）。
        """
        # 如果龙胆已解锁，闪可以被当作杀在出牌阶段使用
        if card.name_enum == CardName.SHAN and self.is_skill_unlocked("龙胆"):
            # 闪当作杀使用，检查是否有合法目标
            # 同时遵循“出杀次数限制”：如果本回合已使用过杀且未装备诸葛连弩，则不能再使用（闪转杀计入杀的使用次数）
            # 如果装备了诸葛连弩，则不受次数限制
            if not (self.weapon and self.weapon.name_enum == CardName.ZHU_GE_LIAN_NU):
                if self.sha_used_this_turn:
                    return False
            targets = self._get_targets_for_card_with_longdan(card, available_targets)
            return len(targets) > 0
        
        # 其他情况使用基类逻辑
        return super()._can_play_card(card, available_targets)
    
    def _get_targets_for_card_with_longdan(self, card: Card, available_targets: Dict[str, List[int]] = None) -> List[int]:
        """获取龙胆转化后的目标（闪当作杀时）"""
        if card.name_enum != CardName.SHAN or not self.is_skill_unlocked("龙胆"):
            return self._get_targets_for_card(card, available_targets)
        
        # 闪当作杀使用，使用杀的目标逻辑（可攻击目标）
        if available_targets is None:
            return []
        return available_targets.get("attackable", [])

    def ask_use_shan(self, context: str = "") -> Optional[Card]:
        """询问玩家是否使用闪（考虑龙胆技能）
        
        赵云的龙胆技能使响应牌既可以是闪也可以是杀。
        
        Args:
            context: 使用上下文描述
            
        Returns:
            选择的闪或杀，或None（不使用）
        """
        if not self.is_skill_unlocked("龙胆"):
            # 没有龙胆，使用基类逻辑
            return super().ask_use_shan(context)
        
        # 龙胆已解锁，可以选择闪或杀
        available_cards = [card for card in self.hand_cards 
                          if card.name_enum in [CardName.SHAN, CardName.SHA]]
        
        if not available_cards:
            return None
        
        # 使用专门的响应类查询方法
        # 这里我们用SHAN作为主要请求类型，但可用卡牌包含闪和杀
        selected_card = self.control.ask_use_card_response(CardName.SHAN, available_cards, context)
        
        if selected_card is not None:
            # 如果选择了使用牌，从手牌中移除
            if selected_card in self.hand_cards:
                self.hand_cards.remove(selected_card)
            
            # 标记龙胆转化：如果用杀当闪，记录原始卡牌类型
            if selected_card.name_enum == CardName.SHA:
                selected_card.converted_from = CardName.SHA
                game_logger.log_info(f"{self.name} 发动[龙胆]：将【杀】当【闪】使用")
        
        return selected_card

    def ask_use_sha(self, context: str = "") -> Optional[Card]:
        """询问玩家是否使用杀（考虑龙胆技能）
        
        赵云的龙胆技能使响应牌既可以是杀也可以是闪（如决斗响应）。
        
        Args:
            context: 使用上下文描述
            
        Returns:
            选择的杀或闪，或None（不使用）
        """
        if not self.is_skill_unlocked("龙胆"):
            # 没有龙胆，使用基类逻辑
            return super().ask_use_sha(context)
        
        # 龙胆已解锁，可以选择杀或闪
        available_cards = [card for card in self.hand_cards 
                          if card.name_enum in [CardName.SHA, CardName.SHAN]]
        
        if not available_cards:
            return None
        
        # 使用专门的响应类查询方法
        # 这里我们用SHA作为主要请求类型，但可用卡牌包含杀和闪
        selected_card = self.control.ask_use_card_response(CardName.SHA, available_cards, context)
        
        if selected_card is not None:
            # 如果选择了使用牌，从手牌中移除
            if selected_card in self.hand_cards:
                self.hand_cards.remove(selected_card)
            
            # 标记龙胆转化：如果用闪当杀，记录原始卡牌类型
            if selected_card.name_enum == CardName.SHAN:
                selected_card.converted_from = CardName.SHAN
                game_logger.log_info(f"{self.name} 发动[龙胆]：将【闪】当【杀】使用")
        
        return selected_card


