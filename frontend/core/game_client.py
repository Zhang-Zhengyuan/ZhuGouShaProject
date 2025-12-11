import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
import pygame
import threading
import queue
from typing import Optional, Dict, Any
from frontend.util.size import DEFAULT_WINDOW_SIZE
from frontend.util.color import default_colors
from config.enums import EffectName, CardName, EquipmentType, EquipmentName

from frontend.core.renderer import Renderer
from frontend.core.animation_manager import AnimationManager

from config.simple_card_config import SimpleGameConfig
from frontend.config.card_config import CardConfig

from frontend.core.game_state import game_state, GameStateEnum
from communicator.communicator import communicator, AckEvent

from communicator.comm_event import DebugEvent, AskPlayCardEvent, PlayCardResponseEvent, AskTargetEvent, TargetResponseEvent

class GameClient:
    def __init__(self, config: SimpleGameConfig, screen: Optional[pygame.Surface]=None, clock: Optional[pygame.time.Clock]=None):
        self.config = config
        self.screen = screen
        self.clock = clock if clock is not None else pygame.time.Clock()

        self.renderer = Renderer(config, self.screen)
        self.animation_mgr = AnimationManager(self.renderer)
        self.winner_info = None  # 存储胜利信息
        self.selecting_cards = [] # 当前可选的牌列表
        self.selecting_targets = [] # 当前可选的目标列表

    def after_draw_card(self, card_config: CardConfig, to_player: int, event_id: int):
        # 返回draw_card_event的on_complete调用，处理牌局状态更新等
        player = self.renderer.player_views[to_player]
        player.add_card(card_config)
        player.card_cnt += 1
        communicator.send_to_backend(AckEvent(original_event_id=event_id, success=True, message="Draw card processed"))
        game_state.set_state(GameStateEnum.WAITING)
    def draw_card_event(self, card_config: CardConfig, to_player: int, event_id: int):
        # 处理摸牌事件，添加动画等
        player = self.renderer.player_views[to_player]
        if player.is_self:
            to_pos = player.card_center_pos
        else:
            to_pos = player.character_pos
        face_up = player.is_self
        if to_pos != (None, None):
            self.animation_mgr.add_draw_card_animation(card_config, to_pos, face_up, on_complete=lambda: self.after_draw_card(card_config, to_player, event_id))

    def set_waiting_and_ack(self, event_id: int):
        communicator.send_to_backend(AckEvent(original_event_id=event_id, success=True, message="Event processed"))
        game_state.set_state(GameStateEnum.WAITING)
    def after_play_card(self, display_card_config: CardConfig, effective_card_config: CardConfig, from_player: int, to_player: int, event_id: int):
        # 返回play_card_event的on_complete调用，处理牌局状态更新等
        from_pv = self.renderer.player_views[from_player]
        center_pos = self.renderer.screen_center
        # 如果 to_player == -1，作为中心展示（如万箭、决斗显示）
        if to_player == -1:
            # 中心展示使用展示卡
            self.animation_mgr.add_show_card(display_card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
            return

        to_pv = self.renderer.player_views[to_player]

        # 根据生效卡决定特效（例如被视为杀则显示伤害特效），但展示卡仍使用 display_card_config
        effective_name = effective_card_config.name

        if effective_name == CardName.SHA:
            effect_pos = to_pv.character_pos
            # 先播放伤害特效，再展示卡片到中心
            self.animation_mgr.add_effect(EffectName.HURT, effect_pos, duration_frames=60, on_complete=lambda: game_state.set_state(GameStateEnum.WAITING))
            self.animation_mgr.add_show_card(display_card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
        elif effective_name == CardName.SHAN:
            self.animation_mgr.add_show_card(display_card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
        elif effective_name == CardName.TAO:
            effect_pos = to_pv.character_pos
            self.animation_mgr.add_show_card(display_card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
        elif effective_name == CardName.JUE_DOU:
            effect_pos = to_pv.character_pos
            self.animation_mgr.add_effect(EffectName.BOOM, effect_pos, duration_frames=60, on_complete=lambda: game_state.set_state(GameStateEnum.WAITING))
            self.animation_mgr.add_show_card(display_card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
        else:
            # 默认展示
            self.animation_mgr.add_show_card(display_card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
    def play_card_event(self, display_card: CardConfig, removal_card: CardConfig, effective_card: Optional[CardConfig], from_player: int, to_player: int, event_id: int):
        # 处理出牌事件，添加动画等
        from_pv = self.renderer.player_views[from_player]
        from_pv.card_cnt -= 1
        # 目的地位置（统一使用屏幕中心作为动画目标，后续在 after_play_card 中会根据 to_player 决定效果位置）
        to_pos = self.renderer.screen_center

        # 从手牌中移除时使用 removal_card（匹配原始牌名+花色+点数）
        if from_pv.is_self:
            from_pos = from_pv.card_center_pos
            from_pv.remove_card(removal_card)
        else:
            from_pos = from_pv.character_pos

        # 使用 display_card 做动画（展示用）
        if to_pos != (None, None):
            # effective_card 已由调用方传入（来自后端的 card_config 转为 CardConfig）
            if effective_card is None:
                # 保守回退：如果调用方未传入，则把 display_card 作为生效卡
                effective_card_cfg = display_card
            else:
                effective_card_cfg = effective_card

            after_lambda = lambda: self.after_play_card(display_card, effective_card_cfg, from_player, to_player, event_id=event_id)
            self.animation_mgr.add_play_card_animation(display_card, from_pos, to_pos, on_complete=after_lambda)
    def change_hp_event(self, player_id: int, new_hp: int, event_id: int):
        # 处理血量变化事件，更新显示等
        player = self.renderer.player_views[player_id]
        old_hp = player.get_hp()
        player.update_hp(new_hp)
        if new_hp < old_hp:
            effect_pos = player.character_pos
            self.animation_mgr.add_effect(EffectName.DAMAGE, effect_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
        elif new_hp > old_hp:
            effect_pos = player.character_pos
            self.animation_mgr.add_effect(EffectName.HEAL, effect_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))
        else:
            self.set_waiting_and_ack(event_id=event_id)

    def after_discard_card(self, card_config: CardConfig, event_id: int):
        # 处理弃牌后的逻辑
        center_pos = self.renderer.deck_center_pos
        self.animation_mgr.add_show_card(card_config, center_pos, duration_frames=60, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))

    def discard_card_event(self, card: CardConfig, player_id: int, event_id: int):
        # 处理弃牌事件，添加动画等
        player = self.renderer.player_views[player_id]
        if not (card.name.value in EquipmentName._value2member_map_):
            player.card_cnt -= 1
        if player.is_self:
            player.remove_card(card)
        # 添加弃牌动画
        from_pos = player.character_pos if not player.is_self else player.card_center_pos
        to_pos = self.renderer.deck_center_pos
        if to_pos != (None, None):
            self.animation_mgr.add_discard_card_animation(card, from_pos, to_pos, on_complete=lambda: self.after_discard_card(card, event_id=event_id))

    def equip_change_event(self, player_id: int, equip_name: CardName, equip_type: EquipmentType, event_id: int):
        # 处理装备变化事件，更新装备栏等
        player = self.renderer.player_views[player_id]
        player.equipment[equip_type] = equip_name
        game_state.set_state(GameStateEnum.WAITING)
        communicator.send_to_backend(AckEvent(original_event_id=event_id, success=True, message="Equip change processed"))

    def death_event(self, player_id: int, event_id: int):
        # 处理角色死亡事件，播放动画等
        player = self.renderer.player_views[player_id]
        player.dead = True
        game_state.set_state(GameStateEnum.WAITING)
        communicator.send_to_backend(AckEvent(original_event_id=event_id, success=True, message="Death event processed"))
        # effect_pos = player.character_pos
        # self.animation_mgr.add_effect(EffectName.DEATH, effect_pos, duration_frames=90, on_complete=lambda: self.set_waiting_and_ack(event_id=event_id))

    def run(self):
        running = True
        game_state.set_state(GameStateEnum.WAITING)
        while running:
            if game_state.state == GameStateEnum.WAITING:
                event = communicator.receive_from_backend()
                if event is not None:
                    event_id = getattr(event, '_event_id', None)
                    # 处理不同类型的事件
                    if type(event).__name__ == "DrawCardEvent":
                        simple_card_cfg = event.card_config
                        card_cfg = CardConfig(card_name=simple_card_cfg.name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)
                        self.draw_card_event(card_cfg, event.to_player, event_id=event_id)

                    elif type(event).__name__ == "PlayCardEvent":
                        simple_card_cfg = event.card_config
                        # 展示用卡片：如果后端提供了 conversion_display，优先使用它作为展示用卡牌
                        conv_disp = getattr(event, 'conversion_display', None)
                        if conv_disp:
                            try:
                                # conv_disp 可能是 CardName 枚举或字符串
                                if isinstance(conv_disp, str):
                                    from config.enums import CardName as _CardNameEnum
                                    disp_name = _CardNameEnum[conv_disp]
                                else:
                                    disp_name = conv_disp
                                display_card_cfg = CardConfig(card_name=disp_name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)
                            except Exception:
                                display_card_cfg = CardConfig(card_name=simple_card_cfg.name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)
                        else:
                            display_card_cfg = CardConfig(card_name=simple_card_cfg.name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)

                        # 移除用卡片：优先使用后端传来的 original_card_name（原始牌名），否则使用 card_config.name
                        removal_name = getattr(event, 'original_card_name', None) or simple_card_cfg.name
                        try:
                            from config.enums import CardName as _CardNameEnum
                            if isinstance(removal_name, str):
                                removal_card_name = _CardNameEnum[removal_name]
                            else:
                                removal_card_name = removal_name
                        except Exception:
                            removal_card_name = simple_card_cfg.name

                        removal_card_cfg = CardConfig(card_name=removal_card_name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)

                        # 构建生效卡（来自后端的 card_config）并传入 play_card_event
                        effective_card_cfg = CardConfig(card_name=simple_card_cfg.name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)
                        # 传入展示卡、移除卡和生效卡，前端用展示卡做动画，用移除卡从手牌中匹配并删除，生效卡决定特效
                        self.play_card_event(display_card_cfg, removal_card_cfg, effective_card_cfg, event.from_player, event.to_player, event_id=event_id)

                    elif type(event).__name__ == "HPChangeEvent":
                        self.change_hp_event(event.player_id, event.new_hp, event_id=event_id)

                    elif type(event).__name__ == "DiscardCardEvent":
                        simple_card_cfg = event.card_config
                        card_cfg = CardConfig(card_name=simple_card_cfg.name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)
                        self.discard_card_event(card_cfg, event.player, event_id=event_id)

                    elif type(event).__name__ == "StealCardEvent":
                        # 处理夺牌事件：播放一张背面牌从被夺者移动到接收者，完成后更新视图手牌
                        simple_card_cfg = event.card_config
                        card_cfg = CardConfig(card_name=simple_card_cfg.name, suit=simple_card_cfg.suit, rank=simple_card_cfg.rank)
                        from_pv = self.renderer.player_views[event.from_player]
                        to_pv = self.renderer.player_views[event.to_player]

                        # 调整被夺者手牌计数与视图（若被夺者是本地，则移除具体卡牌）
                        if not (card_cfg.name.value in []):
                            pass
                        # 被夺者手牌数先减1（界面计数）
                        if hasattr(from_pv, 'card_cnt'):
                            from_pv.card_cnt = max(0, from_pv.card_cnt - 1)
                        if from_pv.is_self:
                            # 如果被夺者是本地，移除与 card_cfg 匹配的一张手牌（若存在）
                            try:
                                from_pv.remove_card(card_cfg)
                            except Exception:
                                pass

                        # 目标接收位置：若接收者是本地，使用手牌中心；否则使用角色位置
                        if to_pv.is_self:
                            target_pos = to_pv.card_center_pos
                        else:
                            target_pos = to_pv.character_pos

                        # 动画完成后的回调：把牌加入接收者视图或更新计数，然后 ACK 后端
                        def _on_steal_complete():
                            try:
                                if to_pv.is_self:
                                    to_pv.add_card(card_cfg)
                                    to_pv.card_cnt += 1
                                else:
                                    # 非本地玩家，仅增加计数
                                    to_pv.card_cnt += 1
                            finally:
                                self.set_waiting_and_ack(event_id=event_id)

                        # 播放夺牌动画（使用背面到目标）
                        from_pos = from_pv.character_pos if not from_pv.is_self else from_pv.card_center_pos
                        to_pos = target_pos
                        if to_pos != (None, None):
                            self.animation_mgr.add_steal_animation(card_cfg, from_pos, to_pos, on_complete=_on_steal_complete)
                        else:
                            # 若无目标位置，直接完成回调
                            _on_steal_complete()

                    elif type(event).__name__ == "EquipChangeEvent":
                        self.equip_change_event(event.player_id, event.equip_name, event.equip_type, event_id=event_id)

                    elif type(event).__name__ == "DeathEvent":
                        self.death_event(event.player_id, event_id=event_id)

                    elif type(event).__name__ == "GameOverEvent":
                        self.winner_info = event.winner_info
                        game_state.set_state(GameStateEnum.ENDED)
                        # 不需要ACK，直接结束

                    elif type(event).__name__ == "AskPlayCardEvent":
                        self.selecting_cards = event.available_cards
                        game_state.set_state(GameStateEnum.SELECTING)
                        print(f"[前端] 收到选牌请求，可选: {len(self.selecting_cards)} 张 (右键跳过)")

                    elif type(event).__name__ == "AskTargetEvent":
                        self.selecting_targets = event.available_targets
                        game_state.set_state(GameStateEnum.SELECTING_TARGET)
                        print(f"[前端] 收到选目标请求，可选: {self.selecting_targets} (右键取消)")
                        # 标记可选目标
                        for pv in self.renderer.player_views:
                            if pv.id in self.selecting_targets:
                                pv.is_target_selectable = True
                            else:
                                pv.is_target_selectable = False

                    else:
                        pass
                else:
                    pass

            elif game_state.state == GameStateEnum.ANIMATING:
                pass
            elif game_state.state == GameStateEnum.SELECTING:
                pass
            elif game_state.state == GameStateEnum.PAUSED:
                pass
            elif game_state.state == GameStateEnum.ENDED:
                running = False
            else:
                pass

            # 处理本地 Pygame 事件
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.VIDEORESIZE:
                    # 更新窗口大小并通知渲染器
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                    self.renderer.handle_resize(self.screen)
                
                elif ev.type == pygame.MOUSEMOTION:
                    # 处理鼠标悬停
                    for pv in self.renderer.player_views:
                        if pv.is_self:
                            pv.handle_mouse_motion(ev.pos)

                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:  # 左键
                        mouse_pos = ev.pos
                        
                        # 优先处理选牌逻辑
                        if game_state.state == GameStateEnum.SELECTING:
                            clicked_card_view = None
                            for pv in self.renderer.player_views:
                                if pv.is_self:
                                    clicked_card_view = pv.handle_mouse_click(mouse_pos)
                                    break
                            
                            if clicked_card_view:
                                # 找到对应的索引
                                selected_idx = -1
                                for i, simple_cfg in enumerate(self.selecting_cards):
                                    # 比较 card_view.config 和 simple_cfg
                                    if (clicked_card_view.config.name == simple_cfg.name and 
                                        clicked_card_view.config.suit == simple_cfg.suit and 
                                        clicked_card_view.config.rank == simple_cfg.rank):
                                        selected_idx = i
                                        break
                                
                                if selected_idx != -1:
                                    print(f"[前端] 选择了第 {selected_idx} 张牌: {clicked_card_view.config.name}")
                                    communicator.send_to_backend(PlayCardResponseEvent(card_index=selected_idx))
                                    game_state.set_state(GameStateEnum.WAITING)
                                    self.selecting_cards = []
                                else:
                                    print("[前端] 这张牌当前不可用")
                        
                        # 处理选目标逻辑
                        elif game_state.state == GameStateEnum.SELECTING_TARGET:
                            clicked_target_id = None
                            for pv in self.renderer.player_views:
                                if pv.is_target_selectable and pv.check_character_click(mouse_pos):
                                    clicked_target_id = pv.id
                                    break
                            
                            if clicked_target_id is not None:
                                print(f"[前端] 选择了目标: {clicked_target_id}")
                                communicator.send_to_backend(TargetResponseEvent(target_ids=[clicked_target_id]))
                                game_state.set_state(GameStateEnum.WAITING)
                                # 清除标记
                                for pv in self.renderer.player_views:
                                    pv.is_target_selectable = False
                                self.selecting_targets = []

                        if hasattr(self.renderer, 'debug_win_rect') and self.renderer.debug_win_rect.collidepoint(mouse_pos):
                            print("[Debug] 点击一键胜利")
                            communicator.send_to_backend(DebugEvent(command="win"))
                        elif hasattr(self.renderer, 'debug_lose_rect') and self.renderer.debug_lose_rect.collidepoint(mouse_pos):
                            print("[Debug] 点击一键失败")
                            communicator.send_to_backend(DebugEvent(command="lose"))

                    elif ev.button == 3: # 右键
                        if game_state.state == GameStateEnum.SELECTING:
                            print("[前端] 跳过出牌")
                            communicator.send_to_backend(PlayCardResponseEvent(card_index=-1))
                            game_state.set_state(GameStateEnum.WAITING)
                            self.selecting_cards = []
                        elif game_state.state == GameStateEnum.SELECTING_TARGET:
                            print("[前端] 取消选择目标")
                            communicator.send_to_backend(TargetResponseEvent(target_ids=None))
                            game_state.set_state(GameStateEnum.WAITING)
                            # 清除标记
                            for pv in self.renderer.player_views:
                                pv.is_target_selectable = False
                            self.selecting_targets = []
                        
                        # 处理卡牌点击
                        clicked_card = None
                        for pv in self.renderer.player_views:
                            if pv.is_self:
                                clicked_card = pv.handle_mouse_click(mouse_pos)
                                break
                        
                        if clicked_card and game_state.state == GameStateEnum.SELECTING:
                            # 在可选列表中查找点击的牌
                            found_idx = -1
                            for i, sc in enumerate(self.selecting_cards):
                                # 比较 CardConfig 和 SimpleCardConfig
                                if (clicked_card.config.name == sc.name and 
                                    clicked_card.config.suit == sc.suit and 
                                    clicked_card.config.rank == sc.rank):
                                    found_idx = i
                                    break
                            
                            if found_idx != -1:
                                print(f"[前端] 选择了第 {found_idx} 张牌")
                                communicator.send_to_backend(PlayCardResponseEvent(card_index=found_idx))
                                game_state.set_state(GameStateEnum.WAITING)
                                self.selecting_cards = []
                            else:
                                print("[前端] 点击的牌不在可选列表中")

                    elif ev.button == 3: # 右键
                        if game_state.state == GameStateEnum.SELECTING:
                             print("[前端] 跳过出牌")
                             communicator.send_to_backend(PlayCardResponseEvent(card_index=-1))
                             game_state.set_state(GameStateEnum.WAITING)
                             self.selecting_cards = []

            self.animation_mgr.update()
            self.renderer.draw()
            self.clock.tick(30)

        # 退出清理
        try:
            self._stop_event.set()
        except Exception:
            pass
        # pygame.quit()  # 由外部管理pygame生命周期，避免关闭display导致后续界面无法显示
        return self.winner_info
