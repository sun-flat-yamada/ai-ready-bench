"""Tests for the ReferenceSoftwareConverter across all supported formats."""

import tempfile
from pathlib import Path
from aiready.dataset.generator import SyntheticDatasetGenerator
from aiready.converters.reference import ReferenceSoftwareConverter
from aiready.evaluators.benchmark_runner import BenchmarkRunner


def test_reference_converter_full_suite():
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_dir = Path(tmpdir) / "dataset"
        work_dir = Path(tmpdir) / "runs"

        # 1. Generate test cases
        gen = SyntheticDatasetGenerator(dataset_dir)
        case_paths = gen.generate_all()
        assert len(case_paths) == 8

        # 2. Run benchmark on reference converter
        converter = ReferenceSoftwareConverter()
        runner = BenchmarkRunner()
        result = runner.run_suite(
            dataset_root=dataset_dir,
            converter=converter,
            work_dir=work_dir,
        )

        assert result.total_cases == 8
        assert result.successful_cases == 8
        assert result.mean_composite_score >= 85.0
        assert result.mean_teds_score >= 0.85
        assert result.mean_table_score >= 0.85
        assert result.mean_image_score >= 0.85
        assert result.mean_link_integrity >= 0.95
        assert result.mean_kebab_compliance >= 0.95
