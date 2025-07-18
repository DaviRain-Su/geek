# WeChat Public Account Crawler

A Python-based crawler for extracting articles from WeChat public accounts (微信公众号).

## ✨ Features

- 🤖 Browser automation using Playwright to handle JavaScript-rendered content
- 📊 Structured data extraction (title, content, author, publish time, images)
- 💾 Flexible storage options (SQLite/MongoDB)
- 🔄 Proxy rotation support for avoiding rate limits
- 📈 Crawl job tracking and statistics
- 🚀 Async/await for efficient concurrent crawling
- 🎯 Web UI for database management (Mongo Express & Redis Commander)
- 📝 **Markdown Export** - Export articles to organized Markdown files with auto-tagging
- 🏷️ **Smart Classification** - AI-powered article categorization and tagging
- 📊 **Analytics Dashboard** - Comprehensive data analysis and visualization

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker Desktop (for Option A) or Homebrew (for Option B)

### Installation

1. **Clone the repository:**
```bash
cd /Users/davirian/dev/geek
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
uv pip install -r requirements.txt
playwright install chromium
```

4. **Set up databases (choose one option):**

   **Option A: Docker (Recommended) - One Command Setup**
   ```bash
   # Start MongoDB, Redis, and Web UIs with one command
   ./docker-services.sh start

   # Copy Docker-specific environment config
   cp .env.docker .env
   ```

   Services will be available at:
   - MongoDB: `mongodb://admin:wechat123@localhost:27017/`
   - Redis: `redis://:wechat123@localhost:6379/0`
   - Mongo Express (Web UI): http://localhost:8081 (admin/wechat123)
   - Redis Commander (Web UI): http://localhost:8082

   **Option B: Homebrew**
   ```bash
   # Install and start MongoDB & Redis
   ./start_services.sh
   cp .env.example .env
   ```

   **Option C: SQLite (No installation needed)**
   ```bash
   # Just copy the env file, SQLite will be created automatically
   cp .env.example .env
   ```

5. **Verify installation:**
```bash
python main.py stats
```

## 📖 Usage

### Basic Commands

```bash
# Method 1: Get series/album articles (BEST for series articles like "日报 #123")
python main.py series "https://mp.weixin.qq.com/s/7gWx7Lj8AOOKnD7KscgNMg"
python main.py series "https://mp.weixin.qq.com/s/..." --max-articles 100

# Method 2: Get history articles from a single article
python main.py history "https://mp.weixin.qq.com/s/7gWx7Lj8AOOKnD7KscgNMg"
python main.py history "https://mp.weixin.qq.com/s/..." --max-articles 50

# Method 3: Discover articles starting from a single article
python main.py discover "https://mp.weixin.qq.com/s/7gWx7Lj8AOOKnD7KscgNMg"
python main.py discover "https://mp.weixin.qq.com/s/..." --max-articles 20 --use-proxy

# Method 4: Crawl by account name (may be blocked by anti-crawling)
python main.py crawl "公众号名称"
python main.py crawl "公众号名称" --max-articles 10 --use-proxy

# Method 5: Crawl a single article
python main.py article "https://mp.weixin.qq.com/s/..."

# View statistics
python main.py stats

# Export to Markdown (NEW!)
python main.py export --format markdown
python main.py export --format markdown --limit 100 --output my_articles

# Export to Simple List (NEW!)
python main.py export --format simple
python main.py export --format simple --limit 100 --output my_list.md

# Export to Obsidian (NEW!)
./scripts/export_obsidian.sh                    # Export index only
./scripts/export_obsidian.sh --full             # Export all articles
./scripts/export_obsidian.sh --full --limit 100 # Export first 100 articles
```

### 📝 Export Options

#### 1. **Complete Markdown Export**
Export all articles to organized Markdown files with automatic categorization and tagging:

```bash
# Quick export using script
./scripts/export_markdown.sh

# Export with custom options
./scripts/export_markdown.sh -l 100 -o ~/Documents/articles

# Export using CLI
python3 main.py export --format markdown --limit 50 --no-author
```

**Features:**
- 🏷️ **Auto-tagging** - Smart tags based on content analysis
- 📂 **Smart categorization** - Automatic classification by topic
- 📊 **Quality analysis** - Article quality scoring and insights
- 📅 **Multiple views** - Organized by category, author, and date
- 🔍 **Rich metadata** - Comprehensive article information

#### 2. **Simple List Export**
Export all articles to a single Markdown file with simple format: `[title](url) -- description`

```bash
# Export all articles to single file
python3 main.py export --format simple

# Quick export using script
./scripts/export_simple.sh

# Export with custom options
./scripts/export_simple.sh -l 1000 -o my_articles.md
```

**Features:**
- 📋 **Single file** - All articles in one convenient file
- 🔗 **Clickable links** - Direct links to original articles
- 📝 **Concise format** - Title, link, and brief description
- 📊 **Smart sorting** - Sort by date, title, or author
- 👥 **Group by author** - Optional grouping by author or date

#### 3. **Obsidian Export**
Export all articles to Obsidian knowledge management system with rich metadata and linking:

```bash
# Export index only (quick start)
./scripts/export_obsidian.sh

# Export all articles with full features
./scripts/export_obsidian.sh --full

# Export with custom options
./scripts/export_obsidian.sh --full --limit 100 --vault ~/Documents/MyVault
```

**Features:**
- 🏷️ **Smart tagging** - Auto-categorization by topic, difficulty, quality
- 🔗 **Wikilinks** - Connected knowledge graph with bidirectional links
- 📊 **Dataview queries** - Dynamic content filtering and analytics
- 📝 **YAML frontmatter** - Rich metadata for each article
- 👥 **Author notes** - Dedicated pages for each author with statistics
- 🎨 **Templates** - Consistent formatting and structure
- 📱 **Mobile ready** - Works perfectly with Obsidian mobile apps

**Export Guides:**
- [Complete Markdown Export Guide](MARKDOWN_EXPORT_GUIDE.md)
- [Simple List Export Guide](SIMPLE_EXPORT_GUIDE.md)
- [Obsidian Export Guide](OBSIDIAN_EXPORT_GUIDE.md)

### Docker Service Management

```bash
# Service commands
./docker-services.sh start     # Start all services
./docker-services.sh stop      # Stop all services
./docker-services.sh status    # Check service status
./docker-services.sh logs      # View logs
./docker-services.sh restart   # Restart services

# Database access
./docker-services.sh shell     # MongoDB shell
./docker-services.sh redis-cli # Redis CLI

# Cleanup (WARNING: removes all data)
./docker-services.sh clean
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# MongoDB settings
MONGODB_URI=mongodb://admin:wechat123@localhost:27017/  # For Docker
MONGODB_DB=wechat_crawler

# Redis settings
REDIS_URL=redis://:wechat123@localhost:6379/0  # For Docker

# Crawler settings
CRAWL_DELAY=5  # Seconds between requests
MAX_RETRIES=3
TIMEOUT=30

# Proxy settings
USE_PROXY=false
PROXY_LIST_FILE=proxies.txt
```

### Proxy Configuration

To use proxy rotation:

1. Create `proxies.txt` file:
```
host:port
http://username:password@host:port
socks5://host:port
```

2. Run with proxy flag:
```bash
python main.py crawl "公众号名称" --use-proxy
```

## 📊 Data Management

### Web Interfaces

When using Docker, access these UIs:
- **Mongo Express**: http://localhost:8081 - Browse and manage MongoDB data
- **Redis Commander**: http://localhost:8082 - Monitor Redis cache

### Crawling Strategies

**🎯 `series` command** - Perfect for series articles like "日报 #123", "Weekly #45":
- Automatically detects article series/albums
- Uses navigation links (上一篇/下一篇) to discover all episodes
- Analyzes title patterns to identify series
- Accesses album directory if available
- Best for: Newsletter series, daily reports, numbered articles

**📚 `history` command** - General purpose history article discovery:
- Searches account profile and history pages
- Extracts links from article content
- Mines JavaScript data for recommendations
- Best for: General account exploration

**🔍 `discover` command** - Smart article discovery:
- Multi-strategy content discovery
- Scrolling and dynamic loading
- Best for: Mixed content exploration

### Data Structure

Articles are stored with the following fields:
- `url`: Article URL
- `title`: Article title
- `content`: Full text content
- `author`: Author name
- `account_name`: WeChat account name
- `publish_time`: Publication timestamp
- `images`: List of image URLs
- `cover_image`: Cover image URL
- `read_count`, `like_count`: Engagement metrics
- `raw_html`: Original HTML (for reprocessing)
- `crawl_time`: When the article was crawled

## 🏗️ Project Structure

```
├── crawler/          # Browser automation and crawling logic
│   ├── browser.py    # Playwright browser management
│   ├── wechat.py     # WeChat-specific crawling
│   └── article_discovery.py # Article discovery from single article
├── parser/           # HTML parsing and data extraction
│   └── article.py    # Article content parser
├── storage/          # Database models and operations
│   ├── models.py     # Data models
│   └── database.py   # Database operations
├── proxy/            # Proxy rotation management
│   └── manager.py    # Proxy pool manager
├── utils/            # Configuration and logging
├── docker-services.sh # Docker management script
├── docker-compose.yml # Docker services configuration
└── main.py           # CLI entry point
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using port 27017 (MongoDB)
   lsof -i :27017

   # Check what's using port 6379 (Redis)
   lsof -i :6379
   ```

2. **Docker not running**
   ```bash
   # Start Docker Desktop on macOS
   open -a Docker
   ```

3. **Browser automation fails**
   ```bash
   # Reinstall Playwright browsers
   playwright install chromium --force
   ```

4. **Connection errors**
   ```bash
   # Verify services are running
   ./docker-services.sh status
   ```

## 🚨 Important Notes

1. **Rate Limiting**: WeChat implements strict rate limiting. The default 5-second delay between requests is recommended.
2. **Anti-Crawling**: The crawler uses stealth techniques but detection is still possible.
3. **Legal Compliance**: Ensure you have permission to crawl content and comply with WeChat's terms of service.
4. **Resource Usage**: Browser automation can be resource-intensive. Monitor CPU and memory usage.

## 🔮 Future Enhancements

- [ ] Distributed crawling with Celery task_queue
- [ ] REST API for programmatic access
- [ ] Advanced anti-detection strategies
- [ ] Export to multiple formats (CSV, JSON, Excel)
- [ ] Scheduled crawling with cron integration
- [ ] Article deduplication and versioning

## 📄 License

This project is for educational purposes. Ensure compliance with all applicable laws and terms of service when using.
