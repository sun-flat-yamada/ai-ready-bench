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

We encourage you to submit benchmarks of your open-source parsers, commercial adapters, or research models:

1. Generate the deterministic test suite:
   ```bash
   uv run aiready generate-dataset --output-dir ./data/benchmark-suite
   ```
2. Benchmark your pipeline:
   ```bash
   uv run aiready run \
     --dataset ./data/benchmark-suite \
     --converter custom \
     --name "YourAgentName" \
     --custom-cmd "python my_parser.py {input} {output_dir}" \
     --output-json ./reports/your_agent.json
   ```
3. Package and verify submission:
   ```bash
   uv run aiready submit \
     --result ./reports/your_agent.json \
     --agent-name "YourAgentName" \
     --author "your-github-username" \
     --version "1.0.0" \
     --description "Brief description of the model or layout engine"
   ```
4. Commit the new file in `submissions/` and open a Pull Request.
5. GitHub Actions will automatically validate the checksum and publish the update to the live GitHub Pages leaderboard.

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
