"""JSON and CSV raw metric export utilities."""

import csv
import json
from pathlib import Path
from aiready.evaluators.benchmark_runner import BenchmarkRunResult


def export_to_json(result: BenchmarkRunResult, output_path: Path):
    """Export benchmark run results to indented JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def export_to_csv(result: BenchmarkRunResult, output_path: Path):
    """Export case breakdown metrics to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_name", "format", "category", "success", "composite_score_100",
        "teds", "table_fidelity", "image_integrity", "kebab_compliance",
        "link_integrity", "cleanliness", "latency_ms", "tokens_cl100k", "peak_memory_mb"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in result.cases:
            writer.writerow({
                "case_name": c.case_name,
                "format": c.format,
                "category": c.category,
                "success": c.success,
                "composite_score_100": c.composite_score_100,
                "teds": c.scores.get("teds", 0.0),
                "table_fidelity": c.scores.get("table_fidelity", 0.0),
                "image_integrity": c.scores.get("image_integrity", 0.0),
                "kebab_compliance": c.scores.get("kebab_compliance", 0.0),
                "link_integrity": c.scores.get("link_integrity", 0.0),
                "cleanliness": c.scores.get("cleanliness", 0.0),
                "latency_ms": c.cost_metrics.get("latency_ms", 0.0),
                "tokens_cl100k": c.cost_metrics.get("tokens_cl100k", 0),
                "peak_memory_mb": c.cost_metrics.get("peak_memory_mb", 0.0),
            })
