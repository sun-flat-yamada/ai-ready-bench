# AI Agent Operating Guidelines: ai-ready-bench

This document outlines mandatory operational protocols and constraints for AI coding agents operating within this repository.

## 1. Benchmark Execution & Sandbox Security Protocol

When evaluating or benchmarking document converters (either built-in or external third-party tools like MarkItDown, PyMuPDF4LLM, Docling, or participant custom models):

1. **Docker-First Policy (MANDATORY)**:
   - Always prioritize executing benchmarks within the secure, unprivileged Docker container sandbox (`docker/Dockerfile` or `docker/docker-compose.yml`).
   - The container environment enforces non-root execution (`10001:10001`), capability drops (`--cap-drop=ALL`), privilege restriction (`no-new-privileges:true`), and resource limits (4GB RAM, 2.0 CPUs).
2. **Local Fallback User Confirmation Rule (CRITICAL)**:
   - If Docker is not installed or the Docker daemon is unreachable, the agent **MUST NOT** silently execute untrusted converter packages on the host machine.
   - The agent **MUST explicitly ask the user for confirmation** before proceeding with host-level ephemeral virtualenv execution.
   - Example prompt to user:
     > "Docker is not available in the current environment. To ensure safety, benchmarks typically run in an isolated container. Would you like to proceed with a temporary local cleanroom sandbox instead?"
   - If the user confirms, execute using `python scripts/sandboxed_benchmark.py <tool> --allow-local-fallback`.
   - If the user denies or does not respond affirmatively, halt benchmark execution.

## 2. Benchmark Knowledge & Skills

- When a user asks to participate in the benchmark, run an evaluation, or submit results, activate the **`benchmark-participant`** skill located at:
  [`.agents/skills/benchmark-participant/SKILL.md`](.agents/skills/benchmark-participant/SKILL.md).

## 3. Submission Integrity Rules

- Benchmark results MUST be generated through `aiready run` or `scripts/sandboxed_benchmark.py`.
- Submissions MUST be packaged and cryptographically hashed via `aiready submit`.
- Never manually edit SHA256 checksums or raw scores in `submissions/runs/`.
- Never commit test runs, temporary conversion artifacts (`runs/`), or virtual environments (`.venv`).
- Ensure all custom converters adhere strictly to the **AI-Ready Image Contract**:
  - Figures placed in `images/`.
  - Filenames strictly kebab-case: `^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$`.
  - Zero broken markdown links.
