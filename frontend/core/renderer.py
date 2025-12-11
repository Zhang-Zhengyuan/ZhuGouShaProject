import pygame
from config.simple_card_config import SimpleGameConfig, SimpleCardConfig
from config.enums import CardName
from frontend.util.color import default_colors
from frontend.ui.player_view import PlayerView
from config.enums import ControlType
from frontend.core.asset_manager import AssetManager
from frontend.ui.card_sprite import CardSprite
from frontend.config.card_config import CardConfig
class Renderer:
    def __init__(self, config: SimpleGameConfig, screen: pygame.Surface):
        self.config = config
        self.screen = screen
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg.fill(default_colors["greybrown"])
        self.asset_mgr = AssetManager()
        self.all_sprites = pygame.sprite.LayeredDirty()
        # Initialize card sprites in deck:
        self.deck_center_pos = self._get_deck_center_pos()
        self.screen_center = (self.screen.get_width() // 2, self.deck_center_pos[1])
        
        # 调试按钮区域
        self.debug_win_rect = pygame.Rect(10, 10, 80, 30)
        self.debug_lose_rect = pygame.Rect(100, 10, 80, 30)

        # Initialize player view:
        self.player_views = []
        total_players = len(config.players_config)
        # 以第一个被标记为 HUMAN 的玩家为主视角（如果没有 HUMAN，则默认第0位）
        primary_self_index = 0
        for idx, p_cfg in enumerate(config.players_config):
            if hasattr(p_cfg, 'control_type') and p_cfg.control_type == ControlType.HUMAN:
                primary_self_index = idx
                break

        # 计算屏幕相关坐标
        screen_width, screen_height = self.screen.get_size()
        # 主视角放在底部中心
        self_pos = (screen_width // 2 + 200, screen_height - 100)

        # 非主视角玩家均匀分布在顶部
        other_positions = []
        other_count = total_players - 1
        if other_count > 0:
            margin = -60
            avail_width = max(100, screen_width - 2 * margin)
            # 将other_count玩家分布在顶部区域
            for k in range(other_count):
                x = margin + int((k + 1) * avail_width / (other_count + 1))
                other_positions.append((x, 100))

        # 分配位置并创建 PlayerView
        other_idx = 0
        for i, p_cfg in enumerate(config.players_config):
            is_self = (i == primary_self_index)
            if is_self:
                char_pos = self_pos
                card_center = ((char_pos[0] - 140) // 2, char_pos[1] + 50)
            else:
                char_pos = other_positions[other_idx] if other_idx < len(other_positions) else (50 + other_idx * 120, 100)
                card_center = (None, None)
                other_idx += 1

            pv = PlayerView(config, p_cfg, i, is_self, asset_mgr=self.asset_mgr, character_pos=char_pos, card_center_pos=card_center)
            self.player_views.append(pv)
    
    def add_sprite(self, sprite: CardSprite):
        self.all_sprites.add(sprite)
    def remove_sprite(self, sprite: CardSprite):
        self.all_sprites.remove(sprite)

    def handle_resize(self, new_screen: pygame.Surface):
        """处理窗口大小改变事件"""
        self.screen = new_screen
        # 重新创建背景
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg.fill(default_colors["greybrown"])
        # 重新计算位置
        self.deck_center_pos = self._get_deck_center_pos()
        self.screen_center = (self.screen.get_width() // 2, self.deck_center_pos[1])
        # 通知所有玩家视图更新位置
        for player_view in self.player_views:
            player_view.handle_resize(self.screen)

    def _get_deck_center_pos(self):
        screen_width, screen_height = pygame.display.get_surface().get_size()
        return (screen_width - 100, screen_height // 2)
    def draw_deck(self, screen: pygame.Surface):
        deck_surf = self.asset_mgr.get_deck_surface()
        rect = deck_surf.get_rect(center=self.deck_center_pos)
        screen.blit(deck_surf, rect.topleft)

    def draw(self):
        self.screen.blit(self.bg, (0, 0))
        for pv in self.player_views:
            pv.draw(self.screen)
        
        # 绘制调试按钮
        pygame.draw.rect(self.screen, (0, 200, 0), self.debug_win_rect)
        pygame.draw.rect(self.screen, (200, 0, 0), self.debug_lose_rect)
        
        font = pygame.font.SysFont("SimHei", 20)
        win_text = font.render("一键胜利", True, (255, 255, 255))
        lose_text = font.render("一键失败", True, (255, 255, 255))
        
        self.screen.blit(win_text, (self.debug_win_rect.x + 5, self.debug_win_rect.y + 5))
        self.screen.blit(lose_text, (self.debug_lose_rect.x + 5, self.debug_lose_rect.y + 5))
        
        self.draw_deck(self.screen)
        self.all_sprites.draw(self.screen)
        pygame.display.flip()
        self.draw_deck(self.screen)
        # Update dirty sprites
        self.all_sprites.draw(self.screen)
        pygame.display.flip()