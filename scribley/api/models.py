from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ArticleStatus(str, Enum):
    draft = "draft"
    public = "public"
    unlisted = "unlisted"

class ArticleBase(BaseModel):
    title: str = Field(..., description="The title of the article")
    content: str = Field(..., description="The content of the article in Markdown format")
    tags: List[str] = Field(default_factory=list, description="Tags for the article")
    subtitle: Optional[str] = Field(None, description="Optional subtitle for the article")

class ArticleCreate(ArticleBase):
    publish_status: ArticleStatus = Field(default=ArticleStatus.draft, description="Publication status")
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the article")
    publication_id: Optional[str] = Field(None, description="ID of the publication to publish to")

class Article(ArticleBase):
    id: str = Field(..., description="The unique identifier of the article")
    created_at: datetime = Field(..., description="When the article was created")
    updated_at: datetime = Field(..., description="When the article was last updated")
    published_at: Optional[datetime] = Field(None, description="When the article was published")
    status: ArticleStatus = Field(..., description="Current status of the article")
    medium_id: Optional[str] = Field(None, description="ID of the article on Medium")
    medium_url: Optional[str] = Field(None, description="URL of the article on Medium")
    publication_id: Optional[str] = Field(None, description="ID of the publication it was published to")

class PublicationBase(BaseModel):
    name: str = Field(..., description="Name of the publication")
    description: Optional[str] = Field(None, description="Description of the publication")

class Publication(PublicationBase):
    id: str = Field(..., description="The unique identifier of the publication")
    url: str = Field(..., description="URL of the publication")
    image_url: Optional[str] = Field(None, description="URL of the publication's image")

class UserBase(BaseModel):
    username: str = Field(..., description="Medium username")
    name: str = Field(..., description="User's name")

class User(UserBase):
    id: str = Field(..., description="Medium user ID")
    image_url: Optional[str] = Field(None, description="URL of the profile image")
    url: str = Field(..., description="Medium profile URL")

class MediumAPIResponse(BaseModel):
    data: Dict[str, Any] = Field(..., description="Response data from Medium API")
    success: bool = Field(..., description="Whether the API call was successful")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message") 