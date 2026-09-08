"""Submission packaging and automated git ingestion client."""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

from aiready.evaluators.benchmark_runner import BenchmarkRunResult
from aiready.agent.schema import AgentSubmission, SystemEnvironment


def slugify(text: str) -> str:
    """Convert text to safe slug."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return clean or "agent"


class AgentSubmitter:
    """Packages local benchmark run results into signed submission manifests."""

    def __init__(self, submissions_dir: Path):
        self.submissions_dir = Path(submissions_dir)
        self.submissions_dir.mkdir(parents=True, exist_ok=True)

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
        """Write submission manifest to disk inside the submissions directory."""
        fname = f"{submission.agent_id}_v{submission.version}.json"
        dest = self.submissions_dir / fname
        dest.write_text(submission.model_dump_json(indent=2), encoding="utf-8")
        return dest
