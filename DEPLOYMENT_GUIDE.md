# 🚀 Web3极客日报 - 免费部署指南

本指南将帮你将Web3极客日报部署为公开的免费服务，包括后端API和前端网页。

## 🎯 推荐的免费部署方案

### 方案一：Railway + Vercel (最推荐)
- **后端**: Railway (免费$5/月额度)
- **前端**: Vercel (免费无限制)
- **数据库**: SQLite (包含在后端)
- **优势**: 部署简单，性能稳定，自动HTTPS

### 方案二：Render + Netlify
- **后端**: Render (免费层)
- **前端**: Netlify (免费层)
- **优势**: 界面友好，CI/CD完善

### 方案三：Docker自部署
- **服务器**: DigitalOcean/AWS/阿里云等
- **容器**: Docker
- **优势**: 完全控制，可扩展

## 📋 部署前准备

### 1. 代码准备
```bash
# 确保所有文件就绪
ls -la
# 应该包含：
# - web_api.py (后端API)
# - frontend/ (前端文件)
# - data/wechat_crawler.db (数据库)
# - requirements-deploy.txt (部署依赖)
# - Dockerfile (容器配置)
```

### 2. 数据库检查
```bash
# 确认数据库包含数据
python main.py stats
```

## 🚂 Railway部署 (推荐)

### 步骤1: 准备GitHub仓库
```bash
# 1. 创建GitHub仓库
# 2. 推送代码
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/geekdaily.git
git push -u origin main
```

### 步骤2: Railway部署后端
1. 访问 [Railway.app](https://railway.app)
2. 用GitHub账号登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择你的项目仓库
5. 配置环境变量：
   ```
   PYTHONPATH=/app
   PORT=8000
   DATABASE_URL=sqlite:///data/wechat_crawler.db
   CORS_ORIGINS=["https://yourdomain.vercel.app"]
   ```
6. 设置启动命令：
   ```
   python -m uvicorn web_api:app --host 0.0.0.0 --port $PORT
   ```
7. 部署完成后获得API地址，如：`https://your-app.railway.app`

### 步骤3: Vercel部署前端
1. 访问 [Vercel.com](https://vercel.com)
2. 用GitHub账号登录
3. 导入项目，选择 `frontend` 文件夹
4. 在设置中添加环境变量：
   ```
   API_BASE_URL=https://your-app.railway.app
   ```
5. 部署完成后获得前端地址，如：`https://geekdaily.vercel.app`

## 🎨 Render部署

### 后端部署 (Render)
1. 访问 [Render.com](https://render.com)
2. 连接GitHub账号
3. 创建 "New Web Service"
4. 配置：
   - **Build Command**: `pip install -r requirements-deploy.txt`
   - **Start Command**: `python -m uvicorn web_api:app --host 0.0.0.0 --port $PORT`
   - **Environment**: `Python 3.12`
5. 添加环境变量（同Railway）

### 前端部署 (Netlify)
1. 访问 [Netlify.com](https://netlify.com)
2. 拖拽 `frontend` 文件夹到部署区域
3. 设置环境变量指向后端API地址

## 🐳 Docker部署

### 构建镜像
```bash
# 构建后端API镜像
docker build -t geekdaily-api .

# 运行容器
docker run -d \
  --name geekdaily \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  geekdaily-api
```

### 使用docker-compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=sqlite:///data/wechat_crawler.db
  
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
```

## 🔧 环境配置

### 后端环境变量
```bash
# 必需
PORT=8000
PYTHONPATH=/app
DATABASE_URL=sqlite:///data/wechat_crawler.db

# 可选
CORS_ORIGINS=["https://yourdomain.com"]
LOG_LEVEL=INFO
MAX_PAGE_SIZE=100
```

### 前端环境变量
```bash
# API服务器地址
API_BASE_URL=https://your-api-server.com
```

## 🌍 域名配置

### 自定义域名 (可选)
1. **购买域名** (推荐：Namecheap, GoDaddy)
2. **配置DNS**:
   - A记录指向服务器IP
   - CNAME记录指向部署平台域名
3. **SSL证书**: 大部分平台自动提供

## 📊 性能优化

### 数据库优化
```bash
# 数据库索引检查
sqlite3 data/wechat_crawler.db ".schema"

# 定期清理和优化
sqlite3 data/wechat_crawler.db "VACUUM;"
```

### API优化
- 启用Gzip压缩
- 设置合理的缓存策略
- 限制请求频率

### 前端优化
- CDN加速静态资源
- 启用浏览器缓存
- 图片懒加载

## 🔒 安全配置

### API安全
```python
# 在web_api.py中添加
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.railway.app"]
)
```

### CORS配置
```python
# 生产环境限制域名
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

## 📈 监控和维护

### 健康检查
```bash
# API健康检查
curl https://your-api.railway.app/health

# 统计信息
curl https://your-api.railway.app/stats
```

### 日志监控
- Railway: 内置日志查看
- Render: 实时日志流
- Docker: `docker logs geekdaily`

### 数据备份
```bash
# 定期备份数据库
cp data/wechat_crawler.db backups/backup_$(date +%Y%m%d).db

# 导出JSON格式
python main.py export --format json
```

## 💰 成本估算

### 免费方案 (推荐)
- **Railway**: $5/月免费额度 (足够小型应用)
- **Vercel**: 完全免费
- **总成本**: $0/月

### 付费升级
- **Railway Pro**: $20/月 (更多资源)
- **自定义域名**: $10-15/年
- **CDN加速**: $0-10/月

## 🎯 快速部署清单

### ✅ 部署前检查
- [ ] 代码推送到GitHub
- [ ] 数据库文件存在且有数据
- [ ] requirements-deploy.txt准备好
- [ ] 环境变量配置完成

### ✅ Railway部署
- [ ] 注册Railway账号
- [ ] 连接GitHub仓库
- [ ] 配置环境变量
- [ ] 设置启动命令
- [ ] 获取API地址

### ✅ Vercel部署
- [ ] 注册Vercel账号
- [ ] 部署frontend文件夹
- [ ] 配置API_BASE_URL环境变量
- [ ] 获取前端地址
- [ ] 测试完整功能

### ✅ 最终测试
- [ ] API健康检查
- [ ] 前端页面加载
- [ ] 搜索功能
- [ ] 文章详情
- [ ] 统计信息

## 🔗 有用链接

- **Railway**: https://railway.app
- **Vercel**: https://vercel.com  
- **Render**: https://render.com
- **Netlify**: https://netlify.com
- **DigitalOcean**: https://digitalocean.com

## 🆘 故障排除

### 常见问题
1. **API无法访问**: 检查CORS设置和端口配置
2. **数据库错误**: 确保数据库文件在正确位置
3. **前端API调用失败**: 检查API_BASE_URL环境变量
4. **部署失败**: 查看部署日志，检查依赖文件

### 调试技巧
```bash
# 本地测试部署配置
docker build -t test .
docker run -p 8000:8000 test

# 检查API响应
curl -v https://your-api-domain.com/health
```

---

🎉 **恭喜！按照这个指南，你可以将Web3极客日报部署为一个完全免费的公开服务！**

📱 **用户可以通过以下方式访问：**
- 🌐 **网站**: https://yourdomain.vercel.app
- 📡 **API**: https://yourapi.railway.app
- 📖 **文档**: https://yourapi.railway.app/docs