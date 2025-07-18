#!/usr/bin/env python3
"""
前端应用演示脚本
展示完整的前后端集成功能
"""

import subprocess
import time
import webbrowser
import requests
import json
from pathlib import Path

def check_api_server():
    """检查API服务器是否运行"""
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """启动API服务器"""
    print("🚀 启动API服务器...")
    
    # 尝试激活虚拟环境并启动
    try:
        # 检查虚拟环境
        venv_path = Path('.venv/bin/activate')
        if venv_path.exists():
            cmd = 'source .venv/bin/activate && python main.py api --port 8000'
        else:
            cmd = 'python3 main.py api --port 8000'
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务器启动
        for i in range(10):
            time.sleep(1)
            if check_api_server():
                print("✅ API服务器启动成功")
                return process
            print(f"⏳ 等待API服务器启动... ({i+1}/10)")
        
        print("❌ API服务器启动失败")
        return None
        
    except Exception as e:
        print(f"❌ 启动API服务器失败: {e}")
        return None

def start_frontend_server():
    """启动前端服务器"""
    print("🌐 启动前端服务器...")
    
    try:
        frontend_dir = Path('frontend')
        if not frontend_dir.exists():
            print("❌ 前端目录不存在")
            return None
        
        # 启动简单的HTTP服务器
        process = subprocess.Popen(
            ['python3', '-m', 'http.server', '3000'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(2)  # 等待服务器启动
        
        # 测试前端服务器
        try:
            response = requests.get('http://localhost:3000', timeout=5)
            if response.status_code == 200:
                print("✅ 前端服务器启动成功")
                return process
        except:
            pass
        
        print("❌ 前端服务器启动失败")
        return None
        
    except Exception as e:
        print(f"❌ 启动前端服务器失败: {e}")
        return None

def demo_api_endpoints():
    """演示API端点功能"""
    print("\n📡 API端点演示")
    print("-" * 50)
    
    endpoints = [
        ('/health', '健康检查'),
        ('/stats', '统计信息'),
        ('/articles?limit=3', '文章列表'),
        ('/accounts', '账号列表')
    ]
    
    for endpoint, description in endpoints:
        try:
            print(f"\n🔍 测试: {description} ({endpoint})")
            response = requests.get(f'http://127.0.0.1:8000{endpoint}', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功 - 状态码: {response.status_code}")
                
                if endpoint == '/stats':
                    stats = data.get('data', {}).get('overview', {})
                    print(f"   📊 总文章数: {stats.get('total_articles', 0)}")
                    print(f"   👥 作者数量: {stats.get('total_authors', 0)}")
                
                elif endpoint == '/articles?limit=3':
                    articles = data.get('data', {}).get('articles', [])
                    print(f"   📰 返回文章: {len(articles)} 篇")
                    for article in articles[:2]:
                        title = article.get('title', '')[:40] + '...'
                        author = article.get('author', '')
                        print(f"      • {title} (作者: {author})")
                
                elif endpoint == '/accounts':
                    accounts = data.get('data', {}).get('accounts', [])
                    print(f"   🏢 账号数量: {len(accounts)}")
                    for account in accounts[:3]:
                        name = account.get('name', '')
                        count = account.get('article_count', 0)
                        print(f"      • {name}: {count} 篇文章")
                        
            else:
                print(f"❌ 失败 - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")

def demo_frontend_features():
    """演示前端功能"""
    print("\n🌐 前端功能演示")
    print("-" * 50)
    
    print("📱 前端应用特性:")
    print("  🏠 首页 - 数据概览和搜索")
    print("  📰 文章列表 - 分页浏览和筛选")  
    print("  📊 统计页面 - 数据可视化")
    print("  ℹ️  关于页面 - 项目信息")
    print()
    print("🎨 界面特点:")
    print("  ✨ 响应式设计 - 适配各种设备")
    print("  🎯 现代界面 - Material Design风格")
    print("  🔍 智能搜索 - 全文搜索支持")
    print("  📱 移动优化 - 触摸友好交互")
    print()
    print("⚡ 技术特性:")
    print("  🚀 原生JavaScript - 无框架依赖")
    print("  💾 智能缓存 - 优化加载性能")
    print("  🔄 实时数据 - API动态更新")
    print("  🛡️ 错误处理 - 优雅降级")

def main():
    """主演示流程"""
    print("🎪 Web3极客日报 - 完整应用演示")
    print("=" * 60)
    print()
    print("📋 演示内容:")
    print("1. 启动后端API服务器")
    print("2. 启动前端Web服务器") 
    print("3. 测试API端点功能")
    print("4. 展示前端应用特性")
    print("5. 打开浏览器进行体验")
    print()
    
    # 检查API服务器状态
    if check_api_server():
        print("✅ API服务器已在运行")
        api_process = None
    else:
        api_process = start_api_server()
        if not api_process:
            print("❌ 无法启动API服务器，演示终止")
            return
    
    # 演示API功能
    demo_api_endpoints()
    
    # 启动前端服务器
    frontend_process = start_frontend_server()
    if not frontend_process:
        print("❌ 无法启动前端服务器")
        if api_process:
            api_process.terminate()
        return
    
    # 演示前端功能
    demo_frontend_features()
    
    # 打开浏览器
    print(f"\n🌐 打开浏览器体验应用...")
    print(f"🔗 前端地址: http://localhost:3000")
    print(f"🔗 API文档: http://127.0.0.1:8000/docs")
    
    try:
        webbrowser.open('http://localhost:3000')
        print("✅ 已自动打开浏览器")
    except:
        print("⚠️  请手动打开浏览器访问 http://localhost:3000")
    
    print(f"\n🎯 体验指南:")
    print(f"1. 🏠 首页 - 查看统计信息，尝试搜索功能")
    print(f"2. 📰 文章列表 - 浏览文章，使用筛选器")
    print(f"3. 🔍 搜索测试 - 搜索 'Web3', 'DeFi', '区块链' 等关键词")
    print(f"4. 📊 统计页面 - 查看数据分析")
    print(f"5. 📱 移动测试 - 调整浏览器窗口大小测试响应式")
    
    print(f"\n⏹️  停止服务:")
    print(f"   按 Ctrl+C 停止演示并关闭所有服务")
    
    try:
        # 保持服务运行
        input("\n⏸️  按回车键停止演示...")
    except KeyboardInterrupt:
        print("\n👋 收到停止信号")
    
    # 清理进程
    print("🧹 清理服务...")
    if frontend_process:
        frontend_process.terminate()
        print("✅ 前端服务器已停止")
    
    if api_process:
        api_process.terminate()
        print("✅ API服务器已停止")
    
    print("👋 演示结束，感谢体验！")

if __name__ == "__main__":
    main()