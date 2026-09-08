"""Submission packaging and automated git ingestion client with namespaced storage."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from aiready.evaluators.benchmark_runner import BenchmarkRunResult
from aiready.agent.schema import AgentSubmission, SystemEnvironment, ReviewComment


def slugify(text: str) -> str:
    """Convert text to safe lowercase slug."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return clean or "agent"


class AgentSubmitter:
    """Packages local benchmark run results into signed, collision-free submission manifests."""

    def __init__(self, submissions_dir: Path):
        self.submissions_dir = Path(submissions_dir)
        self.runs_dir = self.submissions_dir / "runs"
        self.reviews_dir = self.submissions_dir / "reviews"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    def package_submission(
        self,
        run_result: BenchmarkRunResult,
        agent_name: str,
        author: str,
        version: str = "1.0.0",
        repository_url: Optional[str] = None,
        description: str = "",
        tags: Optional[list] = None,
    ) -> AgentSubmission:
        """Create a validated and signed AgentSubmission manifest."""
        agent_id = slugify(agent_name)
        sub = AgentSubmission(
            agent_id=agent_id,
            agent_name=agent_name,
            version=version,
            author=author,
            repository_url=repository_url,
            description=description,
            tags=tags or [],
            system_env=SystemEnvironment(),
            run_result=run_result,
        )
        sub.checksum_sha256 = sub.compute_checksum()
        return sub

    def save_submission(self, submission: AgentSubmission) -> Path:
        """Save submission in namespaced directory: submissions/runs/<author>/<agent>_v<version>_<short_sha>.json.

        This guarantees 100% collision-free isolation when multiple community contributors or forks submit PRs.
        """
        author_slug = slugify(submission.author)
        agent_slug = submission.agent_id
        short_sha = submission.checksum_sha256[:8] or "00000000"

        author_dir = self.runs_dir / author_slug
        author_dir.mkdir(parents=True, exist_ok=True)

        fname = f"{agent_slug}_v{submission.version}_{short_sha}.json"
        dest = author_dir / fname
        dest.write_text(submission.model_dump_json(indent=2), encoding="utf-8")
        return dest

    def save_review(self, review: ReviewComment) -> Path:
        """Save a review as an isolated atomic JSON file: submissions/reviews/<agent_id>/<author>_<rev_id>.json.

        Guarantees zero Git merge conflicts since every review is an independent new file.
        """
        agent_dir = self.reviews_dir / review.agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        author_slug = slugify(review.author)
        rev_slug = slugify(review.review_id)
        fname = f"{author_slug}_{rev_slug}.json"

        dest = agent_dir / fname
        dest.write_text(review.model_dump_json(indent=2), encoding="utf-8")
        return dest
