"""Base converter protocol and execution result models."""

import time
import psutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class ConversionResult(BaseModel):
    """Result returned by a document converter execution."""
    markdown_content: str = Field(description="Generated AI-ready Markdown text")
    images_dir: Optional[Path] = Field(default=None, description="Path to extracted images directory")
    extracted_images_count: int = 0
    latency_ms: float = 0.0
    peak_memory_mb: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseConverter(ABC):
    """Abstract base class for document conversion engines."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        """Convert an input document into AI-ready Markdown with extracted kebab-case images."""
        pass

    def run_monitored(self, input_path: Path, output_dir: Path) -> ConversionResult:
        """Execute convert() while monitoring execution time and peak memory footprint."""
        output_dir.mkdir(parents=True, exist_ok=True)

        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 * 1024)
        start_time = time.perf_counter()

        try:
            result = self.convert(input_path, output_dir)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            mem_after = process.memory_info().rss / (1024 * 1024)
            return ConversionResult(
                markdown_content="",
                images_dir=output_dir / "images",
                extracted_images_count=0,
                latency_ms=round(elapsed_ms, 2),
                peak_memory_mb=round(max(mem_before, mem_after), 2),
                success=False,
                error_message=str(e),
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        mem_after = process.memory_info().rss / (1024 * 1024)

        result.latency_ms = round(elapsed_ms, 2)
        result.peak_memory_mb = round(max(mem_before, mem_after), 2)
        return result
