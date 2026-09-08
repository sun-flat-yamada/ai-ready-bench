"""Tests for agent runner packaging and submission integrity."""

import tempfile
from pathlib import Path
from typer.testing import CliRunner

from aiready.agent.submitter import AgentSubmitter, slugify
from aiready.evaluators.benchmark_runner import BenchmarkRunResult
from aiready.cli import app

runner = CliRunner()


def test_slugify():
    assert slugify("IBM Docling v2.0") == "ibm-docling-v2-0"
    assert slugify("Microsoft MarkItDown!") == "microsoft-markitdown"


def test_package_and_verify_submission():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = BenchmarkRunResult(
            converter_name="test-agent",
            timestamp="2026-09-08 00:00:00",
            total_cases=1,
            successful_cases=1,
            mean_composite_score=95.0,
            mean_teds_score=0.95,
            mean_table_score=0.95,
            mean_image_score=0.95,
            mean_link_integrity=1.0,
            mean_kebab_compliance=1.0,
            mean_cleanliness_score=1.0,
            mean_latency_ms=10.0,
            mean_peak_memory_mb=50.0,
            total_tokens_cl100k=100,
            projected_cost_per_1k_suite_usd={"gpt-4o": 0.25},
            cases=[],
        )

        submitter = AgentSubmitter(Path(tmpdir))
        sub = submitter.package_submission(
            run_result=res,
            agent_name="Custom Test Agent",
            author="tester",
            version="1.0.0",
        )

        assert sub.verify_integrity() is True
        assert sub.agent_id == "custom-test-agent"
        dest = submitter.save_submission(sub)
        assert dest.exists()


def test_cli_submit_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        res_file = Path(tmpdir) / "run.json"
        res = BenchmarkRunResult(
            converter_name="cli-agent",
            timestamp="2026-09-08 00:00:00",
            total_cases=1,
            successful_cases=1,
            mean_composite_score=90.0,
            mean_teds_score=0.9,
            mean_table_score=0.9,
            mean_image_score=0.9,
            mean_link_integrity=1.0,
            mean_kebab_compliance=1.0,
            mean_cleanliness_score=1.0,
            mean_latency_ms=20.0,
            mean_peak_memory_mb=60.0,
            total_tokens_cl100k=200,
            projected_cost_per_1k_suite_usd={},
            cases=[],
        )
        res_file.write_text(res.model_dump_json(), encoding="utf-8")
        sub_dir = Path(tmpdir) / "submissions"

        cli_res = runner.invoke(app, [
            "submit",
            "--result", str(res_file),
            "--agent-name", "CLI-Agent",
            "--author", "tester",
            "--submissions-dir", str(sub_dir),
        ])
        assert cli_res.exit_code == 0
        assert "Successfully packaged submission!" in cli_res.output
        assert (sub_dir / "cli-agent_v1.0.0.json").exists()
