"""Schemas for agent benchmark submissions, machine specs, and community reviews."""

import hashlib
import platform
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from aiready.evaluators.benchmark_runner import BenchmarkRunResult


class SystemEnvironment(BaseModel):
    """Runtime execution environment metadata."""
    os: str = Field(default_factory=lambda: f"{platform.system()} {platform.release()} ({platform.machine()})")
    python_version: str = Field(default_factory=lambda: sys.version.split()[0])
    cpu_model: str = Field(default_factory=lambda: platform.processor() or "Generic CPU")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ReviewComment(BaseModel):
    """Community review / word-of-mouth feedback."""
    review_id: str
    agent_id: str
    author: str
    persona: str = Field(description="e.g. RAG Architect, MLOps Engineer, Enterprise SecOps")
    rating: int = Field(ge=1, le=5, description="1 to 5 stars")
    title: str
    body: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class AgentSubmission(BaseModel):
    """Standardized package submitted by local agent runners."""
    agent_id: str = Field(description="Unique kebab-case agent identifier (e.g. docling-v2-ocr)")
    agent_name: str = Field(description="Human-readable name")
    version: str = "1.0.0"
    author: str
    repository_url: Optional[str] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    system_env: SystemEnvironment = Field(default_factory=SystemEnvironment)
    run_result: BenchmarkRunResult
    checksum_sha256: str = ""

    def compute_checksum(self) -> str:
        """Compute SHA256 of the execution run result to verify payload integrity."""
        raw_json = self.run_result.model_dump_json()
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify checksum integrity against the run result."""
        return self.checksum_sha256 == self.compute_checksum()
