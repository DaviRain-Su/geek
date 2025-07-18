#!/bin/bash

# Docker services management script for WeChat Crawler

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not installed. Please install Docker Desktop for Mac first:${NC}"
        echo "https://www.docker.com/products/docker-desktop/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
        exit 1
    fi
}

# Display usage
usage() {
    echo -e "${BLUE}WeChat Crawler Docker Services Manager${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show service status"
    echo "  logs      - Show service logs"
    echo "  clean     - Stop services and remove data"
    echo "  shell     - Open MongoDB shell"
    echo "  redis-cli - Open Redis CLI"
    echo "  help      - Show this help message"
    echo ""
    echo "Web UIs:"
    echo "  Mongo Express: http://localhost:8081 (admin/wechat123)"
    echo "  Redis Commander: http://localhost:8082"
}

# Start services
start_services() {
    echo -e "${YELLOW}🚀 Starting WeChat Crawler services...${NC}"
    
    # Copy Docker env file if not exists
    if [ ! -f .env ]; then
        cp .env.docker .env
        echo -e "${GREEN}✅ Created .env file with Docker configuration${NC}"
    fi
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be healthy
    echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
    
    # Wait for MongoDB
    echo -n "MongoDB: "
    for i in {1..30}; do
        if docker exec wechat_mongodb mongosh --quiet --eval "db.version()" &>/dev/null; then
            echo -e "${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Wait for Redis
    echo -n "Redis: "
    for i in {1..30}; do
        if docker exec wechat_redis redis-cli -a wechat123 ping &>/dev/null; then
            echo -e "${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "\n${GREEN}✨ All services started successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service URLs:${NC}"
    echo "  - MongoDB: mongodb://admin:wechat123@localhost:27017/"
    echo "  - Redis: redis://:wechat123@localhost:6379"
    echo "  - Mongo Express: http://localhost:8081 (admin/wechat123)"
    echo "  - Redis Commander: http://localhost:8082"
}

# Stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping WeChat Crawler services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Restart services
restart_services() {
    stop_services
    echo ""
    start_services
}

# Show status
show_status() {
    echo -e "${BLUE}📊 WeChat Crawler Service Status${NC}"
    echo ""
    docker-compose ps
    echo ""
    
    # Check MongoDB connection
    echo -n "MongoDB connection: "
    if docker exec wechat_mongodb mongosh --quiet --eval "db.version()" &>/dev/null; then
        echo -e "${GREEN}✅ Connected${NC}"
        # Show database stats
        docker exec wechat_mongodb mongosh wechat_crawler --quiet --eval "db.stats().dataSize" | xargs -I {} echo "  Database size: {} bytes"
    else
        echo -e "${RED}❌ Not connected${NC}"
    fi
    
    # Check Redis connection
    echo -n "Redis connection: "
    if docker exec wechat_redis redis-cli -a wechat123 ping &>/dev/null; then
        echo -e "${GREEN}✅ Connected${NC}"
        # Show Redis info
        docker exec wechat_redis redis-cli -a wechat123 INFO server | grep redis_version | xargs -I {} echo "  {}"
    else
        echo -e "${RED}❌ Not connected${NC}"
    fi
}

# Show logs
show_logs() {
    echo -e "${BLUE}📋 Showing service logs (Ctrl+C to exit)${NC}"
    docker-compose logs -f --tail=50
}

# Clean everything
clean_all() {
    echo -e "${RED}⚠️  WARNING: This will remove all data!${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker-compose down -v
        echo -e "${GREEN}✅ All services stopped and data removed${NC}"
    else
        echo "Cancelled"
    fi
}

# MongoDB shell
mongo_shell() {
    echo -e "${BLUE}🔧 Opening MongoDB shell...${NC}"
    echo "Use 'exit' to quit"
    docker exec -it wechat_mongodb mongosh -u admin -p wechat123 --authenticationDatabase admin wechat_crawler
}

# Redis CLI
redis_cli() {
    echo -e "${BLUE}🔧 Opening Redis CLI...${NC}"
    echo "Use 'exit' to quit"
    docker exec -it wechat_redis redis-cli -a wechat123
}

# Main script
check_docker

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_all
        ;;
    shell)
        mongo_shell
        ;;
    redis-cli)
        redis_cli
        ;;
    help)
        usage
        ;;
    *)
        usage
        ;;
esac