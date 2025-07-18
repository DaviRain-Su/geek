# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project implements a web crawler for WeChat public accounts to extract all articles from specified accounts.

## Technical Requirements

### Core Functionality
- Crawl all articles from specified WeChat public accounts (微信公众号)
- Extract article metadata: title, author, publish date, content, images, read count, like count
- Handle pagination and historical articles
- Store extracted data in a structured format

### Technical Challenges
1. **Access Restrictions**: WeChat articles are protected behind authentication and anti-crawling mechanisms
2. **Dynamic Content**: Articles are loaded dynamically via JavaScript
3. **Rate Limiting**: WeChat implements strict rate limiting and IP blocking
4. **Mobile-First Design**: Content is optimized for mobile viewing

### Recommended Approach
1. **Selenium/Playwright**: Use browser automation to handle JavaScript rendering
2. **Proxy Rotation**: Implement proxy rotation to avoid IP blocking
3. **Request Throttling**: Add delays between requests to avoid rate limiting
4. **Data Storage**: Use database (PostgreSQL/MongoDB) for structured storage
5. **Queue System**: Implement task queue for reliable crawling (Redis/RabbitMQ)

### Key Components to Implement
- `crawler/`: Core crawling logic with browser automation
- `parser/`: HTML parsing and data extraction
- `storage/`: Database models and storage logic
- `proxy/`: Proxy management and rotation
- `task_queue/`: Task queue for crawling jobs
- `api/`: REST API for accessing crawled data

## Build and Run Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment configuration
cp .env.example .env
```

### Running the Crawler
```bash
# Method 1: Get series/album articles (best for series like "日报 #123")
python main.py series "https://mp.weixin.qq.com/s/..."
python main.py series "https://mp.weixin.qq.com/s/..." --max-articles 100

# Method 2: Get history articles from account
python main.py history "https://mp.weixin.qq.com/s/..."
python main.py history "https://mp.weixin.qq.com/s/..." --max-articles 50

# Method 3: Discover articles from a single article
python main.py discover "https://mp.weixin.qq.com/s/..."
python main.py discover "https://mp.weixin.qq.com/s/..." --max-articles 20

# Method 4: Crawl by account name
python main.py crawl "公众号名称"
python main.py crawl "公众号名称" --max-articles 10 --use-proxy

# Method 5: Crawl a single article
python main.py article "https://mp.weixin.qq.com/s/..."

# View statistics
python main.py stats
```

### Development
```bash
# Run with debug logging
export LOGURU_LEVEL=DEBUG
python main.py crawl "test"

# Format code (when black is installed)
black .

# Type checking (when mypy is installed)
mypy .
```

## Architecture Overview

The crawler is built with an async architecture using Playwright for browser automation:

1. **Browser Layer** (`crawler/browser.py`): Manages Playwright browser instances with stealth mode
2. **Crawler Layer** (`crawler/wechat.py`): Implements WeChat-specific crawling logic
3. **Parser Layer** (`parser/article.py`): Extracts structured data from HTML
4. **Storage Layer** (`storage/`): Handles data persistence with SQLite/MongoDB
5. **Proxy Layer** (`proxy/manager.py`): Manages proxy rotation for rate limit avoidance

Key design decisions:
- Mobile viewport simulation to match WeChat's mobile-first design
- Stealth techniques to avoid detection
- Flexible storage backend (SQLite for simplicity, MongoDB for scale)
- Modular architecture for easy extension

## Current Status

✅ **已完成功能**：
- 微信公众号文章爬虫（多种方式：系列、历史、发现、账号名）
- 数据库存储和管理（SQLite/MongoDB双支持）
- RESTful API服务（FastAPI）
- 现代化前端界面（HTML/CSS/JS）
- 数据导出和导入（JSON、TXT、CSV格式）
- JSON文件合并和清洗功能
- 智能文章拆分（合集文章自动拆分为独立条目）
- 数据去重和URL修复
- 完整的部署方案（Docker + 多平台免费部署）

## 📋 待实现功能规划

### 🚀 第一阶段：内容增强功能

#### 📊 数据分析功能
- [ ] **趋势分析系统**
  - 分析热门技术栈和关键词趋势
  - 作者活跃度和影响力分析
  - 文章发布频率和时间分布统计
  - 技术领域热度变化追踪
  
- [ ] **智能标签系统**
  - 自动提取文章关键词和技术标签
  - 生成标签云和相关性分析
  - 基于标签的文章分类和推荐
  - 用户自定义标签管理

- [ ] **内容质量评估**
  - 基于内容长度、链接质量、作者权威性的评分系统
  - 文章可读性和技术深度分析
  - 重复内容检测和相似度分析
  - 内容新鲜度和时效性评估

#### 🔍 搜索功能增强
- [ ] **高级搜索引擎**
  - 支持复杂查询语法（AND、OR、NOT、引号精确匹配）
  - 模糊搜索和拼写纠错
  - 搜索结果高亮和排序优化
  - 保存搜索条件和快速搜索

- [ ] **智能搜索体验**
  - 实时搜索建议和自动补全
  - 搜索历史记录和管理
  - 热门搜索词统计和推荐
  - 按时间范围、作者、技术栈的高级过滤

### 🌐 第二阶段：多源数据聚合

#### 📡 外部数据源集成
- [ ] **RSS聚合器**
  - 支持订阅技术博客RSS feeds
  - 自动抓取和解析RSS内容
  - RSS源管理和质量评估
  - 重复内容检测和去重

- [ ] **GitHub监控系统**
  - 监控指定仓库的更新和releases
  - 抓取README、文档变更
  - 星标数、fork数趋势分析
  - 开源项目热度排行

- [ ] **社交媒体监控**
  - Twitter/X技术推文抓取
  - Reddit技术社区帖子监控
  - Hacker News热门技术文章
  - 技术会议和活动信息聚合

#### 🤖 AI功能集成
- [ ] **内容处理AI**
  - 自动生成文章摘要和关键点提取
  - 标题优化和SEO改进建议
  - 英文技术文章自动翻译
  - 内容情感倾向和技术难度分析

- [ ] **推荐系统**
  - 基于用户阅读历史的个性化推荐
  - 相似文章和相关内容推荐
  - 基于协同过滤的智能推荐
  - 新技术和热门趋势推送

### 📈 第三阶段：数据管理优化

#### 🔄 同步和备份系统
- [ ] **增量同步机制**
  - 定期检查和同步新文章
  - 避免重复抓取的智能判断
  - 增量更新和差异检测
  - 同步状态监控和报告

- [ ] **数据备份策略**
  - 自动备份到云存储（S3、阿里云OSS、Google Cloud）
  - 数据版本控制和回滚机制
  - 定期备份验证和完整性检查
  - 灾难恢复和数据迁移工具

#### 📋 高级内容管理
- [ ] **内容生命周期管理**
  - 文章版本历史和变更追踪
  - 过期内容自动归档
  - 内容质量持续监控
  - 死链检测和自动修复

- [ ] **用户交互功能**
  - 文章评分和评论系统
  - 用户收藏夹和阅读列表
  - 个人笔记和标注功能
  - 阅读进度和状态追踪

### 🎯 第四阶段：用户体验提升

#### 📱 界面和体验优化
- [ ] **主题和样式系统**
  - 深色/浅色主题动态切换
  - 多种阅读模式（专注、列表、卡片）
  - 自定义字体、大小、行距设置
  - 移动端体验优化

- [ ] **离线和缓存功能**
  - 离线阅读支持和文章缓存
  - Service Worker实现渐进式Web应用
  - 智能预加载和懒加载
  - 网络状态感知和优化

#### 🔔 通知和订阅系统
- [ ] **多渠道通知**
  - 邮件订阅和定期文章推送
  - 微信企业号/钉钉机器人集成
  - Webhook回调和API通知
  - 个性化通知设置和频率控制

- [ ] **内容分发**
  - 生成个人定制RSS feed
  - 社交媒体自动分享
  - 文章导出为PDF、EPUB格式
  - 知识库和文档生成

### 🔧 第五阶段：技术工具和监控

#### 📊 监控和分析平台
- [ ] **全面监控系统**
  - 实时访问统计和用户行为分析
  - API性能监控和错误追踪
  - 爬虫效率和成功率监控
  - 系统资源使用和性能优化

- [ ] **SEO和营销工具**
  - 自动生成sitemap和robots.txt
  - Meta标签和Open Graph优化
  - 搜索引擎收录状态监控
  - 网站速度和Core Web Vitals优化

#### 🛠️ 开发者工具增强
- [ ] **API和集成工具**
  - GraphQL API支持
  - Webhook和事件系统
  - 第三方应用集成SDK
  - API版本管理和文档自动生成

- [ ] **数据处理工具**
  - 批量数据操作和管理界面
  - 数据导入导出更多格式支持
  - 数据清洗和预处理工具
  - 数据分析和报表生成

### 🤝 第六阶段：社区和协作功能

#### 👥 社区建设
- [ ] **用户系统**
  - 用户注册、登录、个人资料管理
  - 用户权限和角色管理
  - 社交功能（关注、粉丝、动态）
  - 用户贡献积分和成就系统

- [ ] **内容协作**
  - 用户投稿和内容提交
  - 众包标签和分类
  - 内容审核和质量控制流程
  - 协作编辑和版本管理

## 🎯 优先级建议

### 🥇 高优先级（建议立即实现）
1. **📊 趋势分析系统** - 提供数据价值洞察
2. **🔍 高级搜索功能** - 提升用户体验
3. **📡 RSS聚合器** - 扩展内容来源
4. **🤖 AI摘要生成** - 提高内容可读性
5. **📱 主题切换功能** - 改善界面体验

### 🥈 中优先级（第二阶段实现）
1. **🔄 增量同步系统** - 提高数据管理效率
2. **📋 用户收藏功能** - 增强用户粘性
3. **🔔 通知推送系统** - 提高用户活跃度
4. **📊 访问统计分析** - 了解用户行为
5. **🌐 多语言支持** - 扩大用户群体

### 🥉 低优先级（长期规划）
1. **👥 用户系统和社区** - 构建用户生态
2. **📝 内容协作功能** - 用户生成内容
3. **🔧 高级开发者工具** - 面向开发者
4. **📈 商业化功能** - 盈利模式探索

## 💡 实现建议

### 技术栈推荐
- **前端增强**: React/Vue.js重构，支持PWA
- **后端扩展**: FastAPI + Celery异步任务队列
- **数据库升级**: PostgreSQL + Redis缓存
- **AI集成**: OpenAI API、本地LLM（如Ollama）
- **部署优化**: Kubernetes + 微服务架构

### 开发流程
1. **功能设计** - 详细需求分析和用户体验设计
2. **原型开发** - 快速原型和用户反馈收集
3. **迭代开发** - 敏捷开发和持续集成
4. **测试部署** - 自动化测试和分阶段部署
5. **用户反馈** - 数据驱动的功能优化

## 当前配置

项目已配置完整的开发和部署环境，包括：
- 完整的爬虫系统和数据处理
- RESTful API和现代化前端
- Docker容器化和多平台部署
- 详细的文档和使用指南