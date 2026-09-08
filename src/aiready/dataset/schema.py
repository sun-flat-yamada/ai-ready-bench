"""Schemas for test datasets and ground-truth expectations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ExpectedImageInfo(BaseModel):
    """Ground truth expectations for an embedded image."""
    image_id: str = Field(description="Unique image identifier within the document")
    expected_filename: str = Field(description="Strict kebab-case filename (e.g. system-architecture-v2.png)")
    summary: str = Field(description="Semantic summary / alt text description")
    keywords: List[str] = Field(default_factory=list, description="Crucial keywords expected in the summary")
    source_context: Optional[str] = Field(default=None, description="Nearby paragraph or section header")


class GroundTruthMetadata(BaseModel):
    """Metadata describing the target document and its expected AI-ready representation."""
    doc_id: str
    format: str
    description: str
    category: str = Field(description="e.g. office-word, office-excel, office-ppt, office-visio, office-project, office-db, pdf, image")
    expected_headings_count: int = 0
    expected_tables_count: int = 0
    expected_images_count: int = 0
    expected_images: List[ExpectedImageInfo] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    expected_token_count_range: Optional[Dict[str, int]] = None
