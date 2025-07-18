import os
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from storage.models import Base, ArticleDB, CrawlJobDB, Article, CrawlJob
from utils.config import settings
from utils.logger import logger


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, use_mongodb: bool = True):
        self.use_mongodb = use_mongodb
        
        if use_mongodb:
            self._init_mongodb()
        else:
            self._init_sqlite()
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(settings.mongodb_uri)
        self.db = self.client[settings.mongodb_db]
        self.articles_collection = self.db.articles
        self.jobs_collection = self.db.crawl_jobs
        
        # Create indexes
        self.articles_collection.create_index("url", unique=True)
        self.articles_collection.create_index("account_name")
        self.articles_collection.create_index("publish_time")
        self.jobs_collection.create_index("account_name")
        self.jobs_collection.create_index("status")
        
        logger.info("MongoDB initialized successfully")
    
    def _init_sqlite(self):
        """Initialize SQLite connection"""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'wechat_crawler.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info("SQLite initialized successfully")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get SQLite session context manager"""
        if self.use_mongodb:
            raise RuntimeError("Session is only available for SQLite")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # Article operations
    def save_article(self, article: Article) -> bool:
        """Save article to database"""
        try:
            if self.use_mongodb:
                article_dict = article.dict()
                article_dict['_id'] = str(article.url)
                self.articles_collection.insert_one(article_dict)
            else:
                with self.get_session() as session:
                    db_article = ArticleDB.from_article(article)
                    session.add(db_article)
            
            logger.info(f"Saved article: {article.title}")
            return True
            
        except (DuplicateKeyError, IntegrityError):
            logger.warning(f"Article already exists: {article.url}")
            return False
        except Exception as e:
            logger.error(f"Failed to save article: {str(e)}")
            return False
    
    def get_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Get article by URL"""
        try:
            if self.use_mongodb:
                return self.articles_collection.find_one({"_id": url})
            else:
                with self.get_session() as session:
                    article = session.query(ArticleDB).filter_by(url=url).first()
                    return article.to_dict() if article else None
        except Exception as e:
            logger.error(f"Failed to get article: {str(e)}")
            return None
    
    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get article by URL (alias for get_article)"""
        return self.get_article(url)
    
    def get_articles_by_account(self, account_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get articles by account name"""
        try:
            if self.use_mongodb:
                if account_name:
                    cursor = self.articles_collection.find(
                        {"account_name": account_name}
                    ).sort([("publish_time", -1), ("_id", -1)]).skip(offset).limit(limit)
                else:
                    cursor = self.articles_collection.find().sort([("publish_time", -1), ("_id", -1)]).skip(offset).limit(limit)
                return list(cursor)
            else:
                with self.get_session() as session:
                    query = session.query(ArticleDB)
                    if account_name:
                        query = query.filter_by(account_name=account_name)
                    # 复合排序：有发布时间的按发布时间降序，没有的按抓取时间降序，最后按ID降序
                    articles = query.order_by(
                        desc(ArticleDB.publish_time.isnot(None)),  # 有发布时间的排前面
                        desc(ArticleDB.publish_time),              # 发布时间降序
                        desc(ArticleDB.crawl_time),               # 抓取时间降序
                        desc(ArticleDB.id)                        # ID降序作为最终排序
                    ).offset(offset).limit(limit).all()
                    return [article.to_dict() for article in articles]
        except Exception as e:
            logger.error(f"Failed to get articles by account: {str(e)}")
            return []
    
    def search_articles(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search articles by title or content"""
        try:
            if self.use_mongodb:
                # Create text index if not exists
                self.articles_collection.create_index([("title", "text"), ("content", "text")])
                cursor = self.articles_collection.find(
                    {"$text": {"$search": query}}
                ).limit(limit)
                return list(cursor)
            else:
                with self.get_session() as session:
                    # Simple LIKE search for SQLite
                    pattern = f"%{query}%"
                    articles = session.query(ArticleDB).filter(
                        or_(
                            ArticleDB.title.like(pattern),
                            ArticleDB.content.like(pattern)
                        )
                    ).order_by(
                        desc(ArticleDB.publish_time.isnot(None)),  # 有发布时间的排前面
                        desc(ArticleDB.publish_time),              # 发布时间降序
                        desc(ArticleDB.crawl_time),               # 抓取时间降序
                        desc(ArticleDB.id)                        # ID降序作为最终排序
                    ).limit(limit).all()
                    return [article.to_dict() for article in articles]
        except Exception as e:
            logger.error(f"Failed to search articles: {str(e)}")
            return []
    
    def get_article_count(self, account_name: Optional[str] = None) -> int:
        """Get total article count"""
        try:
            if self.use_mongodb:
                filter_dict = {"account_name": account_name} if account_name else {}
                return self.articles_collection.count_documents(filter_dict)
            else:
                with self.get_session() as session:
                    query = session.query(ArticleDB)
                    if account_name:
                        query = query.filter_by(account_name=account_name)
                    return query.count()
        except Exception as e:
            logger.error(f"Failed to get article count: {str(e)}")
            return 0
    
    # Crawl job operations
    def create_job(self, job: CrawlJob) -> str:
        """Create a new crawl job"""
        try:
            if self.use_mongodb:
                result = self.jobs_collection.insert_one(job.dict())
                return str(result.inserted_id)
            else:
                with self.get_session() as session:
                    db_job = CrawlJobDB(**job.dict(exclude={'id'}))
                    session.add(db_job)
                    session.flush()
                    return str(db_job.id)
        except Exception as e:
            logger.error(f"Failed to create job: {str(e)}")
            return ""
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update crawl job"""
        try:
            if self.use_mongodb:
                from bson import ObjectId
                result = self.jobs_collection.update_one(
                    {"_id": ObjectId(job_id)},
                    {"$set": updates}
                )
                return result.modified_count > 0
            else:
                with self.get_session() as session:
                    job = session.query(CrawlJobDB).filter_by(id=int(job_id)).first()
                    if job:
                        for key, value in updates.items():
                            setattr(job, key, value)
                        return True
                    return False
        except Exception as e:
            logger.error(f"Failed to update job: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get crawl job by ID"""
        try:
            if self.use_mongodb:
                from bson import ObjectId
                job = self.jobs_collection.find_one({"_id": ObjectId(job_id)})
                if job:
                    job['id'] = str(job['_id'])
                    del job['_id']
                return job
            else:
                with self.get_session() as session:
                    job = session.query(CrawlJobDB).filter_by(id=int(job_id)).first()
                    return job.to_dict() if job else None
        except Exception as e:
            logger.error(f"Failed to get job: {str(e)}")
            return None
    
    def get_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get crawl jobs by status"""
        try:
            if self.use_mongodb:
                filter_dict = {"status": status} if status else {}
                cursor = self.jobs_collection.find(filter_dict).sort("created_at", -1).limit(limit)
                jobs = []
                for job in cursor:
                    job['id'] = str(job['_id'])
                    del job['_id']
                    jobs.append(job)
                return jobs
            else:
                with self.get_session() as session:
                    query = session.query(CrawlJobDB)
                    if status:
                        query = query.filter_by(status=status)
                    jobs = query.order_by(desc(CrawlJobDB.created_at)).limit(limit).all()
                    return [job.to_dict() for job in jobs]
        except Exception as e:
            logger.error(f"Failed to get jobs: {str(e)}")
            return []
    
    def close(self):
        """Close database connections"""
        if self.use_mongodb:
            self.client.close()
        logger.info("Database connections closed")