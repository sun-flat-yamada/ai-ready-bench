"""Benchmark execution harness and composite scoring engine."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from aiready.config import BenchmarkSettings
from aiready.dataset.schema import GroundTruthMetadata
from aiready.converters.base import BaseConverter, ConversionResult
from aiready.metrics.ast_tree import (
    parse_markdown_to_ast,
    calculate_tree_similarity,
    evaluate_heading_hierarchy,
)
from aiready.metrics.table_eval import (
    extract_tables_from_markdown,
    evaluate_table_fidelity,
)
from aiready.metrics.image_eval import evaluate_image_pipeline
from aiready.metrics.text_eval import evaluate_cleanliness
from aiready.metrics.cost_eval import evaluate_cost_and_performance, count_tokens


class TestCaseResult(BaseModel):
    """Evaluation result for a single document test case."""
    case_name: str
    doc_id: str
    format: str
    category: str
    success: bool
    error_message: Optional[str] = None
    scores: Dict[str, float] = Field(default_factory=dict)
    image_metrics: Dict[str, Any] = Field(default_factory=dict)
    table_metrics: Dict[str, Any] = Field(default_factory=dict)
    cost_metrics: Dict[str, Any] = Field(default_factory=dict)
    cleanliness_metrics: Dict[str, Any] = Field(default_factory=dict)
    composite_score_100: float = 0.0


class BenchmarkRunResult(BaseModel):
    """Aggregated benchmark run result across all test cases."""
    converter_name: str
    timestamp: str
    total_cases: int
    successful_cases: int
    mean_composite_score: float
    mean_teds_score: float
    mean_table_score: float
    mean_image_score: float
    mean_link_integrity: float
    mean_kebab_compliance: float
    mean_cleanliness_score: float
    mean_latency_ms: float
    mean_peak_memory_mb: float
    total_tokens_cl100k: int
    projected_cost_per_1k_suite_usd: Dict[str, float]
    cases: List[TestCaseResult] = Field(default_factory=list)


class BenchmarkRunner:
    """Orchestrates test execution and metric aggregation."""

    def __init__(self, settings: Optional[BenchmarkSettings] = None):
        self.settings = settings or BenchmarkSettings()

    def run_suite(
        self,
        dataset_root: Path,
        converter: BaseConverter,
        work_dir: Path,
        selected_category: Optional[str] = None,
    ) -> BenchmarkRunResult:
        """Run benchmark on all test cases inside dataset_root."""
        dataset_root = Path(dataset_root)
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        case_dirs = sorted([d for d in dataset_root.iterdir() if d.is_dir() and (d / "metadata.json").exists()])
        case_results: List[TestCaseResult] = []

        for c_dir in case_dirs:
            meta_path = c_dir / "metadata.json"
            meta = GroundTruthMetadata.model_validate_json(meta_path.read_text(encoding="utf-8"))

            if selected_category and meta.category != selected_category:
                continue

            # Find input file
            input_candidates = [f for f in c_dir.iterdir() if f.name.startswith("input.")]
            if not input_candidates:
                continue
            input_file = input_candidates[0]
            expected_md_file = c_dir / "expected.md"
            gold_md = expected_md_file.read_text(encoding="utf-8") if expected_md_file.exists() else ""

            # Target output folder for this converter on this case
            case_output_dir = work_dir / converter.name / c_dir.name

            # Run converter
            conv_res: ConversionResult = converter.run_monitored(input_file, case_output_dir)

            if not conv_res.success:
                case_results.append(TestCaseResult(
                    case_name=c_dir.name,
                    doc_id=meta.doc_id,
                    format=meta.format,
                    category=meta.category,
                    success=False,
                    error_message=conv_res.error_message,
                ))
                continue

            pred_md = conv_res.markdown_content

            # 1. Structural AST / TEDS
            pred_ast = parse_markdown_to_ast(pred_md)
            gold_ast = parse_markdown_to_ast(gold_md)
            teds_score = calculate_tree_similarity(pred_ast, gold_ast)
            heading_score = evaluate_heading_hierarchy(pred_md, gold_md)

            # 2. Table Evaluation
            pred_tables = extract_tables_from_markdown(pred_md)
            gold_tables = extract_tables_from_markdown(gold_md)
            tbl_res = evaluate_table_fidelity(pred_tables, gold_tables)

            # 3. Image Extraction, Kebab-case & Link Integrity
            img_res = evaluate_image_pipeline(
                markdown_text=pred_md,
                extracted_images_dir=conv_res.images_dir,
                expected_images=meta.expected_images,
            )

            # 4. Cleanliness
            clean_res = evaluate_cleanliness(pred_md)

            # 5. Cost & Performance
            gold_tokens = count_tokens(gold_md)
            cost_res = evaluate_cost_and_performance(
                markdown_text=pred_md,
                latency_ms=conv_res.latency_ms,
                peak_memory_mb=conv_res.peak_memory_mb,
                gold_token_count=gold_tokens,
            )

            # Composite Score (0 - 100)
            w = self.settings.composite_weights
            composite = (
                teds_score * w.structure_fidelity +
                tbl_res["overall_table_score"] * w.table_fidelity +
                img_res["overall_image_score"] * w.image_integrity +
                clean_res["cleanliness_score"] * w.cleanliness +
                heading_score * w.metadata_completeness
            ) * 100.0

            case_results.append(TestCaseResult(
                case_name=c_dir.name,
                doc_id=meta.doc_id,
                format=meta.format,
                category=meta.category,
                success=True,
                scores={
                    "teds": teds_score,
                    "heading_hierarchy": heading_score,
                    "table_fidelity": tbl_res["overall_table_score"],
                    "image_integrity": img_res["overall_image_score"],
                    "kebab_compliance": img_res["kebab_compliance_rate"],
                    "link_integrity": img_res["link_integrity_score"],
                    "cleanliness": clean_res["cleanliness_score"],
                },
                image_metrics=img_res,
                table_metrics=tbl_res,
                cost_metrics=cost_res,
                cleanliness_metrics=clean_res,
                composite_score_100=round(composite, 2),
            ))

        # Aggregate summary statistics
        total = len(case_results)
        successful = [c for c in case_results if c.success]
        s_count = len(successful)

        mean_comp = sum(c.composite_score_100 for c in successful) / s_count if s_count else 0.0
        mean_teds = sum(c.scores.get("teds", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_tbl = sum(c.scores.get("table_fidelity", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_img = sum(c.scores.get("image_integrity", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_link = sum(c.scores.get("link_integrity", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_kebab = sum(c.scores.get("kebab_compliance", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_clean = sum(c.scores.get("cleanliness", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_lat = sum(c.cost_metrics.get("latency_ms", 0.0) for c in successful) / s_count if s_count else 0.0
        mean_mem = sum(c.cost_metrics.get("peak_memory_mb", 0.0) for c in successful) / s_count if s_count else 0.0
        total_tok = sum(c.cost_metrics.get("tokens_cl100k", 0) for c in successful)

        # Cost per 1000 suite runs
        suite_costs = {}
        for m_name in ["gpt-4o", "claude-3-5-sonnet", "gemini-2-0-flash", "deepseek-v3"]:
            c_sum = sum(c.cost_metrics.get("projected_cost_per_1k_docs_usd", {}).get(m_name, 0.0) for c in successful)
            suite_costs[m_name] = round(c_sum, 4)

        return BenchmarkRunResult(
            converter_name=converter.name,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_cases=total,
            successful_cases=s_count,
            mean_composite_score=round(mean_comp, 2),
            mean_teds_score=round(mean_teds, 4),
            mean_table_score=round(mean_tbl, 4),
            mean_image_score=round(mean_img, 4),
            mean_link_integrity=round(mean_link, 4),
            mean_kebab_compliance=round(mean_kebab, 4),
            mean_cleanliness_score=round(mean_clean, 4),
            mean_latency_ms=round(mean_lat, 2),
            mean_peak_memory_mb=round(mean_mem, 2),
            total_tokens_cl100k=total_tok,
            projected_cost_per_1k_suite_usd=suite_costs,
            cases=case_results,
        )
