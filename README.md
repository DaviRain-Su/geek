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
```

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
