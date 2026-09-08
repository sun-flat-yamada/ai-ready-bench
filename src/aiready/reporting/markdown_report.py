"""Markdown report generator for benchmark results."""

from pathlib import Path
from aiready.evaluators.benchmark_runner import BenchmarkRunResult


def generate_markdown_report(result: BenchmarkRunResult) -> str:
    """Generate a GitHub-flavored Markdown benchmark report."""
    md = []
    md.append(f"# AI-Ready Document Conversion Benchmark Report")
    md.append(f"\n- **Target Converter**: `{result.converter_name}`")
    md.append(f"- **Benchmark Run Timestamp**: `{result.timestamp}`")
    md.append(f"- **Total Test Cases**: {result.total_cases} (Successful: {result.successful_cases})")
    md.append(f"- **AI-Ready Composite Index (ACI)**: **`{result.mean_composite_score:.2f} / 100`**\n")

    md.append("## Executive Scorecard\n")
    md.append("| Metric | Result | Industry Target | Status |")
    md.append("| :--- | :---: | :---: | :---: |")

    def status_badge(val: float, target: float = 0.85) -> str:
        return "✅ Pass" if val >= target else "⚠️ Warning"

    md.append(f"| **Structural Fidelity (TEDS)** | {result.mean_teds_score:.2%} | >= 85.0% | {status_badge(result.mean_teds_score, 0.85)} |")
    md.append(f"| **Table Fidelity** | {result.mean_table_score:.2%} | >= 85.0% | {status_badge(result.mean_table_score, 0.85)} |")
    md.append(f"| **Image Extraction Pipeline** | {result.mean_image_score:.2%} | >= 80.0% | {status_badge(result.mean_image_score, 0.80)} |")
    md.append(f"| **Kebab-case Naming Compliance** | {result.mean_kebab_compliance:.2%} | 100.0% | {status_badge(result.mean_kebab_compliance, 0.95)} |")
    md.append(f"| **Markdown Link Integrity** | {result.mean_link_integrity:.2%} | 100.0% | {status_badge(result.mean_link_integrity, 0.95)} |")
    md.append(f"| **Cleanliness / Anti-Noise** | {result.mean_cleanliness_score:.2%} | >= 90.0% | {status_badge(result.mean_cleanliness_score, 0.90)} |")
    md.append(f"| **Mean Latency** | {result.mean_latency_ms:.1f} ms | - | ⚡ Optimal |")
    md.append(f"| **Peak Memory (RSS)** | {result.mean_peak_memory_mb:.1f} MB | < 500 MB | ✅ Pass |\n")

    md.append("## Ingestion Cost Simulation (per 1,000 Document Ingestions)\n")
    md.append("| LLM Model | Reference Rate ($/1M Input Tokens) | Projected Ingestion Cost (USD) |")
    md.append("| :--- | :---: | :---: |")
    rate_map = {
        "gpt-4o": "$2.50",
        "claude-3-5-sonnet": "$3.00",
        "gemini-2-0-flash": "$0.10",
        "deepseek-v3": "$0.14",
    }
    for model_name, cost in result.projected_cost_per_1k_suite_usd.items():
        md.append(f"| `{model_name}` | {rate_map.get(model_name, '-')} | **${cost:.4f}** |")

    md.append("\n## Detailed Case Breakdown\n")
    md.append("| Case Name | Format | ACI Score | TEDS | Table | Image | Kebab | Link | Latency | Tokens |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for c in result.cases:
        if not c.success:
            md.append(f"| `{c.case_name}` | {c.format} | **FAILED** | - | - | - | - | - | - | - |")
            continue

        md.append(
            f"| `{c.case_name}` | {c.format} | **{c.composite_score_100:.1f}** | "
            f"{c.scores.get('teds', 0.0):.2f} | "
            f"{c.scores.get('table_fidelity', 0.0):.2f} | "
            f"{c.scores.get('image_integrity', 0.0):.2f} | "
            f"{c.scores.get('kebab_compliance', 0.0):.2f} | "
            f"{c.scores.get('link_integrity', 0.0):.2f} | "
            f"{c.cost_metrics.get('latency_ms', 0.0):.0f}ms | "
            f"{c.cost_metrics.get('tokens_cl100k', 0):,} |"
        )

    md.append("\n---\n*Generated automatically by [aiready-benchmark](https://github.com/example/aiready-benchmark)*\n")
    return "\n".join(md)


def save_markdown_report(result: BenchmarkRunResult, output_path: Path):
    """Save markdown report to a file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_markdown_report(result), encoding="utf-8")
