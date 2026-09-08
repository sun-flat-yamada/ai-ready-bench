"""Token efficiency, cost modeling, and runtime performance metrics."""

from typing import Dict, Any, Optional
import tiktoken
from aiready.config import DEFAULT_PRICING, ModelPricing


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Accurately count tokens using tiktoken BPE tokenizer."""
    try:
        enc = tiktoken.get_encoding(encoding_name)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text, disallowed_special=()))


def simulate_model_costs(token_count: int, multiplier: int = 1000) -> Dict[str, float]:
    """Calculate projected LLM input costs for processing N documents."""
    costs: Dict[str, float] = {}
    for model_name, pricing in DEFAULT_PRICING.items():
        # Cost for (token_count * multiplier) input tokens
        total_tokens = token_count * multiplier
        cost_usd = (total_tokens / 1_000_000.0) * pricing.input_per_million
        costs[model_name] = round(cost_usd, 5)
    return costs


def evaluate_cost_and_performance(
    markdown_text: str,
    latency_ms: float,
    peak_memory_mb: float,
    gold_token_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Profile token footprint, throughput, and multi-model API cost projections."""
    cl100k_tokens = count_tokens(markdown_text, "cl100k_base")
    o200k_tokens = count_tokens(markdown_text, "o200k_base")

    # Token efficiency: ratio against gold standard if available
    token_ratio = 1.0
    if gold_token_count and gold_token_count > 0:
        token_ratio = round(cl100k_tokens / gold_token_count, 4)

    # Cost projections for 1,000 document queries
    batch_costs_1k = simulate_model_costs(cl100k_tokens, multiplier=1000)

    # Throughput (tokens per second)
    throughput_tps = round((cl100k_tokens / (latency_ms / 1000.0)), 1) if latency_ms > 0 else 0.0

    return {
        "tokens_cl100k": cl100k_tokens,
        "tokens_o200k": o200k_tokens,
        "token_inflation_ratio": token_ratio,
        "latency_ms": round(latency_ms, 2),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "throughput_tokens_per_sec": throughput_tps,
        "projected_cost_per_1k_docs_usd": batch_costs_1k,
    }
