"""Tests for image extraction, kebab-case naming, and link integrity metrics."""

import tempfile
from pathlib import Path
from aiready.metrics.image_eval import (
    is_kebab_case_filename,
    extract_markdown_image_links,
    evaluate_image_pipeline,
)
from aiready.dataset.schema import ExpectedImageInfo


def test_is_kebab_case_filename():
    assert is_kebab_case_filename("quarterly-revenue-breakdown-2025.png") is True
    assert is_kebab_case_filename("cloud-native-topology.jpg") is True
    assert is_kebab_case_filename("core-datacenter-switch.webp") is True

    # Violations
    assert is_kebab_case_filename("Image_1.png") is False  # underscore, uppercase
    assert is_kebab_case_filename("QuarterlyReport.png") is False  # camelcase
    assert is_kebab_case_filename("my image file.png") is False  # spaces
    assert is_kebab_case_filename("invalid-extension.exe") is False


def test_markdown_image_link_extraction():
    md = (
        "Here is a chart:\n\n"
        "![Revenue Chart](images/quarterly-revenue-breakdown-2025.png)\n\n"
        "And another diagram:\n\n"
        "![Topology](images/cloud-native-topology.jpg \"System Arch\")\n"
    )
    links = extract_markdown_image_links(md)
    assert len(links) == 2
    assert links[0]["filename"] == "quarterly-revenue-breakdown-2025.png"
    assert links[1]["filename"] == "cloud-native-topology.jpg"


def test_evaluate_image_pipeline_integrity():
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = Path(tmpdir) / "images"
        images_dir.mkdir()

        valid_file = images_dir / "valid-kebab-chart.png"
        valid_file.write_bytes(b"dummy")

        md = "# Report\n\n![valid-kebab-chart](images/valid-kebab-chart.png)\n"
        expected = [
            ExpectedImageInfo(
                image_id="img-1",
                expected_filename="valid-kebab-chart.png",
                summary="valid-kebab-chart",
                keywords=["kebab", "chart"],
            )
        ]

        res = evaluate_image_pipeline(md, images_dir, expected)
        assert res["extraction_rate"] == 1.0
        assert res["kebab_compliance_rate"] == 1.0
        assert res["link_integrity_score"] == 1.0
        assert len(res["broken_links"]) == 0
        assert res["overall_image_score"] > 0.95


def test_broken_link_and_orphan_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = Path(tmpdir) / "images"
        images_dir.mkdir()

        # Physical file exists on disk
        (images_dir / "orphan-chart.png").write_bytes(b"dummy")

        # Markdown references a file that does NOT exist
        md = "# Report\n\n![missing](images/non-existent-chart.png)\n"

        res = evaluate_image_pipeline(md, images_dir, [])
        assert res["link_integrity_score"] == 0.0
        assert len(res["broken_links"]) == 1
        assert "orphan-chart.png" in res["orphan_images"]
