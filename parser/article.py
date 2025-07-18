import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from storage.models import Article
from utils.logger import logger


class ArticleParser:
    """Parser for WeChat articles"""
    
    def parse(self, html: str, url: str, js_data: Optional[Dict[str, Any]] = None) -> Optional[Article]:
        """
        Parse WeChat article HTML and extract structured data
        
        Args:
            html: HTML content of the article
            url: URL of the article
            js_data: Additional data extracted from JavaScript variables
            
        Returns:
            Article object or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract basic information
            title = self._extract_title(soup, js_data)
            if not title:
                logger.warning(f"No title found for article: {url}")
                return None
            
            content = self._extract_content(soup)
            if not content:
                logger.warning(f"No content found for article: {url}")
                return None
            
            # Extract metadata
            author = self._extract_author(soup, js_data)
            account_name = self._extract_account_name(soup, js_data)
            publish_time = self._extract_publish_time(soup, js_data)
            
            # Extract media
            images = self._extract_images(soup, url)
            cover_image = self._extract_cover_image(soup, js_data, images)
            
            # Extract engagement metrics
            read_count = self._extract_read_count(soup, js_data)
            like_count = self._extract_like_count(soup, js_data)
            
            # Create article object
            article = Article(
                url=url,
                title=title,
                content=content,
                author=author,
                account_name=account_name,
                publish_time=publish_time,
                images=images,
                cover_image=cover_image,
                read_count=read_count,
                like_count=like_count,
                raw_html=html,
                crawl_time=datetime.now()
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to parse article {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract article title"""
        # Try JavaScript data first
        if js_data and js_data.get('title'):
            return js_data['title'].strip()
        
        # Try various selectors
        selectors = [
            'h1#activity-name',
            'h2#activity-name',
            'h1.rich_media_title',
            'h2.rich_media_title',
            'meta[property="og:title"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content"""
        content_element = soup.select_one('#js_content')
        if not content_element:
            content_element = soup.select_one('.rich_media_content')
        
        if content_element:
            # Remove script and style tags
            for tag in content_element(['script', 'style']):
                tag.decompose()
            
            # Get text content with preserved structure
            content = content_element.get_text(separator='\n', strip=True)
            
            # Clean up excessive whitespace
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            return content
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract article author"""
        # Try JavaScript data
        if js_data and js_data.get('author'):
            return js_data['author'].strip()
        
        # Try various selectors
        selectors = [
            'span#js_author_name',
            'span.rich_media_meta_text:contains("作者")',
            'meta[name="author"]',
            'span#js_name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                text = element.get_text(strip=True)
                # Remove "作者:" prefix if present
                text = re.sub(r'^作者[:：]\s*', '', text)
                return text
        
        return None
    
    def _extract_account_name(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract WeChat account name"""
        # Try JavaScript data
        if js_data:
            if js_data.get('nickname'):
                return js_data['nickname'].strip()
            if js_data.get('account_name'):
                return js_data['account_name'].strip()
        
        # Try various selectors
        selectors = [
            'span#js_name',
            'strong#profileBt a',
            'a#js_name',
            'span.profile_nickname'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_publish_time(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]]) -> Optional[datetime]:
        """Extract article publish time"""
        # Try JavaScript data
        if js_data and js_data.get('publish_time'):
            try:
                timestamp = int(js_data['publish_time'])
                return datetime.fromtimestamp(timestamp)
            except:
                pass
        
        # Try various selectors
        selectors = [
            'em#publish_time',
            'span#publish_time',
            'span.publish_time',
            'meta[property="article:published_time"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    time_str = element.get('content', '')
                else:
                    time_str = element.get_text(strip=True)
                
                # Try to parse the time string
                try:
                    # Common formats
                    for fmt in ['%Y-%m-%d', '%Y年%m月%d日', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']:
                        try:
                            return datetime.strptime(time_str, fmt)
                        except:
                            continue
                except:
                    pass
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all images from article"""
        images = []
        
        # Find images in content
        content_element = soup.select_one('#js_content') or soup.select_one('.rich_media_content')
        if content_element:
            for img in content_element.find_all('img'):
                # Try different attributes
                src = img.get('data-src') or img.get('src') or img.get('data-backup-src')
                if src:
                    # Make URL absolute
                    absolute_url = urljoin(base_url, src)
                    if absolute_url not in images:
                        images.append(absolute_url)
        
        return images
    
    def _extract_cover_image(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]], images: List[str]) -> Optional[str]:
        """Extract cover image"""
        # Try JavaScript data
        if js_data and js_data.get('cdn_url'):
            return js_data['cdn_url']
        
        # Try meta tags
        meta_image = soup.select_one('meta[property="og:image"]')
        if meta_image:
            return meta_image.get('content')
        
        # Use first image if available
        if images:
            return images[0]
        
        return None
    
    def _extract_read_count(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]]) -> int:
        """Extract read count (if available)"""
        # This is typically loaded dynamically and may not be in initial HTML
        # Would need additional API calls to get real-time stats
        return 0
    
    def _extract_like_count(self, soup: BeautifulSoup, js_data: Optional[Dict[str, Any]]) -> int:
        """Extract like count (if available)"""
        # This is typically loaded dynamically and may not be in initial HTML
        # Would need additional API calls to get real-time stats
        return 0