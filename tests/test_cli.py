"""Tests for the aiready CLI commands."""

import tempfile
from pathlib import Path
from typer.testing import CliRunner
from aiready.cli import app

runner = CliRunner()


def test_cli_generate_dataset():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "data"
        result = runner.invoke(app, ["generate-dataset", "--output-dir", str(out_dir)])
        assert result.exit_code == 0
        assert "Successfully generated" in result.output
        assert (out_dir / "01_word_annual_report").exists()


def test_cli_run_and_reporting():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        work_dir = Path(tmpdir) / "runs"
        json_out = Path(tmpdir) / "result.json"
        md_out = Path(tmpdir) / "report.md"
        html_out = Path(tmpdir) / "dashboard.html"

        # Generate dataset
        gen_res = runner.invoke(app, ["generate-dataset", "--output-dir", str(data_dir)])
        assert gen_res.exit_code == 0

        # Run benchmark
        run_res = runner.invoke(app, [
            "run",
            "--dataset", str(data_dir),
            "--converter", "reference",
            "--work-dir", str(work_dir),
            "--output-json", str(json_out),
            "--output-md", str(md_out),
            "--output-html", str(html_out),
        ])
        assert run_res.exit_code == 0
        assert "Overall Suite Performance Summary" in run_res.output
        assert json_out.exists()
        assert md_out.exists()
        assert html_out.exists()

        # Test report command with existing JSON
        rep_res = runner.invoke(app, [
            "report",
            "--input", str(json_out),
            "--format", "console",
        ])
        assert rep_res.exit_code == 0
        assert "AI-Ready Document Conversion Benchmark" in rep_res.output


def test_cli_verify_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "test.md"
        img_dir = Path(tmpdir) / "images"
        img_dir.mkdir()
        (img_dir / "cloud-architecture.png").write_bytes(b"dummy")

        md_file.write_text("# Test\n\n![cloud-architecture](images/cloud-architecture.png)\n", encoding="utf-8")

        res = runner.invoke(app, [
            "verify",
            "--markdown", str(md_file),
            "--images-dir", str(img_dir),
        ])
        assert res.exit_code == 0
        assert "Image Extraction & Link Integrity Verification" in res.output
