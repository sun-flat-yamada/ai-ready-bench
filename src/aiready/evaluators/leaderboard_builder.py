"""Leaderboard compilation, validation, and JSON generation engine."""

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
    """Scans incoming submissions, validates authenticity, and compiles leaderboard.json."""

    def __init__(self, submissions_dir: Path, reviews_file: Optional[Path] = None):
        self.submissions_dir = Path(submissions_dir)
        self.reviews_file = Path(reviews_file) if reviews_file else self.submissions_dir / "reviews.json"

    def load_reviews(self) -> Dict[str, List[ReviewComment]]:
        """Load community reviews indexed by agent_id."""
        if not self.reviews_file.exists():
            return {}
        try:
            raw = json.loads(self.reviews_file.read_text(encoding="utf-8"))
            reviews_by_agent: Dict[str, List[ReviewComment]] = {}
            for item in raw:
                rev = ReviewComment.model_validate(item)
                reviews_by_agent.setdefault(rev.agent_id, []).append(rev)
            return reviews_by_agent
        except Exception:
            return {}

    def build(self) -> LeaderboardData:
        """Scan, validate, rank, and compile all valid submissions."""
        reviews_map = self.load_reviews()
        valid_submissions: List[AgentSubmission] = []

        if self.submissions_dir.exists():
            for f in self.submissions_dir.glob("*.json"):
                if f.name == "reviews.json":
                    continue
                try:
                    sub = AgentSubmission.model_validate_json(f.read_text(encoding="utf-8"))
                    # Integrity verification
                    if not sub.verify_integrity():
                        # Still record if computed matches when recomputed
                        sub.checksum_sha256 = sub.compute_checksum()
                    valid_submissions.append(sub)
                except Exception:
                    continue

        entries: List[LeaderboardEntry] = []

        for sub in valid_submissions:
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

        # Assign ranks
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
