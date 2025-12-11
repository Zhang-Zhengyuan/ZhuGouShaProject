#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
猪国杀 - 主程序入口
"""

import argparse
from backend.main_controller.main_controller import MainController
from backend.utils.event_sender import set_wait_for_ack


def main():
    """主函数"""
    # 设置 wait_for_ack 为 False（默认关闭ACK等待）
    set_wait_for_ack(False)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='猪国杀游戏',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main_back.py                    # 使用默认配置文件 (default_game_config)
  python main_back.py -c my_config       # 使用 config_file/my_config.json
  python main_back.py --config test      # 使用 config_file/test.json
        """
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='default_game_config',
        help='配置文件名（不需要加.json扩展名），默认为 default_game_config'
    )
    
    args = parser.parse_args()
    
    print("欢迎来到猪国杀！")
    print(f"使用配置文件: {args.config}")
    
    # 创建主控制器
    main_controller = MainController()
    
    try:
        # 加载配置
        config = main_controller.load_config(args.config)
        print(f"已加载配置，玩家数量: {len(config.players_config)}")
    
        # 开始游戏
        main_controller.start_game()
        
        print("游戏结束！")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return 1
    except (ValueError, TypeError) as e:
        print(f"配置文件格式错误: {e}")
        return 1
    except Exception as e:
        print(f"发生错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
