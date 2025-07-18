# Local Services Setup Guide for Mac

## 1. MongoDB Installation and Setup

### Install MongoDB using Homebrew:
```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Verify MongoDB is running
mongosh --eval "db.version()"
```

### Alternative: Run MongoDB with Docker:
```bash
# Pull and run MongoDB container
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:latest

# Check if running
docker ps | grep mongodb
```

## 2. Redis Installation and Setup

### Install Redis using Homebrew:
```bash
# Install Redis
brew install redis

# Start Redis service
brew services start redis

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### Alternative: Run Redis with Docker:
```bash
# Pull and run Redis container
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:latest

# Check if running
docker ps | grep redis
```

## 3. Quick Setup Script

Create a file `start_services.sh`:
```bash
#!/bin/bash

echo "Starting local services..."

# Start MongoDB
if command -v mongod &> /dev/null; then
    brew services start mongodb-community
    echo "✅ MongoDB started"
else
    echo "❌ MongoDB not installed. Run: brew install mongodb-community"
fi

# Start Redis
if command -v redis-server &> /dev/null; then
    brew services start redis
    echo "✅ Redis started"
else
    echo "❌ Redis not installed. Run: brew install redis"
fi

# Check services
echo -e "\n📊 Service Status:"
brew services list | grep -E "mongodb-community|redis"
```

Make it executable:
```bash
chmod +x start_services.sh
./start_services.sh
```

## 4. Using SQLite Instead (No Installation Required)

If you prefer not to install MongoDB/Redis, the crawler can use SQLite which requires no installation:

Update your `.env` file:
```env
# Use SQLite instead (no installation needed)
USE_SQLITE=true

# MongoDB and Redis URLs (not used when USE_SQLITE=true)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=wechat_crawler
REDIS_URL=redis://localhost:6379/0
```

## 5. Verify Services

### Check MongoDB:
```bash
# Using mongosh
mongosh --eval "db.serverStatus().version"

# Or using connection string
mongosh "mongodb://localhost:27017/" --eval "db.version()"
```

### Check Redis:
```bash
# Test Redis connection
redis-cli ping

# Get Redis info
redis-cli INFO server | grep redis_version
```

## 6. Stop Services When Not Needed

```bash
# Stop MongoDB
brew services stop mongodb-community

# Stop Redis  
brew services stop redis

# List all services
brew services list
```

## 7. Docker Compose Option (All Services at Once)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:latest
    container_name: wechat_mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=wechat_crawler

  redis:
    image: redis:latest
    container_name: wechat_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mongodb_data:
  redis_data:
```

Run with:
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

## Troubleshooting

### MongoDB Issues:
```bash
# Check MongoDB log
tail -f /usr/local/var/log/mongodb/mongo.log

# Reset MongoDB
brew services stop mongodb-community
rm -rf /usr/local/var/mongodb
brew services start mongodb-community
```

### Redis Issues:
```bash
# Check Redis config
redis-cli CONFIG GET dir

# Test Redis
redis-cli SET test "hello"
redis-cli GET test
```

### Port Already in Use:
```bash
# Find process using port 27017 (MongoDB)
lsof -i :27017

# Find process using port 6379 (Redis)
lsof -i :6379

# Kill process
kill -9 <PID>
```