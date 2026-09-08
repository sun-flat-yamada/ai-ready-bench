"""Tests for agent runner packaging and submission integrity with namespaced storage."""

import tempfile
from pathlib import Path
from typer.testing import CliRunner

from aiready.agent.submitter import AgentSubmitter, slugify
from aiready.agent.schema import ReviewComment
from aiready.evaluators.benchmark_runner import BenchmarkRunResult
from aiready.cli import app

runner = CliRunner()


def test_slugify():
    assert slugify("IBM Docling v2.0") == "ibm-docling-v2-0"
    assert slugify("Microsoft MarkItDown!") == "microsoft-markitdown"


def test_package_and_verify_submission_namespacing():
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
            author="contributor-alice",
            version="1.0.0",
        )

        assert sub.verify_integrity() is True
        assert sub.agent_id == "custom-test-agent"

        # Verify saved in author namespaced folder
        dest = submitter.save_submission(sub)
        assert dest.exists()
        assert "contributor-alice" in str(dest)
        assert "runs" in str(dest)


def test_concurrent_contributors_no_collision():
    """Verify two contributors submitting the same agent name never collide."""
    with tempfile.TemporaryDirectory() as tmpdir:
        submitter = AgentSubmitter(Path(tmpdir))
        res = BenchmarkRunResult(
            converter_name="docling-custom",
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
            mean_latency_ms=15.0,
            mean_peak_memory_mb=40.0,
            total_tokens_cl100k=100,
            projected_cost_per_1k_suite_usd={},
            cases=[],
        )

        sub_alice = submitter.package_submission(res, "Docling Custom", "alice", "1.0.0")
        dest_alice = submitter.save_submission(sub_alice)

        sub_bob = submitter.package_submission(res, "Docling Custom", "bob", "1.0.0")
        dest_bob = submitter.save_submission(sub_bob)

        assert dest_alice != dest_bob
        assert dest_alice.exists()
        assert dest_bob.exists()


def test_atomic_review_saving():
    with tempfile.TemporaryDirectory() as tmpdir:
        submitter = AgentSubmitter(Path(tmpdir))
        rev = ReviewComment(
            review_id="rev-101",
            agent_id="ibm-docling",
            author="charlie",
            persona="MLOps",
            rating=5,
            title="Fast and robust",
            body="Great experience",
        )
        dest = submitter.save_review(rev)
        assert dest.exists()
        assert "reviews" in str(dest)
        assert "ibm-docling" in str(dest)
        assert dest.name == "charlie_rev-101.json"


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
        runs_found = list((sub_dir / "runs" / "tester").glob("cli-agent_v1.0.0_*.json"))
        assert len(runs_found) == 1
