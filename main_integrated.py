#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
猪国杀 - 前后端通信集成运行脚本
基于communicator模块实现前后端分离运行
使用多线程同时启动前后端，通过队列进行通信
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

import pygame
import threading
import time
import signal
import sys
from typing import Optional, Dict, Any
from frontend.ui.start_screen import StartScreen
from frontend.ui.game_over_screen import GameOverScreen
from frontend.core.game_client import GameClient
from frontend.util.size import DEFAULT_WINDOW_SIZE
from backend.main_controller.main_controller import MainController
from config.simple_card_config import SimpleGameConfig, SimplePlayerConfig
from communicator.communicator import communicator
from backend.utils.event_sender import set_wait_for_ack
from config.enums import ControlType
from config.enums import CharacterName, PlayerIdentity
from campaign.flow import start_chapter_one_headless, start_chapter_two_headless
from campaign.chapter1 import get_chapter_one_config
from campaign.chapter2 import get_chapter_two_config
from campaign.chapter3 import get_chapter_three_config
from config.simple_detailed_config import create_simple_default_game_config

class GameManager:
    """游戏管理器，负责前后端协调"""

    def __init__(self):
        self.backend_thread: Optional[threading.Thread] = None
        self.frontend_client: Optional[GameClient] = None
        self.running = False
        self.config: Optional[SimpleGameConfig] = None

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器，用于优雅退出"""
        print(f"\n接收到信号 {signum}，正在关闭游戏...")
        self.shutdown()
        sys.exit(0)

    def run_backend(self):
        """运行后端游戏逻辑"""
        try:
            print("[后端] 游戏逻辑启动...")
            main_controller = MainController()
            main_controller.config = self.config
            self.running = True
            main_controller.start_game()
            print("[后端] 游戏逻辑结束")
        except Exception as e:
            print(f"[后端] 运行错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False

    def run_frontend(self, screen, clock):
        """运行前端UI"""
        try:
            print("[前端] UI启动...")
            self.frontend_client = GameClient(self.config, screen, clock)
            result = self.frontend_client.run()
            print("[前端] UI结束")
            return result
        except Exception as e:
            print(f"[前端] 运行错误: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.running = False

    def start(self):
        """启动游戏"""
        print("=" * 60)
        print("猪国杀 - 前后端通信集成版")
        print("=" * 60)
        print("基于communicator模块实现前后端分离通信")
        print("使用多线程和队列进行异步通信")
        print("=" * 60)

        # 初始化pygame
        pygame.init()

        # 显示配置选择界面
        print("\n配置选择：")
        print("1.  点击'选择配置文件'按钮选择JSON配置文件")
        print("2.  点击'随机开始'按钮使用默认配置")
        print("4.  关闭窗口退出程序\n")

        starter = StartScreen()
        config_result = starter.run()

        if config_result is None:
            print("[错误] 未加载配置，退出程序。")
            pygame.quit()
            return

        # 创建pygame窗口和时钟
        screen = pygame.display.set_mode(DEFAULT_WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("猪国杀 - 通信集成版")
        clock = pygame.time.Clock()

        while True:
            # 处理配置
            current_chapter = "unknown"
            # 如果是章节标识（由 StartScreen 返回），调用对应章节的配置生成函数
            if isinstance(config_result, dict) and config_result.get('__chapter__') == 'chapter1':
                self.config = create_simple_default_game_config()
                self.config.players_config = get_chapter_one_config()
                current_chapter = "chapter1"
            elif isinstance(config_result, dict) and config_result.get('__chapter__') == 'chapter2':
                self.config = create_simple_default_game_config()
                self.config.players_config = get_chapter_two_config()
                current_chapter = "chapter2"
            elif isinstance(config_result, dict) and config_result.get('__chapter__') == 'chapter3':
                self.config = create_simple_default_game_config()
                self.config.players_config = get_chapter_three_config()
                current_chapter = "chapter3"
            elif isinstance(config_result, dict):
                self.config = SimpleGameConfig.from_dict(config_result)
            elif isinstance(config_result, SimpleGameConfig):
                self.config = config_result
            else:
                print(f"[错误] 未知的配置类型: {type(config_result)}")
                break

            try:
                player_count = len(self.config.players_config)
            except Exception:
                player_count = '未知'
            print(f"\n[成功] 已加载配置，玩家数量: {player_count}")
            print("[启动] 正在启动前后端...")

            # 自动设置忠臣（赵云）为真人玩家控制
            for idx, pconf in enumerate(self.config.players_config):
                if pconf.name == "忠臣":
                    pconf.control_type = ControlType.HUMAN
                    print(f"\n[配置] 已将玩家 {idx} ({pconf.name} - {pconf.character_name.name}) 设为真人控制")
                    break

            # 在后台线程启动后端（普通模式或章节模式）
            print("[系统] 启动后端线程...")
            if isinstance(config_result, dict) and config_result.get('__chapter__') == 'chapter1':
                # 第一章模式：使用 campaign 的 headless 启动函数
                self.backend_thread = threading.Thread(
                    target=lambda: start_chapter_one_headless(human_control=True, ai_count=4),
                    daemon=True,
                    name="BackendThread"
                )
            elif isinstance(config_result, dict) and config_result.get('__chapter__') == 'chapter2':
                # 第二章模式：使用 campaign 的 headless 启动函数
                self.backend_thread = threading.Thread(
                    target=lambda: start_chapter_two_headless(human_control=True, ai_count=4),
                    daemon=True,
                    name="BackendThread"
                )
            elif isinstance(config_result, dict) and config_result.get('__chapter__') == 'chapter3':
                # 第三章模式：使用 run_backend
                self.backend_thread = threading.Thread(
                    target=self.run_backend,
                    daemon=True,
                    name="BackendThread"
                )
            else:
                self.backend_thread = threading.Thread(
                    target=self.run_backend,
                    daemon=True,
                    name="BackendThread"
                )
            self.backend_thread.start()

            # 等待后端初始化
            time.sleep(1.0)

            # 检查后端是否启动成功
            if not self.backend_thread.is_alive():
                print("[错误] 后端启动失败")
                break

            print("[系统] 后端启动成功，启动前端...")

            # 启动前端（主线程）
            winner_info = None
            try:
                winner_info = self.run_frontend(screen, clock)
            except KeyboardInterrupt:
                print("\n[警告] 用户中断")
            except Exception as e:
                print(f"[错误] 前端运行错误: {e}")
                import traceback
                traceback.print_exc()
            
            # 关闭后端
            self.shutdown_backend()

            # 如果没有胜利信息（用户直接关闭窗口），则退出
            if not winner_info:
                break

            # 显示游戏结束界面
            game_over_screen = GameOverScreen(winner_info, current_chapter, self.frontend_client.renderer.screen.get_size())
            action = game_over_screen.run()

            if action == "exit":
                break
            elif action == "next_chapter":
                if current_chapter == "chapter1":
                    config_result = {'__chapter__': 'chapter2'}
                elif current_chapter == "chapter2":
                    config_result = {'__chapter__': 'chapter3'}
            elif action == "restart":
                # 保持 config_result 不变，重新开始
                pass
            else:
                break

        self.shutdown()
    def shutdown_backend(self):
        """关闭后端线程和清理通信"""
        print("\n[系统] 正在关闭后端...")
        self.running = False

        # 等待后端线程结束
        if self.backend_thread and self.backend_thread.is_alive():
            print("[系统] 等待后端线程结束...")
            self.backend_thread.join(timeout=2.0)
            
        # 清理通信器
        try:
            communicator.pending_acks.clear()
            communicator.ack_results.clear()
            while not communicator.btf_queue.empty():
                try: communicator.btf_queue.get_nowait()
                except: break
            while not communicator.ftb_queue.empty():
                try: communicator.ftb_queue.get_nowait()
                except: break
            print("[系统] 通信器已清理")
        except Exception as e:
            print(f"[警告] 清理通信器时出错: {e}")

    def shutdown(self):
        """优雅关闭游戏"""
        self.shutdown_backend()
        pygame.quit()
        print("[成功] 游戏已关闭")


def main():
    """主函数"""
    set_wait_for_ack(True)
    game_manager = GameManager()
    game_manager.start()


if __name__ == "__main__":
    main()