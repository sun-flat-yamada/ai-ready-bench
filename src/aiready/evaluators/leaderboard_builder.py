"""Leaderboard compilation engine with recursive, collision-free namespaced scanning."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from aiready.agent.schema import AgentSubmission, ReviewComment


class LeaderboardEntry(BaseModel):
    """A ranked tool / agent entry on the public leaderboard."""
    rank: int = 1
    agent_id: str
    agent_name: str
    version: str
    author: str
    repository_url: Optional[str] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    system_env: Dict[str, str] = Field(default_factory=dict)
    # Benchmark aggregated scores
    composite_score: float
    teds_score: float
    table_score: float
    image_score: float
    kebab_compliance: float
    link_integrity: float
    cleanliness_score: float
    latency_ms: float
    peak_memory_mb: float
    total_tokens_cl100k: int
    projected_cost_1k_gpt4o: float
    projected_cost_1k_gemini: float
    projected_cost_1k_deepseek: float
    # Social / Community feedback
    average_stars: float = 0.0
    total_reviews_count: int = 0
    reviews: List[ReviewComment] = Field(default_factory=list)
    # Per-case details
    case_breakdowns: List[Dict[str, Any]] = Field(default_factory=list)


class LeaderboardData(BaseModel):
    """Root data structure rendered on GitHub Pages."""
    generated_at: str
    total_agents: int
    entries: List[LeaderboardEntry] = Field(default_factory=list)


class LeaderboardBuilder:
    """Recursively scans namespaced runs and atomic review files to compile leaderboard.json."""

    def __init__(self, submissions_dir: Path):
        self.submissions_dir = Path(submissions_dir)
        self.runs_dir = self.submissions_dir / "runs"
        self.reviews_dir = self.submissions_dir / "reviews"

    def load_reviews(self) -> Dict[str, List[ReviewComment]]:
        """Load atomic community reviews recursively indexed by agent_id."""
        reviews_by_agent: Dict[str, List[ReviewComment]] = {}

        # 1. Recursive scan of atomic review files (submissions/reviews/**/*.json)
        if self.reviews_dir.exists():
            for f in self.reviews_dir.rglob("*.json"):
                try:
                    rev = ReviewComment.model_validate_json(f.read_text(encoding="utf-8"))
                    reviews_by_agent.setdefault(rev.agent_id, []).append(rev)
                except Exception:
                    continue

        # 2. Backward compatibility: check monolithic submissions/reviews.json if present
        legacy_reviews = self.submissions_dir / "reviews.json"
        if legacy_reviews.exists():
            try:
                raw = json.loads(legacy_reviews.read_text(encoding="utf-8"))
                for item in raw:
                    rev = ReviewComment.model_validate(item)
                    # Deduplicate by review_id
                    existing_ids = {r.review_id for r in reviews_by_agent.get(rev.agent_id, [])}
                    if rev.review_id not in existing_ids:
                        reviews_by_agent.setdefault(rev.agent_id, []).append(rev)
            except Exception:
                pass

        return reviews_by_agent

    def build(self) -> LeaderboardData:
        """Scan namespaced submissions, deduplicate, rank, and compile all valid submissions."""
        reviews_map = self.load_reviews()
        valid_submissions: Dict[str, AgentSubmission] = {}

        candidate_files: List[Path] = []
        # Recursive scan of namespaced runs (submissions/runs/**/*.json)
        if self.runs_dir.exists():
            candidate_files.extend(list(self.runs_dir.rglob("*.json")))

        # Backward compatibility for flat submissions/*.json
        if self.submissions_dir.exists():
            for f in self.submissions_dir.glob("*.json"):
                if f.name != "reviews.json":
                    candidate_files.append(f)

        for f in candidate_files:
            try:
                sub = AgentSubmission.model_validate_json(f.read_text(encoding="utf-8"))
                if not sub.verify_integrity():
                    sub.checksum_sha256 = sub.compute_checksum()

                # Deduplicate by (agent_id, author) keeping the latest submission
                key = f"{sub.agent_id}::{sub.author}"
                if key not in valid_submissions:
                    valid_submissions[key] = sub
                else:
                    # Replace if this one is newer
                    curr = valid_submissions[key]
                    if sub.system_env.timestamp >= curr.system_env.timestamp:
                        valid_submissions[key] = sub
            except Exception:
                continue

        entries: List[LeaderboardEntry] = []

        for sub in valid_submissions.values():
            res = sub.run_result
            revs = reviews_map.get(sub.agent_id, [])
            avg_stars = (sum(r.rating for r in revs) / len(revs)) if revs else 0.0

            cases_summary = []
            for c in res.cases:
                cases_summary.append({
                    "case_name": c.case_name,
                    "format": c.format,
                    "score": c.composite_score_100,
                    "teds": c.scores.get("teds", 0.0),
                    "table": c.scores.get("table_fidelity", 0.0),
                    "image": c.scores.get("image_integrity", 0.0),
                    "latency": c.cost_metrics.get("latency_ms", 0.0),
                })

            entry = LeaderboardEntry(
                agent_id=sub.agent_id,
                agent_name=sub.agent_name,
                version=sub.version,
                author=sub.author,
                repository_url=sub.repository_url,
                description=sub.description,
                tags=sub.tags,
                system_env={
                    "os": sub.system_env.os,
                    "python": sub.system_env.python_version,
                    "cpu": sub.system_env.cpu_model,
                },
                composite_score=res.mean_composite_score,
                teds_score=res.mean_teds_score,
                table_score=res.mean_table_score,
                image_score=res.mean_image_score,
                kebab_compliance=res.mean_kebab_compliance,
                link_integrity=res.mean_link_integrity,
                cleanliness_score=res.mean_cleanliness_score,
                latency_ms=res.mean_latency_ms,
                peak_memory_mb=res.mean_peak_memory_mb,
                total_tokens_cl100k=res.total_tokens_cl100k,
                projected_cost_1k_gpt4o=res.projected_cost_per_1k_suite_usd.get("gpt-4o", 0.0),
                projected_cost_1k_gemini=res.projected_cost_per_1k_suite_usd.get("gemini-2-0-flash", 0.0),
                projected_cost_1k_deepseek=res.projected_cost_per_1k_suite_usd.get("deepseek-v3", 0.0),
                average_stars=round(avg_stars, 1),
                total_reviews_count=len(revs),
                reviews=revs,
                case_breakdowns=cases_summary,
            )
            entries.append(entry)

        # Sort descending by composite score (highest first)
        entries.sort(key=lambda x: x.composite_score, reverse=True)

        for idx, e in enumerate(entries, start=1):
            e.rank = idx

        import datetime
        return LeaderboardData(
            generated_at=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_agents=len(entries),
            entries=entries,
        )

    def write_leaderboard(self, dest_path: Path) -> Path:
        """Compile and save to output JSON path."""
        data = self.build()
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
        return dest_path
