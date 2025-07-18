import asyncio
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import quote, unquote
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from crawler.browser import CrawlerBase
from parser.article import ArticleParser
from storage.models import Article
from utils.logger import logger
from utils.config import settings


class WeChatCrawler(CrawlerBase):
    """WeChat public account article crawler"""
    
    def __init__(self):
        super().__init__()
        self.parser = ArticleParser()
        
    async def crawl_account(self, account_name: str, max_articles: Optional[int] = None) -> List[Article]:
        """
        Crawl articles from a WeChat public account
        
        Args:
            account_name: The name of the WeChat public account
            max_articles: Maximum number of articles to crawl (None for all)
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            # Search for the account
            account_url = await self._search_account(account_name)
            if not account_url:
                logger.error(f"Account '{account_name}' not found")
                return articles
            
            # Get article list
            article_urls = await self._get_article_list(account_url, max_articles)
            logger.info(f"Found {len(article_urls)} articles for account '{account_name}'")
            
            # Crawl each article
            for i, url in enumerate(article_urls):
                try:
                    logger.info(f"Crawling article {i+1}/{len(article_urls)}: {url}")
                    article = await self._crawl_article(url)
                    if article:
                        articles.append(article)
                    
                    # Delay between requests
                    await asyncio.sleep(settings.crawl_delay)
                    
                except Exception as e:
                    logger.error(f"Failed to crawl article {url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to crawl account '{account_name}': {str(e)}")
            
        return articles
    
    async def crawl_article(self, article_url: str) -> Optional[Article]:
        """
        Crawl a single WeChat article
        
        Args:
            article_url: URL of the article
            
        Returns:
            Article object or None if failed
        """
        return await self._crawl_article(article_url)
    
    async def _search_account(self, account_name: str) -> Optional[str]:
        """Search for WeChat public account and return its URL"""
        page = await self.browser_manager.new_page()
        
        try:
            # Use WeChat search
            search_url = f"https://weixin.sogou.com/weixin?type=1&query={quote(account_name)}"
            logger.info(f"Searching for account at: {search_url}")
            
            # Navigate to search page
            response = await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            logger.info(f"Search page response status: {response.status}")
            
            # Wait a bit for page to load
            await page.wait_for_timeout(3000)
            
            # Take screenshot for debugging
            await page.screenshot(path="logs/search_page.png")
            logger.info("Screenshot saved to logs/search_page.png")
            
            # Try multiple selectors for search results
            selectors_to_try = [
                ".news-list",
                ".results",
                "#sogou_vr_11002301_box_0",
                ".news-box",
                ".sp-box"
            ]
            
            result_found = False
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found search results with selector: {selector}")
                    result_found = True
                    break
                except:
                    logger.debug(f"Selector {selector} not found")
                    continue
            
            if not result_found:
                logger.warning("No search results container found, trying alternative approach")
                # Get page content for debugging
                content = await page.content()
                with open("logs/search_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("Page content saved to logs/search_page.html")
                
                # Check if there's a CAPTCHA or anti-bot protection
                if "验证码" in content or "captcha" in content.lower():
                    logger.error("CAPTCHA detected - manual intervention required")
                    return None
                
                # Try to find any links that might be WeChat accounts
                links = await page.query_selector_all("a[href*='mp.weixin.qq.com']")
                if links:
                    first_link = links[0]
                    href = await first_link.get_attribute("href")
                    logger.info(f"Found WeChat link directly: {href}")
                    return href
                
                return None
            
            # Look for the first result and try to get the account link
            result_selectors = [
                ".news-list li:first-child .txt-box h3 a",
                ".results .result:first-child h3 a",
                ".news-box:first-child h3 a",
                "h3 a[href*='mp.weixin.qq.com']"
            ]
            
            account_link = None
            for selector in result_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        href = await element.get_attribute("href")
                        if href and "mp.weixin.qq.com" in href:
                            account_link = href
                            logger.info(f"Found account link with selector {selector}: {href}")
                            break
                except:
                    continue
            
            if account_link:
                return account_link
            
            # If no direct link found, try clicking on the first result
            clickable_selectors = [
                ".news-list li:first-child .txt-box h3 a",
                ".results .result:first-child h3 a",
                ".news-box:first-child h3 a"
            ]
            
            for selector in clickable_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"Clicking on result with selector: {selector}")
                        await element.click()
                        
                        # Wait for navigation or new tab
                        await page.wait_for_timeout(3000)
                        
                        # Check if we're on a WeChat page now
                        current_url = page.url
                        if "mp.weixin.qq.com" in current_url:
                            logger.info(f"Navigated to WeChat page: {current_url}")
                            return current_url
                        
                        # Check for new tabs
                        if len(page.context.pages) > 1:
                            new_page = page.context.pages[-1]
                            new_url = new_page.url
                            if "mp.weixin.qq.com" in new_url:
                                logger.info(f"Found WeChat page in new tab: {new_url}")
                                await new_page.close()
                                return new_url
                            await new_page.close()
                        
                        break
                except Exception as e:
                    logger.debug(f"Failed to click with selector {selector}: {str(e)}")
                    continue
            
            logger.warning(f"Could not find account '{account_name}' in search results")
            return None
            
        except Exception as e:
            logger.error(f"Failed to search account: {str(e)}")
            return None
            
        finally:
            await page.close()
    
    async def _get_article_list(self, account_url: str, max_articles: Optional[int] = None) -> List[str]:
        """Get list of article URLs from account page"""
        page = await self.browser_manager.new_page()
        article_urls = []
        
        try:
            await page.goto(account_url, wait_until="networkidle", timeout=settings.timeout * 1000)
            
            # Different strategies to get article list
            # Strategy 1: Direct article links
            article_links = await page.query_selector_all("a[href*='mp.weixin.qq.com']")
            
            if not article_links:
                # Strategy 2: Try to find article list container
                await page.wait_for_selector(".weui_msg_card", timeout=10000)
                article_links = await page.query_selector_all(".weui_msg_card")
            
            for link in article_links:
                href = await link.get_attribute("href")
                if href and "mp.weixin.qq.com" in href:
                    article_urls.append(href)
                    if max_articles and len(article_urls) >= max_articles:
                        break
            
            # Try to load more articles if needed
            if (not max_articles or len(article_urls) < max_articles):
                await self._load_more_articles(page, article_urls, max_articles)
            
        except Exception as e:
            logger.error(f"Failed to get article list: {str(e)}")
            
        finally:
            await page.close()
            
        return article_urls[:max_articles] if max_articles else article_urls
    
    async def _load_more_articles(self, page: Page, article_urls: List[str], max_articles: Optional[int]):
        """Try to load more articles by scrolling"""
        prev_count = len(article_urls)
        
        for _ in range(5):  # Try scrolling 5 times
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Get new links
            new_links = await page.query_selector_all("a[href*='mp.weixin.qq.com']")
            
            for link in new_links:
                href = await link.get_attribute("href")
                if href and href not in article_urls and "mp.weixin.qq.com" in href:
                    article_urls.append(href)
                    if max_articles and len(article_urls) >= max_articles:
                        return
            
            # Check if we got new articles
            if len(article_urls) == prev_count:
                break
            prev_count = len(article_urls)
    
    async def _crawl_article(self, url: str) -> Optional[Article]:
        """Crawl a single article and extract data"""
        page = await self.browser_manager.new_page()
        
        try:
            logger.info(f"Navigating to article: {url}")
            
            # Navigate to article with longer timeout
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            if response.status != 200:
                logger.warning(f"Got status {response.status} for {url}")
                return None
            
            logger.info(f"Page loaded with status {response.status}")
            
            # Wait for page to load and take screenshot for debugging
            await page.wait_for_timeout(3000)
            await page.screenshot(path="logs/article_page.png")
            logger.info("Screenshot saved to logs/article_page.png")
            
            # Try multiple content selectors
            content_found = False
            content_selectors = ["#js_content", ".rich_media_content", "[data-role='content']", ".content"]
            
            for selector in content_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found content with selector: {selector}")
                    content_found = True
                    break
                except:
                    logger.debug(f"Selector {selector} not found")
                    continue
            
            if not content_found:
                logger.warning("No content selector found, trying to parse anyway")
                
                # Save page content for debugging
                html_content = await page.content()
                with open("logs/article_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Page HTML saved to logs/article_page.html")
                
                # Check if there's anti-bot protection
                if any(keyword in html_content.lower() for keyword in ["验证码", "captcha", "blocked", "forbidden"]):
                    logger.error("Anti-bot protection detected")
                    return None
            
            # Extract HTML content
            html_content = await page.content()
            
            # Get additional data from JavaScript variables
            js_data = await self._extract_js_data(page)
            logger.info(f"Extracted JS data: {js_data}")
            
            # Parse article
            article = self.parser.parse(html_content, url, js_data)
            
            if article:
                logger.info(f"Successfully parsed article: {article.title}")
            else:
                logger.warning("Article parsing returned None")
            
            return article
            
        except PlaywrightTimeout:
            logger.error(f"Timeout while crawling article: {url}")
            # Save page content for debugging even on timeout
            try:
                html_content = await page.content()
                with open("logs/timeout_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Timeout page content saved to logs/timeout_page.html")
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to crawl article {url}: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await page.close()
            
        return None
    
    async def _extract_js_data(self, page: Page) -> Dict[str, Any]:
        """Extract data from JavaScript variables in the page"""
        try:
            js_data = await page.evaluate("""
                () => {
                    const data = {};
                    
                    // Try to get various WeChat article variables
                    if (typeof msg_title !== 'undefined') data.title = msg_title;
                    if (typeof msg_desc !== 'undefined') data.description = msg_desc;
                    if (typeof msg_link !== 'undefined') data.link = msg_link;
                    if (typeof msg_source_url !== 'undefined') data.source_url = msg_source_url;
                    if (typeof publish_time !== 'undefined') data.publish_time = publish_time;
                    if (typeof user_name !== 'undefined') data.account_name = user_name;
                    if (typeof nickname !== 'undefined') data.nickname = nickname;
                    if (typeof round_head_img !== 'undefined') data.account_avatar = round_head_img;
                    if (typeof ori_head_img_url !== 'undefined') data.original_avatar = ori_head_img_url;
                    if (typeof msg_cdn_url !== 'undefined') data.cdn_url = msg_cdn_url;
                    if (typeof idx !== 'undefined') data.index = idx;
                    
                    return data;
                }
            """)
            return js_data
        except:
            return {}