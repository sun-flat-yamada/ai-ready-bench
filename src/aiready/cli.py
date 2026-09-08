"""Robust Typer-based CLI for the AI-Ready Document Conversion Benchmark Suite."""

from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aiready.dataset.generator import SyntheticDatasetGenerator
from aiready.converters.reference import ReferenceSoftwareConverter
from aiready.converters.custom_adapter import CustomCommandConverter
from aiready.evaluators.benchmark_runner import BenchmarkRunner, BenchmarkRunResult
from aiready.reporting.console import print_console_summary
from aiready.reporting.markdown_report import save_markdown_report
from aiready.reporting.json_exporter import export_to_json, export_to_csv
from aiready.reporting.html_dashboard import save_html_dashboard
from aiready.metrics.image_eval import evaluate_image_pipeline
from aiready.dataset.schema import ExpectedImageInfo

app = typer.Typer(
    name="aiready",
    help="AI-Ready Document Conversion Benchmark Suite across Office, PDF, and Image formats.",
    add_completion=False,
)
console = Console()


@app.command("generate-dataset")
def generate_dataset(
    output_dir: Path = typer.Option(
        Path("./data/benchmark-suite"),
        "--output-dir", "-o",
        help="Target directory to generate deterministic test cases and ground truth.",
    ),
):
    """Generate reproducible synthetic benchmark documents across 8 formats with ground truth."""
    console.print(f"[bold cyan]Generating reproducible benchmark dataset at:[/bold cyan] {output_dir}")
    gen = SyntheticDatasetGenerator(output_dir)
    paths = gen.generate_all()
    console.print(f"[bold green]Successfully generated {len(paths)} benchmark test suites![/bold green]")
    for p in paths:
        console.print(f"  - {p.name}")


@app.command("run")
def run_benchmark(
    dataset_dir: Path = typer.Option(
        Path("./data/benchmark-suite"),
        "--dataset", "-d",
        help="Path to directory containing benchmark test cases.",
    ),
    converter_type: str = typer.Option(
        "reference",
        "--converter", "-c",
        help="Converter to test: 'reference' (pure software) or 'custom' (external CLI).",
    ),
    custom_command: Optional[str] = typer.Option(
        None,
        "--custom-cmd",
        help="Command template for custom converter. E.g. 'python convert.py {input} {output_dir}'",
    ),
    converter_name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Custom label name for the converter under test.",
    ),
    work_dir: Path = typer.Option(
        Path("./runs"),
        "--work-dir", "-w",
        help="Working directory for conversion outputs.",
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        help="Filter benchmark to a specific category (e.g. office-word, office-visio, pdf).",
    ),
    output_json: Optional[Path] = typer.Option(
        None,
        "--output-json",
        help="File path to save full results JSON.",
    ),
    output_md: Optional[Path] = typer.Option(
        None,
        "--output-md",
        help="File path to save GitHub-flavored Markdown report.",
    ),
    output_html: Optional[Path] = typer.Option(
        None,
        "--output-html",
        help="File path to save interactive HTML dashboard.",
    ),
):
    """Run benchmark evaluation on the specified dataset using the chosen converter."""
    if not dataset_dir.exists():
        console.print(f"[bold yellow]Dataset not found at {dataset_dir}. Generating now...[/bold yellow]")
        gen = SyntheticDatasetGenerator(dataset_dir)
        gen.generate_all()

    # Choose converter
    if converter_type == "custom":
        if not custom_command:
            console.print("[bold red]Error: --custom-cmd must be provided when --converter is 'custom'[/bold red]")
            raise typer.Exit(code=1)
        name = converter_name or "custom-converter"
        converter = CustomCommandConverter(name=name, command_template=custom_command)
    else:
        name = converter_name or "reference-software"
        converter = ReferenceSoftwareConverter(name=name)

    runner = BenchmarkRunner()
    console.print(f"[bold cyan]Running benchmark for converter '[magenta]{converter.name}[/magenta]'...[/bold cyan]")
    result = runner.run_suite(
        dataset_root=dataset_dir,
        converter=converter,
        work_dir=work_dir,
        selected_category=category,
    )

    # Print Rich Console Report
    print_console_summary(result, console=console)

    # Save exports
    if output_json:
        export_to_json(result, output_json)
        console.print(f"Saved JSON results to [green]{output_json}[/green]")
    if output_md:
        save_markdown_report(result, output_md)
        console.print(f"Saved Markdown report to [green]{output_md}[/green]")
    if output_html:
        save_html_dashboard(result, output_html)
        console.print(f"Saved HTML dashboard to [green]{output_html}[/green]")


@app.command("report")
def report_results(
    input_json: Path = typer.Option(
        ...,
        "--input", "-i",
        help="Path to benchmark result JSON file.",
    ),
    report_format: str = typer.Option(
        "console",
        "--format", "-f",
        help="Output format: console, markdown, html, csv.",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="File path to write the formatted report (if not console).",
    ),
):
    """Render or convert an existing benchmark result JSON into console/markdown/html/csv."""
    if not input_json.exists():
        console.print(f"[bold red]Input file not found: {input_json}[/bold red]")
        raise typer.Exit(code=1)

    result = BenchmarkRunResult.model_validate_json(input_json.read_text(encoding="utf-8"))

    if report_format == "console":
        print_console_summary(result, console=console)
    elif report_format == "markdown":
        out_path = output_file or Path("benchmark_report.md")
        save_markdown_report(result, out_path)
        console.print(f"Markdown report saved to [green]{out_path}[/green]")
    elif report_format == "html":
        out_path = output_file or Path("benchmark_dashboard.html")
        save_html_dashboard(result, out_path)
        console.print(f"HTML dashboard saved to [green]{out_path}[/green]")
    elif report_format == "csv":
        out_path = output_file or Path("benchmark_cases.csv")
        export_to_csv(result, out_path)
        console.print(f"CSV exported to [green]{out_path}[/green]")
    else:
        console.print(f"[bold red]Unknown format: {report_format}[/bold red]")
        raise typer.Exit(code=1)


@app.command("verify")
def verify_output(
    markdown_path: Path = typer.Option(
        ...,
        "--markdown", "-m",
        help="Path to generated Markdown file to verify.",
    ),
    images_dir: Optional[Path] = typer.Option(
        None,
        "--images-dir",
        help="Path to extracted images directory.",
    ),
):
    """Independently verify image extraction, kebab-case naming, and link integrity for a document."""
    if not markdown_path.exists():
        console.print(f"[bold red]Markdown file not found: {markdown_path}[/bold red]")
        raise typer.Exit(code=1)

    md_text = markdown_path.read_text(encoding="utf-8", errors="replace")
    img_res = evaluate_image_pipeline(
        markdown_text=md_text,
        extracted_images_dir=images_dir,
        expected_images=[],
    )

    console.print(Panel("[bold cyan]Image Extraction & Link Integrity Verification[/bold cyan]"))
    table = Table(show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Result")

    table.add_row("Extracted Images on Disk", str(img_res["extracted_image_count"]))
    table.add_row("Markdown Image Tags", str(img_res["markdown_image_links_count"]))
    table.add_row("Kebab-case Compliance", f"{img_res['kebab_compliance_rate']:.1%}")
    table.add_row("Link Integrity (No 404s)", f"{img_res['link_integrity_score']:.1%}")
    table.add_row("Broken Links", str(img_res["broken_links"]) if img_res["broken_links"] else "[green]None[/green]")
    table.add_row("Orphan Images", str(img_res["orphan_images"]) if img_res["orphan_images"] else "[green]None[/green]")

    console.print(table)


@app.command("compare")
def compare_runs(
    run_a: Path = typer.Option(..., "--run-a", help="First benchmark result JSON"),
    run_b: Path = typer.Option(..., "--run-b", help="Second benchmark result JSON"),
):
    """Compare two benchmark runs side-by-side."""
    res_a = BenchmarkRunResult.model_validate_json(run_a.read_text(encoding="utf-8"))
    res_b = BenchmarkRunResult.model_validate_json(run_b.read_text(encoding="utf-8"))

    table = Table(title=f"Comparison: {res_a.converter_name} vs {res_b.converter_name}", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column(f"{res_a.converter_name} (A)", justify="right")
    table.add_column(f"{res_b.converter_name} (B)", justify="right")
    table.add_column("Delta (B - A)", justify="right")

    metrics = [
        ("Composite ACI Score", res_a.mean_composite_score, res_b.mean_composite_score, "{:.2f}"),
        ("TEDS (Structure)", res_a.mean_teds_score, res_b.mean_teds_score, "{:.2%}"),
        ("Table Fidelity", res_a.mean_table_score, res_b.mean_table_score, "{:.2%}"),
        ("Image Pipeline", res_a.mean_image_score, res_b.mean_image_score, "{:.2%}"),
        ("Link Integrity", res_a.mean_link_integrity, res_b.mean_link_integrity, "{:.2%}"),
        ("Cleanliness", res_a.mean_cleanliness_score, res_b.mean_cleanliness_score, "{:.2%}"),
        ("Mean Latency (ms)", res_a.mean_latency_ms, res_b.mean_latency_ms, "{:.1f}"),
        ("Peak Memory (MB)", res_a.mean_peak_memory_mb, res_b.mean_peak_memory_mb, "{:.1f}"),
    ]

    for label, val_a, val_b, fmt in metrics:
        delta = val_b - val_a
        delta_str = f"+{fmt.format(delta)}" if delta > 0 else fmt.format(delta)
        delta_color = "green" if delta >= 0 else "red"
        # Invert color for latency and memory (lower is better)
        if "Latency" in label or "Memory" in label:
            delta_color = "green" if delta <= 0 else "red"

        table.add_row(
            label,
            fmt.format(val_a),
            fmt.format(val_b),
            f"[{delta_color}]{delta_str}[/{delta_color}]",
        )

    console.print(table)


@app.command("submit")
def submit_agent_result(
    result_json: Path = typer.Option(..., "--result", "-r", help="Path to benchmark result JSON file."),
    agent_name: str = typer.Option(..., "--agent-name", "-n", help="Name of the agent or tool (e.g. Docling-Custom)."),
    author: str = typer.Option(..., "--author", "-a", help="Author name or GitHub handle."),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Agent or pipeline version."),
    repo_url: Optional[str] = typer.Option(None, "--repo-url", help="URL to agent repository or paper."),
    description: str = typer.Option("", "--description", help="Brief summary of the agent architecture."),
    submissions_dir: Path = typer.Option(Path("./submissions"), "--submissions-dir", help="Submissions directory."),
):
    """Package and submit local benchmark results for inclusion on the community leaderboard."""
    from aiready.agent.submitter import AgentSubmitter

    if not result_json.exists():
        console.print(f"[bold red]Result file not found: {result_json}[/bold red]")
        raise typer.Exit(code=1)

    res = BenchmarkRunResult.model_validate_json(result_json.read_text(encoding="utf-8"))
    submitter = AgentSubmitter(submissions_dir)
    sub = submitter.package_submission(
        run_result=res,
        agent_name=agent_name,
        author=author,
        version=version,
        repository_url=repo_url,
        description=description,
    )
    dest = submitter.save_submission(sub)

    console.print(Panel(f"[bold green]Successfully packaged submission![/bold green]\n"
                        f"File: [cyan]{dest}[/cyan]\n"
                        f"Checksum (SHA256): [dim]{sub.checksum_sha256}[/dim]"))
    console.print("[bold yellow]To submit to the public leaderboard:[/bold yellow]")
    console.print(f"  1. Commit and push: [dim]git add {dest} && git commit -m 'feat: submit {agent_name} v{version}'[/dim]")
    console.print("  2. Open a Pull Request to master. GitHub Actions will validate and publish automatically!")


@app.command("build-leaderboard")
def build_leaderboard(
    submissions_dir: Path = typer.Option(Path("./submissions"), "--submissions-dir", help="Directory with submissions."),
    output_json: Path = typer.Option(Path("./docs/data/leaderboard.json"), "--output", "-o", help="Target output JSON path."),
):
    """Scan submissions and compile the public leaderboard data for GitHub Pages."""
    from aiready.evaluators.leaderboard_builder import LeaderboardBuilder

    builder = LeaderboardBuilder(submissions_dir)
    data = builder.build()
    out = builder.write_leaderboard(output_json)

    console.print(f"[bold green]Compiled leaderboard with {data.total_agents} agents to:[/bold green] [cyan]{out}[/cyan]")


if __name__ == "__main__":
    app()
