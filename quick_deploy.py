#!/usr/bin/env python3
"""
快速部署助手
帮助用户选择最适合的部署方案并提供详细指导
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def check_requirements():
    """检查部署要求"""
    print("📋 检查部署要求...")
    
    required_files = [
        "web_api.py",
        "storage/database.py", 
        "storage/models.py",
        "data/wechat_crawler.db",
        "frontend/index.html"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("✅ 所有必要文件检查完成")
    return True

def check_database():
    """检查数据库状态"""
    print("📊 检查数据库...")
    
    try:
        # 简单检查数据库文件大小
        db_path = "data/wechat_crawler.db"
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            if size > 1024:  # 大于1KB
                print(f"✅ 数据库文件存在，大小: {size/1024/1024:.1f}MB")
                return True
            else:
                print("⚠️  数据库文件太小，可能没有数据")
                return False
        else:
            print("❌ 数据库文件不存在")
            return False
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def create_deployment_package():
    """创建部署包"""
    print("📦 创建部署包...")
    
    try:
        # 创建部署目录
        deploy_dir = "deploy_package"
        if os.path.exists(deploy_dir):
            shutil.rmtree(deploy_dir)
        os.makedirs(deploy_dir)
        
        # 复制必要文件
        files_to_copy = [
            "web_api.py",
            "storage/",
            "utils/",
            "data/wechat_crawler.db",
            "requirements-deploy.txt",
            "Dockerfile",
            "railway.toml",
            ".env.production"
        ]
        
        for item in files_to_copy:
            src = item
            dst = os.path.join(deploy_dir, item)
            
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        
        # 复制前端文件到单独目录
        frontend_deploy = os.path.join(deploy_dir, "frontend")
        shutil.copytree("frontend", frontend_deploy)
        
        print(f"✅ 部署包已创建: {deploy_dir}/")
        return deploy_dir
        
    except Exception as e:
        print(f"❌ 创建部署包失败: {e}")
        return None

def show_deployment_options():
    """显示部署选项"""
    print("\n🚀 选择部署方案:")
    print("-" * 50)
    
    options = [
        {
            "name": "Railway + Vercel",
            "difficulty": "⭐⭐",
            "cost": "免费",
            "features": "自动HTTPS, 全球CDN, 简单配置",
            "best_for": "推荐给所有用户"
        },
        {
            "name": "Render + Netlify", 
            "difficulty": "⭐⭐⭐",
            "cost": "免费",
            "features": "GitHub集成, 自动部署",
            "best_for": "熟悉Git的用户"
        },
        {
            "name": "Docker部署",
            "difficulty": "⭐⭐⭐⭐",
            "cost": "服务器费用",
            "features": "完全控制, 可扩展",
            "best_for": "技术专家"
        }
    ]
    
    for i, option in enumerate(options, 1):
        print(f"{i}. {option['name']}")
        print(f"   难度: {option['difficulty']}")
        print(f"   成本: {option['cost']}")
        print(f"   特点: {option['features']}")
        print(f"   适合: {option['best_for']}")
        print()

def railway_deployment_guide():
    """Railway部署指南"""
    print("🚂 Railway + Vercel 部署指南")
    print("=" * 50)
    
    steps = [
        {
            "title": "第1步: 准备GitHub仓库",
            "commands": [
                "git init",
                "git add .",
                "git commit -m 'Deploy GeekDaily'",
                "# 在GitHub创建新仓库后:",
                "git remote add origin https://github.com/你的用户名/geekdaily.git",
                "git push -u origin main"
            ],
            "notes": "如果没有GitHub账号，请先注册: https://github.com"
        },
        {
            "title": "第2步: Railway部署后端",
            "commands": [
                "1. 访问 https://railway.app",
                "2. 用GitHub账号登录",
                "3. 点击 'New Project'",
                "4. 选择 'Deploy from GitHub repo'",
                "5. 选择你的项目仓库",
                "6. Railway会自动检测并部署"
            ],
            "notes": "部署完成后，你会得到一个API地址，如: https://geekdaily-production.railway.app"
        },
        {
            "title": "第3步: 配置环境变量",
            "commands": [
                "在Railway项目设置中添加:",
                "PORT = 8000",
                "PYTHONPATH = /app", 
                "DATABASE_URL = sqlite:///data/wechat_crawler.db"
            ],
            "notes": "这些变量确保应用正确运行"
        },
        {
            "title": "第4步: Vercel部署前端",
            "commands": [
                "1. 访问 https://vercel.com",
                "2. 用GitHub账号登录",
                "3. 导入项目，选择 'frontend' 文件夹",
                "4. 在环境变量中设置:",
                "   API_BASE_URL = 你的Railway API地址",
                "5. 点击部署"
            ],
            "notes": "前端部署完成后，你会得到一个网站地址"
        }
    ]
    
    for step in steps:
        print(f"\n{step['title']}")
        print("-" * 30)
        for cmd in step['commands']:
            if cmd.startswith('#') or cmd.startswith('1.'):
                print(f"  {cmd}")
            else:
                print(f"  $ {cmd}")
        print(f"💡 {step['notes']}")
    
    print(f"\n🎉 部署完成后的访问地址:")
    print(f"🌐 前端网站: https://your-project.vercel.app")
    print(f"📡 API接口: https://your-project.railway.app")
    print(f"📖 API文档: https://your-project.railway.app/docs")

def test_local_deployment():
    """测试本地部署"""
    print("🧪 测试本地部署...")
    
    try:
        # 测试API导入
        import web_api
        print("✅ API模块导入成功")
        
        # 测试数据库连接
        from storage.database import DatabaseManager
        db = DatabaseManager(use_mongodb=False)
        count = db.get_article_count()
        db.close()
        print(f"✅ 数据库连接成功，包含 {count} 篇文章")
        
        return True
        
    except Exception as e:
        print(f"❌ 本地测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎪 Web3极客日报 - 快速部署助手")
    print("=" * 60)
    
    # 检查系统要求
    if not check_requirements():
        print("\n❌ 系统检查失败，请先完成项目设置")
        return
    
    if not check_database():
        print("\n⚠️  数据库问题，建议先导入一些数据")
        response = input("是否继续部署？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            return
    
    # 测试本地部署
    if not test_local_deployment():
        print("\n❌ 本地测试失败，请检查代码")
        return
    
    # 创建部署包
    deploy_dir = create_deployment_package()
    if not deploy_dir:
        return
    
    # 显示部署选项
    show_deployment_options()
    
    # 获取用户选择
    try:
        choice = input("选择部署方案 (1-3): ").strip()
        
        if choice == "1":
            railway_deployment_guide()
        elif choice == "2":
            print("📖 请查看 DEPLOYMENT_GUIDE.md 了解Render部署详情")
        elif choice == "3":
            print("🐳 Docker部署:")
            print("  $ docker build -t geekdaily .")
            print("  $ docker run -p 8000:8000 geekdaily")
        else:
            print("📖 请查看 DEPLOYMENT_GUIDE.md 了解完整部署选项")
    
    except KeyboardInterrupt:
        print("\n\n👋 部署已取消")
    
    print(f"\n📁 部署文件已准备在: {deploy_dir}/")
    print(f"📖 详细文档: DEPLOYMENT_GUIDE.md")
    print(f"🔧 部署脚本: deploy.sh")

if __name__ == "__main__":
    main()