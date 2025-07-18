import random
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp
from pathlib import Path
from utils.config import settings
from utils.logger import logger


class ProxyInfo:
    """Information about a proxy"""
    def __init__(self, host: str, port: int, username: Optional[str] = None, password: Optional[str] = None, protocol: str = "http"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol
        self.last_used = None
        self.failure_count = 0
        self.success_count = 0
        self.is_alive = True
        
    def to_playwright_proxy(self) -> Dict[str, Any]:
        """Convert to Playwright proxy format"""
        proxy = {
            "server": f"{self.protocol}://{self.host}:{self.port}"
        }
        if self.username and self.password:
            proxy.update({
                "username": self.username,
                "password": self.password
            })
        return proxy
    
    def to_url(self) -> str:
        """Convert to proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def reliability_score(self) -> float:
        """Calculate reliability score based on success/failure ratio"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5  # Neutral for new proxies
        return self.success_count / total


class ProxyManager:
    """Manages proxy rotation for crawling"""
    
    def __init__(self):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.min_rotation_interval = 60  # seconds
        self.max_failures = 5
        self.test_url = "https://weixin.sogou.com/"
        
    async def initialize(self):
        """Initialize proxy list"""
        if not settings.use_proxy:
            logger.info("Proxy usage disabled in settings")
            return
        
        # Load proxies from file
        await self._load_proxies_from_file()
        
        # Test all proxies
        if self.proxies:
            await self._test_all_proxies()
            logger.info(f"Initialized {len(self.get_alive_proxies())} working proxies")
    
    async def _load_proxies_from_file(self):
        """Load proxies from file"""
        proxy_file = Path(settings.proxy_list_file)
        
        if not proxy_file.exists():
            logger.warning(f"Proxy file not found: {proxy_file}")
            return
        
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse proxy format: protocol://username:password@host:port
                    # or simple format: host:port
                    proxy_info = self._parse_proxy_line(line)
                    if proxy_info:
                        self.proxies.append(proxy_info)
            
            logger.info(f"Loaded {len(self.proxies)} proxies from file")
            
        except Exception as e:
            logger.error(f"Failed to load proxies: {str(e)}")
    
    def _parse_proxy_line(self, line: str) -> Optional[ProxyInfo]:
        """Parse a proxy line from file"""
        try:
            # Full format with auth
            if '@' in line:
                if '://' in line:
                    protocol, rest = line.split('://', 1)
                else:
                    protocol = 'http'
                    rest = line
                
                auth, address = rest.split('@', 1)
                username, password = auth.split(':', 1)
                host, port = address.split(':', 1)
                
                return ProxyInfo(
                    host=host,
                    port=int(port),
                    username=username,
                    password=password,
                    protocol=protocol
                )
            
            # Simple format
            else:
                if '://' in line:
                    protocol, address = line.split('://', 1)
                else:
                    protocol = 'http'
                    address = line
                
                host, port = address.split(':', 1)
                
                return ProxyInfo(
                    host=host,
                    port=int(port),
                    protocol=protocol
                )
                
        except Exception as e:
            logger.warning(f"Failed to parse proxy line '{line}': {str(e)}")
            return None
    
    async def _test_all_proxies(self):
        """Test all proxies concurrently"""
        tasks = [self._test_proxy(proxy) for proxy in self.proxies]
        await asyncio.gather(*tasks)
    
    async def _test_proxy(self, proxy: ProxyInfo) -> bool:
        """Test if a proxy is working"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy.to_url(),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        proxy.is_alive = True
                        proxy.success_count += 1
                        logger.debug(f"Proxy {proxy.host}:{proxy.port} is alive")
                        return True
                    else:
                        proxy.is_alive = False
                        proxy.failure_count += 1
                        logger.debug(f"Proxy {proxy.host}:{proxy.port} returned status {response.status}")
                        return False
                        
        except Exception as e:
            proxy.is_alive = False
            proxy.failure_count += 1
            logger.debug(f"Proxy {proxy.host}:{proxy.port} failed: {str(e)}")
            return False
    
    def get_alive_proxies(self) -> List[ProxyInfo]:
        """Get list of alive proxies"""
        return [p for p in self.proxies if p.is_alive and p.failure_count < self.max_failures]
    
    def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get next proxy in rotation"""
        if not settings.use_proxy:
            return None
        
        alive_proxies = self.get_alive_proxies()
        if not alive_proxies:
            logger.warning("No alive proxies available")
            return None
        
        # Sort by reliability score (descending) and last used time
        sorted_proxies = sorted(
            alive_proxies,
            key=lambda p: (p.reliability_score, p.last_used is None, p.last_used or datetime.min),
            reverse=True
        )
        
        # Get proxies that haven't been used recently
        now = datetime.now()
        available_proxies = [
            p for p in sorted_proxies
            if p.last_used is None or (now - p.last_used).seconds >= self.min_rotation_interval
        ]
        
        if not available_proxies:
            # If all proxies were used recently, use the one with oldest last_used
            proxy = sorted_proxies[-1]
        else:
            # Use the most reliable available proxy
            proxy = available_proxies[0]
        
        proxy.last_used = now
        return proxy
    
    def get_random_proxy(self) -> Optional[ProxyInfo]:
        """Get a random alive proxy"""
        if not settings.use_proxy:
            return None
        
        alive_proxies = self.get_alive_proxies()
        if not alive_proxies:
            return None
        
        return random.choice(alive_proxies)
    
    def mark_proxy_success(self, proxy: ProxyInfo):
        """Mark a proxy as successful"""
        proxy.success_count += 1
        proxy.failure_count = max(0, proxy.failure_count - 1)  # Reduce failure count
        proxy.is_alive = True
        logger.debug(f"Proxy {proxy.host}:{proxy.port} marked as successful")
    
    def mark_proxy_failure(self, proxy: ProxyInfo):
        """Mark a proxy as failed"""
        proxy.failure_count += 1
        
        if proxy.failure_count >= self.max_failures:
            proxy.is_alive = False
            logger.warning(f"Proxy {proxy.host}:{proxy.port} marked as dead after {self.max_failures} failures")
        else:
            logger.debug(f"Proxy {proxy.host}:{proxy.port} failed {proxy.failure_count} times")
    
    async def refresh_proxy_list(self):
        """Refresh proxy list by retesting all proxies"""
        logger.info("Refreshing proxy list...")
        
        # Reset failure counts for dead proxies to give them another chance
        for proxy in self.proxies:
            if not proxy.is_alive and proxy.failure_count >= self.max_failures:
                proxy.failure_count = self.max_failures - 1
                proxy.is_alive = True
        
        # Retest all proxies
        await self._test_all_proxies()
        
        alive_count = len(self.get_alive_proxies())
        logger.info(f"Proxy refresh complete. {alive_count} alive proxies")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        alive_proxies = self.get_alive_proxies()
        
        return {
            "total_proxies": len(self.proxies),
            "alive_proxies": len(alive_proxies),
            "dead_proxies": len(self.proxies) - len(alive_proxies),
            "average_reliability": sum(p.reliability_score for p in alive_proxies) / len(alive_proxies) if alive_proxies else 0,
            "proxies": [
                {
                    "host": p.host,
                    "port": p.port,
                    "is_alive": p.is_alive,
                    "reliability_score": p.reliability_score,
                    "success_count": p.success_count,
                    "failure_count": p.failure_count
                }
                for p in self.proxies
            ]
        }