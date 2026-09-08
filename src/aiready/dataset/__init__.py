"""Dataset package for aiready benchmark."""

from aiready.dataset.schema import GroundTruthMetadata, ExpectedImageInfo
from aiready.dataset.generator import SyntheticDatasetGenerator

__all__ = ["GroundTruthMetadata", "ExpectedImageInfo", "SyntheticDatasetGenerator"]
