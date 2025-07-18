#!/bin/bash
# 部署脚本

set -e

echo "🚀 开始部署Web3极客日报..."

# 检查必要文件
echo "📋 检查文件..."
required_files=("web_api.py" "storage/database.py" "storage/models.py" "data/wechat_crawler.db")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done
echo "✅ 文件检查完成"

# 创建生产环境数据库副本
echo "📊 准备数据库..."
if [ -f "data/wechat_crawler.db" ]; then
    cp data/wechat_crawler.db data/production.db
    echo "✅ 数据库副本创建完成"
else
    echo "❌ 找不到数据库文件"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
if [ -f "requirements-deploy.txt" ]; then
    pip install -r requirements-deploy.txt
else
    pip install fastapi uvicorn sqlalchemy pydantic requests python-dotenv loguru
fi
echo "✅ 依赖安装完成"

# 测试API服务器
echo "🧪 测试API服务器..."
python -c "
import sys
sys.path.append('.')
from web_api import app
print('✅ API模块加载成功')
"

# 显示部署选项
echo ""
echo "🎯 部署选项:"
echo "1. Railway (推荐) - 免费且稳定"
echo "2. Render - 免费层"
echo "3. Heroku - 需要信用卡"
echo "4. DigitalOcean App Platform - 免费试用"
echo "5. Docker部署 - 自己的服务器"
echo ""

# Railway部署说明
echo "🚂 Railway部署步骤:"
echo "1. 访问 https://railway.app"
echo "2. 连接GitHub账号"
echo "3. 导入这个项目"
echo "4. 设置启动命令: python -m uvicorn web_api:app --host 0.0.0.0 --port \$PORT"
echo "5. 添加环境变量:"
echo "   - PORT=8000"
echo "   - PYTHONPATH=/app"
echo "   - DATABASE_URL=sqlite:///data/wechat_crawler.db"
echo ""

# Render部署说明
echo "🎨 Render部署步骤:"
echo "1. 访问 https://render.com"
echo "2. 连接GitHub账号"
echo "3. 创建新的Web Service"
echo "4. 设置构建命令: pip install -r requirements-deploy.txt"
echo "5. 设置启动命令: python -m uvicorn web_api:app --host 0.0.0.0 --port \$PORT"
echo ""

# 前端部署说明
echo "🌐 前端部署 (Vercel):"
echo "1. 访问 https://vercel.com"
echo "2. 导入frontend文件夹"
echo "3. 自动部署静态网站"
echo "4. 设置环境变量 API_BASE_URL 为后端地址"
echo ""

# Docker部署说明
echo "🐳 Docker部署:"
echo "1. 构建镜像: docker build -t geekdaily ."
echo "2. 运行容器: docker run -p 8000:8000 -v \$(pwd)/data:/app/data geekdaily"
echo ""

echo "✅ 部署准备完成！选择一个平台开始部署。"