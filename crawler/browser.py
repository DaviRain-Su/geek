import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from fake_useragent import UserAgent
from utils.config import settings
from utils.logger import logger


class BrowserManager:
    """Manages Playwright browser instances for crawling"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.ua = UserAgent()
        
    async def start(self, proxy: Optional[Dict[str, Any]] = None):
        """Start the browser with specified configuration"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser launch arguments
            launch_args = {
                "headless": settings.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-web-security",
                    "--disable-features=site-per-process",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu"
                ]
            }
            
            # Add proxy if provided
            if proxy:
                launch_args["proxy"] = proxy
            
            # Launch browser based on type
            if settings.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(**launch_args)
            elif settings.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**launch_args)
            else:
                self.browser = await self.playwright.webkit.launch(**launch_args)
            
            # Create context with mobile viewport
            context_options = {
                "viewport": {
                    "width": settings.viewport_width,
                    "height": settings.viewport_height
                },
                "user_agent": settings.user_agent or self._get_mobile_user_agent(),
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
                "permissions": ["geolocation"],
                "ignore_https_errors": True,
                "bypass_csp": True,
                "extra_http_headers": {
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Add stealth scripts to avoid detection
            await self._add_stealth_scripts()
            
            logger.info(f"Browser started successfully with type: {settings.browser_type}")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the browser and cleanup resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping browser: {str(e)}")
    
    async def new_page(self) -> Page:
        """Create a new page in the browser context"""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        page = await self.context.new_page()
        
        # Add page-level stealth
        await page.add_init_script("""
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
            
            // Override chrome property
            window.chrome = { runtime: {} };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)
        
        return page
    
    def _get_mobile_user_agent(self) -> str:
        """Get a mobile user agent string"""
        mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.40(0x18002831) NetType/WIFI Language/zh_CN",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.40.2560(0x28002837) NetType/WIFI Language/zh_CN",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.40.2560(0x28002837) NetType/WIFI Language/zh_CN"
        ]
        
        # Try to get WeChat-specific user agent
        try:
            return self.ua.random
        except:
            # Fallback to predefined mobile agents
            import random
            return random.choice(mobile_agents)
    
    async def _add_stealth_scripts(self):
        """Add stealth scripts to the context"""
        await self.context.add_init_script("""
            // Stealth mode scripts
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin' },
                    { name: 'Chrome PDF Viewer' },
                    { name: 'Native Client' }
                ]
            });
            
            // Mock WebGL vendor
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
        """)


class CrawlerBase:
    """Base class for crawlers with browser management"""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        
    async def __aenter__(self):
        await self.browser_manager.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser_manager.stop()
        
    async def crawl(self, *args, **kwargs):
        """To be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement crawl method")