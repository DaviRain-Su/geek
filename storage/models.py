from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# SQLAlchemy Base
Base = declarative_base()


class Article(BaseModel):
    """Pydantic model for article data"""
    url: HttpUrl
    title: str
    content: str
    author: Optional[str] = None
    account_name: Optional[str] = None
    publish_time: Optional[datetime] = None
    images: List[str] = Field(default_factory=list)
    cover_image: Optional[str] = None
    read_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    raw_html: Optional[str] = None
    crawl_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ArticleDB(Base):
    """SQLAlchemy model for article storage"""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(200))
    account_name = Column(String(200), index=True)
    publish_time = Column(DateTime)
    images = Column(JSON)  # Store as JSON array
    cover_image = Column(String(500))
    read_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    raw_html = Column(Text)
    crawl_time = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'account_name': self.account_name,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'images': self.images or [],
            'cover_image': self.cover_image,
            'read_count': self.read_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'crawl_time': self.crawl_time.isoformat() if self.crawl_time else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_article(cls, article: Article):
        """Create from Article pydantic model"""
        return cls(
            url=str(article.url),
            title=article.title,
            content=article.content,
            author=article.author,
            account_name=article.account_name,
            publish_time=article.publish_time,
            images=article.images,
            cover_image=article.cover_image,
            read_count=article.read_count,
            like_count=article.like_count,
            comment_count=article.comment_count,
            raw_html=article.raw_html,
            crawl_time=article.crawl_time
        )


class CrawlJob(BaseModel):
    """Model for crawl job tracking"""
    id: Optional[str] = None
    account_name: str
    status: str = "pending"  # pending, running, completed, failed
    total_articles: int = 0
    crawled_articles: int = 0
    failed_articles: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CrawlJobDB(Base):
    """SQLAlchemy model for crawl job tracking"""
    __tablename__ = 'crawl_jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_name = Column(String(200), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)
    total_articles = Column(Integer, default=0)
    crawled_articles = Column(Integer, default=0)
    failed_articles = Column(Integer, default=0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'account_name': self.account_name,
            'status': self.status,
            'total_articles': self.total_articles,
            'crawled_articles': self.crawled_articles,
            'failed_articles': self.failed_articles,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }