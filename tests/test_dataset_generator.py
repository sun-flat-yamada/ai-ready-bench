"""Tests for synthetic benchmark dataset generator."""

import tempfile
from pathlib import Path
from aiready.dataset.generator import SyntheticDatasetGenerator
from aiready.dataset.schema import GroundTruthMetadata


def test_generate_all_datasets():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = SyntheticDatasetGenerator(Path(tmpdir))
        case_paths = gen.generate_all()

        assert len(case_paths) == 8

        for c_dir in case_paths:
            assert c_dir.exists()
            assert (c_dir / "expected.md").exists()
            assert (c_dir / "metadata.json").exists()

            meta = GroundTruthMetadata.model_validate_json((c_dir / "metadata.json").read_text(encoding="utf-8"))
            assert meta.doc_id
            assert meta.format

            input_files = list(c_dir.glob("input.*"))
            assert len(input_files) >= 1

            if meta.expected_images_count > 0:
                exp_img_dir = c_dir / "expected_images"
                assert exp_img_dir.exists()
                imgs = list(exp_img_dir.glob("*.*"))
                assert len(imgs) == meta.expected_images_count
