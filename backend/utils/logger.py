# 日志系统模块
import logging
import os
from datetime import datetime
from typing import Optional
import threading


class GameLogger:
    """游戏日志系统
    
    负责管理游戏日志的创建、记录和保存
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.logger = None
        self.log_file_path = None
        self.is_test_mode = False
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        self.logger = logging.getLogger('game_logger')
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
    
    def start_game_session(self, is_test: bool = False) -> str:
        """开始新的游戏会话
        
        Args:
            is_test: 是否为测试模式
            
        Returns:
            日志文件路径
        """
        self.is_test_mode = is_test
        
        # 创建日志目录
        if is_test:
            log_dir = os.path.join(os.getcwd(), 'logs', 'test')
        else:
            log_dir = os.path.join(os.getcwd(), 'logs', 'game')
        
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if is_test:
            filename = f"test_session_{timestamp}.log"
        else:
            filename = f"game_session_{timestamp}.log"
        
        self.log_file_path = os.path.join(log_dir, filename)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器到日志器
        self.logger.addHandler(file_handler)
        
        # 记录游戏开始
        self.log_game_start()
        
        return self.log_file_path
    
    def end_game_session(self):
        """结束游戏会话"""
        if self.logger and self.log_file_path:
            self.logger.info("=" * 50)
            self.logger.info("游戏会话结束")
            self.logger.info("=" * 50)
            
            # 移除文件处理器
            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    self.logger.removeHandler(handler)
                    handler.close()
            
            self.log_file_path = None
    
    def log_game_start(self):
        """记录游戏开始"""
        if self.logger:
            self.logger.info("=" * 50)
            self.logger.info("游戏开始")
            self.logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"模式: {'测试模式' if self.is_test_mode else '正常模式'}")
            self.logger.info("=" * 50)
    
    def log_info(self, message: str):
        """记录信息日志"""
        if self.logger:
            self.logger.info(message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        if self.logger:
            self.logger.warning(message)
    
    def log_error(self, message: str):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message)
    
    def log_debug(self, message: str):
        """记录调试日志"""
        if self.logger:
            self.logger.debug(message)
    
    def log_player_draw_cards(self, player_name: str, cards: list):
        """记录玩家摸牌"""
        if self.logger and cards:
            card_names = [card.name for card in cards]
            self.logger.info(f"{player_name} 摸牌: {', '.join(card_names)}")
    
    def log_player_play_card(self, player_name: str, card_name: str, targets: list = None, target_names: list = None):
        """记录玩家出牌"""
        if self.logger:
            if targets and target_names:
                self.logger.info(f"{player_name} 使用 {card_name}，目标: {', '.join(target_names)}")
            elif targets:
                target_id_names = [f"玩家{target}" for target in targets]
                self.logger.info(f"{player_name} 使用 {card_name}，目标: {', '.join(target_id_names)}")
            else:
                self.logger.info(f"{player_name} 使用 {card_name}")
    
    def log_player_use_card(self, player_name: str, card_name: str, targets: list = None, target_names: list = None):
        """记录玩家使用牌（响应）"""
        if self.logger:
            if targets and target_names:
                self.logger.info(f"{player_name} 使用 {card_name} 响应，目标: {', '.join(target_names)}")
            elif targets:
                target_id_names = [f"玩家{target}" for target in targets]
                self.logger.info(f"{player_name} 使用 {card_name} 响应，目标: {', '.join(target_id_names)}")
            else:
                self.logger.info(f"{player_name} 使用 {card_name} 响应")
    
    def log_player_damage(self, player_name: str, damage: int, current_hp: int, max_hp: int):
        """记录玩家受伤"""
        if self.logger:
            self.logger.info(f"{player_name} 受到 {damage} 点伤害，当前血量: {current_hp}/{max_hp}")
    
    def log_player_heal(self, player_name: str, heal: int, current_hp: int, max_hp: int):
        """记录玩家治疗"""
        if self.logger:
            self.logger.info(f"{player_name} 恢复 {heal} 点血量，当前血量: {current_hp}/{max_hp}")
    
    def log_player_dying(self, player_name: str):
        """记录玩家濒死"""
        if self.logger:
            self.logger.warning(f"{player_name} 濒死！")
    
    def log_player_death(self, player_name: str, identity: str = None):
        """记录玩家死亡"""
        if self.logger:
            if identity:
                self.logger.warning(f"{player_name} ({identity}) 死亡！")
            else:
                self.logger.warning(f"{player_name} 死亡！")
    
    def log_player_equip(self, player_name: str, equipment_name: str, equipment_type: str):
        """记录玩家装备"""
        if self.logger:
            self.logger.info(f"{player_name} 装备 {equipment_name} ({equipment_type})")
    
    def log_card_effect(self, card_name: str, effect_description: str):
        """记录牌效果"""
        if self.logger:
            self.logger.info(f"{card_name} 效果: {effect_description}")
    
    def log_turn_start(self, player_name: str, turn_number: int):
        """记录回合开始"""
        if self.logger:
            self.logger.info(f"=== 第 {turn_number} 回合开始，{player_name} 的回合 ===")
    
    def log_turn_end(self, player_name: str):
        """记录回合结束"""
        if self.logger:
            self.logger.info(f"{player_name} 回合结束")
    
    def log_phase_start(self, player_name: str, phase: str):
        """记录阶段开始"""
        if self.logger:
            self.logger.info(f"{player_name} 进入 {phase} 阶段")
    
    def log_game_event(self, event_description: str):
        """记录游戏事件"""
        if self.logger:
            self.logger.info(f"游戏事件: {event_description}")
    
    def log_player_status(self, player_name: str, player_id: int, current_hp: int, max_hp: int, 
                         hand_cards: list, weapon: object = None, armor: object = None, 
                         horse_plus: object = None, horse_minus: object = None, 
                         identity: str = None, character: str = None):
        """记录玩家状态
        
        Args:
            player_name: 玩家名称
            player_id: 玩家ID
            current_hp: 当前血量
            max_hp: 最大血量
            hand_cards: 手牌列表
            weapon: 武器
            armor: 防具
            horse_plus: +1马（防御马）
            horse_minus: -1马（进攻马）
            identity: 身份
            character: 武将
        """
        if self.logger:
            # 基本信息
            status_info = f"玩家{player_id} ({player_name})"
            if identity:
                status_info += f" [{identity}]"
            if character:
                status_info += f" ({character})"
            status_info += f" - 血量: {current_hp}/{max_hp}"
            
            # 手牌信息
            if hand_cards:
                card_names = [card.name for card in hand_cards]
                status_info += f" - 手牌: {', '.join(card_names)}"
            else:
                status_info += " - 手牌: 无"
            
            # 装备信息
            equipment = []
            if weapon:
                equipment.append(f"武器: {weapon.name}")
            if armor:
                equipment.append(f"防具: {armor.name}")
            if horse_plus:
                equipment.append(f"防御马: {horse_plus.name}")
            if horse_minus:
                equipment.append(f"进攻马: {horse_minus.name}")
            
            if equipment:
                status_info += f" - 装备: {', '.join(equipment)}"
            else:
                status_info += " - 装备: 无"
            
            self.logger.info(status_info)
    
    def log_deck_status(self, deck):
        """记录牌堆状态
        
        Args:
            deck: 牌堆对象
        """
        if self.logger:
            self.logger.info("=" * 60)
            self.logger.info("当前牌堆状态:")
            
            # 正常牌堆信息
            deck_size = deck.get_deck_size()
            self.logger.info(f"正常牌堆: {deck_size} 张牌")
            
            # 弃牌堆信息
            discard_size = deck.get_discard_size()
            self.logger.info(f"弃牌堆: {discard_size} 张牌")
            
            # 如果弃牌堆有牌，显示最后几张牌的信息
            if discard_size > 0:
                recent_discards = deck.discard_pile[-5:] if discard_size >= 5 else deck.discard_pile
                discard_names = [card.name for card in recent_discards]
                if discard_size > 5:
                    self.logger.info(f"弃牌堆最后5张牌: {', '.join(discard_names)}")
                else:
                    self.logger.info(f"弃牌堆所有牌: {', '.join(discard_names)}")
            
            self.logger.info("=" * 60)
    
    def log_all_players_status(self, players: list):
        """记录所有玩家状态"""
        if self.logger:
            self.logger.info("=" * 60)
            self.logger.info("当前所有玩家状态:")
            for player in players:
                self.log_player_status(
                    player_name=player.name,
                    player_id=player.player_id,
                    current_hp=player.current_hp,
                    max_hp=player.max_hp,
                    hand_cards=player.hand_cards,
                    weapon=player.weapon,
                    armor=player.armor,
                    horse_plus=player.horse_plus,
                    horse_minus=player.horse_minus,
                    identity=player.identity.value if player.identity else None,
                    character=player.character_name.value if player.character_name else None
                )
            self.logger.info("=" * 60)


# 全局日志器实例
game_logger = GameLogger()
