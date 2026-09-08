"""Rich console reporting for benchmark execution results."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from aiready.evaluators.benchmark_runner import BenchmarkRunResult


def print_console_summary(result: BenchmarkRunResult, console: Console = None):
    """Render a comprehensive, colorized benchmark scorecard in the terminal."""
    if console is None:
        console = Console()

    # Title Panel
    title_text = Text()
    title_text.append("AI-Ready Document Conversion Benchmark\n", style="bold cyan")
    title_text.append(f"Converter: {result.converter_name}  |  Timestamp: {result.timestamp}", style="dim")
    console.print(Panel(title_text, expand=False, border_style="cyan"))

    # Overall Summary Table
    summary_table = Table(title="Overall Suite Performance Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    summary_table.add_column("Status / Evaluation Target")

    def format_score(score: float, threshold: float = 0.85) -> str:
        color = "green" if score >= threshold else ("yellow" if score >= 0.70 else "red")
        return f"[{color}]{score:.2%}[/{color}]"

    summary_table.add_row(
        "Composite Score (ACI)",
        f"[bold yellow]{result.mean_composite_score:.2f} / 100[/bold yellow]",
        "Target: >= 85.0"
    )
    summary_table.add_row("Structure Fidelity (TEDS)", format_score(result.mean_teds_score), "Target: >= 85.0%")
    summary_table.add_row("Table Fidelity", format_score(result.mean_table_score), "Target: >= 85.0%")
    summary_table.add_row("Image Pipeline Overall", format_score(result.mean_image_score), "Target: >= 80.0%")
    summary_table.add_row("Kebab-case Naming Compliance", format_score(result.mean_kebab_compliance, 0.95), "Target: 100.0%")
    summary_table.add_row("Markdown Link Integrity", format_score(result.mean_link_integrity, 0.95), "Target: 100.0% (Zero broken links)")
    summary_table.add_row("Cleanliness / Anti-Noise", format_score(result.mean_cleanliness_score, 0.90), "Target: >= 90.0%")
    summary_table.add_row("Mean Latency", f"{result.mean_latency_ms:.1f} ms", "Processing speed per document")
    summary_table.add_row("Peak Memory (RSS)", f"{result.mean_peak_memory_mb:.1f} MB", "Resident Memory Footprint")
    summary_table.add_row("Suite Output Tokens (cl100k)", f"{result.total_tokens_cl100k:,}", "BPE Token volume")

    console.print(summary_table)

    # Multi-Model Cost Simulation Table
    cost_table = Table(title="Projected LLM Input Ingestion Cost (per 1,000 Suite Executions)", show_header=True, header_style="bold blue")
    cost_table.add_column("Target Model", style="bold")
    cost_table.add_column("Price Rate ($/1M in)", justify="right")
    cost_table.add_column("Projected Cost (USD)", justify="right")

    rate_map = {
        "gpt-4o": "$2.50",
        "claude-3-5-sonnet": "$3.00",
        "gemini-2-0-flash": "$0.10",
        "deepseek-v3": "$0.14",
    }
    for model_name, cost_val in result.projected_cost_per_1k_suite_usd.items():
        cost_table.add_row(model_name, rate_map.get(model_name, "-"), f"${cost_val:.4f}")

    console.print(cost_table)

    # Detailed Per-Case Table
    detail_table = Table(title="Per-Document Evaluation Breakdown", show_header=True, header_style="bold green")
    detail_table.add_column("Case Name", style="bold")
    detail_table.add_column("Format")
    detail_table.add_column("ACI Score", justify="right")
    detail_table.add_column("TEDS", justify="right")
    detail_table.add_column("Table", justify="right")
    detail_table.add_column("Image", justify="right")
    detail_table.add_column("Kebab", justify="right")
    detail_table.add_column("Link", justify="right")
    detail_table.add_column("Latency", justify="right")

    for c in result.cases:
        if not c.success:
            detail_table.add_row(c.case_name, c.format, "[bold red]FAILED[/bold red]", "-", "-", "-", "-", "-", "-")
            continue

        detail_table.add_row(
            c.case_name,
            c.format,
            f"{c.composite_score_100:.1f}",
            f"{c.scores.get('teds', 0.0):.2f}",
            f"{c.scores.get('table_fidelity', 0.0):.2f}",
            f"{c.scores.get('image_integrity', 0.0):.2f}",
            f"{c.scores.get('kebab_compliance', 0.0):.2f}",
            f"{c.scores.get('link_integrity', 0.0):.2f}",
            f"{c.cost_metrics.get('latency_ms', 0.0):.0f}ms",
        )

    console.print(detail_table)
