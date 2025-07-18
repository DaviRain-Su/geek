#!/usr/bin/env python3
"""
Web API for GeekDaily articles
为网页应用提供数据访问接口
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import uvicorn
from datetime import datetime
import json
from storage.database import DatabaseManager
from utils.logger import logger
from analytics.trend_analyzer import TrendAnalyzer
from analytics.tag_extractor import TagExtractor
from analytics.content_evaluator import ContentEvaluator

# 创建FastAPI应用
app = FastAPI(
    title="GeekDaily Articles API",
    description="为Web3极客日报数据提供REST API接口",
    version="1.0.0"
)

# 环境配置
import os
from typing import List

# 获取环境变量
CORS_ORIGINS = os.getenv("CORS_ORIGINS", '["*"]')
if isinstance(CORS_ORIGINS, str):
    import json
    try:
        CORS_ORIGINS = json.loads(CORS_ORIGINS)
    except:
        CORS_ORIGINS = ["*"]

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 数据库连接
db = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库连接"""
    global db
    db = DatabaseManager(use_mongodb=False)
    logger.info("Web API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global db
    if db:
        db.close()
    logger.info("Web API shutdown")

@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "message": "GeekDaily Articles API",
        "version": "1.0.0",
        "endpoints": {
            "articles": "/articles - 获取文章列表",
            "articles_by_id": "/articles/{id} - 获取特定文章",
            "search": "/articles/search - 搜索文章",
            "stats": "/stats - 统计信息",
            "accounts": "/accounts - 账号列表"
        }
    }

@app.get("/articles")
async def get_articles(
    account: Optional[str] = Query(None, description="账号名称筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制 (1-100)"),
    offset: int = Query(0, ge=0, description="跳过数量"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取文章列表
    
    参数:
    - account: 可选，筛选特定账号的文章
    - limit: 返回数量限制，默认20，最大100
    - offset: 跳过的数量，用于分页
    - search: 可选，搜索关键词
    """
    try:
        if search:
            articles = db.search_articles(search, limit)
        else:
            articles = db.get_articles_by_account(account or "", limit, offset)
        
        # 格式化返回数据
        formatted_articles = []
        for article in articles:
            formatted_article = {
                "id": article.get('id'),
                "title": article.get('title', ''),
                "author": article.get('author', ''),
                "account_name": article.get('account_name', ''),
                "url": article.get('url', ''),
                "publish_time": article.get('publish_time', ''),
                "content_preview": (article.get('content', '') or '')[:200],  # 内容预览
                "content_length": len(article.get('content', '') or ''),
                "crawl_time": article.get('crawl_time', ''),
                "read_count": article.get('read_count', 0),
                "like_count": article.get('like_count', 0)
            }
            formatted_articles.append(formatted_article)
        
        # 获取总数（用于分页）
        total_count = db.get_article_count(account)
        
        return {
            "success": True,
            "data": {
                "articles": formatted_articles,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            },
            "message": f"返回 {len(formatted_articles)} 篇文章"
        }
        
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文章失败: {str(e)}")

@app.get("/search")
async def search_articles(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    搜索文章
    
    参数:
    - q: 搜索关键词（必需）
    - limit: 返回数量限制，默认20，最大100
    """
    try:
        articles = db.search_articles(q, limit)
        
        formatted_articles = []
        for article in articles:
            formatted_article = {
                "id": article.get('id'),
                "title": article.get('title', ''),
                "author": article.get('author', ''),
                "account_name": article.get('account_name', ''),
                "url": article.get('url', ''),
                "publish_time": article.get('publish_time', ''),
                "content_preview": (article.get('content', '') or '')[:300],
                "crawl_time": article.get('crawl_time', '')
            }
            formatted_articles.append(formatted_article)
        
        return {
            "success": True,
            "data": {
                "articles": formatted_articles,
                "query": q,
                "count": len(formatted_articles)
            },
            "message": f"搜索到 {len(formatted_articles)} 篇相关文章"
        }
        
    except Exception as e:
        logger.error(f"搜索文章失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/articles/{article_id}")
async def get_article_by_id(article_id: int):
    """
    获取特定文章的详细信息
    
    参数:
    - article_id: 文章ID
    """
    try:
        # 通过ID查询文章
        if db.use_mongodb:
            article = db.articles_collection.find_one({"id": article_id})
        else:
            with db.get_session() as session:
                from storage.models import ArticleDB
                article_obj = session.query(ArticleDB).filter_by(id=article_id).first()
                article = article_obj.to_dict() if article_obj else None
        
        if not article:
            raise HTTPException(status_code=404, detail=f"文章ID {article_id} 未找到")
        
        return {
            "success": True,
            "data": {
                "id": article.get('id'),
                "title": article.get('title', ''),
                "author": article.get('author', ''),
                "account_name": article.get('account_name', ''),
                "url": article.get('url', ''),
                "content": article.get('content', ''),
                "publish_time": article.get('publish_time', ''),
                "crawl_time": article.get('crawl_time', ''),
                "images": article.get('images', []),
                "cover_image": article.get('cover_image', ''),
                "read_count": article.get('read_count', 0),
                "like_count": article.get('like_count', 0),
                "comment_count": article.get('comment_count', 0)
            },
            "message": "文章详情获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文章详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文章详情失败: {str(e)}")

@app.get("/articles/search")
async def search_articles(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    搜索文章
    
    参数:
    - q: 搜索关键词（必需）
    - limit: 返回数量限制，默认20，最大100
    """
    try:
        articles = db.search_articles(q, limit)
        
        formatted_articles = []
        for article in articles:
            formatted_article = {
                "id": article.get('id'),
                "title": article.get('title', ''),
                "author": article.get('author', ''),
                "account_name": article.get('account_name', ''),
                "url": article.get('url', ''),
                "publish_time": article.get('publish_time', ''),
                "content_preview": (article.get('content', '') or '')[:300],
                "crawl_time": article.get('crawl_time', '')
            }
            formatted_articles.append(formatted_article)
        
        return {
            "success": True,
            "data": {
                "articles": formatted_articles,
                "query": q,
                "count": len(formatted_articles)
            },
            "message": f"搜索到 {len(formatted_articles)} 篇相关文章"
        }
        
    except Exception as e:
        logger.error(f"搜索文章失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/stats")
async def get_stats():
    """
    获取统计信息
    """
    try:
        total_articles = db.get_article_count()
        
        # 获取所有文章来分析账号分布
        all_articles = db.get_articles_by_account("", limit=10000)
        
        # 统计账号分布
        accounts = {}
        authors = {}
        recent_articles = []
        
        for article in all_articles:
            # 账号统计
            account_name = article.get('account_name', 'Unknown')
            accounts[account_name] = accounts.get(account_name, 0) + 1
            
            # 作者统计
            author = article.get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
            
            # 最近文章（取前10篇）
            if len(recent_articles) < 10:
                recent_articles.append({
                    "id": article.get('id'),
                    "title": article.get('title', ''),
                    "author": author,
                    "account_name": account_name,
                    "publish_time": article.get('publish_time', ''),
                    "url": article.get('url', '')
                })
        
        # 排序统计数据
        top_accounts = sorted(accounts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "success": True,
            "data": {
                "overview": {
                    "total_articles": total_articles,
                    "total_accounts": len(accounts),
                    "total_authors": len(authors)
                },
                "top_accounts": [{"name": name, "count": count} for name, count in top_accounts],
                "top_authors": [{"name": name, "count": count} for name, count in top_authors],
                "recent_articles": recent_articles
            },
            "message": "统计信息获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@app.get("/accounts")
async def get_accounts():
    """
    获取所有账号列表
    """
    try:
        all_articles = db.get_articles_by_account("", limit=10000)
        
        # 统计账号信息
        accounts_info = {}
        for article in all_articles:
            account_name = article.get('account_name', 'Unknown')
            if account_name not in accounts_info:
                accounts_info[account_name] = {
                    "name": account_name,
                    "article_count": 0,
                    "latest_article": None,
                    "authors": set()
                }
            
            accounts_info[account_name]["article_count"] += 1
            accounts_info[account_name]["authors"].add(article.get('author', 'Unknown'))
            
            # 更新最新文章（简单根据处理顺序）
            if not accounts_info[account_name]["latest_article"]:
                accounts_info[account_name]["latest_article"] = {
                    "title": article.get('title', ''),
                    "publish_time": article.get('publish_time', ''),
                    "url": article.get('url', '')
                }
        
        # 转换为列表格式
        accounts_list = []
        for account_info in accounts_info.values():
            account_info["author_count"] = len(account_info["authors"])
            account_info["authors"] = list(account_info["authors"])
            accounts_list.append(account_info)
        
        # 按文章数量排序
        accounts_list.sort(key=lambda x: x["article_count"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "accounts": accounts_list,
                "total_accounts": len(accounts_list)
            },
            "message": f"返回 {len(accounts_list)} 个账号信息"
        }
        
    except Exception as e:
        logger.error(f"获取账号列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取账号列表失败: {str(e)}")

# Analytics API Endpoints

@app.get("/analytics/trends")
async def get_technology_trends(
    days: int = Query(30, ge=1, le=365, description="分析天数，默认30天")
):
    """
    获取技术趋势分析
    
    参数:
    - days: 分析时间范围（天数），默认30天，最大365天
    """
    try:
        analyzer = TrendAnalyzer()
        results = analyzer.analyze_technology_trends(days)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"技术趋势分析完成（最近{days}天）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"技术趋势分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"技术趋势分析失败: {str(e)}")

@app.get("/analytics/authors")
async def get_author_activity(
    days: int = Query(30, ge=1, le=365, description="分析天数，默认30天")
):
    """
    获取作者活跃度分析
    
    参数:
    - days: 分析时间范围（天数），默认30天，最大365天
    """
    try:
        analyzer = TrendAnalyzer()
        results = analyzer.analyze_author_activity(days)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"作者活跃度分析完成（最近{days}天）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"作者活跃度分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"作者活跃度分析失败: {str(e)}")

@app.get("/analytics/publishing")
async def get_publication_patterns(
    days: int = Query(90, ge=1, le=365, description="分析天数，默认90天")
):
    """
    获取发布模式分析
    
    参数:
    - days: 分析时间范围（天数），默认90天，最大365天
    """
    try:
        analyzer = TrendAnalyzer()
        results = analyzer.analyze_publication_patterns(days)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"发布模式分析完成（最近{days}天）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布模式分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发布模式分析失败: {str(e)}")

@app.get("/analytics/report")
async def get_comprehensive_report(
    days: int = Query(30, ge=1, le=365, description="分析天数，默认30天")
):
    """
    获取综合分析报告
    
    参数:
    - days: 分析时间范围（天数），默认30天，最大365天
    """
    try:
        analyzer = TrendAnalyzer()
        results = analyzer.get_comprehensive_trends(days)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"综合分析报告生成完成（最近{days}天）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"综合分析报告生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"综合分析报告生成失败: {str(e)}")

@app.get("/analytics/tags/extract")
async def extract_article_tags(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="处理文章数量限制")
):
    """
    提取文章标签
    
    参数:
    - limit: 处理文章数量限制，默认处理所有文章
    """
    try:
        extractor = TagExtractor()
        results = extractor.batch_tag_articles(limit=limit)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"标签提取完成，处理了{results['summary']['successfully_tagged']}篇文章"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标签提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"标签提取失败: {str(e)}")

@app.get("/analytics/tags/trends")
async def get_tag_trends(
    days: int = Query(30, ge=1, le=365, description="分析天数，默认30天")
):
    """
    获取标签趋势分析
    
    参数:
    - days: 分析时间范围（天数），默认30天，最大365天
    """
    try:
        extractor = TagExtractor()
        results = extractor.analyze_tag_trends(days)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"标签趋势分析完成（最近{days}天）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标签趋势分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"标签趋势分析失败: {str(e)}")

@app.get("/analytics/quality/evaluate")
async def evaluate_content_quality(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="评估文章数量限制")
):
    """
    评估内容质量
    
    参数:
    - limit: 评估文章数量限制，默认评估所有文章
    """
    try:
        evaluator = ContentEvaluator()
        results = evaluator.batch_evaluate_quality(limit=limit)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"内容质量评估完成，评估了{results['summary']['successfully_evaluated']}篇文章"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"内容质量评估失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内容质量评估失败: {str(e)}")

@app.get("/analytics/quality/insights")
async def get_quality_insights(
    min_score: float = Query(0.7, ge=0.0, le=1.0, description="高质量文章最低评分")
):
    """
    获取质量洞察报告
    
    参数:
    - min_score: 高质量文章最低评分（0.0-1.0），默认0.7
    """
    try:
        evaluator = ContentEvaluator()
        results = evaluator.get_quality_insights(min_quality_score=min_score)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "data": results,
            "message": f"质量洞察报告生成完成（最低评分≥{min_score}）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"质量洞察报告生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"质量洞察报告生成失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        total_articles = db.get_article_count()
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "database": "connected",
                "total_articles": total_articles,
                "timestamp": datetime.now().isoformat()
            },
            "message": "API运行正常"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """启动Web API服务器"""
    print(f"🚀 启动GeekDaily Articles API服务器...")
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"📊 交互式文档: http://{host}:{port}/redoc")
    print()
    print(f"🔧 可用端点:")
    print(f"  GET  /articles                     - 获取文章列表")
    print(f"  GET  /articles/{{id}}                - 获取特定文章")
    print(f"  GET  /articles/search              - 搜索文章")
    print(f"  GET  /stats                       - 统计信息")
    print(f"  GET  /accounts                    - 账号列表")
    print(f"  GET  /analytics/trends            - 技术趋势分析")
    print(f"  GET  /analytics/authors           - 作者活跃度分析")
    print(f"  GET  /analytics/publishing        - 发布模式分析")
    print(f"  GET  /analytics/report            - 综合分析报告")
    print(f"  GET  /analytics/tags/extract      - 智能标签提取")
    print(f"  GET  /analytics/tags/trends       - 标签趋势分析")
    print(f"  GET  /analytics/quality/evaluate  - 内容质量评估")
    print(f"  GET  /analytics/quality/insights  - 质量洞察报告")
    print(f"  GET  /health                      - 健康检查")
    print()
    
    try:
        uvicorn.run(
            "web_api:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 API服务器已停止")
    except Exception as e:
        print(f"❌ API服务器启动失败: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GeekDaily Articles Web API")
    parser.add_argument('--host', default='127.0.0.1', help='Host address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, reload=args.reload)