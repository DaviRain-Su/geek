"""服务器测试"""
import pytest
from pathlib import Path
import sys

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import server


def test_server_imports():
    """测试服务器模块可以正常导入"""
    assert hasattr(server, 'start_server')
    assert hasattr(server, 'main')
    assert hasattr(server, 'CORSRequestHandler')


def test_cors_handler():
    """测试CORS处理器"""
    from http.server import SimpleHTTPRequestHandler
    assert issubclass(server.CORSRequestHandler, SimpleHTTPRequestHandler)


def test_main_function():
    """测试主函数存在"""
    assert callable(server.main)
    assert callable(server.start_server)