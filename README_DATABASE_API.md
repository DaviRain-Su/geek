# 数据库存储与Web API使用指南

## 概述

本项目现在支持将JSON数据导入数据库，并提供Web API接口来访问这些数据，方便后续制作网页应用。

## 主要功能

### 1. JSON数据导入到数据库

将清洗后的JSON文件导入到SQLite数据库中，便于管理和查询。

#### 基本使用

```bash
# 导入JSON文件到数据库
python main.py import data/geekdaily.json

# 指定账号名称
python main.py import data/api_data.json --account "Web3极客日报"

# 强制更新已存在的文章
python main.py import data/updated_data.json --force

# 导入时不清理内容
python main.py import data/raw_data.json --no-clean
```

#### 支持的JSON格式

1. **结构化格式** (推荐)
```json
{
  "export_info": {
    "total": 100,
    "export_time": "2024-01-18 14:00:00"
  },
  "articles": [
    {
      "id": 1,
      "attributes": {
        "title": "文章标题",
        "author": "作者名",
        "url": "https://example.com/article1",
        "time": "2025-01-15",
        "introduce": "文章简介"
      }
    }
  ]
}
```

2. **简单格式**
```json
{
  "articles": [
    {
      "title": "文章标题",
      "author": "作者名",
      "url": "https://example.com/article1",
      "content": "文章内容",
      "publish_time": "2025-01-15"
    }
  ]
}
```

### 2. Web API服务器

提供RESTful API接口来访问数据库中的文章数据。

#### 启动API服务器

```bash
# 启动API服务器（默认地址：127.0.0.1:8000）
python main.py api

# 指定地址和端口
python main.py api --host 0.0.0.0 --port 8080

# 开发模式（支持热重载）
python main.py api --reload
```

#### API端点

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/` | GET | API信息 | - |
| `/articles` | GET | 获取文章列表 | `account`, `limit`, `offset`, `search` |
| `/articles/{id}` | GET | 获取特定文章 | - |
| `/articles/search` | GET | 搜索文章 | `q`, `limit` |
| `/stats` | GET | 统计信息 | - |
| `/accounts` | GET | 账号列表 | - |
| `/health` | GET | 健康检查 | - |

#### API使用示例

```bash
# 获取所有文章（前20篇）
curl "http://localhost:8000/articles"

# 获取特定账号的文章
curl "http://localhost:8000/articles?account=Web3极客日报&limit=10"

# 搜索文章
curl "http://localhost:8000/articles/search?q=DeFi&limit=5"

# 获取文章详情
curl "http://localhost:8000/articles/1"

# 获取统计信息
curl "http://localhost:8000/stats"

# 获取所有账号
curl "http://localhost:8000/accounts"
```

#### API响应格式

所有API响应都遵循统一格式：

```json
{
  "success": true,
  "data": {
    // 具体数据内容
  },
  "message": "操作结果信息"
}
```

### 3. 数据库查询命令

#### 查看统计信息
```bash
python main.py stats
```

#### 列出文章
```bash
# 列出所有文章
python main.py list

# 列出特定账号的文章
python main.py list --account "Web3极客日报"

# 搜索文章
python main.py list --search "DeFi"

# 限制显示数量
python main.py list --limit 10
```

#### 查看文章详情
```bash
# 通过文章ID查看
python main.py detail --id 1

# 通过URL查看
python main.py detail --url "https://example.com/article"
```

## 完整工作流程

### 1. 数据获取与清洗
```bash
# 获取API数据
python main.py fetch --max-pages 5

# 清洗数据（去除无效项目）
python main.py clean data/api_geekdailies_*.json --exclude-fields episode time

# 合并多个文件
python main.py merge file1.json file2.json --strategy url
```

### 2. 导入数据库
```bash
# 导入清洗后的数据
python main.py import data/api_geekdailies_*_cleaned_*.json --account "Web3极客日报"
```

### 3. 启动Web服务
```bash
# 启动API服务器
python main.py api --host 0.0.0.0 --port 8000
```

### 4. 访问数据
- **API文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc  
- **获取文章**: http://localhost:8000/articles
- **搜索文章**: http://localhost:8000/articles/search?q=关键词

## 数据库说明

### 存储位置
- SQLite数据库文件: `data/wechat_crawler.db`
- 自动创建数据表和索引

### 数据结构
- **articles表**: 存储文章内容
- **crawl_jobs表**: 存储爬取任务记录

### 数据字段
- `id`: 自增主键
- `url`: 文章URL（唯一）
- `title`: 文章标题
- `content`: 文章内容
- `author`: 作者
- `account_name`: 账号名称
- `publish_time`: 发布时间
- `crawl_time`: 爬取时间
- `read_count`, `like_count`: 阅读数、点赞数

## 前端集成建议

### 1. React/Vue.js应用
```javascript
// 获取文章列表
const response = await fetch('http://localhost:8000/articles?limit=20');
const data = await response.json();
const articles = data.data.articles;

// 搜索文章
const searchResponse = await fetch(`http://localhost:8000/articles/search?q=${keyword}`);
const searchData = await searchResponse.json();
```

### 2. 分页支持
```javascript
// 分页获取文章
const getArticles = async (page = 1, limit = 20) => {
  const offset = (page - 1) * limit;
  const response = await fetch(`http://localhost:8000/articles?limit=${limit}&offset=${offset}`);
  return response.json();
};
```

### 3. 实时统计
```javascript
// 获取统计信息
const getStats = async () => {
  const response = await fetch('http://localhost:8000/stats');
  return response.json();
};
```

## 安全建议

### 生产环境配置
1. **CORS设置**: 在`web_api.py`中限制`allow_origins`为特定域名
2. **访问控制**: 添加API密钥或JWT认证
3. **速率限制**: 添加请求频率限制
4. **HTTPS**: 使用HTTPS协议

### 数据备份
```bash
# 定期备份数据库
cp data/wechat_crawler.db data/backup_$(date +%Y%m%d).db

# 导出数据为JSON
python main.py export --format json
```

## 故障排除

### 常见问题

1. **ModuleNotFoundError**: 运行 `bash install_dependencies.sh`
2. **数据库连接失败**: 检查 `data/` 目录权限
3. **API启动失败**: 确保端口未被占用
4. **数据导入失败**: 检查JSON格式是否正确

### 日志查看
应用使用loguru记录详细日志，可以查看具体错误信息。

---

现在你有了完整的数据存储和Web API系统，可以很方便地制作网页应用来展示和管理文章数据了！