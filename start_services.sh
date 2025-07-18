#!/bin/bash

echo "🚀 Starting local services for WeChat Crawler..."

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew not installed. Please install Homebrew first:${NC}"
    echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Start MongoDB
echo -e "\n${YELLOW}MongoDB:${NC}"
if command -v mongod &> /dev/null; then
    if brew services start mongodb-community 2>/dev/null; then
        echo -e "${GREEN}✅ MongoDB started successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  MongoDB might already be running${NC}"
    fi
    
    # Test MongoDB connection
    if mongosh --quiet --eval "db.version()" &>/dev/null; then
        echo -e "${GREEN}✅ MongoDB connection verified${NC}"
    else
        echo -e "${RED}❌ Cannot connect to MongoDB${NC}"
    fi
else
    echo -e "${RED}❌ MongoDB not installed${NC}"
    echo "To install: brew tap mongodb/brew && brew install mongodb-community"
fi

# Start Redis
echo -e "\n${YELLOW}Redis:${NC}"
if command -v redis-server &> /dev/null; then
    if brew services start redis 2>/dev/null; then
        echo -e "${GREEN}✅ Redis started successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis might already be running${NC}"
    fi
    
    # Test Redis connection
    if redis-cli ping | grep -q PONG; then
        echo -e "${GREEN}✅ Redis connection verified${NC}"
    else
        echo -e "${RED}❌ Cannot connect to Redis${NC}"
    fi
else
    echo -e "${RED}❌ Redis not installed${NC}"
    echo "To install: brew install redis"
fi

# Show service status
echo -e "\n${YELLOW}📊 Service Status:${NC}"
brew services list | grep -E "mongodb-community|redis" | while read line; do
    if echo "$line" | grep -q "started"; then
        echo -e "${GREEN}$line${NC}"
    else
        echo -e "${RED}$line${NC}"
    fi
done

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
fi

echo -e "\n${GREEN}✨ Setup complete!${NC}"
echo -e "\nYou can now run:"
echo -e "${YELLOW}python main.py stats${NC} - to verify database connection"
echo -e "${YELLOW}python main.py crawl \"公众号名称\"${NC} - to start crawling"