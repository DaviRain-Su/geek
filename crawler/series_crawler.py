import asyncio
import re
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin
from playwright.async_api import Page
from crawler.browser import CrawlerBase
from utils.logger import logger


class SeriesCrawler(CrawlerBase):
    """专门用于获取微信文章合集/系列的爬虫"""
    
    def __init__(self):
        super().__init__()
        self.discovered_urls: Set[str] = set()
        self.series_info = {}
        
    async def get_series_articles(self, start_url: str, max_articles: Optional[int] = None) -> List[Dict]:
        """
        从合集/系列文章获取所有相关文章
        
        Args:
            start_url: 起始文章URL
            max_articles: 最大获取数量
            
        Returns:
            系列文章列表
        """
        series_articles = []
        
        try:
            logger.info(f"开始获取系列文章: {start_url}")
            
            # 方法1: 通过合集目录页面
            album_articles = await self._get_articles_from_album(start_url, max_articles)
            series_articles.extend(album_articles)
            
            # 方法2: 通过上一篇/下一篇导航
            nav_articles = await self._get_articles_from_navigation(start_url, max_articles)
            series_articles.extend(nav_articles)
            
            # 方法3: 通过系列标题模式匹配
            pattern_articles = await self._get_articles_by_title_pattern(start_url, max_articles)
            series_articles.extend(pattern_articles)
            
            # 去重并排序
            unique_articles = self._deduplicate_and_sort_articles(series_articles)
            
            logger.info(f"总共发现 {len(unique_articles)} 篇系列文章")
            return unique_articles[:max_articles] if max_articles else unique_articles
            
        except Exception as e:
            logger.error(f"获取系列文章失败: {str(e)}")
            return series_articles
    
    async def _get_articles_from_album(self, start_url: str, max_articles: Optional[int]) -> List[Dict]:
        """通过合集/专辑页面获取文章"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            
            # 查找合集信息
            await self._extract_album_info(page)
            
            # 查找合集目录链接
            album_link = await self._find_album_directory_link(page)
            
            if album_link:
                logger.info(f"找到合集目录: {album_link}")
                articles = await self._crawl_album_directory(album_link, max_articles)
            else:
                # 尝试其他方式访问合集
                articles = await self._try_alternative_album_access(page, max_articles)
            
        except Exception as e:
            logger.error(f"从合集获取文章失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _get_articles_from_navigation(self, start_url: str, max_articles: Optional[int]) -> List[Dict]:
        """通过上一篇/下一篇导航获取文章"""
        articles = []
        visited_urls = set()
        
        # 双向搜索：向前和向后
        await self._navigate_direction(start_url, "prev", articles, visited_urls, max_articles)
        await self._navigate_direction(start_url, "next", articles, visited_urls, max_articles)
        
        return articles
    
    async def _navigate_direction(self, start_url: str, direction: str, articles: List[Dict], 
                                visited_urls: Set[str], max_articles: Optional[int]):
        """在指定方向上导航获取文章"""
        current_url = start_url
        consecutive_errors = 0
        max_consecutive_errors = 3  # 连续错误次数限制
        
        while current_url and (not max_articles or len(articles) < max_articles):
            if current_url in visited_urls:
                logger.info(f"跳过已访问的URL: {current_url}")
                break
            
            # 检查是否是异常页面URL
            if self._is_error_page(current_url):
                logger.warning(f"检测到异常URL，跳过: {current_url}")
                break
                
            visited_urls.add(current_url)
            page = await self.browser_manager.new_page()
            
            try:
                await page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)  # 等待页面完全加载
                
                # 检查页面是否加载成功
                page_title = await page.title()
                if self._is_error_page(current_url, page_title):
                    logger.warning(f"页面加载异常 '{page_title}'，跳过并继续: {current_url}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"连续{max_consecutive_errors}次遇到异常，停止导航")
                        break
                    # 尝试继续导航
                    next_url = await self._click_navigation_link(page, direction)
                    if next_url and next_url != current_url and not self._is_error_page(next_url):
                        current_url = next_url
                        logger.info(f"跳过异常页面，继续导航到: {next_url}")
                        continue
                    else:
                        break
                
                # 重置错误计数器
                consecutive_errors = 0
                
                # 提取当前文章信息
                article_info = await self._extract_article_info(page, current_url)
                if article_info:
                    articles.append(article_info)
                    logger.info(f"发现文章: {article_info['title']}")
                else:
                    logger.warning(f"无法提取文章信息，但尝试继续导航: {current_url}")
                
                # 查找并点击导航链接
                next_url = await self._click_navigation_link(page, direction)
                if next_url and next_url != current_url:
                    # 检查下一个URL是否有效，如果异常则重试
                    if self._is_error_page(next_url):
                        logger.warning(f"下一个URL是异常页面，尝试重试: {next_url}")
                        retry_url = await self._retry_with_delay(page, direction, current_url)
                        if retry_url and not self._is_error_page(retry_url):
                            current_url = retry_url
                            logger.info(f"重试成功，继续导航到: {retry_url}")
                            continue
                        else:
                            logger.warning(f"重试失败，停止{direction}方向导航")
                            break
                    current_url = next_url
                    logger.info(f"导航到: {next_url}")
                else:
                    logger.info(f"未找到有效的导航链接，结束{direction}方向的导航")
                    break
                    
            except Exception as e:
                logger.warning(f"导航到 {current_url} 失败: {str(e)}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"连续{max_consecutive_errors}次导航失败，停止导航")
                    break
                # 尝试获取下一个链接继续
                try:
                    next_url = await self._click_navigation_link(page, direction)
                    if next_url and next_url != current_url and not self._is_error_page(next_url):
                        current_url = next_url
                        logger.info(f"遇到错误，但尝试继续导航到: {next_url}")
                        continue
                except:
                    pass
                break
            finally:
                await page.close()
            
            # 延迟避免过快请求
            await asyncio.sleep(3)
    
    async def _get_articles_by_title_pattern(self, start_url: str, max_articles: Optional[int]) -> List[Dict]:
        """通过标题模式匹配获取系列文章"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            
            # 提取当前文章标题
            title = await self._extract_article_title(page)
            if not title:
                return articles
            
            # 分析标题模式
            series_pattern = self._analyze_title_pattern(title)
            if not series_pattern:
                return articles
            
            logger.info(f"检测到系列模式: {series_pattern}")
            
            # 基于模式搜索相关文章
            pattern_articles = await self._search_by_pattern(series_pattern, max_articles)
            articles.extend(pattern_articles)
            
        except Exception as e:
            logger.error(f"通过标题模式获取文章失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _extract_album_info(self, page: Page):
        """提取合集信息"""
        try:
            # 查找合集名称
            album_selectors = [
                '.album_name_title',
                '.weui-pc-popover__title',
                '[class*="album"]',
                '.js_album_name'
            ]
            
            for selector in album_selectors:
                element = await page.query_selector(selector)
                if element:
                    album_name = await element.text_content()
                    if album_name:
                        self.series_info['album_name'] = album_name.strip()
                        logger.info(f"合集名称: {album_name}")
                        break
            
            # 查找合集描述
            desc_element = await page.query_selector('.album_desc, .weui-pc-popover__bd')
            if desc_element:
                desc = await desc_element.text_content()
                if desc:
                    self.series_info['description'] = desc.strip()
            
        except Exception as e:
            logger.warning(f"提取合集信息失败: {str(e)}")
    
    async def _find_album_directory_link(self, page: Page) -> Optional[str]:
        """查找合集目录链接"""
        try:
            # 查找目录/合集相关链接
            directory_selectors = [
                'a[href*="album"]',
                'a[href*="collection"]',
                'a[href*="series"]',
                '.album_read_more a',
                '.weui-pc-popover a',
                'a:text("目录")',
                'a:text("合集")',
                'a:text("查看更多")'
            ]
            
            for selector in directory_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        href = await element.get_attribute('href')
                        if href:
                            full_url = urljoin(page.url, href)
                            return full_url
                except:
                    continue
            
        except Exception as e:
            logger.warning(f"查找合集目录链接失败: {str(e)}")
            
        return None
    
    async def _click_navigation_link(self, page: Page, direction: str) -> Optional[str]:
        """点击导航链接并获取新URL"""
        try:
            if direction == "prev":
                selectors = [
                    '.album_read_nav_prev',
                    '[class*="album_read"] [class*="prev"]'
                ]
            else:  # next
                selectors = [
                    '.album_read_nav_next',
                    '[class*="album_read"] [class*="next"]'
                ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # 滚动到元素
                        await element.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1000)
                        
                        # 悬停触发
                        await element.hover()
                        await page.wait_for_timeout(1000)
                        
                        # 记录当前URL
                        current_url = page.url
                        
                        # 点击元素
                        await element.click()
                        
                        # 等待导航
                        try:
                            await page.wait_for_url(lambda url: url != current_url, timeout=10000)
                            new_url = page.url
                            
                            # 验证新URL是否有效，并尝试重试
                            if self._is_error_page(new_url):
                                logger.warning(f"导航到异常页面，尝试重试: {new_url}")
                                retry_url = await self._retry_with_delay(page, direction, current_url)
                                if retry_url and not self._is_error_page(retry_url):
                                    return retry_url
                                logger.warning(f"重试后仍然异常，跳过: {new_url}")
                                return None
                            
                            return new_url
                        except:
                            # 如果没有导航，可能是在同一页面中加载了内容
                            await page.wait_for_timeout(3000)
                            new_url = page.url
                            if new_url != current_url:
                                # 验证新URL是否有效，并尝试重试
                                if self._is_error_page(new_url):
                                    logger.warning(f"导航到异常页面，尝试重试: {new_url}")
                                    retry_url = await self._retry_with_delay(page, direction, current_url)
                                    if retry_url and not self._is_error_page(retry_url):
                                        return retry_url
                                    logger.warning(f"重试后仍然异常，跳过: {new_url}")
                                    return None
                                return new_url
                        
                        break
                        
                except Exception as e:
                    logger.debug(f"尝试{selector}失败: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"点击{direction}导航失败: {str(e)}")
            
        return None
    
    async def _retry_with_delay(self, page: Page, direction: str, original_url: str, max_retries: int = 2) -> Optional[str]:
        """遇到异常页面时的重试机制"""
        import random
        
        for retry in range(max_retries):
            try:
                logger.info(f"第 {retry + 1} 次重试导航 ({direction})")
                
                # 等待一段时间后重试
                delay = random.uniform(3, 8)  # 3-8秒随机延迟
                logger.info(f"等待 {delay:.1f} 秒后重试...")
                await asyncio.sleep(delay)
                
                # 刷新页面回到原始状态
                await page.goto(original_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                
                # 重新尝试导航
                selectors = [
                    '.album_read_nav_prev' if direction == "prev" else '.album_read_nav_next',
                    f'[class*="album_read"] [class*="{direction}"]'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            await element.scroll_into_view_if_needed()
                            await page.wait_for_timeout(1000)
                            await element.hover()
                            await page.wait_for_timeout(1000)
                            
                            current_url = page.url
                            await element.click()
                            
                            # 等待导航
                            try:
                                await page.wait_for_url(lambda url: url != current_url, timeout=8000)
                                new_url = page.url
                                
                                if not self._is_error_page(new_url):
                                    logger.info(f"重试成功，导航到: {new_url}")
                                    return new_url
                                else:
                                    logger.warning(f"重试 {retry + 1} 仍然异常: {new_url}")
                                    break
                                    
                            except:
                                # 检查页面是否有变化
                                await page.wait_for_timeout(2000)
                                new_url = page.url
                                if new_url != current_url and not self._is_error_page(new_url):
                                    logger.info(f"重试成功（延迟导航），导航到: {new_url}")
                                    return new_url
                                break
                                
                    except Exception as e:
                        logger.debug(f"重试选择器 {selector} 失败: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.warning(f"重试 {retry + 1} 失败: {str(e)}")
                continue
        
        logger.warning(f"所有重试都失败，无法导航到有效页面")
        return None
    
    async def _find_navigation_link(self, page: Page, direction: str) -> Optional[str]:
        """查找导航链接（上一篇/下一篇）- 备用方法"""
        try:
            if direction == "prev":
                selectors = [
                    '.album_read_nav_prev a',
                    '.js_prev_article',
                    'a:text("上一篇")',
                    '.prev-article a',
                    '[class*="prev"] a'
                ]
            else:  # next
                selectors = [
                    '.album_read_nav_next a',
                    '.js_next_article', 
                    'a:text("下一篇")',
                    '.next-article a',
                    '[class*="next"] a'
                ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        href = await element.get_attribute('href')
                        if href and 'mp.weixin.qq.com' in href:
                            return href
                except:
                    continue
            
        except Exception as e:
            logger.warning(f"查找{direction}导航链接失败: {str(e)}")
            
        return None
    
    def _is_error_page(self, url: str, title: str = None) -> bool:
        """检测是否是错误或异常页面"""
        error_indicators = [
            'wappoc_appmsgcaptcha',  # 验证码页面
            'mp_profile_redirect',   # 重定向错误
            'error',                 # 一般错误页面
            'blocked',               # 被屏蔽页面
            'forbidden',             # 禁止访问
        ]
        
        # 检查URL中的错误指示器
        for indicator in error_indicators:
            if indicator in url.lower():
                return True
        
        # 检查标题中的错误指示器
        if title:
            error_titles = [
                '环境异常',
                '系统错误',
                '页面不存在',
                '网络错误',
                '验证码',
                'Error',
                'Not Found'
            ]
            for error_title in error_titles:
                if error_title in title:
                    return True
        
        return False
    
    async def _extract_article_info(self, page: Page, url: str) -> Optional[Dict]:
        """提取文章基本信息"""
        try:
            # 检查是否是异常页面
            if self._is_error_page(url):
                logger.warning(f"检测到异常页面，跳过: {url}")
                return None
            
            # 提取标题
            title_selectors = [
                'h1#activity-name',
                'h2#activity-name', 
                '.rich_media_title',
                'h1',
                'h2'
            ]
            
            title = None
            for selector in title_selectors:
                element = await page.query_selector(selector)
                if element:
                    title = await element.text_content()
                    if title:
                        title = title.strip()
                        break
            
            if not title:
                logger.warning(f"无法提取标题，跳过: {url}")
                return None
            
            # 检查标题是否包含错误信息
            if self._is_error_page(url, title):
                logger.warning(f"检测到错误页面标题 '{title}'，跳过: {url}")
                return None
            
            # 提取发布时间
            time_element = await page.query_selector('#publish_time, .publish_time')
            publish_time = None
            if time_element:
                publish_time = await time_element.text_content()
            
            return {
                'url': url,
                'title': title,
                'publish_time': publish_time,
                'source': 'navigation'
            }
            
        except Exception as e:
            logger.warning(f"提取文章信息失败: {str(e)}")
            return None
    
    async def _extract_article_title(self, page: Page) -> Optional[str]:
        """提取文章标题"""
        try:
            title_selectors = [
                'h1#activity-name',
                'h2#activity-name',
                '.rich_media_title h1',
                '.rich_media_title',
                'h1', 'h2'
            ]
            
            for selector in title_selectors:
                element = await page.query_selector(selector)
                if element:
                    title = await element.text_content()
                    if title:
                        return title.strip()
            
        except Exception as e:
            logger.warning(f"提取标题失败: {str(e)}")
            
        return None
    
    def _analyze_title_pattern(self, title: str) -> Optional[Dict]:
        """分析标题模式"""
        try:
            # 模式1: "Series Name #123" 格式
            pattern1 = r'^(.+?)\s*#(\d+)$'
            match1 = re.match(pattern1, title)
            if match1:
                return {
                    'type': 'hash_number',
                    'series_name': match1.group(1).strip(),
                    'number': int(match1.group(2)),
                    'pattern': pattern1
                }
            
            # 模式2: "Series Name (123)" 格式
            pattern2 = r'^(.+?)\s*\((\d+)\)$'
            match2 = re.match(pattern2, title)
            if match2:
                return {
                    'type': 'parentheses_number',
                    'series_name': match2.group(1).strip(),
                    'number': int(match2.group(2)),
                    'pattern': pattern2
                }
            
            # 模式3: "Series Name 第123期" 格式
            pattern3 = r'^(.+?)\s*第(\d+)期$'
            match3 = re.match(pattern3, title)
            if match3:
                return {
                    'type': 'episode_number',
                    'series_name': match3.group(1).strip(),
                    'number': int(match3.group(2)),
                    'pattern': pattern3
                }
            
            # 模式4: "Series Name Vol.123" 格式
            pattern4 = r'^(.+?)\s*Vol\.?(\d+)$'
            match4 = re.match(pattern4, title, re.IGNORECASE)
            if match4:
                return {
                    'type': 'volume_number',
                    'series_name': match4.group(1).strip(),
                    'number': int(match4.group(2)),
                    'pattern': pattern4
                }
            
        except Exception as e:
            logger.warning(f"分析标题模式失败: {str(e)}")
            
        return None
    
    async def _search_by_pattern(self, pattern: Dict, max_articles: Optional[int]) -> List[Dict]:
        """基于模式搜索相关文章"""
        # 这里可以实现基于模式的搜索逻辑
        # 由于微信的搜索限制，这个功能可能需要配合其他方法使用
        return []
    
    async def _crawl_album_directory(self, album_url: str, max_articles: Optional[int]) -> List[Dict]:
        """爬取合集目录页面"""
        articles = []
        page = await self.browser_manager.new_page()
        
        try:
            await page.goto(album_url, wait_until="domcontentloaded", timeout=60000)
            
            # 查找文章列表
            article_links = await page.query_selector_all('a[href*="mp.weixin.qq.com"]')
            
            for link in article_links:
                try:
                    href = await link.get_attribute('href')
                    title_element = await link.query_selector('.title, h3, h4')
                    title = await title_element.text_content() if title_element else await link.text_content()
                    
                    if href and title:
                        articles.append({
                            'url': href,
                            'title': title.strip(),
                            'source': 'album_directory'
                        })
                        
                        if max_articles and len(articles) >= max_articles:
                            break
                            
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.error(f"爬取合集目录失败: {str(e)}")
        finally:
            await page.close()
            
        return articles
    
    async def _try_alternative_album_access(self, page: Page, max_articles: Optional[int]) -> List[Dict]:
        """尝试其他方式访问合集"""
        articles = []
        
        try:
            # 尝试点击合集相关元素
            album_elements = await page.query_selector_all('.album_name_title, .weui-pc-popover__title')
            
            for element in album_elements:
                try:
                    await element.click()
                    await page.wait_for_timeout(2000)
                    
                    # 查找弹出的文章列表
                    popup_links = await page.query_selector_all('.weui-pc-popover a[href*="mp.weixin.qq.com"]')
                    
                    for link in popup_links:
                        href = await link.get_attribute('href')
                        title = await link.text_content()
                        
                        if href and title:
                            articles.append({
                                'url': href,
                                'title': title.strip(),
                                'source': 'album_popup'
                            })
                            
                            if max_articles and len(articles) >= max_articles:
                                break
                    
                    break  # 找到就退出
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.warning(f"尝试其他合集访问方式失败: {str(e)}")
            
        return articles
    
    def _deduplicate_and_sort_articles(self, articles: List[Dict]) -> List[Dict]:
        """去重并排序文章"""
        # 去重
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        # 尝试按标题中的数字排序
        def extract_number(title: str) -> int:
            # 尝试提取标题中的数字
            numbers = re.findall(r'#(\d+)|第(\d+)期|Vol\.?(\d+)|\((\d+)\)', title, re.IGNORECASE)
            if numbers:
                for group in numbers[0]:
                    if group:
                        return int(group)
            return 0
        
        try:
            unique_articles.sort(key=lambda x: extract_number(x['title']))
        except:
            pass  # 如果排序失败，保持原顺序
        
        return unique_articles
    
    def get_series_info(self) -> Dict:
        """获取系列信息"""
        return self.series_info