import os
import pygame
from config.enums import CardName, CharacterName, EffectName, PlayerIdentity

class AssetManager:
    def __init__(self, asset_root=None):
        self._cache = {}

        if asset_root is None:
            asset_root = os.path.join("frontend", "assets")
        asset_root = os.path.normpath(asset_root)

        self.card_base_path = os.path.join(asset_root, "cards")
        self.character_base_path = os.path.join(asset_root, "characters")
        self.effect_base_path = os.path.join(asset_root, "effects")

    def get_card_surface(self, code: CardName) -> pygame.Surface:
        key = ("card", code.value)
        if key in self._cache:
            return self._cache[key]

        filename = f"{code.value}.jpg"
        path = os.path.join(self.card_base_path, filename)

        surf = pygame.image.load(path).convert_alpha()
        self._cache[key] = surf
        return surf

    def get_card_back(self) -> pygame.Surface:
        key = ("card", "back")
        if key in self._cache:
            return self._cache[key]

        path = os.path.join(self.card_base_path, "back.jpg")
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            # 占位图
            surf = pygame.Surface((100, 150))
            surf.fill((180, 180, 180))
        self._cache[key] = surf
        return surf

    def get_deck_surface(self) -> pygame.Surface:
        """
        返回牌堆图像的 Surface 对象
        """
        key = ("card", "deck")
        if key in self._cache:
            return self._cache[key]

        path = os.path.join(self.card_base_path, "deck.jpg")
        surf = pygame.image.load(path).convert_alpha()
        self._cache[key] = surf
        return surf

    def get_character_surface(self, code: CharacterName) -> pygame.Surface:
        key = ("character", code.value)
        if key in self._cache:
            return self._cache[key]

        filename = f"{code.value}.jpg"
        path = os.path.join(self.character_base_path, filename)

        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            # 占位图
            surf = pygame.Surface((100, 150))
            surf.fill((180, 180, 180))

        self._cache[key] = surf
        return surf

    def get_effect_surface(self, code: EffectName) -> pygame.Surface:
        key = ("effect", code.value)
        if key in self._cache:
            return self._cache[key]

        filename = f"{code.value}.png"
        path = os.path.join(self.effect_base_path, filename)

        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            # 占位图
            surf = pygame.Surface((100, 100))
            surf.fill((255, 0, 0))

        self._cache[key] = surf
        return surf

    def get_select_icon(self) -> pygame.Surface:
        """获取选择指示图标"""
        key = ("ui", "select")
        if key in self._cache:
            return self._cache[key]
        
        path = os.path.join(self.effect_base_path, "select.png")
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            # 占位图：绿色圆圈
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 255, 0, 180), (30, 30), 25, 4)
            
        self._cache[key] = surf
        return surf
    
    def get_death_effect_surface(self, identity: PlayerIdentity) -> pygame.Surface:
        """
        根据玩家身份获取死亡特效图像
        """
        if identity == PlayerIdentity.LORD:
            id_str = "zhugong"
        elif identity == PlayerIdentity.LOYALIST:
            id_str = "zhongchen"
        elif identity == PlayerIdentity.REBEL:
            id_str = "fanzei"
        elif identity == PlayerIdentity.TRAITOR:
            id_str = "neijian"
        key = ("effect", f"death_{id_str}")
        if key in self._cache:
            return self._cache[key]

        filename = f"dead_{id_str}.png"
        path = os.path.join(self.effect_base_path, filename)

        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            # 占位图
            surf = pygame.Surface((100, 100))
            surf.fill((0, 0, 0))

        self._cache[key] = surf
        return surf
