import asyncio
import re
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from playwright.async_api import Page
from crawler.browser import CrawlerBase
from utils.logger import logger


class ArticleDiscovery(CrawlerBase):
    """Discover articles from a WeChat account starting from a single article"""
    
    def __init__(self):
        super().__init__()
        self.discovered_urls: Set[str] = set()
        self.account_name = None
        
    async def discover_from_article(self, start_url: str, max_articles: Optional[int] = None) -> List[str]:
        """
        Discover articles from a WeChat account starting from a single article
        
        Args:
            start_url: URL of a WeChat article to start from
            max_articles: Maximum number of articles to discover
            
        Returns:
            List of discovered article URLs
        """
        discovered_articles = []
        
        try:
            # Start with the initial article
            self.discovered_urls.add(start_url)
            discovered_articles.append(start_url)
            
            logger.info(f"Starting discovery from: {start_url}")
            
            # Extract account information from the first article
            await self._extract_account_info(start_url)
            
            # Discover more articles through various methods
            await self._discover_through_profile(start_url, discovered_articles, max_articles)
            await self._discover_through_related_links(start_url, discovered_articles, max_articles)
            await self._discover_through_navigation(start_url, discovered_articles, max_articles)
            
            logger.info(f"Discovery complete. Found {len(discovered_articles)} articles")
            return discovered_articles
            
        except Exception as e:
            logger.error(f"Failed to discover articles: {str(e)}")
            return discovered_articles
    
    async def _extract_account_info(self, article_url: str):
        """Extract account information from the article"""
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(article_url, wait_until="networkidle", timeout=30000)
            
            # Extract account name and info
            account_selectors = [
                'span#js_name',
                'strong#profileBt a',
                'a#js_name',
                '.profile_nickname'
            ]
            
            for selector in account_selectors:
                element = await page.query_selector(selector)
                if element:
                    self.account_name = await element.get_text_content()
                    logger.info(f"Detected account: {self.account_name}")
                    break
            
        except Exception as e:
            logger.warning(f"Failed to extract account info: {str(e)}")
        finally:
            await page.close()
    
    async def _discover_through_profile(self, start_url: str, discovered_articles: List[str], max_articles: Optional[int]):
        """Discover articles through the account profile page"""
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="networkidle", timeout=30000)
            
            # Look for profile link
            profile_selectors = [
                'a#js_name',
                'strong#profileBt a',
                'a[href*="profile"]'
            ]
            
            profile_url = None
            for selector in profile_selectors:
                element = await page.query_selector(selector)
                if element:
                    href = await element.get_attribute('href')
                    if href:
                        profile_url = urljoin(start_url, href)
                        break
            
            if profile_url:
                logger.info(f"Found profile URL: {profile_url}")
                await self._crawl_profile_page(profile_url, discovered_articles, max_articles)
            
        except Exception as e:
            logger.warning(f"Failed to discover through profile: {str(e)}")
        finally:
            await page.close()
    
    async def _crawl_profile_page(self, profile_url: str, discovered_articles: List[str], max_articles: Optional[int]):
        """Crawl the account profile page for article links"""
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(profile_url, wait_until="networkidle", timeout=30000)
            
            # Look for article links
            await self._extract_article_links_from_page(page, discovered_articles, max_articles)
            
            # Try to load more articles by scrolling
            await self._scroll_and_load_more(page, discovered_articles, max_articles)
            
        except Exception as e:
            logger.warning(f"Failed to crawl profile page: {str(e)}")
        finally:
            await page.close()
    
    async def _discover_through_related_links(self, start_url: str, discovered_articles: List[str], max_articles: Optional[int]):
        """Discover articles through related links in the article content"""
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="networkidle", timeout=30000)
            
            # Extract all WeChat article links from the content
            await self._extract_article_links_from_page(page, discovered_articles, max_articles)
            
        except Exception as e:
            logger.warning(f"Failed to discover through related links: {str(e)}")
        finally:
            await page.close()
    
    async def _discover_through_navigation(self, start_url: str, discovered_articles: List[str], max_articles: Optional[int]):
        """Discover articles through navigation elements like 'previous article' links"""
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="networkidle", timeout=30000)
            
            # Look for navigation links
            navigation_selectors = [
                'a[href*="mp.weixin.qq.com"]:contains("上一篇")',
                'a[href*="mp.weixin.qq.com"]:contains("下一篇")',
                'a[href*="mp.weixin.qq.com"]:contains("往期")',
                'a[href*="mp.weixin.qq.com"]:contains("更多")',
                '.js_previous_article',
                '.js_next_article'
            ]
            
            for selector in navigation_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href and self._is_valid_wechat_article(href):
                            if href not in self.discovered_urls:
                                self.discovered_urls.add(href)
                                discovered_articles.append(href)
                                logger.info(f"Found navigation link: {href}")
                                
                                if max_articles and len(discovered_articles) >= max_articles:
                                    return
                except:
                    continue
            
        except Exception as e:
            logger.warning(f"Failed to discover through navigation: {str(e)}")
        finally:
            await page.close()
    
    async def _extract_article_links_from_page(self, page: Page, discovered_articles: List[str], max_articles: Optional[int]):
        """Extract WeChat article links from the current page"""
        try:
            # Find all WeChat article links
            links = await page.query_selector_all('a[href*="mp.weixin.qq.com"]')
            
            for link in links:
                href = await link.get_attribute('href')
                if href and self._is_valid_wechat_article(href):
                    if href not in self.discovered_urls:
                        self.discovered_urls.add(href)
                        discovered_articles.append(href)
                        logger.info(f"Discovered article: {href}")
                        
                        if max_articles and len(discovered_articles) >= max_articles:
                            return
            
        except Exception as e:
            logger.warning(f"Failed to extract article links: {str(e)}")
    
    async def _scroll_and_load_more(self, page: Page, discovered_articles: List[str], max_articles: Optional[int]):
        """Scroll to load more articles and extract links"""
        try:
            prev_count = len(discovered_articles)
            
            for _ in range(5):  # Try scrolling 5 times
                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Extract new links
                await self._extract_article_links_from_page(page, discovered_articles, max_articles)
                
                # Check if we found new articles
                if len(discovered_articles) == prev_count:
                    break
                    
                prev_count = len(discovered_articles)
                
                if max_articles and len(discovered_articles) >= max_articles:
                    break
            
        except Exception as e:
            logger.warning(f"Failed to scroll and load more: {str(e)}")
    
    def _is_valid_wechat_article(self, url: str) -> bool:
        """Check if URL is a valid WeChat article"""
        try:
            if not url or 'mp.weixin.qq.com' not in url:
                return False
            
            # Parse URL to check for article pattern
            parsed = urlparse(url)
            if '/s/' not in parsed.path and '/s?' not in parsed.query:
                return False
            
            # Skip certain types of URLs
            skip_patterns = [
                'action=profile',
                'action=follow',
                '__biz=',  # These are usually account pages, not articles
            ]
            
            for pattern in skip_patterns:
                if pattern in url:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_account_name(self) -> Optional[str]:
        """Get the detected account name"""
        return self.account_name