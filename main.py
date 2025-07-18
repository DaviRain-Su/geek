import asyncio
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os
import requests
from crawler.wechat import WeChatCrawler
from crawler.article_discovery import ArticleDiscovery
from crawler.history_crawler import HistoryCrawler
from crawler.series_crawler import SeriesCrawler
from storage.database import DatabaseManager
from storage.models import CrawlJob
from proxy.manager import ProxyManager
from utils.logger import logger
from utils.config import settings
from analytics.trend_analyzer import TrendAnalyzer
from analytics.tag_extractor import TagExtractor
from analytics.content_evaluator import ContentEvaluator


def _is_error_url(url: str) -> bool:
    """检测是否是错误或异常URL"""
    error_indicators = [
        'wappoc_appmsgcaptcha',  # 验证码页面
        'mp_profile_redirect',   # 重定向错误
        'error',                 # 一般错误页面
        'blocked',               # 被屏蔽页面
        'forbidden',             # 禁止访问
    ]
    
    for indicator in error_indicators:
        if indicator in url.lower():
            return True
    return False


def _is_error_title(title: str) -> bool:
    """检测是否是错误标题"""
    if not title:
        return True
    
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


def _clean_article_content(content: str) -> str:
    """清理文章内容，去除模板文字和广告"""
    if not content:
        return content
    
    import re
    
    # 定义需要删除的模板内容
    template_patterns = [
        # Rebase 相关的模板内容
        r'微信不支持外部链接.*?阅读原文.*?浏览每期日报内容。',
        r'Web3 极客日报是为 Web3 时代的极客们准备的日常读物.*?并注明日报贡献。',
        r'网站:\s*https://rebase\.network',
        r'公众号:\s*rebase_network',
        
        # 通用的微信公众号模板
        r'点击.*?阅读原文.*?查看.*?',
        r'长按.*?识别.*?二维码.*?关注',
        r'扫描.*?二维码.*?关注.*?公众号',
        r'关注.*?公众号.*?获取更多.*?',
        r'更多.*?内容.*?请关注.*?',
        r'欢迎.*?转发.*?分享.*?朋友圈',
        
        # 其他常见的结尾模板
        r'本文.*?首发.*?公众号.*?',
        r'原文链接.*?https?://[^\s]+',
        r'来源.*?https?://[^\s]+',
        r'声明.*?本文.*?转载.*?',
        r'免责声明.*?投资有风险.*?',
        
        # 清理多余的空行和分隔符
        r'\n\s*\n\s*\n',  # 多个连续空行
        r'[=\-_]{3,}',    # 连续的分隔符
    ]
    
    cleaned_content = content
    
    # 应用所有清理规则
    for pattern in template_patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
    
    # 清理多余的空白字符
    cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)  # 多个空行变成两个
    cleaned_content = re.sub(r'^\s+|\s+$', '', cleaned_content)  # 去除首尾空白
    
    return cleaned_content


def _extract_episode_from_title(title: str) -> str:
    """从标题中提取期数"""
    import re
    
    # 尝试匹配不同格式的期数
    patterns = [
        r'#(\d+)',                    # #1350
        r'第\s*(\d+)\s*期',           # 第1350期
        r'Vol\.?\s*(\d+)',            # Vol.1350 或 Vol 1350
        r'\((\d+)\)',                 # (1350)
        r'【(\d+)】',                 # 【1350】
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return f"#{match.group(1)}"
    
    return ""


def _get_content_summary(content: str, max_length: int = 200) -> str:
    """生成内容摘要"""
    import re
    
    if not content:
        return ""
    
    # 清理内容
    cleaned = _clean_article_content(content)
    
    # 移除换行符，保留空格
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 截取摘要
    if len(cleaned) <= max_length:
        return cleaned
    
    # 在合适的位置截断（句号、问号、感叹号）
    summary = cleaned[:max_length]
    
    # 尝试在标点符号处截断
    last_punct = max(
        summary.rfind('。'),
        summary.rfind('！'),
        summary.rfind('？'),
        summary.rfind('.'),
        summary.rfind('!'),
        summary.rfind('?')
    )
    
    if last_punct > max_length * 0.7:  # 如果标点在70%以后的位置
        summary = summary[:last_punct + 1]
    else:
        summary += "..."
    
    return summary


def _format_article_to_structured(article: dict, article_id: int) -> dict:
    """将文章转换为结构化格式"""
    import re
    
    title = article.get('title', '')
    content = article.get('content', '')
    
    # 提取期数
    episode = _extract_episode_from_title(title)
    
    # 清理标题（去除期数部分）
    clean_title = title
    if episode:
        # 移除期数相关的部分
        patterns = [
            r'#\d+\s*',
            r'第\s*\d+\s*期\s*',
            r'Vol\.?\s*\d+\s*',
            r'\(\d+\)\s*',
            r'【\d+】\s*',
        ]
        for pattern in patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE).strip()
    
    # 获取内容摘要
    introduce = _get_content_summary(content)
    
    # 格式化时间
    publish_time = article.get('publish_time', '')
    if publish_time:
        try:
            # 处理不同的时间格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y年%m月%d日']:
                try:
                    dt = datetime.strptime(publish_time.split(' ')[0], fmt)
                    publish_time = dt.strftime('%Y-%m-%d')
                    break
                except:
                    continue
        except:
            pass
    
    return {
        "id": article_id,
        "attributes": {
            "episode": episode,
            "title": clean_title,
            "author": article.get('author', article.get('account_name', 'Unknown')),
            "url": article.get('url', ''),
            "time": publish_time,
            "introduce": introduce,
            "full_content": _clean_article_content(content)  # 保留完整内容供需要时使用
        }
    }


def _extract_daily_items_from_content(content: str) -> list:
    """从Web3极客日报内容中提取每日推荐项目"""
    items = []
    
    if not content:
        return items
    
    import re
    
    # 清理内容
    cleaned_content = _clean_article_content(content)
    
    # 尝试识别日报中的各个推荐项目
    # 通常格式为：1. 标题 作者 链接 介绍
    
    # 分割内容为段落
    paragraphs = cleaned_content.split('\n')
    
    current_item = {}
    item_number = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 检查是否是新的项目开始（通常以数字开头）
        item_match = re.match(r'^(\d+)[\.\、]\s*(.+)', para)
        if item_match:
            # 保存之前的项目
            if current_item and 'title' in current_item:
                items.append(current_item)
            
            item_number += 1
            remaining_text = item_match.group(2)
            
            # 尝试提取标题、作者等信息
            # 格式可能是：标题 by 作者 或 标题（作者）
            by_match = re.search(r'^(.+?)\s+by\s+(\w+)', remaining_text, re.IGNORECASE)
            paren_match = re.search(r'^(.+?)\s*[（(](\w+)[）)]', remaining_text)
            
            if by_match:
                current_item = {
                    'number': item_number,
                    'title': by_match.group(1).strip(),
                    'author': by_match.group(2).strip()
                }
            elif paren_match:
                current_item = {
                    'number': item_number,
                    'title': paren_match.group(1).strip(),
                    'author': paren_match.group(2).strip()
                }
            else:
                current_item = {
                    'number': item_number,
                    'title': remaining_text.strip(),
                    'author': ''
                }
        
        # 检查是否是URL
        elif current_item and re.match(r'^https?://', para):
            current_item['url'] = para
        
        # 否则可能是介绍文字
        elif current_item and 'title' in current_item:
            if 'introduce' not in current_item:
                current_item['introduce'] = para
            else:
                current_item['introduce'] += ' ' + para
    
    # 保存最后一个项目
    if current_item and 'title' in current_item:
        items.append(current_item)
    
    return items


class GeekDailyAPI:
    """极客日报API客户端"""
    
    def __init__(self, base_url: str = "http://101.33.75.240:1337/api/v1/geekdailies"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def fetch_page(self, page: int = 1, page_size: int = 100, sort: str = 'desc') -> Dict[str, Any]:
        """获取指定页面的数据"""
        try:
            params = {
                'pagination[page]': page,
                'pagination[pageSize]': page_size,
                'sort': f'id:{sort}'
            }
            
            logger.info(f"获取第 {page} 页数据 (每页 {page_size} 条)")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            raise
    
    def fetch_all_pages(self, max_pages: Optional[int] = None, page_size: int = 100) -> List[Dict[str, Any]]:
        """获取所有页面的数据"""
        all_items = []
        
        try:
            # 获取第一页获取总页数
            first_page = self.fetch_page(1, page_size)
            all_items.extend(first_page.get('data', []))
            
            # 获取分页信息
            pagination = first_page.get('meta', {}).get('pagination', {})
            total_pages = pagination.get('pageCount', 1)
            total_items = pagination.get('total', 0)
            
            logger.info(f"总共 {total_items} 条数据，{total_pages} 页")
            
            # 限制最大页数
            if max_pages:
                total_pages = min(total_pages, max_pages)
                logger.info(f"限制获取前 {max_pages} 页")
            
            # 获取剩余页面
            if total_pages > 1:
                for page in range(2, total_pages + 1):
                    try:
                        page_data = self.fetch_page(page, page_size)
                        items = page_data.get('data', [])
                        all_items.extend(items)
                        logger.info(f"已获取 {len(all_items)} / {total_items} 条数据")
                        
                        # 简单的延迟避免过快请求
                        import time
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"获取第 {page} 页失败: {str(e)}")
                        continue
            
            logger.info(f"✅ 成功获取 {len(all_items)} 条数据")
            return all_items
            
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            raise


async def fetch_api_data(api_url: str = None, max_pages: Optional[int] = None, output_file: str = None):
    """从API获取所有数据并保存到本地"""
    
    # 设置默认值
    if not api_url:
        api_url = "http://101.33.75.240:1337/api/v1/geekdailies"
    
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/api_geekdailies_{timestamp}.json"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # 初始化API客户端
        api_client = GeekDailyAPI(api_url)
        
        print(f"📡 开始从API获取数据: {api_url}")
        if max_pages:
            print(f"📄 限制获取前 {max_pages} 页")
        
        # 获取所有数据
        all_items = api_client.fetch_all_pages(max_pages)
        
        if not all_items:
            print("❌ 没有获取到任何数据")
            return
        
        # 转换为统一的结构化格式
        structured_data = []
        
        for idx, item in enumerate(all_items, 1):
            try:
                # 适应API数据结构
                attributes = item.get('attributes', {})
                
                structured_item = {
                    "id": item.get('id', idx),
                    "attributes": {
                        "episode": attributes.get('episode', ''),
                        "title": attributes.get('title', ''),
                        "author": attributes.get('author', ''),
                        "url": attributes.get('url', ''),
                        "time": attributes.get('time', ''),
                        "introduce": attributes.get('introduce', '')
                    }
                }
                
                structured_data.append(structured_item)
                
            except Exception as e:
                logger.warning(f"处理第 {idx} 条数据时出错: {str(e)}")
                continue
        
        # 保存到文件
        output_data = {
            "export_info": {
                "source": "API",
                "api_url": api_url,
                "total": len(structured_data),
                "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "max_pages": max_pages
            },
            "articles": structured_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功保存 {len(structured_data)} 条数据到: {output_file}")
        
        # 显示数据统计
        print(f"\n📊 数据统计:")
        print(f"  总条数: {len(structured_data)}")
        
        # 统计作者分布
        authors = {}
        for item in structured_data:
            author = item['attributes'].get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
        
        print(f"  作者数量: {len(authors)}")
        print(f"  热门作者:")
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {author}: {count} 篇")
        
        # 统计时间分布
        years = {}
        for item in structured_data:
            time_str = item['attributes'].get('time', '')
            if time_str:
                try:
                    year = time_str.split('-')[0]
                    years[year] = years.get(year, 0) + 1
                except:
                    pass
        
        if years:
            print(f"  时间分布:")
            for year, count in sorted(years.items(), reverse=True)[:5]:
                print(f"    {year}: {count} 篇")
        
        return output_file
        
    except Exception as e:
        logger.error(f"从API获取数据失败: {str(e)}")
        print(f"❌ 获取数据失败: {str(e)}")
        raise


async def merge_json_files(file1: str, file2: str, output_file: str = None, dedup_strategy: str = 'url', 
                          smart_split: bool = True, filter_bad_data: bool = True, fill_time: bool = True):
    """合并两个JSON文件并去重"""
    
    try:
        # 读取第一个文件
        print(f"📖 读取文件1: {file1}")
        with open(file1, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        
        # 读取第二个文件
        print(f"📖 读取文件2: {file2}")
        with open(file2, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
        
        # 提取文章数据
        articles1 = data1.get('articles', [])
        articles2 = data2.get('articles', [])
        
        print(f"📊 文件1包含 {len(articles1)} 条数据")
        print(f"📊 文件2包含 {len(articles2)} 条数据")
        
        # 合并数据并应用智能处理
        merged_articles = []
        seen = set()
        
        # 统计信息
        duplicates = 0
        split_count = 0
        filtered_count = 0
        time_filled_count = 0
        
        # 辅助函数定义
        def safe_strip(value):
            """安全地处理字符串strip，避免None值错误"""
            if value is None:
                return ''
            return str(value).strip()
        
        def parse_content_items(content_text):
            """解析文章内容，提取独立的文章条目"""
            if not content_text:
                return []
            
            import re
            items = []
            
            # 用更智能的方式切分：按照 "标题\nURL\n作者:\n内容" 的模式
            url_pattern = r'https?://[^\s]+'
            
            # 首先找到所有URL的位置，作为切分点
            urls_in_text = list(re.finditer(url_pattern, content_text))
            
            if not urls_in_text:
                return []
            
            # 按照URL位置切分内容
            for i, url_match in enumerate(urls_in_text):
                # 确定当前文章的开始和结束位置
                start_pos = 0 if i == 0 else urls_in_text[i-1].end()
                end_pos = urls_in_text[i+1].start() if i+1 < len(urls_in_text) else len(content_text)
                
                # 提取当前文章的完整文本块
                article_block = content_text[start_pos:end_pos].strip()
                
                if not article_block:
                    continue
                
                # 分析这个文本块
                url = url_match.group()
                lines = article_block.split('\n')
                
                title = ''
                author = ''
                content_lines = []
                
                url_line_index = -1
                for j, line in enumerate(lines):
                    if url in line:
                        url_line_index = j
                        # URL前面的文本可能是标题
                        url_pos = line.find(url)
                        if url_pos > 0:
                            title = line[:url_pos].strip()
                        break
                
                # 如果URL行前面还有行，可能是标题
                if url_line_index > 0 and not title:
                    for j in range(url_line_index-1, -1, -1):
                        line = lines[j].strip()
                        if line and len(line) < 200:  # 标题不应该太长
                            title = line
                            break
                
                # URL行后面的内容
                for j in range(url_line_index + 1, len(lines)):
                    line = lines[j].strip()
                    if not line:
                        continue
                    
                    # 检查是否是作者格式 (Author:)
                    if ':' in line and len(line.split(':', 1)[0].strip()) < 20:
                        parts = line.split(':', 1)
                        potential_author = parts[0].strip()
                        remaining_content = parts[1].strip()
                        
                        # 如果看起来像作者名
                        if not re.search(r'https?://', potential_author):
                            author = potential_author
                            if remaining_content:
                                content_lines.append(remaining_content)
                        else:
                            content_lines.append(line)
                    else:
                        content_lines.append(line)
                
                # 如果没有找到明确的标题，尝试从内容的第一行提取
                if not title and content_lines:
                    first_line = content_lines[0]
                    if len(first_line) < 150:  # 可能是标题
                        title = first_line
                        content_lines = content_lines[1:]
                
                content = '\n'.join(content_lines).strip()
                
                if title and url:
                    items.append({
                        'title': title,
                        'url': url,
                        'content': content,
                        'author': author
                    })
            
            return items
        
        def fix_url(url_str):
            """修复常见的URL格式问题"""
            if not url_str:
                return ''
            
            url_str = url_str.strip()
            
            # 处理包含多个URL的情况，取第一个有效的
            if ' ' in url_str and ('http://' in url_str or 'https://' in url_str):
                parts = url_str.split()
                for part in parts:
                    if part.startswith(('http://', 'https://')):
                        url_str = part
                        break
            
            # 处理中文前缀的URL（如：中文版：http://...）
            if '：http' in url_str:
                url_str = url_str.split('：http')[1]
                url_str = 'http' + url_str
            elif ':http' in url_str:
                url_str = url_str.split(':http')[1]  
                url_str = 'http' + url_str
            
            # 修复常见的拼写错误
            url_str = url_str.replace('hu.baittps://', 'https://')
            url_str = url_str.replace('htps://', 'https://')
            url_str = url_str.replace('htp://', 'http://')
            
            # 如果没有协议前缀，添加https://
            if url_str and not url_str.startswith(('http://', 'https://', 'ftp://')):
                # 检查是否是域名格式
                if '.' in url_str and not url_str.startswith('/'):
                    url_str = 'https://' + url_str
            
            # 移除URL末尾的多余空格和特殊字符
            url_str = url_str.rstrip()
            
            # 检查URL是否包含无效字符（空格、中文等）
            if url_str.startswith(('http://', 'https://')):
                # 如果包含空格或中文字符，可能是无效URL
                import re
                if re.search(r'[\s\u4e00-\u9fff]', url_str):
                    # 尝试提取第一个有效的URL部分
                    match = re.search(r'https?://[^\s\u4e00-\u9fff]+', url_str)
                    if match:
                        url_str = match.group(0)
                    else:
                        return ''  # 无法修复，返回空字符串
            
            return url_str
        
        def is_valid_article(title, url, content):
            """验证文章数据是否有效"""
            if not title or not url:
                return False
            
            if len(title.strip()) < 2:
                return False
                
            if not url.startswith(('http://', 'https://')):
                return False
                
            return True
        
        def process_articles(articles, source_name):
            """处理文章列表，应用智能拆分和过滤"""
            nonlocal split_count, filtered_count, time_filled_count
            processed_articles = []
            
            for article in articles:
                try:
                    if 'attributes' in article:
                        # 结构化格式：{id: x, attributes: {...}}
                        attrs = article['attributes']
                        title = safe_strip(attrs.get('title', ''))
                        url = safe_strip(attrs.get('url', ''))
                        author = safe_strip(attrs.get('author', ''))
                        introduce = safe_strip(attrs.get('introduce', ''))
                        full_content = safe_strip(attrs.get('full_content', ''))
                        episode = safe_strip(attrs.get('episode', ''))
                        time_str = safe_strip(attrs.get('time', ''))
                    else:
                        # 简单格式：直接是文章字段
                        title = safe_strip(article.get('title', ''))
                        url = safe_strip(article.get('url', ''))
                        author = safe_strip(article.get('author', ''))
                        introduce = safe_strip(article.get('introduce', article.get('content', '')))
                        full_content = safe_strip(article.get('full_content', ''))
                        episode = safe_strip(article.get('episode', ''))
                        time_str = safe_strip(article.get('time', article.get('publish_time', '')))
                    
                    # 检查是否是合集文章（包含多个子文章）
                    content_to_parse = full_content or introduce
                    parsed_items = []
                    
                    if smart_split and content_to_parse and (title == "Web3 极客日报" or "极客日报" in title):
                        # 这是一个合集文章，需要拆分
                        parsed_items = parse_content_items(content_to_parse)
                        if parsed_items:
                            split_count += len(parsed_items)
                            print(f"📰 {source_name}: 拆分合集文章 '{title}' → {len(parsed_items)} 个子文章")
                    
                    # 如果没有拆分出子文章，或者不是合集，保持原样
                    if not parsed_items:
                        parsed_items = [{
                            'title': title,
                            'url': url,
                            'content': content_to_parse,
                            'author': author
                        }]
                    
                    # 处理每个子文章
                    for parsed_item in parsed_items:
                        sub_title = parsed_item.get('title', '').strip()
                        sub_url = parsed_item.get('url', '').strip()
                        sub_content = parsed_item.get('content', '').strip()
                        sub_author = parsed_item.get('author', '').strip() or author
                        
                        # 修复URL
                        sub_url = fix_url(sub_url)
                        
                        # 过滤坏数据
                        if filter_bad_data and not is_valid_article(sub_title, sub_url, sub_content):
                            filtered_count += 1
                            continue
                        
                        # 处理时间字段
                        final_time = time_str
                        if fill_time and not time_str:
                            final_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            time_filled_count += 1
                        
                        # 创建处理后的文章
                        processed_article = {
                            'id': article.get('id', 0),
                            'attributes': {
                                'title': sub_title,
                                'url': sub_url,
                                'author': sub_author,
                                'introduce': sub_content[:200] + '...' if len(sub_content) > 200 else sub_content,
                                'full_content': sub_content,
                                'episode': episode,
                                'time': final_time
                            }
                        }
                        
                        processed_articles.append(processed_article)
                        
                except Exception as e:
                    print(f"⚠️  处理文章时出错: {str(e)}")
                    continue
            
            return processed_articles
        
        # 处理第一个文件的数据
        print(f"🔄 处理文件1数据...")
        processed_articles1 = process_articles(articles1, "文件1")
        
        # 处理第二个文件的数据  
        print(f"🔄 处理文件2数据...")
        processed_articles2 = process_articles(articles2, "文件2")
        
        # 合并处理后的数据并去重
        for article in processed_articles1 + processed_articles2:
            key = _get_dedup_key(article, dedup_strategy)
            if key and key not in seen:
                seen.add(key)
                merged_articles.append(article)
            elif key:
                duplicates += 1
        
        # 按ID排序
        try:
            merged_articles.sort(key=lambda x: int(x.get('id', 0)), reverse=True)
        except:
            # 如果ID不是数字，使用原始顺序
            pass
        
        # 重新编号ID
        for idx, article in enumerate(merged_articles, 1):
            article['id'] = idx
        
        # 设置输出文件名
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/merged_articles_{timestamp}.json"
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:  # 只有当有目录路径时才创建
            os.makedirs(output_dir, exist_ok=True)
        
        # 合并元数据
        merged_data = {
            "export_info": {
                "source": "MERGED",
                "source_files": [file1, file2],
                "total": len(merged_articles),
                "duplicates_removed": duplicates,
                "dedup_strategy": dedup_strategy,
                "merge_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "original_totals": {
                    "file1": len(articles1),
                    "file2": len(articles2)
                },
                "processing_stats": {
                    "smart_split_enabled": smart_split,
                    "filter_bad_data_enabled": filter_bad_data,
                    "fill_time_enabled": fill_time,
                    "articles_split": split_count,
                    "bad_data_filtered": filtered_count,
                    "time_fields_filled": time_filled_count
                }
            },
            "articles": merged_articles
        }
        
        # 保存合并后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 合并完成！")
        print(f"📄 输出文件: {output_file}")
        print(f"📊 合并结果:")
        print(f"  - 原始总数: {len(articles1) + len(articles2)}")
        print(f"  - 处理后总数: {len(processed_articles1) + len(processed_articles2)}")
        print(f"  - 去重后总数: {len(merged_articles)}")
        print(f"  - 删除重复: {duplicates}")
        print(f"  - 去重策略: {dedup_strategy}")
        
        # 智能处理统计
        if smart_split or filter_bad_data or fill_time:
            print(f"\n🧠 智能处理统计:")
            if smart_split and split_count > 0:
                print(f"  - 拆分子文章: {split_count} 个")
            if filter_bad_data and filtered_count > 0:
                print(f"  - 过滤坏数据: {filtered_count} 个")
            if fill_time and time_filled_count > 0:
                print(f"  - 补全时间: {time_filled_count} 个")
        
        # 数据统计
        print(f"\n📈 数据统计:")
        
        # 统计作者分布
        authors = {}
        for article in merged_articles:
            author = article.get('attributes', {}).get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
        
        print(f"  作者数量: {len(authors)}")
        print(f"  热门作者:")
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {author}: {count} 篇")
        
        # 统计时间分布
        years = {}
        for article in merged_articles:
            time_str = article.get('attributes', {}).get('time', '')
            if time_str:
                try:
                    year = time_str.split('-')[0]
                    years[year] = years.get(year, 0) + 1
                except:
                    pass
        
        if years:
            print(f"  时间分布:")
            for year, count in sorted(years.items(), reverse=True)[:5]:
                print(f"    {year}: {count} 篇")
        
        # 统计期数分布（如果有）
        episodes = {}
        for article in merged_articles:
            episode = article.get('attributes', {}).get('episode', '')
            if episode:
                episodes[episode] = episodes.get(episode, 0) + 1
        
        if episodes:
            print(f"  期数统计: {len(episodes)} 个不同期数")
            print(f"  最新期数: {max(episodes.keys()) if episodes else 'None'}")
        
        return output_file
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ 合并失败: {str(e)}")
        raise


def _get_dedup_key(article: dict, strategy: str) -> str:
    """根据策略获取去重键"""
    
    attributes = article.get('attributes', {})
    
    if strategy == 'url':
        # 使用URL作为去重键
        url = attributes.get('url', '')
        if url:
            return url.strip()
    
    elif strategy == 'title':
        # 使用标题作为去重键
        title = attributes.get('title', '')
        if title:
            return title.strip()
    
    elif strategy == 'episode':
        # 使用期数作为去重键
        episode = attributes.get('episode', '')
        if episode:
            return episode.strip()
    
    elif strategy == 'title_author':
        # 使用标题+作者作为去重键
        title = attributes.get('title', '').strip()
        author = attributes.get('author', '').strip()
        if title and author:
            return f"{title}_{author}"
    
    elif strategy == 'url_title':
        # 使用URL+标题作为去重键
        url = attributes.get('url', '').strip()
        title = attributes.get('title', '').strip()
        if url and title:
            return f"{url}_{title}"
    
    # 默认使用URL，如果没有URL则使用标题
    url = attributes.get('url', '').strip()
    if url:
        return url
    
    title = attributes.get('title', '').strip()
    if title:
        return title
    
    # 如果都没有，返回None（不去重）
    return None


async def analyze_json_files(*files: str):
    """分析JSON文件的内容和结构"""
    
    print(f"🔍 分析 {len(files)} 个JSON文件")
    print("=" * 60)
    
    for i, file_path in enumerate(files, 1):
        try:
            print(f"\n📁 文件 {i}: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = data.get('articles', [])
            export_info = data.get('export_info', {})
            
            print(f"📊 基本信息:")
            print(f"  - 数据总数: {len(articles)}")
            print(f"  - 数据源: {export_info.get('source', 'Unknown')}")
            print(f"  - 导出时间: {export_info.get('export_time', export_info.get('merge_time', 'Unknown'))}")
            
            if articles:
                # 分析数据结构
                sample = articles[0]
                attributes = sample.get('attributes', {})
                
                print(f"📋 数据结构:")
                print(f"  - ID范围: {min(a.get('id', 0) for a in articles)} - {max(a.get('id', 0) for a in articles)}")
                print(f"  - 字段: {list(attributes.keys())}")
                
                # 统计有效数据
                has_url = sum(1 for a in articles if a.get('attributes', {}).get('url'))
                has_title = sum(1 for a in articles if a.get('attributes', {}).get('title'))
                has_episode = sum(1 for a in articles if a.get('attributes', {}).get('episode'))
                
                print(f"📈 数据完整性:")
                print(f"  - 有URL: {has_url}/{len(articles)} ({has_url/len(articles)*100:.1f}%)")
                print(f"  - 有标题: {has_title}/{len(articles)} ({has_title/len(articles)*100:.1f}%)")
                print(f"  - 有期数: {has_episode}/{len(articles)} ({has_episode/len(articles)*100:.1f}%)")
                
                # 预览数据
                print(f"🔍 数据预览:")
                for j, article in enumerate(articles[:3], 1):
                    attrs = article.get('attributes', {})
                    print(f"  {j}. {attrs.get('episode', 'N/A')} - {attrs.get('title', 'No Title')[:40]}...")
                    print(f"     作者: {attrs.get('author', 'Unknown')} | 时间: {attrs.get('time', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 分析文件 {file_path} 失败: {str(e)}")
    
    print(f"\n💡 合并建议:")
    print(f"  - 使用URL去重: python main.py merge file1.json file2.json --strategy url")
    print(f"  - 使用标题去重: python main.py merge file1.json file2.json --strategy title")
    print(f"  - 使用期数去重: python main.py merge file1.json file2.json --strategy episode")


async def clean_json_data(input_file: str, output_file: str = None, 
                         require_fields: List[str] = None, 
                         clean_empty: bool = True,
                         validate_urls: bool = False,
                         exclude_fields: List[str] = None):
    """清洗JSON数据，删除不完整的条目"""
    
    # 设置默认的必需字段
    if require_fields is None:
        require_fields = ['author', 'url', 'title']
    
    # 设置默认的排除字段
    if exclude_fields is None:
        exclude_fields = []
    
    try:
        print(f"🧹 开始清洗数据: {input_file}")
        print(f"📋 清洗规则:")
        print(f"  - 必需字段: {', '.join(require_fields)}")
        print(f"  - 清理空值: {clean_empty}")
        print(f"  - 验证URL: {validate_urls}")
        if exclude_fields:
            print(f"  - 排除字段: {', '.join(exclude_fields)}")
        
        # 读取原始文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_articles = data.get('articles', [])
        print(f"📊 原始数据: {len(original_articles)} 条")
        
        # 清洗数据
        cleaned_articles = []
        removed_count = 0
        removal_reasons = {
            'missing_required_fields': 0,
            'empty_values': 0,
            'invalid_urls': 0,
            'empty_title': 0,
            'empty_author': 0,
            'empty_url': 0
        }
        
        for article in original_articles:
            attributes = article.get('attributes', {})
            should_remove = False
            
            # 检查必需字段是否存在且非空
            for field in require_fields:
                field_value = attributes.get(field)
                if field_value is not None:
                    field_value = str(field_value).strip()
                else:
                    field_value = ''
                
                if not field_value:
                    should_remove = True
                    removal_reasons['missing_required_fields'] += 1
                    removal_reasons[f'empty_{field}'] += 1
                    break
            
            # 如果启用了清理空值，检查其他重要字段
            if not should_remove and clean_empty:
                # 检查标题是否有意义（不只是空格或特殊字符）
                title = attributes.get('title')
                if title is not None:
                    title = str(title).strip()
                    if title and len(title) < 2:  # 标题太短
                        should_remove = True
                        removal_reasons['empty_values'] += 1
                
                # 检查介绍是否过短
                introduce = attributes.get('introduce')
                if introduce is not None:
                    introduce = str(introduce).strip()
                    if introduce and len(introduce) < 5:  # 介绍太短
                        # 不删除，但记录
                        pass
            
            # 如果启用了URL验证
            if not should_remove and validate_urls:
                url = attributes.get('url')
                if url is not None:
                    url = str(url).strip()
                    if url and not _is_valid_url(url):
                        should_remove = True
                        removal_reasons['invalid_urls'] += 1
            
            # 保留有效的文章
            if not should_remove:
                # 如果有字段需要排除，创建清理后的文章副本
                if exclude_fields:
                    cleaned_article = article.copy()
                    cleaned_attributes = cleaned_article.get('attributes', {}).copy()
                    
                    # 移除排除的字段
                    for exclude_field in exclude_fields:
                        if exclude_field in cleaned_attributes:
                            del cleaned_attributes[exclude_field]
                    
                    cleaned_article['attributes'] = cleaned_attributes
                    cleaned_articles.append(cleaned_article)
                else:
                    cleaned_articles.append(article)
            else:
                removed_count += 1
        
        # 重新编号ID
        for idx, article in enumerate(cleaned_articles, 1):
            article['id'] = idx
        
        # 设置输出文件名
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"data/{base_name}_cleaned_{timestamp}.json"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 更新元数据
        cleaned_data = data.copy()
        original_export_info = data.get('export_info', {})
        
        cleaned_data['export_info'] = {
            **original_export_info,
            "source": f"CLEANED_{original_export_info.get('source', 'UNKNOWN')}",
            "original_file": input_file,
            "total": len(cleaned_articles),
            "original_total": len(original_articles),
            "removed_count": removed_count,
            "removal_reasons": removal_reasons,
            "clean_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "clean_rules": {
                "require_fields": require_fields,
                "clean_empty": clean_empty,
                "validate_urls": validate_urls,
                "exclude_fields": exclude_fields
            }
        }
        cleaned_data['articles'] = cleaned_articles
        
        # 保存清洗后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        # 显示清洗结果
        print(f"\n✅ 数据清洗完成！")
        print(f"📄 输出文件: {output_file}")
        print(f"📊 清洗结果:")
        print(f"  - 原始数据: {len(original_articles)} 条")
        print(f"  - 清洗后数据: {len(cleaned_articles)} 条")
        print(f"  - 删除数据: {removed_count} 条")
        print(f"  - 保留率: {len(cleaned_articles)/len(original_articles)*100:.1f}%")
        
        # 显示删除原因统计
        if removed_count > 0:
            print(f"\n🗑️ 删除原因统计:")
            for reason, count in removal_reasons.items():
                if count > 0:
                    print(f"  - {reason}: {count} 条")
        
        # 数据质量分析
        print(f"\n📈 数据质量分析:")
        
        # 统计字段完整性
        field_completeness = {}
        for field in ['author', 'url', 'title', 'episode', 'time', 'introduce']:
            complete_count = 0
            for a in cleaned_articles:
                field_value = a.get('attributes', {}).get(field)
                if field_value is not None and str(field_value).strip():
                    complete_count += 1
            field_completeness[field] = complete_count / len(cleaned_articles) * 100 if cleaned_articles else 0
        
        for field, percentage in field_completeness.items():
            print(f"  - {field}: {percentage:.1f}% 完整")
        
        return output_file
        
    except FileNotFoundError:
        print(f"❌ 文件未找到: {input_file}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ 清洗失败: {str(e)}")
        raise


def _is_valid_url(url: str) -> bool:
    """验证URL是否有效"""
    import re
    
    # 基本URL格式验证
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


async def batch_clean_directory(directory: str, pattern: str = "*.json", 
                               require_fields: List[str] = None,
                               clean_empty: bool = True,
                               validate_urls: bool = False,
                               exclude_fields: List[str] = None):
    """批量清洗目录中的JSON文件"""
    import glob
    
    print(f"🔄 批量清洗目录: {directory}")
    print(f"📁 文件模式: {pattern}")
    
    # 查找匹配的文件
    search_pattern = os.path.join(directory, pattern)
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"❌ 未找到匹配的文件: {search_pattern}")
        return
    
    print(f"📋 找到 {len(files)} 个文件待处理")
    
    results = []
    
    for file_path in files:
        try:
            print(f"\n🧹 处理文件: {os.path.basename(file_path)}")
            result = await clean_json_data(
                file_path, 
                require_fields=require_fields,
                clean_empty=clean_empty,
                validate_urls=validate_urls,
                exclude_fields=exclude_fields
            )
            results.append(result)
            
        except Exception as e:
            print(f"❌ 处理文件 {file_path} 失败: {str(e)}")
            continue
    
    print(f"\n✅ 批量清洗完成！")
    print(f"📊 处理结果: {len(results)}/{len(files)} 个文件成功")
    
    if results:
        print(f"📄 输出文件:")
        for result in results:
            print(f"  - {result}")
    
    return results


async def crawl_account(account_name: str, max_articles: Optional[int] = None, use_proxy: bool = False):
    """
    Crawl articles from a WeChat public account
    
    Args:
        account_name: Name of the WeChat public account
        max_articles: Maximum number of articles to crawl
        use_proxy: Whether to use proxy rotation
    """
    # Initialize components
    db = DatabaseManager(use_mongodb=False)  # Use SQLite for simplicity
    proxy_manager = ProxyManager() if use_proxy else None
    
    # Create crawl job
    job = CrawlJob(
        account_name=account_name,
        status="running",
        start_time=datetime.now()
    )
    job_id = db.create_job(job)
    logger.info(f"Created crawl job {job_id} for account '{account_name}'")
    
    try:
        # Initialize proxy manager if needed
        if proxy_manager:
            await proxy_manager.initialize()
        
        # Create crawler
        async with WeChatCrawler() as crawler:
            # Set proxy if available
            if proxy_manager:
                proxy = proxy_manager.get_next_proxy()
                if proxy:
                    await crawler.browser_manager.stop()
                    await crawler.browser_manager.start(proxy=proxy.to_playwright_proxy())
                    logger.info(f"Using proxy: {proxy.host}:{proxy.port}")
            
            # Crawl articles
            logger.info(f"Starting to crawl account '{account_name}'...")
            articles = await crawler.crawl_account(account_name, max_articles)
            
            # Save articles to database
            saved_count = 0
            for article in articles:
                if db.save_article(article):
                    saved_count += 1
            
            # Update job status
            db.update_job(job_id, {
                "status": "completed",
                "total_articles": len(articles),
                "crawled_articles": saved_count,
                "failed_articles": len(articles) - saved_count,
                "end_time": datetime.now()
            })
            
            logger.info(f"Crawl completed! Found {len(articles)} articles, saved {saved_count} new articles")
            
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        db.update_job(job_id, {
            "status": "failed",
            "error_message": str(e),
            "end_time": datetime.now()
        })
        raise
    finally:
        db.close()


async def crawl_single_article(article_url: str, show_content: bool = False):
    """
    Crawl a single WeChat article
    
    Args:
        article_url: URL of the article to crawl
        show_content: Whether to display article content in console
    """
    db = DatabaseManager(use_mongodb=False)
    
    try:
        async with WeChatCrawler() as crawler:
            logger.info(f"Crawling article: {article_url}")
            article = await crawler.crawl_article(article_url)
            
            if article:
                # Display article info
                print("\n" + "="*60)
                print(f"📄 Title: {article.title}")
                print(f"✍️  Author: {article.author or 'Unknown'}")
                print(f"📱 Account: {article.account_name or 'Unknown'}")
                print(f"📅 Publish Time: {article.publish_time or 'Unknown'}")
                print(f"🖼️  Images: {len(article.images)} found")
                print(f"📏 Content length: {len(article.content)} characters")
                
                if show_content and article.content:
                    print("\n📖 Article Content:")
                    print("="*60)
                    paragraphs = article.content.split('\n')
                    paragraphs = [p.strip() for p in paragraphs if p.strip()]
                    
                    for i, paragraph in enumerate(paragraphs[:10]):  # Show first 10 paragraphs
                        if len(paragraph) > 300:
                            paragraph = paragraph[:300] + "..."
                        print(f"\n{i+1}. {paragraph}")
                    
                    if len(paragraphs) > 10:
                        print(f"\n... and {len(paragraphs) - 10} more paragraphs")
                
                # Save to database
                if db.save_article(article):
                    print("✅ Successfully saved article to database")
                else:
                    print("ℹ️  Article already exists in database")
                    
            else:
                print("❌ Failed to crawl article")
                
    except Exception as e:
        logger.error(f"Error crawling article: {str(e)}")
        raise
    finally:
        db.close()


async def test_crawler(show_content: bool = False):
    """Test crawler with predefined article"""
    test_url = "https://mp.weixin.qq.com/s/7gWx7Lj8AOOKnD7KscgNMg"
    print(f"🧪 Testing crawler with: {test_url}")
    await crawl_single_article(test_url, show_content)


async def get_history_articles(article_url: str, max_articles: Optional[int] = None, use_proxy: bool = False):
    """
    从单篇文章获取该公众号的历史文章
    
    Args:
        article_url: 起始文章URL
        max_articles: 最大获取数量
        use_proxy: 是否使用代理
    """
    # Initialize components
    db = DatabaseManager(use_mongodb=False)
    proxy_manager = ProxyManager() if use_proxy else None
    
    try:
        # Initialize proxy manager if needed
        if proxy_manager:
            await proxy_manager.initialize()
        
        # 获取历史文章列表
        async with HistoryCrawler() as crawler:
            # Set proxy if available
            if proxy_manager:
                proxy = proxy_manager.get_next_proxy()
                if proxy:
                    await crawler.browser_manager.stop()
                    await crawler.browser_manager.start(proxy=proxy.to_playwright_proxy())
                    logger.info(f"Using proxy: {proxy.host}:{proxy.port}")
            
            logger.info(f"开始获取历史文章: {article_url}")
            history_articles = await crawler.get_history_articles(article_url, max_articles)
            account_info = crawler.get_account_info()
            account_name = account_info.get('name', 'Unknown Account')
            
            logger.info(f"发现 {len(history_articles)} 篇历史文章，账号: {account_name}")
        
        if not history_articles:
            logger.warning("未发现历史文章")
            print("❌ 未找到历史文章，可能的原因：")
            print("   - 该公众号没有开放历史文章")
            print("   - 需要关注后才能查看历史文章")
            print("   - 反爬虫机制阻止了访问")
            return
        
        # 显示发现的文章列表
        print(f"\n📚 发现 {len(history_articles)} 篇历史文章")
        print("=" * 80)
        
        for i, article in enumerate(history_articles[:10]):  # 显示前10篇
            print(f"{i+1:2d}. {article['title']}")
            print(f"    URL: {article['url']}")
            print(f"    来源: {article['source']}")
            print()
        
        if len(history_articles) > 10:
            print(f"... 还有 {len(history_articles) - 10} 篇文章")
        
        # 询问是否开始爬取
        print(f"\n🤔 是否开始爬取这些文章？(y/N): ", end="")
        try:
            import sys
            response = input().lower().strip()
            if response in ['y', 'yes', '是']:
                # 开始批量爬取
                await _batch_crawl_articles(history_articles, account_name, db, proxy_manager)
            else:
                print("取消爬取")
        except KeyboardInterrupt:
            print("\n取消爬取")
        
    except Exception as e:
        logger.error(f"获取历史文章失败: {str(e)}")
        raise
    finally:
        db.close()


async def _batch_crawl_articles(articles: list, account_name: str, db, proxy_manager):
    """批量爬取文章"""
    # Create crawl job
    job = CrawlJob(
        account_name=account_name,
        status="running",
        start_time=datetime.now(),
        total_articles=len(articles)
    )
    job_id = db.create_job(job)
    logger.info(f"创建爬取任务 {job_id}，共 {len(articles)} 篇文章")
    
    try:
        async with WeChatCrawler() as crawler:
            # Set proxy if available
            if proxy_manager:
                proxy = proxy_manager.get_next_proxy()
                if proxy:
                    await crawler.browser_manager.stop()
                    await crawler.browser_manager.start(proxy=proxy.to_playwright_proxy())
            
            saved_count = 0
            failed_count = 0
            
            for i, article_info in enumerate(articles):
                try:
                    url = article_info['url']
                    title = article_info['title']
                    
                    # 检查是否是异常URL
                    if _is_error_url(url) or _is_error_title(title):
                        failed_count += 1
                        logger.warning(f"跳过异常文章 {i+1}/{len(articles)}: {title} - {url}")
                        print(f"⚠️  跳过异常: {title}")
                        continue
                    
                    logger.info(f"爬取文章 {i+1}/{len(articles)}: {title}")
                    
                    # 增加随机延迟以避免检测
                    import random
                    delay = random.uniform(5, 15)  # 5-15秒随机延迟
                    logger.info(f"等待 {delay:.1f} 秒以避免反爬检测...")
                    await asyncio.sleep(delay)
                    
                    article = await crawler.crawl_article(url)
                    
                    if article:
                        if db.save_article(article):
                            saved_count += 1
                            print(f"✅ 已保存: {article.title}")
                        else:
                            print(f"ℹ️  已存在: {article.title}")
                    else:
                        failed_count += 1
                        print(f"❌ 失败: {article_info['title']}")
                    
                    # Update job progress
                    db.update_job(job_id, {
                        "crawled_articles": saved_count,
                        "failed_articles": failed_count
                    })
                    
                    # Delay between requests
                    await asyncio.sleep(settings.crawl_delay)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"爬取文章失败 {article_info.get('url', '')}: {str(e)}")
                    continue
            
            # Update final job status
            db.update_job(job_id, {
                "status": "completed",
                "crawled_articles": saved_count,
                "failed_articles": failed_count,
                "end_time": datetime.now()
            })
            
            print(f"\n🎉 爬取完成！保存 {saved_count} 篇新文章，{failed_count} 篇失败")
            
    except Exception as e:
        logger.error(f"批量爬取失败: {str(e)}")
        db.update_job(job_id, {
            "status": "failed",
            "error_message": str(e),
            "end_time": datetime.now()
        })


async def get_series_articles(article_url: str, max_articles: Optional[int] = None, use_proxy: bool = False):
    """
    从系列/合集文章获取所有相关文章
    
    Args:
        article_url: 系列文章URL
        max_articles: 最大获取数量
        use_proxy: 是否使用代理
    """
    # Initialize components
    db = DatabaseManager(use_mongodb=False)
    proxy_manager = ProxyManager() if use_proxy else None
    
    try:
        # Initialize proxy manager if needed
        if proxy_manager:
            await proxy_manager.initialize()
        
        # 获取系列文章列表
        async with SeriesCrawler() as crawler:
            # Set proxy if available
            if proxy_manager:
                proxy = proxy_manager.get_next_proxy()
                if proxy:
                    await crawler.browser_manager.stop()
                    await crawler.browser_manager.start(proxy=proxy.to_playwright_proxy())
                    logger.info(f"Using proxy: {proxy.host}:{proxy.port}")
            
            logger.info(f"开始获取系列文章: {article_url}")
            series_articles = await crawler.get_series_articles(article_url, max_articles)
            series_info = crawler.get_series_info()
            series_name = series_info.get('album_name', 'Unknown Series')
            
            logger.info(f"发现 {len(series_articles)} 篇系列文章，系列: {series_name}")
        
        if not series_articles:
            logger.warning("未发现系列文章")
            print("❌ 未找到系列文章，可能的原因：")
            print("   - 该文章不属于任何合集/系列")
            print("   - 合集目录访问受限")
            print("   - 文章标题不符合系列模式")
            return
        
        # 显示发现的系列文章列表
        print(f"\n📖 发现系列文章：{series_name}")
        print(f"📊 共 {len(series_articles)} 篇文章")
        print("=" * 80)
        
        for i, article in enumerate(series_articles):
            print(f"{i+1:3d}. {article['title']}")
            print(f"     来源: {article['source']} | URL: {article['url'][:50]}...")
            print()
        
        # 询问是否开始爬取
        print(f"\n🤔 是否开始爬取这 {len(series_articles)} 篇系列文章？(y/N): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', '是']:
                # 开始批量爬取
                await _batch_crawl_articles(series_articles, series_name, db, proxy_manager)
            else:
                print("取消爬取")
        except KeyboardInterrupt:
            print("\n取消爬取")
        
    except Exception as e:
        logger.error(f"获取系列文章失败: {str(e)}")
        raise
    finally:
        db.close()


async def discover_from_article(article_url: str, max_articles: Optional[int] = None, use_proxy: bool = False):
    """
    Discover and crawl articles from a WeChat account starting from a single article
    
    Args:
        article_url: URL of a WeChat article to start from
        max_articles: Maximum number of articles to discover and crawl
        use_proxy: Whether to use proxy rotation
    """
    # Initialize components
    db = DatabaseManager(use_mongodb=False)
    proxy_manager = ProxyManager() if use_proxy else None
    
    try:
        # Initialize proxy manager if needed
        if proxy_manager:
            await proxy_manager.initialize()
        
        # Discover articles starting from the given URL
        async with ArticleDiscovery() as discovery:
            # Set proxy if available
            if proxy_manager:
                proxy = proxy_manager.get_next_proxy()
                if proxy:
                    await discovery.browser_manager.stop()
                    await discovery.browser_manager.start(proxy=proxy.to_playwright_proxy())
                    logger.info(f"Using proxy: {proxy.host}:{proxy.port}")
            
            logger.info(f"Starting article discovery from: {article_url}")
            discovered_urls = await discovery.discover_from_article(article_url, max_articles)
            account_name = discovery.get_account_name() or "Unknown Account"
            
            logger.info(f"Discovered {len(discovered_urls)} articles from account: {account_name}")
        
        if not discovered_urls:
            logger.warning("No articles discovered")
            return
        
        # Create crawl job
        job = CrawlJob(
            account_name=account_name,
            status="running",
            start_time=datetime.now(),
            total_articles=len(discovered_urls)
        )
        job_id = db.create_job(job)
        logger.info(f"Created crawl job {job_id} for {len(discovered_urls)} discovered articles")
        
        # Crawl all discovered articles
        async with WeChatCrawler() as crawler:
            # Set proxy if available
            if proxy_manager:
                proxy = proxy_manager.get_next_proxy()
                if proxy:
                    await crawler.browser_manager.stop()
                    await crawler.browser_manager.start(proxy=proxy.to_playwright_proxy())
            
            saved_count = 0
            failed_count = 0
            
            for i, url in enumerate(discovered_urls):
                try:
                    logger.info(f"Crawling article {i+1}/{len(discovered_urls)}: {url}")
                    article = await crawler.crawl_article(url)
                    
                    if article:
                        if db.save_article(article):
                            saved_count += 1
                            logger.info(f"Saved article: {article.title}")
                        else:
                            logger.info(f"Article already exists: {article.title}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to parse article: {url}")
                    
                    # Update job progress
                    db.update_job(job_id, {
                        "crawled_articles": saved_count,
                        "failed_articles": failed_count
                    })
                    
                    # Delay between requests
                    await asyncio.sleep(settings.crawl_delay)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error crawling article {url}: {str(e)}")
                    continue
            
            # Update final job status
            db.update_job(job_id, {
                "status": "completed",
                "crawled_articles": saved_count,
                "failed_articles": failed_count,
                "end_time": datetime.now()
            })
            
            logger.info(f"Discovery crawl completed! Saved {saved_count} new articles, {failed_count} failed")
            
    except Exception as e:
        logger.error(f"Discovery crawl failed: {str(e)}")
        if 'job_id' in locals():
            db.update_job(job_id, {
                "status": "failed",
                "error_message": str(e),
                "end_time": datetime.now()
            })
        raise
    finally:
        db.close()


async def show_stats():
    """Show database statistics"""
    db = DatabaseManager(use_mongodb=False)
    
    try:
        total_articles = db.get_article_count()
        
        # Get articles by account
        all_articles = db.get_articles_by_account("", limit=1000)
        accounts = {}
        for article in all_articles:
            account_name = article.get('account_name', 'Unknown')
            if account_name not in accounts:
                accounts[account_name] = 0
            accounts[account_name] += 1
        
        # Get recent jobs
        recent_jobs = db.get_jobs(limit=10)
        
        print("\n=== WeChat Crawler Statistics ===")
        print(f"📊 Total Articles: {total_articles}")
        print(f"👥 Total Accounts: {len(accounts)}")
        
        print(f"\n📱 Articles by Account:")
        for account, count in sorted(accounts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {account}: {count} articles")
        
        print(f"\n🔄 Recent Crawl Jobs:")
        for job in recent_jobs:
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "running": "🔄",
                "pending": "⏳"
            }.get(job['status'], "❓")
            
            print(f"{status_emoji} {job['account_name']} - {job['status']} "
                  f"({job['crawled_articles']}/{job['total_articles']} articles)")
        
    finally:
        db.close()


async def list_articles(account_name: Optional[str] = None, limit: int = 20, search: Optional[str] = None):
    """List articles with optional filtering"""
    db = DatabaseManager(use_mongodb=False)
    
    try:
        if search:
            articles = db.search_articles(search, limit)
            print(f"\n🔍 Search results for '{search}' (showing {len(articles)} results):")
        elif account_name:
            articles = db.get_articles_by_account(account_name, limit)
            print(f"\n📱 Articles from '{account_name}' (showing {len(articles)} results):")
        else:
            articles = db.get_articles_by_account("", limit)
            print(f"\n📄 All articles (showing {len(articles)} results):")
        
        print("=" * 100)
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No Title')[:60]
            account = article.get('account_name', 'Unknown')
            author = article.get('author', 'Unknown')
            publish_time = article.get('publish_time', 'Unknown')
            url = article.get('url', '')
            
            print(f"{i:3d}. {title}")
            print(f"     📱 Account: {account} | ✍️  Author: {author}")
            print(f"     📅 Published: {publish_time}")
            print(f"     🔗 URL: {url}")
            print()
        
        if not articles:
            print("No articles found.")
        
    finally:
        db.close()


async def show_article_detail(article_id: Optional[int] = None, url: Optional[str] = None):
    """Show detailed information about a specific article"""
    db = DatabaseManager(use_mongodb=False)
    
    try:
        if url:
            article = db.get_article(url)
        elif article_id:
            # This would need to be implemented in the database manager
            print("❌ Search by ID not yet implemented. Use URL instead.")
            return
        else:
            print("❌ Please provide either article URL or ID")
            return
        
        if not article:
            print("❌ Article not found")
            return
        
        print("\n" + "=" * 80)
        print("📄 ARTICLE DETAILS")
        print("=" * 80)
        
        print(f"📰 Title: {article.get('title', 'No Title')}")
        print(f"✍️  Author: {article.get('author', 'Unknown')}")
        print(f"📱 Account: {article.get('account_name', 'Unknown')}")
        print(f"📅 Published: {article.get('publish_time', 'Unknown')}")
        print(f"🕒 Crawled: {article.get('crawl_time', 'Unknown')}")
        print(f"🔗 URL: {article.get('url', '')}")
        
        images = article.get('images', [])
        print(f"🖼️  Images: {len(images)} found")
        if images:
            for i, img_url in enumerate(images[:3], 1):
                print(f"   {i}. {img_url}")
            if len(images) > 3:
                print(f"   ... and {len(images) - 3} more images")
        
        content = article.get('content', '')
        cleaned_content = _clean_article_content(content)
        
        print(f"\n📝 Content (原始: {len(content)} 字符, 清理后: {len(cleaned_content)} 字符):")
        print("-" * 80)
        
        if cleaned_content:
            # Show first 1000 characters of cleaned content
            preview = cleaned_content[:1000]
            print(preview)
            if len(cleaned_content) > 1000:
                print(f"\n... (showing first 1000 of {len(cleaned_content)} characters)")
                print(f"💡 Full cleaned content is available")
        else:
            print("No content available after cleaning")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()


async def import_json_to_database(input_file: str, account_name: Optional[str] = None, 
                                  skip_existing: bool = True, clean_content: bool = True):
    """
    将JSON文件中的数据导入到数据库
    
    Args:
        input_file: JSON文件路径
        account_name: 指定账号名称（如果JSON中没有）
        skip_existing: 是否跳过已存在的文章（根据URL判断）
        clean_content: 是否清理文章内容
    """
    db = DatabaseManager(use_mongodb=False)
    
    try:
        # 读取JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles_data = data.get('articles', [])
        if not articles_data:
            print(f"❌ JSON文件中没有找到articles字段或为空")
            return
        
        print(f"📄 读取JSON文件: {input_file}")
        print(f"📊 发现 {len(articles_data)} 条数据")
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        # 辅助函数定义
        def safe_strip(value):
            """安全地处理字符串strip，避免None值错误"""
            if value is None:
                return ''
            return str(value).strip()
        
        def parse_content_items(content_text):
            """解析文章内容，提取独立的文章条目"""
            if not content_text:
                return []
            
            import re
            items = []
            
            # 用更智能的方式切分：按照 "标题\nURL\n作者:\n内容" 的模式
            url_pattern = r'https?://[^\s]+'
            
            # 首先找到所有URL的位置，作为切分点
            urls_in_text = list(re.finditer(url_pattern, content_text))
            
            if not urls_in_text:
                return []
            
            # 按照URL位置切分内容
            for i, url_match in enumerate(urls_in_text):
                # 确定当前文章的开始和结束位置
                start_pos = 0 if i == 0 else urls_in_text[i-1].end()
                end_pos = urls_in_text[i+1].start() if i+1 < len(urls_in_text) else len(content_text)
                
                # 提取当前文章的完整文本块
                article_block = content_text[start_pos:end_pos].strip()
                
                if not article_block:
                    continue
                
                # 分析这个文本块
                url = url_match.group()
                lines = article_block.split('\n')
                
                title = ''
                author = ''
                content_lines = []
                
                url_line_index = -1
                for j, line in enumerate(lines):
                    if url in line:
                        url_line_index = j
                        # URL前面的文本可能是标题
                        url_pos = line.find(url)
                        if url_pos > 0:
                            title = line[:url_pos].strip()
                        break
                
                # 如果URL行前面还有行，可能是标题
                if url_line_index > 0 and not title:
                    for j in range(url_line_index-1, -1, -1):
                        line = lines[j].strip()
                        if line and len(line) < 200:  # 标题不应该太长
                            title = line
                            break
                
                # URL行后面的内容
                for j in range(url_line_index + 1, len(lines)):
                    line = lines[j].strip()
                    if not line:
                        continue
                    
                    # 检查是否是作者格式 (Author:)
                    if ':' in line and len(line.split(':', 1)[0].strip()) < 20:
                        parts = line.split(':', 1)
                        potential_author = parts[0].strip()
                        remaining_content = parts[1].strip()
                        
                        # 如果看起来像作者名
                        if not re.search(r'https?://', potential_author):
                            author = potential_author
                            if remaining_content:
                                content_lines.append(remaining_content)
                        else:
                            content_lines.append(line)
                    else:
                        content_lines.append(line)
                
                # 如果没有找到明确的标题，尝试从内容的第一行提取
                if not title and content_lines:
                    first_line = content_lines[0]
                    if len(first_line) < 150:  # 可能是标题
                        title = first_line
                        content_lines = content_lines[1:]
                
                content = '\n'.join(content_lines).strip()
                
                if title and url:
                    items.append({
                        'title': title,
                        'url': url,
                        'content': content,
                        'author': author
                    })
            
            return items
        
        for item in articles_data:
            try:
                if 'attributes' in item:
                    # 结构化格式：{id: x, attributes: {...}}
                    attrs = item['attributes']
                    title = safe_strip(attrs.get('title', ''))
                    url = safe_strip(attrs.get('url', ''))
                    author = safe_strip(attrs.get('author', ''))
                    introduce = safe_strip(attrs.get('introduce', ''))
                    full_content = safe_strip(attrs.get('full_content', ''))
                    episode = safe_strip(attrs.get('episode', ''))
                    time_str = safe_strip(attrs.get('time', ''))
                else:
                    # 简单格式：直接是文章字段
                    title = safe_strip(item.get('title', ''))
                    url = safe_strip(item.get('url', ''))
                    author = safe_strip(item.get('author', ''))
                    introduce = safe_strip(item.get('introduce', item.get('content', '')))
                    full_content = safe_strip(item.get('full_content', ''))
                    episode = safe_strip(item.get('episode', ''))
                    time_str = safe_strip(item.get('time', item.get('publish_time', '')))
                
                # 检查是否是合集文章（包含多个子文章）
                content_to_parse = full_content or introduce
                parsed_items = []
                
                if content_to_parse and (title == "Web3 极客日报" or "极客日报" in title):
                    # 这是一个合集文章，需要拆分
                    parsed_items = parse_content_items(content_to_parse)
                    print(f"📰 发现合集文章: {title}, 拆分出 {len(parsed_items)} 个子文章")
                
                # 如果没有拆分出子文章，或者不是合集，保持原样
                if not parsed_items:
                    parsed_items = [{
                        'title': title,
                        'url': url,
                        'content': content_to_parse,
                        'author': author
                    }]
                
                # URL格式修复
                def fix_url(url_str):
                    """修复常见的URL格式问题"""
                    if not url_str:
                        return ''
                    
                    url_str = url_str.strip()
                    
                    # 处理包含多个URL的情况，取第一个有效的
                    if ' ' in url_str and ('http://' in url_str or 'https://' in url_str):
                        parts = url_str.split()
                        for part in parts:
                            if part.startswith(('http://', 'https://')):
                                url_str = part
                                break
                    
                    # 处理中文前缀的URL（如：中文版：http://...）
                    if '：http' in url_str:
                        url_str = url_str.split('：http')[1]
                        url_str = 'http' + url_str
                    elif ':http' in url_str:
                        url_str = url_str.split(':http')[1]  
                        url_str = 'http' + url_str
                    
                    # 修复常见的拼写错误
                    url_str = url_str.replace('hu.baittps://', 'https://')
                    url_str = url_str.replace('htps://', 'https://')
                    url_str = url_str.replace('htp://', 'http://')
                    
                    # 如果没有协议前缀，添加https://
                    if url_str and not url_str.startswith(('http://', 'https://', 'ftp://')):
                        # 检查是否是域名格式
                        if '.' in url_str and not url_str.startswith('/'):
                            url_str = 'https://' + url_str
                    
                    # 移除URL末尾的多余空格和特殊字符
                    url_str = url_str.rstrip()
                    
                    # 检查URL是否包含无效字符（空格、中文等）
                    if url_str.startswith(('http://', 'https://')):
                        # 如果包含空格或中文字符，可能是无效URL
                        import re
                        if re.search(r'[\s\u4e00-\u9fff]', url_str):
                            # 尝试提取第一个有效的URL部分
                            match = re.search(r'https?://[^\s\u4e00-\u9fff]+', url_str)
                            if match:
                                url_str = match.group(0)
                            else:
                                return ''  # 无法修复，返回空字符串
                    
                    return url_str
                
                # 解析发布时间
                publish_time = None
                if time_str:
                    try:
                        # 尝试多种时间格式
                        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d', '%Y年%m月%d日']:
                            try:
                                publish_time = datetime.strptime(time_str, fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass
                
                # 如果没有有效的发布时间，使用当前时间
                if publish_time is None:
                    publish_time = datetime.now()
                
                # 处理拆分后的每个子文章
                for parsed_item in parsed_items:
                    sub_title = parsed_item.get('title', '').strip()
                    sub_url = parsed_item.get('url', '').strip()
                    sub_content = parsed_item.get('content', '').strip()
                    sub_author = parsed_item.get('author', '').strip() or author
                    
                    # 修复URL
                    sub_url = fix_url(sub_url)
                    
                    # 验证必需字段
                    if not sub_title or not sub_url:
                        print(f"⚠️  跳过无效子文章 - 缺少标题或URL: {sub_title[:30] if sub_title else 'No title'}")
                        error_count += 1
                        continue
                    
                    # 验证URL格式
                    if sub_url and not sub_url.startswith(('http://', 'https://')):
                        print(f"⚠️  跳过无效URL格式: {sub_url[:50]}")
                        error_count += 1
                        continue
                    
                    # 检查是否已存在
                    if skip_existing and db.get_article_by_url(sub_url):
                        skipped_count += 1
                        continue
                    
                    # 准备内容
                    final_content = sub_content
                    if clean_content and final_content:
                        final_content = _clean_article_content(final_content)
                    
                    # 为子文章使用稍微不同的时间（避免完全相同）
                    sub_publish_time = publish_time
                    if len(parsed_items) > 1:
                        import random
                        # 添加随机的几分钟偏移
                        offset_minutes = random.randint(1, len(parsed_items) * 2)
                        from datetime import timedelta
                        sub_publish_time = publish_time + timedelta(minutes=offset_minutes)
                    
                    # 创建Article对象
                    from storage.models import Article
                    article = Article(
                        url=sub_url,
                        title=sub_title,
                        content=final_content or '内容暂无',
                        author=sub_author or 'Unknown',
                        account_name=account_name or sub_author or 'Imported',
                        publish_time=sub_publish_time,
                        images=[],
                        cover_image=None,
                        read_count=0,
                        like_count=0,
                        comment_count=0,
                        raw_html=None,
                        crawl_time=datetime.now()
                    )
                    
                    # 保存到数据库
                    if db.save_article(article):
                        imported_count += 1
                        print(f"✅ 导入: {sub_title[:50]}")
                    else:
                        print(f"ℹ️  已存在: {sub_title[:50]}")
                        skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"❌ 导入失败: {str(e)}")
                continue
        
        print(f"\n🎉 导入完成！")
        print(f"📊 导入统计:")
        print(f"  - 成功导入: {imported_count} 条")
        print(f"  - 已存在跳过: {skipped_count} 条") 
        print(f"  - 错误数据: {error_count} 条")
        print(f"  - 总处理: {len(articles_data)} 条")
        
        return imported_count
        
    except FileNotFoundError:
        print(f"❌ 文件未找到: {input_file}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        raise
    finally:
        db.close()


async def delete_articles(keyword: Optional[str] = None, account: Optional[str] = None, 
                          url_pattern: Optional[str] = None, confirm: bool = True):
    """
    删除匹配条件的文章
    
    Args:
        keyword: 标题关键词匹配
        account: 账号名称匹配
        url_pattern: URL模式匹配
        confirm: 是否需要确认
    """
    db = DatabaseManager(use_mongodb=False)
    
    try:
        # 构建查询条件
        conditions = []
        if keyword:
            conditions.append(f"标题包含 '{keyword}'")
        if account:
            conditions.append(f"账号为 '{account}'")
        if url_pattern:
            conditions.append(f"URL包含 '{url_pattern}'")
        
        if not conditions:
            print("❌ 请至少指定一个删除条件")
            return
        
        print(f"🔍 查找匹配以下条件的文章:")
        for condition in conditions:
            print(f"  - {condition}")
        
        # 查询匹配的文章
        if db.use_mongodb:
            # MongoDB查询逻辑
            query = {}
            if keyword:
                query["title"] = {"$regex": keyword, "$options": "i"}
            if account:
                query["account_name"] = account
            if url_pattern:
                query["url"] = {"$regex": url_pattern, "$options": "i"}
            
            articles = list(db.articles_collection.find(query))
        else:
            # SQLite查询逻辑
            with db.get_session() as session:
                from storage.models import ArticleDB
                from sqlalchemy import and_, or_
                
                query = session.query(ArticleDB)
                
                filter_conditions = []
                if keyword:
                    filter_conditions.append(ArticleDB.title.like(f'%{keyword}%'))
                if account:
                    filter_conditions.append(ArticleDB.account_name == account)
                if url_pattern:
                    filter_conditions.append(ArticleDB.url.like(f'%{url_pattern}%'))
                
                if filter_conditions:
                    query = query.filter(and_(*filter_conditions))
                
                articles = query.all()
                articles = [article.to_dict() for article in articles]
        
        if not articles:
            print("✅ 没有找到匹配的文章")
            return
        
        print(f"\n📋 找到 {len(articles)} 篇匹配的文章:")
        for i, article in enumerate(articles[:10], 1):  # 最多显示10篇
            title = article.get('title', '')[:50]
            author = article.get('author', '')
            account_name = article.get('account_name', '')
            url = article.get('url', '')[:50]
            print(f"  {i}. {title}")
            print(f"     作者: {author} | 账号: {account_name}")
            print(f"     URL: {url}...")
            print()
        
        if len(articles) > 10:
            print(f"     ... 还有 {len(articles) - 10} 篇文章")
        
        # 确认删除
        if confirm:
            print(f"⚠️  警告: 此操作将永久删除 {len(articles)} 篇文章！")
            response = input("确认删除？输入 'yes' 继续，其他任意键取消: ").strip().lower()
            if response != 'yes':
                print("❌ 删除操作已取消")
                return
        
        # 执行删除
        deleted_count = 0
        
        if db.use_mongodb:
            # MongoDB删除
            result = db.articles_collection.delete_many(query)
            deleted_count = result.deleted_count
        else:
            # SQLite删除
            with db.get_session() as session:
                from storage.models import ArticleDB
                
                for article in articles:
                    article_obj = session.query(ArticleDB).filter_by(url=article['url']).first()
                    if article_obj:
                        session.delete(article_obj)
                        deleted_count += 1
        
        print(f"\n🎉 删除完成！")
        print(f"📊 删除统计: 成功删除 {deleted_count} 篇文章")
        
        # 显示删除后的统计
        total_remaining = db.get_article_count()
        print(f"📈 数据库现状: 剩余 {total_remaining} 篇文章")
        
        return deleted_count
        
    except Exception as e:
        print(f"❌ 删除失败: {str(e)}")
        raise
    finally:
        db.close()


async def clear_database(confirm: bool = True):
    """
    清空数据库中的所有文章
    
    Args:
        confirm: 是否需要确认（默认True）
    """
    db = DatabaseManager(use_mongodb=False)
    
    try:
        # 获取当前文章数量
        total_count = db.get_article_count()
        
        if total_count == 0:
            print("📊 数据库已经是空的，无需清理")
            return 0
        
        print(f"📊 数据库当前包含 {total_count} 篇文章")
        
        # 确认删除
        if confirm:
            print(f"⚠️  警告: 此操作将永久删除数据库中的所有 {total_count} 篇文章！")
            response = input("确认清空数据库？输入 'YES' 继续，其他任意键取消: ").strip()
            if response != 'YES':
                print("❌ 清空操作已取消")
                return 0
        
        # 执行清空
        deleted_count = 0
        
        if db.use_mongodb:
            # MongoDB删除所有
            result = db.articles_collection.delete_many({})
            deleted_count = result.deleted_count
        else:
            # SQLite删除所有
            with db.get_session() as session:
                from storage.models import ArticleDB
                deleted_count = session.query(ArticleDB).delete()
        
        print(f"\n🎉 数据库清空完成！")
        print(f"📊 删除统计: 成功删除 {deleted_count} 篇文章")
        print(f"📈 数据库现状: 数据库已清空")
        
        return deleted_count
        
    except Exception as e:
        print(f"❌ 清空数据库失败: {str(e)}")
        raise
    finally:
        db.close()


async def export_articles(account_name: Optional[str] = None, format_type: str = "txt"):
    """Export articles to file"""
    db = DatabaseManager(use_mongodb=False)
    
    try:
        if account_name:
            articles = db.get_articles_by_account(account_name, limit=1000)
            filename = f"export_{account_name}_{format_type}"
        else:
            articles = db.get_articles_by_account("", limit=1000)
            filename = f"export_all_articles.{format_type}"
        
        if not articles:
            print("❌ No articles found to export")
            return
        
        # Clean filename
        import re
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        filepath = f"data/{filename}"
        
        # Create data directory if not exists
        import os
        os.makedirs("data", exist_ok=True)
        
        if format_type == "txt":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"WeChat Articles Export\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Articles: {len(articles)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, article in enumerate(articles, 1):
                    # 清理文章内容
                    original_content = article.get('content', 'No content')
                    cleaned_content = _clean_article_content(original_content)
                    
                    f.write(f"Article {i}\n")
                    f.write(f"Title: {article.get('title', 'No Title')}\n")
                    f.write(f"Author: {article.get('author', 'Unknown')}\n")
                    f.write(f"Account: {article.get('account_name', 'Unknown')}\n")
                    f.write(f"Published: {article.get('publish_time', 'Unknown')}\n")
                    f.write(f"URL: {article.get('url', '')}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"{cleaned_content}\n")
                    f.write("\n" + "=" * 80 + "\n\n")
        
        elif format_type == "json":
            import json
            
            # 转换为结构化格式
            structured_articles = []
            
            # 检查是否是Web3极客日报，需要特殊处理
            is_daily = any('极客日报' in article.get('title', '') for article in articles)
            
            if is_daily:
                # Web3极客日报特殊处理：提取每篇文章中的多个项目
                daily_id = 1
                for article_idx, article in enumerate(articles):
                    episode = _extract_episode_from_title(article.get('title', ''))
                    publish_time = article.get('publish_time', '')
                    
                    # 格式化时间
                    if publish_time:
                        try:
                            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y年%m月%d日']:
                                try:
                                    dt = datetime.strptime(publish_time.split(' ')[0], fmt)
                                    publish_time = dt.strftime('%Y-%m-%d')
                                    break
                                except:
                                    continue
                        except:
                            pass
                    
                    # 提取日报中的各个项目
                    items = _extract_daily_items_from_content(article.get('content', ''))
                    
                    if items:
                        # 为每个项目创建一个条目
                        for item in items:
                            structured_item = {
                                "id": daily_id,
                                "attributes": {
                                    "episode": episode,
                                    "title": item.get('title', ''),
                                    "author": item.get('author', 'Unknown'),
                                    "url": item.get('url', ''),
                                    "time": publish_time,
                                    "introduce": item.get('introduce', '')
                                }
                            }
                            structured_articles.append(structured_item)
                            daily_id += 1
                    else:
                        # 如果无法提取项目，使用整篇文章作为一个条目
                        structured_articles.append(_format_article_to_structured(article, daily_id))
                        daily_id += 1
            else:
                # 普通文章处理
                for idx, article in enumerate(articles, 1):
                    structured_articles.append(_format_article_to_structured(article, idx))
            
            # 保存结构化数据
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "export_info": {
                        "total": len(structured_articles),
                        "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "account": account_name or "all"
                    },
                    "articles": structured_articles
                }, f, ensure_ascii=False, indent=2, default=str)
            
            # 额外保存一个简化版本（不含full_content）
            simplified_filepath = filepath.replace('.json', '_simplified.json')
            simplified_articles = []
            for article in structured_articles:
                simplified = article.copy()
                if 'attributes' in simplified and 'full_content' in simplified['attributes']:
                    del simplified['attributes']['full_content']
                simplified_articles.append(simplified)
            
            with open(simplified_filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "export_info": {
                        "total": len(simplified_articles),
                        "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "account": account_name or "all"
                    },
                    "articles": simplified_articles
                }, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📄 额外保存简化版本到: {simplified_filepath}")
        
        elif format_type == "csv":
            import csv
            # 清理所有文章内容
            cleaned_articles = []
            for article in articles:
                cleaned_article = article.copy()
                if 'content' in cleaned_article:
                    cleaned_article['content'] = _clean_article_content(cleaned_article['content'])
                cleaned_articles.append(cleaned_article)
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                if cleaned_articles:
                    writer = csv.DictWriter(f, fieldnames=cleaned_articles[0].keys())
                    writer.writeheader()
                    writer.writerows(cleaned_articles)
        
        print(f"✅ Exported {len(articles)} articles to: {filepath}")
        
    finally:
        db.close()


async def handle_analytics_command(args):
    """处理analytics相关命令"""
    
    def save_results_if_needed(results, output_file, description):
        """如果指定了输出文件，保存结果"""
        if output_file:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else 'data', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 {description}结果已保存到: {output_file}")
    
    try:
        if args.analytics_command == 'trends':
            print(f"🔍 分析最近 {args.days} 天的技术趋势...")
            analyzer = TrendAnalyzer()
            results = analyzer.analyze_technology_trends(args.days)
            
            if "error" not in results:
                print(f"\n📊 技术趋势分析结果 (最近 {args.days} 天)")
                print("=" * 60)
                print(f"📄 分析文章数: {results['total_articles']}")
                print(f"🏷️  发现关键词: {results['total_keywords']}")
                print(f"🔝 热门技术趋势 (前10名):")
                
                for i, trend in enumerate(results['top_trends'][:10], 1):
                    print(f"  {i:2d}. {trend['keyword']:<20} - {trend['count']:3d} 次 ({trend['percentage']:5.1f}%)")
                
                save_results_if_needed(results, args.output, "技术趋势分析")
            else:
                print(f"❌ 分析失败: {results['error']}")
        
        elif args.analytics_command == 'authors':
            print(f"👥 分析最近 {args.days} 天的作者活跃度...")
            analyzer = TrendAnalyzer()
            results = analyzer.analyze_author_activity(args.days)
            
            if "error" not in results:
                print(f"\n📊 作者活跃度分析结果 (最近 {args.days} 天)")
                print("=" * 60)
                print(f"👨‍💻 活跃作者数: {results['total_authors']}")
                print(f"📄 分析文章数: {results['total_articles']}")
                print(f"🏆 影响力排行榜 (前10名):")
                
                for i, author in enumerate(results['top_authors'][:10], 1):
                    print(f"  {i:2d}. {author['author']:<20} - {author['article_count']:2d} 篇 "
                          f"(影响力: {author['influence_score']:5.1f}, 日均: {author['productivity']:4.2f})")
                    print(f"      关键词: {', '.join(author['top_keywords'])}")
                
                print(f"\n📈 作者分布:")
                dist = results['author_distribution']
                print(f"  • 高产作者 (≥5篇): {dist['highly_active']} 人")
                print(f"  • 中产作者 (2-4篇): {dist['moderately_active']} 人")
                print(f"  • 偶发作者 (1篇): {dist['occasionally_active']} 人")
                
                save_results_if_needed(results, args.output, "作者活跃度分析")
            else:
                print(f"❌ 分析失败: {results['error']}")
        
        elif args.analytics_command == 'publishing':
            print(f"📅 分析最近 {args.days} 天的发布模式...")
            analyzer = TrendAnalyzer()
            results = analyzer.analyze_publication_patterns(args.days)
            
            if "error" not in results:
                print(f"\n📊 发布模式分析结果 (最近 {args.days} 天)")
                print("=" * 60)
                print(f"📄 分析文章数: {results['total_articles']}")
                
                daily_stats = results['daily_statistics']
                print(f"📈 日发布统计:")
                print(f"  • 日均发布: {daily_stats['average']} 篇")
                print(f"  • 最高单日: {daily_stats['maximum']} 篇")
                print(f"  • 最低单日: {daily_stats['minimum']} 篇")
                print(f"  • 最活跃日: {daily_stats['most_active_day']['date']} ({daily_stats['most_active_day']['count']} 篇)")
                
                temporal = results['temporal_patterns']
                print(f"⏰ 时间模式:")
                print(f"  • 最活跃时段: {temporal['most_active_hour']['hour']:02d}:00 ({temporal['most_active_hour']['count']} 篇)")
                print(f"  • 最活跃月份: {temporal['most_active_month']['month']} ({temporal['most_active_month']['count']} 篇)")
                
                summary = results['distribution_summary']
                print(f"📊 覆盖统计:")
                print(f"  • 有文章的天数: {summary['days_with_articles']} 天")
                print(f"  • 活跃周数: {summary['active_weeks']} 周")
                print(f"  • 覆盖率: {summary['coverage_rate']}%")
                
                save_results_if_needed(results, args.output, "发布模式分析")
            else:
                print(f"❌ 分析失败: {results['error']}")
        
        elif args.analytics_command == 'report':
            print(f"📋 生成综合数据分析报告 (最近 {args.days} 天)...")
            analyzer = TrendAnalyzer()
            results = analyzer.get_comprehensive_trends(args.days)
            
            if "error" not in results:
                summary = results['summary']
                print(f"\n📊 综合数据分析报告")
                print("=" * 60)
                print(f"📄 分析文章总数: {summary['total_articles_analyzed']}")
                print(f"👥 活跃作者数量: {summary['total_authors']}")
                print(f"🔥 最热门技术: {summary['most_discussed_tech']}")
                print(f"🏆 最高产作者: {summary['most_productive_author']}")
                print(f"📈 日均发布量: {summary['daily_average']}")
                
                print(f"\n💡 详细分析数据已包含在导出结果中")
                save_results_if_needed(results, args.output, "综合分析报告")
            else:
                print(f"❌ 分析失败: {results['error']}")
        
        elif args.analytics_command == 'tags':
            if args.tag_command == 'extract':
                print(f"🏷️  开始智能标签提取...")
                if args.limit:
                    print(f"📄 处理文章数限制: {args.limit}")
                
                extractor = TagExtractor()
                results = extractor.batch_tag_articles(limit=args.limit)
                
                if "error" not in results:
                    summary = results['summary']
                    print(f"\n📊 标签提取结果")
                    print("=" * 60)
                    print(f"📄 处理文章数: {summary['total_articles_processed']}")
                    print(f"✅ 成功标记数: {summary['successfully_tagged']}")
                    
                    print(f"\n🏷️  热门标签分类:")
                    for category, tags in summary['most_common_tags'].items():
                        if tags:
                            print(f"  {category}:")
                            for tag, count in list(tags.items())[:5]:
                                print(f"    • {tag}: {count} 次")
                    
                    save_results_if_needed(results, args.output, "标签提取")
                else:
                    print(f"❌ 标签提取失败: {results['error']}")
            
            elif args.tag_command == 'trends':
                print(f"📈 分析最近 {args.days} 天的标签趋势...")
                extractor = TagExtractor()
                results = extractor.analyze_tag_trends(args.days)
                
                if "error" not in results:
                    print(f"\n📊 标签趋势分析结果 (最近 {args.days} 天)")
                    print("=" * 60)
                    print(f"📄 分析文章数: {results['total_articles']}")
                    
                    summary = results['summary']
                    print(f"🔥 最热门标签类别: {summary['most_popular_category']}")
                    print(f"🏷️  独特标签总数: {summary['total_unique_tags']}")
                    print(f"📊 平均每篇标签: {summary['average_tags_per_article']}")
                    
                    print(f"\n📈 热门标签分布:")
                    for category, trends in results['trending_tags'].items():
                        if trends:
                            print(f"  {category}:")
                            for trend in trends[:3]:
                                print(f"    • {trend['tag']}: {trend['count']} 次 ({trend['percentage']}%)")
                    
                    save_results_if_needed(results, args.output, "标签趋势分析")
                else:
                    print(f"❌ 标签趋势分析失败: {results['error']}")
            
            else:
                print("❌ 请指定标签子命令: extract 或 trends")
        
        elif args.analytics_command == 'quality':
            if args.quality_command == 'evaluate':
                print(f"📝 开始内容质量评估...")
                if args.limit:
                    print(f"📄 评估文章数限制: {args.limit}")
                
                evaluator = ContentEvaluator()
                results = evaluator.batch_evaluate_quality(limit=args.limit)
                
                if "error" not in results:
                    summary = results['summary']
                    print(f"\n📊 内容质量评估结果")
                    print("=" * 60)
                    print(f"📄 评估文章数: {summary['successfully_evaluated']}")
                    
                    quality_dist = summary['quality_distribution']
                    print(f"🏆 质量等级分布:")
                    print(f"  • A级 (优秀): {quality_dist['A']} 篇")
                    print(f"  • B级 (良好): {quality_dist['B']} 篇")
                    print(f"  • C级 (一般): {quality_dist['C']} 篇")
                    print(f"  • D级 (待改进): {quality_dist['D']} 篇")
                    
                    insights = summary['quality_insights']
                    print(f"\n📈 质量洞察:")
                    print(f"  • 高质量率: {insights['high_quality_rate']}%")
                    print(f"  • 需改进率: {insights['needs_improvement_rate']}%")
                    print(f"  • 平均字数: {insights['average_word_count']} 字")
                    print(f"  • 平均阅读时间: {insights['average_reading_time']} 分钟")
                    
                    avg_metrics = summary['average_metrics']
                    print(f"\n📊 平均质量指标:")
                    print(f"  • 综合评分: {avg_metrics['overall']:.3f}")
                    print(f"  • 原创性: {avg_metrics['originality']:.3f}")
                    print(f"  • 技术深度: {avg_metrics['technical_depth']:.3f}")
                    print(f"  • 可读性: {avg_metrics['readability']:.3f}")
                    print(f"  • 结构化: {avg_metrics['structure']:.3f}")
                    
                    save_results_if_needed(results, args.output, "内容质量评估")
                else:
                    print(f"❌ 质量评估失败: {results['error']}")
            
            elif args.quality_command == 'insights':
                print(f"💡 生成内容质量洞察报告...")
                evaluator = ContentEvaluator()
                results = evaluator.get_quality_insights(min_quality_score=args.min_score)
                
                if "error" not in results:
                    print(f"\n📊 内容质量洞察报告")
                    print("=" * 60)
                    
                    if 'quality_insights' in results:
                        insights = results['quality_insights']
                        if 'high_quality_characteristics' in insights:
                            chars = insights['high_quality_characteristics']
                            print(f"🏆 高质量文章特征 (≥{args.min_score} 分):")
                            print(f"  • 样本数量: {chars['sample_count']} 篇")
                            print(f"  • 平均字数: {chars['average_word_count']} 字")
                            print(f"  • 共同特征:")
                            for pattern in chars.get('common_patterns', []):
                                print(f"    - {pattern}")
                        
                        if 'improvement_recommendations' in insights:
                            print(f"\n💡 改进建议:")
                            for rec in insights['improvement_recommendations']:
                                print(f"  • {rec}")
                    
                    save_results_if_needed(results, args.output, "质量洞察报告")
                else:
                    print(f"❌ 质量洞察分析失败: {results['error']}")
            
            else:
                print("❌ 请指定质量分析子命令: evaluate 或 insights")
        
        else:
            print("❌ 请指定analytics子命令: trends, authors, publishing, report, tags, 或 quality")
    
    except Exception as e:
        logger.error(f"Analytics命令执行失败: {str(e)}")
        print(f"❌ 执行失败: {str(e)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="WeChat Public Account Crawler")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Crawl account command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl a WeChat public account')
    crawl_parser.add_argument('account', help='WeChat public account name')
    crawl_parser.add_argument('--max-articles', type=int, help='Maximum number of articles to crawl')
    crawl_parser.add_argument('--use-proxy', action='store_true', help='Use proxy rotation')
    
    # Crawl single article command
    article_parser = subparsers.add_parser('article', help='Crawl a single article')
    article_parser.add_argument('url', help='Article URL')
    article_parser.add_argument('--show-content', action='store_true', help='Display article content in console')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test crawler with predefined article')
    test_parser.add_argument('--show-content', action='store_true', help='Display article content in console')
    
    # Discover from article command
    discover_parser = subparsers.add_parser('discover', help='Discover and crawl articles starting from a single article')
    discover_parser.add_argument('url', help='WeChat article URL to start discovery from')
    discover_parser.add_argument('--max-articles', type=int, help='Maximum number of articles to discover and crawl')
    discover_parser.add_argument('--use-proxy', action='store_true', help='Use proxy rotation')
    
    # History articles command
    history_parser = subparsers.add_parser('history', help='Get history articles from a WeChat account starting from one article')
    history_parser.add_argument('url', help='WeChat article URL to start from')
    history_parser.add_argument('--max-articles', type=int, help='Maximum number of history articles to get')
    history_parser.add_argument('--use-proxy', action='store_true', help='Use proxy rotation')
    
    # Series articles command
    series_parser = subparsers.add_parser('series', help='Get all articles from a WeChat series/album (most effective for series)')
    series_parser.add_argument('url', help='WeChat series article URL')
    series_parser.add_argument('--max-articles', type=int, help='Maximum number of series articles to get')
    series_parser.add_argument('--use-proxy', action='store_true', help='Use proxy rotation')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show crawler statistics')
    
    # List articles command
    list_parser = subparsers.add_parser('list', help='List articles with optional filtering')
    list_parser.add_argument('--account', help='Filter by account name')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of articles to show (default: 20)')
    list_parser.add_argument('--search', help='Search articles by keyword')
    
    # Show article detail command
    detail_parser = subparsers.add_parser('detail', help='Show detailed information about a specific article')
    detail_parser.add_argument('--url', help='Article URL')
    detail_parser.add_argument('--id', type=int, help='Article ID')
    
    # Export articles command
    export_parser = subparsers.add_parser('export', help='Export articles to file')
    export_parser.add_argument('--account', help='Export articles from specific account')
    export_parser.add_argument('--format', choices=['txt', 'json', 'csv', 'markdown', 'simple'], default='txt', help='Export format (default: txt)')
    export_parser.add_argument('--output', '-o', help='Output directory for markdown export')
    export_parser.add_argument('--limit', '-l', type=int, help='Limit number of articles to export')
    export_parser.add_argument('--no-category', action='store_true', help='Do not export by category (markdown only)')
    export_parser.add_argument('--no-date', action='store_true', help='Do not export by date (markdown only)')
    export_parser.add_argument('--no-author', action='store_true', help='Do not export by author (markdown only)')
    
    # Import JSON to database command
    import_parser = subparsers.add_parser('import', help='Import JSON data to database')
    import_parser.add_argument('file', help='JSON file to import')
    import_parser.add_argument('--account', help='Specify account name if not in JSON data')
    import_parser.add_argument('--force', action='store_true', help='Import even if articles already exist (update existing)')
    import_parser.add_argument('--no-clean', action='store_true', help='Do not clean article content')
    
    # Clear database command
    clear_parser = subparsers.add_parser('clear', help='Clear all articles from database')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Fetch API data command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch all data from API and save to local JSON file')
    fetch_parser.add_argument('--api-url', help='API endpoint URL (default: http://101.33.75.240:1337/api/v1/geekdailies)')
    fetch_parser.add_argument('--max-pages', type=int, help='Maximum number of pages to fetch (default: all)')
    fetch_parser.add_argument('--output', help='Output file path (default: data/api_geekdailies_TIMESTAMP.json)')
    
    # Merge JSON files command
    merge_parser = subparsers.add_parser('merge', help='Merge two JSON files and remove duplicates')
    merge_parser.add_argument('file1', help='First JSON file to merge')
    merge_parser.add_argument('file2', help='Second JSON file to merge')
    merge_parser.add_argument('--output', help='Output file path (default: data/merged_articles_TIMESTAMP.json)')
    merge_parser.add_argument('--strategy', choices=['url', 'title', 'episode', 'title_author', 'url_title'], 
                             default='url', help='Deduplication strategy (default: url)')
    merge_parser.add_argument('--no-split', action='store_true', help='Disable smart splitting of collection articles')
    merge_parser.add_argument('--no-filter', action='store_true', help='Disable filtering of bad data')
    merge_parser.add_argument('--no-fill-time', action='store_true', help='Disable automatic time filling')
    
    # Analyze JSON files command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze JSON files structure and content')
    analyze_parser.add_argument('files', nargs='+', help='JSON files to analyze')
    
    # Clean JSON data command
    clean_parser = subparsers.add_parser('clean', help='Clean JSON data by removing incomplete entries')
    clean_parser.add_argument('input_file', help='Input JSON file to clean')
    clean_parser.add_argument('--output', help='Output file path (default: INPUT_cleaned_TIMESTAMP.json)')
    clean_parser.add_argument('--require-fields', nargs='+', default=['author', 'url', 'title'],
                             help='Required fields that must be non-empty (default: author url title)')
    clean_parser.add_argument('--no-empty-check', action='store_true', 
                             help='Disable additional empty value checks')
    clean_parser.add_argument('--validate-urls', action='store_true',
                             help='Enable URL format validation')
    clean_parser.add_argument('--exclude-fields', nargs='+', default=[],
                             help='Fields to exclude from output (e.g., episode time)')
    
    # Batch clean command
    batch_clean_parser = subparsers.add_parser('batch-clean', help='Batch clean all JSON files in a directory')
    batch_clean_parser.add_argument('directory', help='Directory containing JSON files')
    batch_clean_parser.add_argument('--pattern', default='*.json', help='File pattern to match (default: *.json)')
    batch_clean_parser.add_argument('--require-fields', nargs='+', default=['author', 'url', 'title'],
                                   help='Required fields that must be non-empty (default: author url title)')
    batch_clean_parser.add_argument('--no-empty-check', action='store_true',
                                   help='Disable additional empty value checks')
    batch_clean_parser.add_argument('--validate-urls', action='store_true',
                                   help='Enable URL format validation')
    batch_clean_parser.add_argument('--exclude-fields', nargs='+', default=[],
                                   help='Fields to exclude from output (e.g., episode time)')
    
    # Web API server command
    api_parser = subparsers.add_parser('api', help='Start web API server for data access')
    api_parser.add_argument('--host', default='127.0.0.1', help='Host address (default: 127.0.0.1)')
    api_parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    api_parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    # Delete articles command
    delete_parser = subparsers.add_parser('delete', help='Delete articles from database')
    delete_parser.add_argument('--keyword', help='Delete articles with title containing keyword')
    delete_parser.add_argument('--account', help='Delete articles from specific account')
    delete_parser.add_argument('--url-pattern', help='Delete articles with URL containing pattern')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Analytics commands
    analytics_parser = subparsers.add_parser('analytics', help='Data analytics and insights')
    analytics_subparsers = analytics_parser.add_subparsers(dest='analytics_command', help='Analytics commands')
    
    # Trend analysis command
    trend_parser = analytics_subparsers.add_parser('trends', help='Analyze technology trends')
    trend_parser.add_argument('--days', type=int, default=30, help='Analysis period in days (default: 30)')
    trend_parser.add_argument('--output', help='Save results to JSON file')
    
    # Author activity command
    author_parser = analytics_subparsers.add_parser('authors', help='Analyze author activity and influence')
    author_parser.add_argument('--days', type=int, default=30, help='Analysis period in days (default: 30)')
    author_parser.add_argument('--output', help='Save results to JSON file')
    
    # Publication patterns command
    publish_parser = analytics_subparsers.add_parser('publishing', help='Analyze publication patterns and frequency')
    publish_parser.add_argument('--days', type=int, default=90, help='Analysis period in days (default: 90)')
    publish_parser.add_argument('--output', help='Save results to JSON file')
    
    # Comprehensive report command
    report_parser = analytics_subparsers.add_parser('report', help='Generate comprehensive analytics report')
    report_parser.add_argument('--days', type=int, default=30, help='Analysis period in days (default: 30)')
    report_parser.add_argument('--output', help='Save report to JSON file')
    
    # Tag analysis command
    tag_parser = analytics_subparsers.add_parser('tags', help='Intelligent tagging and tag analysis')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_command', help='Tag commands')
    
    # Extract tags command
    extract_tags_parser = tag_subparsers.add_parser('extract', help='Extract tags from articles')
    extract_tags_parser.add_argument('--limit', type=int, help='Limit number of articles to process')
    extract_tags_parser.add_argument('--output', help='Save results to JSON file')
    
    # Tag trends command
    tag_trends_parser = tag_subparsers.add_parser('trends', help='Analyze tag trends')
    tag_trends_parser.add_argument('--days', type=int, default=30, help='Analysis period in days (default: 30)')
    tag_trends_parser.add_argument('--output', help='Save results to JSON file')
    
    # Quality analysis command
    quality_parser = analytics_subparsers.add_parser('quality', help='Content quality assessment')
    quality_subparsers = quality_parser.add_subparsers(dest='quality_command', help='Quality commands')
    
    # Evaluate quality command
    eval_quality_parser = quality_subparsers.add_parser('evaluate', help='Evaluate content quality')
    eval_quality_parser.add_argument('--limit', type=int, help='Limit number of articles to evaluate')
    eval_quality_parser.add_argument('--output', help='Save results to JSON file')
    
    # Quality insights command
    insights_parser = quality_subparsers.add_parser('insights', help='Get quality insights and recommendations')
    insights_parser.add_argument('--min-score', type=float, default=0.7, help='Minimum quality score for high-quality analysis (default: 0.7)')
    insights_parser.add_argument('--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    if args.command == 'crawl':
        asyncio.run(crawl_account(
            args.account,
            max_articles=args.max_articles,
            use_proxy=args.use_proxy
        ))
    elif args.command == 'article':
        asyncio.run(crawl_single_article(args.url, show_content=args.show_content))
    elif args.command == 'test':
        asyncio.run(test_crawler(show_content=args.show_content))
    elif args.command == 'discover':
        asyncio.run(discover_from_article(
            args.url,
            max_articles=args.max_articles,
            use_proxy=args.use_proxy
        ))
    elif args.command == 'history':
        asyncio.run(get_history_articles(
            args.url,
            max_articles=args.max_articles,
            use_proxy=args.use_proxy
        ))
    elif args.command == 'series':
        asyncio.run(get_series_articles(
            args.url,
            max_articles=args.max_articles,
            use_proxy=args.use_proxy
        ))
    elif args.command == 'stats':
        asyncio.run(show_stats())
    elif args.command == 'list':
        asyncio.run(list_articles(
            account_name=args.account,
            limit=args.limit,
            search=args.search
        ))
    elif args.command == 'detail':
        asyncio.run(show_article_detail(
            article_id=args.id,
            url=args.url
        ))
    elif args.command == 'export':
        if args.format == 'markdown':
            # 使用新的 Markdown 导出器
            from export_to_markdown import MarkdownExporter
            
            output_dir = args.output or 'export/markdown'
            exporter = MarkdownExporter(output_dir=output_dir)
            
            exporter.export_all(
                by_category=not args.no_category,
                by_date=not args.no_date,
                by_author=not args.no_author,
                limit=args.limit
            )
        elif args.format == 'simple':
            # 使用简单列表导出器
            from export_simple_list import SimpleListExporter
            
            output_file = args.output or 'all_articles.md'
            exporter = SimpleListExporter()
            
            exporter.export_to_single_file(
                output_file=output_file,
                limit=args.limit
            )
        else:
            asyncio.run(export_articles(
                account_name=args.account,
                format_type=args.format
            ))
    elif args.command == 'import':
        asyncio.run(import_json_to_database(
            input_file=args.file,
            account_name=args.account,
            skip_existing=not args.force,
            clean_content=not args.no_clean
        ))
    elif args.command == 'clear':
        asyncio.run(clear_database(
            confirm=not args.force
        ))
    elif args.command == 'fetch':
        asyncio.run(fetch_api_data(
            api_url=args.api_url,
            max_pages=args.max_pages,
            output_file=args.output
        ))
    elif args.command == 'merge':
        asyncio.run(merge_json_files(
            file1=args.file1,
            file2=args.file2,
            output_file=args.output,
            dedup_strategy=args.strategy,
            smart_split=not args.no_split,
            filter_bad_data=not args.no_filter,
            fill_time=not args.no_fill_time
        ))
    elif args.command == 'analyze':
        asyncio.run(analyze_json_files(*args.files))
    elif args.command == 'clean':
        asyncio.run(clean_json_data(
            input_file=args.input_file,
            output_file=args.output,
            require_fields=args.require_fields,
            clean_empty=not args.no_empty_check,
            validate_urls=args.validate_urls,
            exclude_fields=args.exclude_fields
        ))
    elif args.command == 'batch-clean':
        asyncio.run(batch_clean_directory(
            directory=args.directory,
            pattern=args.pattern,
            require_fields=args.require_fields,
            clean_empty=not args.no_empty_check,
            validate_urls=args.validate_urls,
            exclude_fields=args.exclude_fields
        ))
    elif args.command == 'api':
        from web_api import run_server
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    elif args.command == 'delete':
        asyncio.run(delete_articles(
            keyword=args.keyword,
            account=args.account,
            url_pattern=args.url_pattern,
            confirm=not args.force
        ))
    elif args.command == 'analytics':
        asyncio.run(handle_analytics_command(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()