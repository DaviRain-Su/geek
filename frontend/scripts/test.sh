#!/bin/bash
# 测试脚本

echo "🧪 运行测试..."

# 创建测试目录（如果不存在）
mkdir -p tests

# 检查是否有测试文件
if [ -z "$(ls -A tests/*.py 2>/dev/null)" ]; then
    echo "⚠️  没有找到测试文件。"
    echo "📝 创建示例测试文件..."
    
    # 创建示例测试文件
    cat > tests/test_server.py << 'EOF'
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
EOF
    
    echo "✅ 已创建示例测试文件: tests/test_server.py"
fi

# 运行 pytest
echo "▶️  运行 pytest..."
uv run pytest -v

echo "✅ 测试完成！"