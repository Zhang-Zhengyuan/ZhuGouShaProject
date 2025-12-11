# 主控制盘模块
from ..game_controller.game_controller import GameController
from ..utils.logger import game_logger
from config.simple_card_config import SimpleGameConfig
from config.simple_detailed_config import load_config


class MainController:
    """主控制盘模块
    
    可以从前端读取配置文件（如果没有则使用默认配置文件）
    前端点击开始后，使用该配置文件新建一个游戏控制盘模块，并进入游戏控制盘模块。
    """
    
    def __init__(self):
        self.config = None
        self.game_controller = None
    
    def load_config(self, config_file_name: str = "default_game_config") -> SimpleGameConfig:
        """加载配置文件
        
        Args:
            config_file_name: 配置文件名（不需要加.json扩展名），默认为 "default_game_config"
                            例如：输入 "my_config" 会查找 "config_file/my_config.json"
            
        Returns:
            SimpleGameConfig配置对象
            
        Raises:
            FileNotFoundError: 如果指定的配置文件不存在
            ValueError: 如果配置文件格式不正确
            TypeError: 如果配置文件类型不正确
        """
        # 调用 config/simple_detailed_config.py 中的 load_config 函数
        self.config = load_config(config_file_name)
        return self.config
    
    def start_game(self) -> None:
        """开始游戏
        
        使用当前配置文件创建游戏控制盘模块并进入游戏
        """
        if self.config is None:
            self.load_config()
        
        # 开始游戏会话日志
        log_path = game_logger.start_game_session(is_test=False)
        game_logger.log_info(f"开始新游戏，玩家数量: {len(self.config.players_config)}")
        
        try:
            self.game_controller = GameController(self.config)
            self.game_controller.start_game()
        finally:
            # 结束游戏会话日志
            game_logger.end_game_session()
    
    def get_config(self) -> SimpleGameConfig:
        """获取当前配置
        
        Returns:
            当前SimpleGameConfig配置对象
        """
        return self.config
