"""
SQLAlchemy models for Scribley
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from .config import Base

# Article-Tag association table (many-to-many)
article_tag = Table(
    "article_tag",
    Base.metadata,
    Column("article_id", String, ForeignKey("articles.id")),
    Column("tag_id", String, ForeignKey("tags.id")),
)

class ArticleStatus(enum.Enum):
    DRAFT = "draft"
    PUBLIC = "public"
    UNLISTED = "unlisted"

class User(Base):
    """User model (synced with Medium user)"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    name = Column(String)
    url = Column(String)
    image_url = Column(String)
    
    # Relationships
    articles = relationship("Article", back_populates="user")
    
    def __init__(self, id, username, name, url, image_url=None):
        self.id = id
        self.username = username
        self.name = name
        self.url = url
        self.image_url = image_url

class Publication(Base):
    """Publication model (synced with Medium publication)"""
    __tablename__ = "publications"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    url = Column(String)
    image_url = Column(String)
    
    # Relationships
    articles = relationship("Article", back_populates="publication")
    
    def __init__(self, id, name, description=None, url=None, image_url=None):
        self.id = id
        self.name = name
        self.description = description
        self.url = url
        self.image_url = image_url

class Tag(Base):
    """Tag model for articles"""
    __tablename__ = "tags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    articles = relationship("Article", secondary=article_tag, back_populates="tags")
    
    def __init__(self, name):
        self.name = name

class Article(Base):
    """Article model for content to be published to Medium"""
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    subtitle = Column(String)
    content = Column(Text, nullable=False)
    status = Column(String, default=ArticleStatus.DRAFT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Medium specific fields
    medium_id = Column(String)
    medium_url = Column(String)
    
    # Relationships
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", back_populates="articles")
    
    publication_id = Column(String, ForeignKey("publications.id"))
    publication = relationship("Publication", back_populates="articles")
    
    tags = relationship("Tag", secondary=article_tag, back_populates="articles")
    
    def __init__(self, title, content, user_id=None, subtitle=None, status=ArticleStatus.DRAFT.value):
        self.title = title
        self.content = content
        self.subtitle = subtitle
        self.status = status
        self.user_id = user_id 