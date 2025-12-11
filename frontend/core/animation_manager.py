
import pygame
from frontend.ui.card_sprite import CardSprite
from frontend.core.renderer import Renderer
from frontend.config.card_config import CardConfig
from config.enums import EffectName
from frontend.ui.effect_sprite import EffectSprite
from frontend.core.game_state import game_state, GameStateEnum
DEFAULT_ANIM_SPEED = 30  # 每帧移动像素数
PLAY_CARD_ANIM_SPEED = 30
class Animation:
    def __init__(self, sprite: CardSprite, target_pos: tuple,  on_complete=None):
        self.sprite = sprite
        self.target_pos = target_pos
        self.is_complete = False
        # 结束后的回调函数类型应该是什么
        self.on_complete = on_complete if on_complete else lambda: None
class Effect:
    def __init__(self, sprite: EffectSprite | CardSprite, duration_frames: int, on_complete=None):
        self.sprite = sprite
        self.duration_frames = duration_frames
        self.on_complete = on_complete if on_complete else lambda: None

class AnimationManager:
    def __init__(self, renderer: Renderer):
        self.renderer = renderer
        self.active_animations = []
        self.show_effects = []

    def add_draw_card_animation(self, card_config: CardConfig, to_pos: tuple, face_up = True, on_complete=None):
        game_state.set_state(GameStateEnum.ANIMATING)
        start_pos = self.renderer.deck_center_pos
        end_pos = to_pos
        card_sprite = CardSprite(start_pos, card_config, face_up=face_up, speed=DEFAULT_ANIM_SPEED, asset_mgr=self.renderer.asset_mgr)
        card_sprite.rect.center = start_pos
        self.renderer.add_sprite(card_sprite)
        self.add_animation(card_sprite, end_pos, on_complete)

    def add_play_card_animation(self, card_config: CardConfig, from_pos: tuple, to_pos: tuple, on_complete=None):
        game_state.set_state(GameStateEnum.ANIMATING)
        start_pos = from_pos
        end_pos = to_pos
        card_sprite = CardSprite(start_pos, card_config, face_up=True, speed=PLAY_CARD_ANIM_SPEED, asset_mgr=self.renderer.asset_mgr)
        card_sprite.rect.center = start_pos
        self.renderer.add_sprite(card_sprite)
        self.add_animation(card_sprite, end_pos, on_complete)

    def add_discard_card_animation(self, card_config: CardConfig, from_pos: tuple, to_pos: tuple, on_complete=None):
        game_state.set_state(GameStateEnum.ANIMATING)
        start_pos = from_pos
        end_pos = to_pos
        card_sprite = CardSprite(start_pos, card_config, face_up=True, speed=DEFAULT_ANIM_SPEED, asset_mgr=self.renderer.asset_mgr)
        card_sprite.rect.center = start_pos
        self.renderer.add_sprite(card_sprite)
        self.add_animation(card_sprite, end_pos, on_complete)

    def add_steal_animation(self, card_config: CardConfig, from_pos: tuple, to_pos: tuple, on_complete=None):
        """
        播放夺牌动画：从被夺玩家位置（通常为角色位置）移动一张背面牌到接收者手牌位置。
        到达后回调用于把牌加入接收者视图并调整手牌计数。
        """
        game_state.set_state(GameStateEnum.ANIMATING)
        start_pos = from_pos
        end_pos = to_pos
        # 使用背面牌进行动画，除非接收者是本地手牌（那会在回调中展示正面）
        card_sprite = CardSprite(start_pos, card_config, face_up=False, speed=DEFAULT_ANIM_SPEED, asset_mgr=self.renderer.asset_mgr)
        card_sprite.rect.center = start_pos
        self.renderer.add_sprite(card_sprite)
        self.add_animation(card_sprite, end_pos, on_complete)

    def add_animation(self, sprite: CardSprite, target_pos, on_complete=None):
        sprite.start_move_to(target_pos)
        self.active_animations.append(Animation(sprite, target_pos, on_complete))

    def add_effect(self, effect_code: EffectName, pos: tuple, duration_frames=60, on_complete=None):
        game_state.set_state(GameStateEnum.ANIMATING)
        effect_sprite = EffectSprite(pos, effect_code, asset_mgr=self.renderer.asset_mgr)
        self.renderer.add_sprite(effect_sprite)
        self.show_effects.append(Effect(effect_sprite, duration_frames, on_complete))

    def add_show_card(self, card_config: CardConfig, pos: tuple, duration_frames=60, on_complete=None):
        game_state.set_state(GameStateEnum.ANIMATING)
        card_sprite = CardSprite(pos, card_config, face_up=True, speed=0, asset_mgr=self.renderer.asset_mgr)
        self.renderer.add_sprite(card_sprite)
        self.show_effects.append(Effect(card_sprite, duration_frames, on_complete))

    def update(self):
        for anim in self.active_animations[:]:
            sprite = anim.sprite
            if sprite.is_animating:
                tx, ty = sprite.anim_target
                cx, cy = sprite.rect.center
                dx, dy = tx - cx, ty - cy
                dist = (dx**2 + dy**2)**0.5
                if dist < sprite.anim_speed:
                    sprite.rect.center = sprite.anim_target
                    sprite.is_animating = False
                    self.active_animations.remove(anim)
                    self.renderer.remove_sprite(sprite)
                    anim.on_complete()
                else:
                    move_x = sprite.anim_speed * dx / dist
                    move_y = sprite.anim_speed * dy / dist
                    sprite.rect.center = (cx + move_x, cy + move_y)
                    sprite.dirty = 1  # Mark as dirty for redraw
        for effect in self.show_effects[:]:
            effect_sprite, frames_left = effect.sprite, effect.duration_frames
            frames_left -= 1
            if frames_left <= 0:
                self.renderer.remove_sprite(effect_sprite)
                self.show_effects.remove(effect)
                if effect.on_complete:
                    effect.on_complete()
            else:
                index = self.show_effects.index(effect)
                effect_sprite.dirty = 1  # Mark as dirty for redraw
                self.show_effects[index] = (Effect(effect_sprite, frames_left, effect.on_complete))