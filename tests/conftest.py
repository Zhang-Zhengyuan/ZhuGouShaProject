"""pytest配置文件"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.logger import game_logger


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """设置测试日志会话"""
    # 开始测试会话日志
    log_path = game_logger.start_game_session(is_test=True)
    print(f"测试日志保存到: {log_path}")
    
    yield
    
    # 结束测试会话日志
    game_logger.end_game_session()


@pytest.fixture(autouse=True)
def test_logging(request):
    """为每个测试添加日志分隔符"""
    test_name = request.node.name
    game_logger.log_info(f"开始测试: {test_name}")
    
    yield
    
    game_logger.log_info(f"结束测试: {test_name}")
    game_logger.log_info("-" * 50)
