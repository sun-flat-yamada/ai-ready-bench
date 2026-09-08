"""Tests for token counting and cost modeling metrics."""

from aiready.metrics.cost_eval import (
    count_tokens,
    simulate_model_costs,
    evaluate_cost_and_performance,
)


def test_count_tokens():
    text = "The quick brown fox jumps over the lazy dog."
    tok_cl100k = count_tokens(text, "cl100k_base")
    tok_o200k = count_tokens(text, "o200k_base")

    assert tok_cl100k > 0
    assert tok_o200k > 0


def test_simulate_model_costs():
    # 1000 tokens * 1000 multiplier = 1,000,000 tokens
    # GPT-4o @ $2.50 per 1M
    costs = simulate_model_costs(1000, multiplier=1000)
    assert costs["gpt-4o"] == 2.50
    assert costs["claude-3-5-sonnet"] == 3.00
    assert costs["gemini-2-0-flash"] == 0.10
    assert costs["deepseek-v3"] == 0.14


def test_evaluate_cost_and_performance():
    text = "# Title\n\nSome paragraph text for benchmark."
    res = evaluate_cost_and_performance(
        markdown_text=text,
        latency_ms=150.0,
        peak_memory_mb=45.2,
        gold_token_count=10,
    )

    assert res["tokens_cl100k"] > 0
    assert res["latency_ms"] == 150.0
    assert res["peak_memory_mb"] == 45.2
    assert "projected_cost_per_1k_docs_usd" in res
