"""Configuration constants and pricing models for aiready-benchmark."""

import re
from typing import Dict
from pydantic import BaseModel, Field


class ModelPricing(BaseModel):
    """Pricing rates per million tokens in USD."""
    input_per_million: float
    output_per_million: float


# Current standard pricing reference (USD per 1M tokens)
DEFAULT_PRICING: Dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing(input_per_million=2.50, output_per_million=10.00),
    "claude-3-5-sonnet": ModelPricing(input_per_million=3.00, output_per_million=15.00),
    "gemini-2-0-flash": ModelPricing(input_per_million=0.10, output_per_million=0.40),
    "deepseek-v3": ModelPricing(input_per_million=0.14, output_per_million=0.28),
}

# Regex for strict kebab-case semantic image filename:
# e.g. "quarterly-revenue-q4-2025.png", "network-topology-diagram.jpg"
KEBAB_CASE_IMAGE_REGEX = re.compile(
    r"^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$"
)

# Markdown image link regex:
# Matches ![alt text](images/kebab-case-file.png)
MARKDOWN_IMAGE_REGEX = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
)


class CompositeWeights(BaseModel):
    """Weights used to calculate the AI-Ready Composite Index (ACI 0-100)."""
    structure_fidelity: float = Field(default=0.30, description="Markdown AST tree edit distance")
    table_fidelity: float = Field(default=0.20, description="Table rows/cols/headers preservation")
    image_integrity: float = Field(default=0.25, description="Image extraction, kebab naming, link integrity")
    cleanliness: float = Field(default=0.15, description="Freedom from noisy boilerplate or raw tags")
    metadata_completeness: float = Field(default=0.10, description="Metadata and heading hierarchy preservation")


class BenchmarkSettings(BaseModel):
    """Global benchmark execution settings."""
    default_tokenizer: str = "cl100k_base"
    fallback_tokenizer: str = "o200k_base"
    composite_weights: CompositeWeights = Field(default_factory=CompositeWeights)
    timeout_seconds: int = 120
    images_dir_name: str = "images"
