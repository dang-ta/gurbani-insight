# File: gurbani-insight/app/models.py

"""
Data models for the Gurbani Insight application.

Defines Pydantic models for API requests and responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for basic search functionality."""
    query: str
    top_k: int = Field(default=3, description="Number of results to return")
    format: str = Field(default="default", description="Format type (default, chat, summary, paragraph)")


class ChatMessage(BaseModel):
    """Model for a single chat message."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request model for chat completion API."""
    messages: List[ChatMessage]
    model: str = Field(default="gurbani-search", description="Model to use for completion")
    top_k: int = Field(default=10, description="Number of passages to retrieve")


class GenerateRequest(BaseModel):
    """Legacy request model for compatibility with older clients."""
    prompt: str
    top_k: int = Field(default=3, description="Number of results to return")


class SearchResult(BaseModel):
    """Model for a single search result."""
    score: float
    text: str
    ang_number: int
    section: str
    raag: Optional[str] = ""
    page_num: int


class SearchResponse(BaseModel):
    """Response model for search API."""
    results: List[SearchResult]
    formatted_response: str


class ChatResponse(BaseModel):
    """Response model for chat completion API."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]