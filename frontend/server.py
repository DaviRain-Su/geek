#!/usr/bin/env python3
"""
简单的HTTP服务器，用于运行前端应用
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持CORS的HTTP请求处理器"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def start_server(port=3000, auto_open=True):
    """启动前端服务器"""
    
    # 切换到frontend目录
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # 检查必要文件是否存在
    required_files = ['index.html', 'css/main.css', 'js/main.js', 'js/api.js']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return
    
    print(f"🚀 启动Web3极客日报前端服务器...")
    print(f"📡 服务地址: http://localhost:{port}")
    print(f"📁 服务目录: {frontend_dir}")
    print()
    print(f"🔧 功能特性:")
    print(f"  📰 文章浏览 - 支持分页和过滤")
    print(f"  🔍 智能搜索 - 全文搜索功能")
    print(f"  📊 数据统计 - 可视化统计信息")
    print(f"  📱 响应式设计 - 完美适配移动设备")
    print(f"  ⚡ 实时数据 - 连接后端API获取最新数据")
    print()
    print(f"⚠️  注意: 请确保后端API服务器正在运行 (python main.py api)")
    print(f"🔗 API服务器: http://127.0.0.1:8000")
    print()
    
    try:
        # 创建服务器
        with socketserver.TCPServer(("", port), CORSRequestHandler) as httpd:
            print(f"✅ 服务器启动成功！按 Ctrl+C 停止服务器")
            
            # 自动打开浏览器
            if auto_open:
                try:
                    webbrowser.open(f'http://localhost:{port}')
                    print(f"🌐 已自动打开浏览器")
                except:
                    print(f"🌐 请手动打开浏览器访问: http://localhost:{port}")
            
            print("-" * 60)
            
            # 启动服务器
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n👋 前端服务器已停止")
    except OSError as e:
        if e.errno == 48:  # 端口被占用
            print(f"❌ 端口 {port} 已被占用，请尝试其他端口:")
            print(f"   python server.py --port 3001")
        else:
            print(f"❌ 启动服务器失败: {e}")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Web3极客日报前端服务器")
    parser.add_argument('--port', type=int, default=3000, help='端口号 (默认: 3000)')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    
    args = parser.parse_args()
    
    start_server(port=args.port, auto_open=not args.no_browser)