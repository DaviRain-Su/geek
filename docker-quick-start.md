# Docker快速启动指南

## 🚀 一键启动所有服务

```bash
# 启动所有服务（MongoDB + Redis + Web管理界面）
./docker-services.sh start
```

## 📊 服务详情

启动后，你将获得以下服务：

### 1. MongoDB (端口: 27017)
- 数据库名: `wechat_crawler`
- 用户名: `admin`
- 密码: `wechat123`
- 连接字符串: `mongodb://admin:wechat123@localhost:27017/`

### 2. Redis (端口: 6379)
- 密码: `wechat123`
- 连接字符串: `redis://:wechat123@localhost:6379/0`

### 3. Mongo Express (端口: 8081)
- Web界面: http://localhost:8081
- 用户名: `admin`
- 密码: `wechat123`
- 功能: 可视化查看和管理MongoDB数据

### 4. Redis Commander (端口: 8082)
- Web界面: http://localhost:8082
- 功能: 可视化查看和管理Redis数据

## 🛠️ 常用命令

```bash
# 查看服务状态
./docker-services.sh status

# 查看日志
./docker-services.sh logs

# 停止服务
./docker-services.sh stop

# 重启服务
./docker-services.sh restart

# 进入MongoDB Shell
./docker-services.sh shell

# 进入Redis CLI
./docker-services.sh redis-cli

# 清理所有数据（危险操作）
./docker-services.sh clean
```

## 🔧 故障排除

### 端口被占用
如果遇到端口冲突，可以修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "27017:27017"  # 改为 "27018:27017"
```

### Docker未启动
确保Docker Desktop已经启动：
```bash
# macOS
open -a Docker
```

### 连接失败
使用Docker配置的.env文件：
```bash
cp .env.docker .env
```

## 📝 验证安装

```bash
# 使用爬虫验证数据库连接
python main.py stats
```

如果看到统计信息，说明服务启动成功！