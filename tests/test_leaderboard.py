"""Tests for leaderboard aggregation, ranking, and review score compilation."""

import json
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from aiready.evaluators.leaderboard_builder import LeaderboardBuilder
from aiready.agent.schema import AgentSubmission, ReviewComment
from aiready.evaluators.benchmark_runner import BenchmarkRunResult
from aiready.cli import app

runner = CliRunner()


def test_leaderboard_builder_aggregation():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_dir = Path(tmpdir) / "submissions"
        sub_dir.mkdir()
        out_json = Path(tmpdir) / "docs" / "data" / "leaderboard.json"

        # 1. Create two dummy submissions
        res1 = BenchmarkRunResult(
            converter_name="agent-fast",
            timestamp="2026-09-08 00:00:00",
            total_cases=1,
            successful_cases=1,
            mean_composite_score=85.0,
            mean_teds_score=0.85,
            mean_table_score=0.85,
            mean_image_score=0.85,
            mean_link_integrity=1.0,
            mean_kebab_compliance=1.0,
            mean_cleanliness_score=1.0,
            mean_latency_ms=10.0,
            mean_peak_memory_mb=50.0,
            total_tokens_cl100k=100,
            projected_cost_per_1k_suite_usd={},
            cases=[],
        )
        sub1 = AgentSubmission(
            agent_id="agent-fast",
            agent_name="Agent Fast",
            version="1.0.0",
            author="dev_a",
            run_result=res1,
        )
        (sub_dir / "agent-fast.json").write_text(sub1.model_dump_json(), encoding="utf-8")

        res2 = BenchmarkRunResult(
            converter_name="agent-super",
            timestamp="2026-09-08 00:00:00",
            total_cases=1,
            successful_cases=1,
            mean_composite_score=98.0,
            mean_teds_score=0.98,
            mean_table_score=0.98,
            mean_image_score=0.98,
            mean_link_integrity=1.0,
            mean_kebab_compliance=1.0,
            mean_cleanliness_score=1.0,
            mean_latency_ms=25.0,
            mean_peak_memory_mb=80.0,
            total_tokens_cl100k=100,
            projected_cost_per_1k_suite_usd={},
            cases=[],
        )
        sub2 = AgentSubmission(
            agent_id="agent-super",
            agent_name="Agent Super",
            version="2.0.0",
            author="dev_b",
            run_result=res2,
        )
        (sub_dir / "agent-super.json").write_text(sub2.model_dump_json(), encoding="utf-8")

        # 2. Add a review
        reviews = [
            {
                "review_id": "r1",
                "agent_id": "agent-super",
                "author": "critic",
                "persona": "RAG Lead",
                "rating": 5,
                "title": "Incredible accuracy",
                "body": "Best parser ever",
                "timestamp": "2026-09-08T00:00:00Z"
            }
        ]
        (sub_dir / "reviews.json").write_text(json.dumps(reviews), encoding="utf-8")

        # 3. Build leaderboard
        builder = LeaderboardBuilder(sub_dir)
        data = builder.build()

        assert data.total_agents == 2
        # Agent Super should be Rank 1 (98.0 score)
        assert data.entries[0].agent_id == "agent-super"
        assert data.entries[0].rank == 1
        assert data.entries[0].average_stars == 5.0
        assert data.entries[0].total_reviews_count == 1

        # Agent Fast should be Rank 2 (85.0 score)
        assert data.entries[1].agent_id == "agent-fast"
        assert data.entries[1].rank == 2

        # Write to JSON
        builder.write_leaderboard(out_json)
        assert out_json.exists()


def test_cli_build_leaderboard():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_dir = Path(tmpdir) / "submissions"
        sub_dir.mkdir()
        out_json = Path(tmpdir) / "leaderboard.json"

        cli_res = runner.invoke(app, [
            "build-leaderboard",
            "--submissions-dir", str(sub_dir),
            "--output", str(out_json),
        ])
        assert cli_res.exit_code == 0
        assert out_json.exists()
