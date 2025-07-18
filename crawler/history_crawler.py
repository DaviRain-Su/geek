import asyncio
import re
import json
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs
from playwright.async_api import Page
from crawler.browser import CrawlerBase
from utils.logger import logger


class HistoryCrawler(CrawlerBase):
    """专门用于获取微信公众号历史文章的爬虫"""
    
    def __init__(self):
        super().__init__()
        self.discovered_urls: Set[str] = set()
        self.account_info = {}
        
    async def get_history_articles(self, start_url: str, max_articles: Optional[int] = None) -> List[Dict]:
        """
        从单篇文章开始获取该公众号的历史文章
        
        Args:
            start_url: 起始文章URL
            max_articles: 最大获取数量
            
        Returns:
            历史文章列表
        """
        history_articles = []
        
        try:
            logger.info(f"开始从文章获取历史记录: {start_url}")
            
            # 方法1: 通过文章页面的账号链接
            account_articles = await self._get_articles_from_account_page(start_url, max_articles)
            history_articles.extend(account_articles)
            
            # 方法2: 通过文章内的相关链接
            related_articles = await self._get_articles_from_content_links(start_url, max_articles)
            history_articles.extend(related_articles)
            
            # 方法3: 通过JS变量中的推荐文章
            js_articles = await self._get_articles_from_js_data(start_url, max_articles)
            history_articles.extend(js_articles)
            
            # 去重
            unique_articles = self._deduplicate_articles(history_articles)
            
            logger.info(f"总共发现 {len(unique_articles)} 篇历史文章")
            return unique_articles[:max_articles] if max_articles else unique_articles
            
        except Exception as e:
            logger.error(f"获取历史文章失败: {str(e)}")
            return history_articles
    
    async def _get_articles_from_account_page(self, start_url: str, max_articles: Optional[int]) -> List[Dict]:
        """通过公众号页面获取文章列表"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            logger.info("页面加载完成，开始查找账号信息")
            
            # 提取账号信息
            await self._extract_account_info(page)
            
            # 查找账号主页链接
            account_link = await self._find_account_profile_link(page)
            
            if account_link:
                logger.info(f"找到账号主页链接: {account_link}")
                # 访问账号主页获取文章列表
                profile_articles = await self._crawl_account_profile(account_link, max_articles)
                articles.extend(profile_articles)
            
            # 查找"查看历史消息"链接
            history_link = await self._find_history_link(page)
            if history_link:
                logger.info(f"找到历史消息链接: {history_link}")
                history_articles = await self._crawl_history_page(history_link, max_articles)
                articles.extend(history_articles)
            
        except Exception as e:
            logger.error(f"从账号页面获取文章失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _get_articles_from_content_links(self, start_url: str, max_articles: Optional[int]) -> List[Dict]:
        """从文章内容中提取相关文章链接"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            
            # 查找所有微信文章链接
            links = await page.query_selector_all('a[href*="mp.weixin.qq.com"]')
            
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href and self._is_valid_article_url(href):
                        articles.append({
                            'url': href,
                            'title': text or '',
                            'source': 'content_link'
                        })
                        
                        if max_articles and len(articles) >= max_articles:
                            break
                            
                except Exception as e:
                    continue
            
            logger.info(f"从内容链接发现 {len(articles)} 篇文章")
            
        except Exception as e:
            logger.error(f"从内容链接获取文章失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _get_articles_from_js_data(self, start_url: str, max_articles: Optional[int]) -> List[Dict]:
        """从页面JS数据中提取相关文章"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            
            # 执行JS代码提取相关数据
            js_data = await page.evaluate("""
                () => {
                    const data = {};
                    
                    // 查找推荐文章
                    if (window.related_article_list) {
                        data.related_articles = window.related_article_list;
                    }
                    
                    // 查找同一作者的其他文章
                    if (window.author_articles) {
                        data.author_articles = window.author_articles;
                    }
                    
                    // 查找历史文章数据
                    if (window.history_articles) {
                        data.history_articles = window.history_articles;
                    }
                    
                    // 查找推荐阅读
                    const recommendElements = document.querySelectorAll('[data-role="recommend"]');
                    data.recommendations = [];
                    recommendElements.forEach(el => {
                        const link = el.querySelector('a[href*="mp.weixin.qq.com"]');
                        if (link) {
                            data.recommendations.push({
                                url: link.href,
                                title: link.textContent || el.textContent
                            });
                        }
                    });
                    
                    return data;
                }
            """)
            
            # 处理JS数据中的文章
            for key, article_list in js_data.items():
                if isinstance(article_list, list):
                    for article in article_list:
                        if isinstance(article, dict) and 'url' in article:
                            articles.append({
                                'url': article['url'],
                                'title': article.get('title', ''),
                                'source': f'js_{key}'
                            })
                            
                            if max_articles and len(articles) >= max_articles:
                                break
            
            logger.info(f"从JS数据发现 {len(articles)} 篇文章")
            
        except Exception as e:
            logger.error(f"从JS数据获取文章失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _extract_account_info(self, page: Page):
        """提取账号信息"""
        try:
            # 账号名称
            name_selectors = ['#js_name', 'strong.profile_nickname', '.account_nickname']
            for selector in name_selectors:
                element = await page.query_selector(selector)
                if element:
                    self.account_info['name'] = await element.text_content()
                    break
            
            # 账号描述
            desc_selectors = ['#js_profile_desc', '.profile_desc']
            for selector in desc_selectors:
                element = await page.query_selector(selector)
                if element:
                    self.account_info['description'] = await element.text_content()
                    break
            
            # 微信号
            wechat_id_selectors = ['#js_wechat_id', '.profile_wechat_id']
            for selector in wechat_id_selectors:
                element = await page.query_selector(selector)
                if element:
                    self.account_info['wechat_id'] = await element.text_content()
                    break
            
            logger.info(f"账号信息: {self.account_info}")
            
        except Exception as e:
            logger.warning(f"提取账号信息失败: {str(e)}")
    
    async def _find_account_profile_link(self, page: Page) -> Optional[str]:
        """查找账号主页链接"""
        try:
            # 常见的账号链接选择器
            profile_selectors = [
                'a#js_name',
                'a[href*="profile"]',
                'strong#profileBt a',
                '.profile_link a'
            ]
            
            for selector in profile_selectors:
                element = await page.query_selector(selector)
                if element:
                    href = await element.get_attribute('href')
                    if href:
                        return urljoin(page.url, href)
            
        except Exception as e:
            logger.warning(f"查找账号链接失败: {str(e)}")
            
        return None
    
    async def _find_history_link(self, page: Page) -> Optional[str]:
        """查找历史消息链接"""
        try:
            # 查找"查看历史消息"或类似的链接
            history_patterns = [
                'a:text("查看历史消息")',
                'a:text("历史消息")',
                'a:text("更多文章")',
                'a[href*="history"]',
                'a[href*="msglist"]'
            ]
            
            for pattern in history_patterns:
                try:
                    element = await page.wait_for_selector(pattern, timeout=2000)
                    if element:
                        href = await element.get_attribute('href')
                        if href:
                            return urljoin(page.url, href)
                except:
                    continue
            
        except Exception as e:
            logger.warning(f"查找历史消息链接失败: {str(e)}")
            
        return None
    
    async def _crawl_account_profile(self, profile_url: str, max_articles: Optional[int]) -> List[Dict]:
        """爬取账号主页的文章"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
            
            # 滚动加载更多文章
            await self._scroll_and_collect_articles(page, articles, max_articles)
            
        except Exception as e:
            logger.error(f"爬取账号主页失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _crawl_history_page(self, history_url: str, max_articles: Optional[int]) -> List[Dict]:
        """爬取历史消息页面"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(history_url, wait_until="domcontentloaded", timeout=60000)
            
            # 滚动加载更多历史文章
            await self._scroll_and_collect_articles(page, articles, max_articles)
            
        except Exception as e:
            logger.error(f"爬取历史消息页面失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _scroll_and_collect_articles(self, page: Page, articles: List[Dict], max_articles: Optional[int]):
        """滚动页面并收集文章链接"""
        try:
            last_count = 0
            scroll_attempts = 0
            max_scrolls = 10
            
            while scroll_attempts < max_scrolls:
                # 收集当前页面的文章链接
                links = await page.query_selector_all('a[href*="mp.weixin.qq.com"]')
                
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        title_element = await link.query_selector('h3, h4, .title, .article-title')
                        title = await title_element.text_content() if title_element else await link.text_content()
                        
                        if href and self._is_valid_article_url(href) and href not in [a['url'] for a in articles]:
                            articles.append({
                                'url': href,
                                'title': title or '',
                                'source': 'profile_scroll'
                            })
                            
                            if max_articles and len(articles) >= max_articles:
                                return
                                
                    except Exception as e:
                        continue
                
                # 检查是否有新文章
                if len(articles) == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_count = len(articles)
                
                # 滚动到底部
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # 尝试点击"加载更多"按钮
                try:
                    load_more = await page.query_selector('a:text("加载更多"), button:text("加载更多"), .load-more')
                    if load_more:
                        await load_more.click()
                        await page.wait_for_timeout(3000)
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"滚动收集文章失败: {str(e)}")
    
    def _is_valid_article_url(self, url: str) -> bool:
        """检查是否为有效的文章URL"""
        try:
            if not url or 'mp.weixin.qq.com' not in url:
                return False
            
            # 必须包含文章标识
            if '/s/' not in url and '/s?' not in url:
                return False
            
            # 排除某些类型的URL
            exclude_patterns = [
                'action=profile',
                'action=follow',
                'scene=',  # 分享场景
                '__biz=',  # 账号页面
                'tempkey='  # 临时链接
            ]
            
            for pattern in exclude_patterns:
                if pattern in url:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """去除重复文章"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def get_account_info(self) -> Dict:
        """获取账号信息"""
        return self.account_info