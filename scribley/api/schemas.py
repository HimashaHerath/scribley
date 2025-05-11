"""
Pydantic schemas for API validation and serialization.
"""
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Union, Any
from datetime import datetime
import uuid

# User schemas
class UserBase(BaseModel):
    username: str
    name: str
    url: str
    image_url: Optional[str] = None

class UserCreate(UserBase):
    id: str

class User(UserBase):
    id: str
    
    model_config = {
        "from_attributes": True
    }

# Publication schemas
class PublicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

class PublicationCreate(PublicationBase):
    id: str

class Publication(PublicationBase):
    id: str
    
    model_config = {
        "from_attributes": True
    }

# Tag schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: str
    
    model_config = {
        "from_attributes": True
    }

# Article schemas
class ArticleBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    content: str
    tags: Optional[List[str]] = []
    status: str = "draft"
    publication_id: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    publication_id: Optional[str] = None

class ArticlePublish(BaseModel):
    status: Optional[str] = "public"
    publication_id: Optional[str] = None

class Article(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    content: str
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    medium_id: Optional[str] = None
    medium_url: Optional[str] = None
    user_id: Optional[str] = None
    publication_id: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }

    @computed_field
    @property
    def tags(self) -> List[str]:
        if hasattr(self, "_tag_names"):
            return self._tag_names
        return [] 