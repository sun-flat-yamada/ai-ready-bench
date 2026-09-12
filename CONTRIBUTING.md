# Contributing to ai-ready-bench

Thank you for your interest in contributing to **ai-ready-bench**! We welcome contributions from developers, researchers, and practitioners in multimodal document processing and document AI.

---

## 🛠️ Development Setup

This project uses modern Python standards (PEP 621) with [`uv`](https://github.com/astral-sh/uv) for fast and reproducible dependency resolution.

```bash
# 1. Clone your fork
git clone https://github.com/sun-flat-yamada/ai-ready-bench.git
cd ai-ready-bench

# 2. Set up virtual environment and install dev dependencies
uv venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

uv pip install -e ".[dev]"

# 3. Verify tests pass
uv run pytest -v
```

---

## 🚀 Submitting a New Document Converter / Agent

We encourage you to submit benchmarks of your open-source parsers, commercial adapters, or research models.

### 🤖 Method A: Using the Benchmark Participant AI Agent (Recommended)

If you are using Antigravity or an AI coding assistant, the benchmark submission protocol has been fully agentified. Simply ask your assistant:

> *"I want to benchmark my converter [converter-name] and submit it to the leaderboard."*

The agent will automatically invoke the [`.agents/skills/benchmark-participant`](.agents/skills/benchmark-participant/SKILL.md) skill:
1. Verifies your test dataset.
2. Runs the measurement securely inside a Docker sandbox by default.
3. If Docker is not available in your environment, the agent asks for your confirmation before falling back to an ephemeral local virtual environment.
4. Verifies AST (TEDS) and the AI-Ready Image Contract.
5. Generates the signed submission manifest and helps open a GitHub PR.

---

### 🛡️ Method B: Manual Sandboxed Execution (Docker-First)

To protect your host machine against untrusted dependencies or malicious packages, benchmark measurement defaults to a hardened Docker container.

```bash
# 1. Generate the deterministic test suite
uv run aiready generate-dataset --output-dir ./data/benchmark-suite

# 2. Run the secure sandboxed benchmark runner (Docker-first by default)
# Supported presets: reference, markitdown, pymupdf4llm, docling
python scripts/sandboxed_benchmark.py docling

# Note: If Docker is not available on your system, the script will prompt you:
# "Do you want to proceed with local sandboxed execution? [y/N]:"
# To explicitly permit local fallback in non-interactive CI/scripts:
python scripts/sandboxed_benchmark.py docling --allow-local-fallback
```

#### For Custom Pipelines:
You can run your own converter command inside Docker directly:
```bash
docker run --rm \
  --user 10001:10001 \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --memory=4g \
  -v "$(pwd)/data:/workspace/data:ro" \
  -v "$(pwd)/runs:/workspace/runs" \
  -v "$(pwd)/reports:/workspace/reports" \
  -v "$(pwd)/submissions:/workspace/submissions" \
  ai-ready-bench:latest \
  run --dataset /workspace/data/benchmark-suite \
      --converter custom \
      --name "YourAgentName" \
      --custom-cmd "python /workspace/runs/my_parser.py {input} {output_dir}" \
      --output-json /workspace/reports/your_agent.json
```

---

### 📦 Packaging & Submitting

```bash
# 3. Package and cryptographically sign your submission manifest
uv run aiready submit \
  --result ./reports/your_agent.json \
  --agent-name "YourAgentName" \
  --author "your-github-username" \
  --version "1.0.0" \
  --description "Brief description of the model or layout engine" \
  --submissions-dir ./submissions

# 4. Commit and open a Pull Request
git checkout -b submit/your-agent-name
git add submissions/runs/your-github-username/
git commit -m "feat(submission): add YourAgentName v1.0.0"
git push origin submit/your-agent-name
```
GitHub Actions will automatically validate the SHA256 checksum and publish the update to the live GitHub Pages leaderboard.

---

## 🧪 Testing Guidelines

- Write deterministic unit tests for any new parser adapter or metric in `tests/`.
- Ensure no flaky tests or external internet dependencies are introduced in the test suite.
- Run `uv run pytest -v` before pushing.

---

## 📜 Pull Request Process

1. Create a feature branch: `git checkout -b feat/my-new-feature`.
2. Follow Conventional Commits format (e.g. `feat:`, `fix:`, `docs:`, `test:`).
3. Ensure all CI checks pass.
4. Fill out the PR template with clear context and rationale.
