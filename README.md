# AI-Ready Document Conversion Benchmark Suite (`aiready`)

[![CI](https://github.com/sun-flat-yamada/ai-ready-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/sun-flat-yamada/ai-ready-bench/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-Live%20on%20GitHub%20Pages-brightgreen.svg)](https://sun-flat-yamada.github.io/ai-ready-bench/)
[![Tests](https://img.shields.io/badge/pytest-20%20passed-brightgreen.svg)]()

A software-driven, deterministic benchmark framework for evaluating document-to-AI-ready Markdown converters. It covers Office suites (Word, Excel, PowerPoint, Visio, Project, Access/DB), PDF, and Images, enforcing strict AST structural fidelity (TEDS), deterministic image extraction with kebab-case semantic naming, link integrity cross-checks, and token economic profiling.

Live Interactive Leaderboard: **[https://sun-flat-yamada.github.io/ai-ready-bench/](https://sun-flat-yamada.github.io/ai-ready-bench/)**

---

## 🚀 Key Highlights

- **Multi-Format Enterprise Coverage**:
  - **Word (`.docx`)**: Heading hierarchies, styled tables, embedded figures.
  - **Excel (`.xlsx`)**: Multi-sheet workbooks, formatted financial tables, charts.
  - **PowerPoint (`.pptx`)**: Multi-column slides, text boxes, diagrams.
  - **Visio (`.vsdx`)**: OPC XML shapes, diagram topology connections, embedded media.
  - **Project (`.xml`)**: Work Breakdown Structure (WBS), task durations, progress.
  - **Database (`.sqlite` / `.accdb`)**: Relational tables, schemas, structured records.
  - **PDF (`.pdf`)**: Academic layouts, multi-page tables, embedded graphics.
  - **Images (`.png`, `.jpg`)**: Standalone infographics and diagrams.
- **The AI-Ready Image Contract**:
  - Automatically extracts figures into an `images/` directory.
  - Validates strict kebab-case semantic naming (`^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$`).
  - Verifies zero broken links (`![alt](images/kebab-name.png)`) and checks for orphaned images.
- **Deterministic Software Evaluation (No Lazy LLM Prompts)**:
  - **Tree Edit Distance Similarity (TEDS)** on parsed Markdown ASTs.
  - **Table Structure Fidelity** (row/column dimensions and cell content F1).
  - **Cleanliness / Anti-Noise Ratio** (penalizes unhandled raw HTML tags and junk characters).
- **Processing Performance & Token Economics**:
  - Exact BPE token counting with `tiktoken` (`cl100k_base` and `o200k_base`).
  - Memory Peak RSS (MB) and execution latency profiling.
  - Projected input cost simulation per 1,000 documents for **GPT-4o**, **Claude 3.5 Sonnet**, **Gemini 2.0 Flash**, and **DeepSeek-V3**.
- **100% Reproducible Test Suite**:
  - Deterministic synthetic generator creating all 8 document types with ground-truth Markdown and images on demand with zero external downloads.
- **Polished via Multi-Persona Review**:
  - Co-designed with feedback from RAG Architects, Enterprise Security Auditors, MLOps Engineers, and OSS Researchers ([docs/PERSONA_REVIEWS.md](docs/PERSONA_REVIEWS.md)).

---

## 📦 Installation

Requires Python 3.10 or newer. Using [`uv`](https://github.com/astral-sh/uv) is recommended:

```bash
# Clone the repository
git clone https://github.com/sun-flat-yamada/ai-ready-bench.git
cd ai-ready-bench

# Create virtual environment and install dependencies
uv venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

uv pip install -e ".[dev]"
```

---

## ⚡ Quick Start

### 1. Generate Deterministic Test Cases
Generate the 8 standard benchmark documents and their matching ground truth:

```bash
uv run aiready generate-dataset --output-dir ./data/benchmark-suite
```

### 2. Run the Benchmark on the Built-in Reference Parser
Execute the benchmark harness and generate Rich terminal, Markdown, HTML, and JSON reports:

```bash
uv run aiready run \
  --dataset ./data/benchmark-suite \
  --converter reference \
  --work-dir ./runs \
  --output-json ./reports/run_reference.json \
  --output-md ./reports/report.md \
  --output-html ./reports/dashboard.html
```

### 3. Verify an Output Document's Image & Link Integrity
Quickly verify any generated Markdown file and its extracted images directory:

```bash
uv run aiready verify \
  --markdown ./runs/reference-software/01_word_annual_report/output.md \
  --images-dir ./runs/reference-software/01_word_annual_report/images
```

---

## 🏆 Public Leaderboard & Community Ratings (GitHub Pages)

The repository hosts an automated, interactive leaderboard deployable directly to **GitHub Pages** (`/docs` directory):

- **Live Ranking Table**: Real-time ranking sorted by Composite ACI Score, TEDS, Table Fidelity, Image Integrity, Latency, and Ingestion Cost.
- **⭐️ Star Ratings & Word-of-Mouth Reviews**: Community members can rate agents (1-5 stars) and post detailed feedback from distinct engineering personas (RAG Architect, MLOps, Enterprise Security, AI Researcher).
- **GitHub Issue Sync**: Reviews can be submitted directly through the web UI and mirrored as GitHub Issues for permanent repository record.

To view locally:
```bash
python -m http.server --directory docs 8000
# Open http://localhost:8000 in your browser
```

---

## 🤖 Distribute & Submit Your Custom Agent / Tool

Participants can benchmark their open-source or proprietary converters and submit results to the community leaderboard securely.

### 🧠 Benchmark Participant AI Agent
For AI pair programming (Antigravity, Cursor, Claude Code), this workflow is encapsulated in the **[`benchmark-participant`](.agents/skills/benchmark-participant/SKILL.md)** skill and repository rules ([`AGENTS.md`](AGENTS.md)). Simply request:
> *"Benchmark my converter [name] and prepare a submission for the leaderboard."*

The agent handles Docker detection, secure execution, link/image validation, and PR creation.

### 🛡️ Secure Execution: Docker-First Sandboxing
External converters can execute arbitrary code. Benchmark execution defaults to an isolated Docker container with dropped capabilities, non-root user (`benchuser:10001`), and memory/CPU limits:

```bash
# 1. Run via Docker-first sandbox (with interactive local fallback confirmation)
python scripts/sandboxed_benchmark.py docling

# 2. In non-interactive CI or when allowing local fallback without prompt:
python scripts/sandboxed_benchmark.py docling --allow-local-fallback

# 3. Compile the leaderboard locally or open a Pull Request
uv run aiready build-leaderboard --submissions-dir ./submissions --output ./docs/data/leaderboard.json
```

When a Pull Request with a new file in `submissions/runs/<author>/` is opened, the automated GitHub Actions workflow verifies the SHA256 payload checksum, compiles the leaderboard, and deploys it to GitHub Pages.

---

## 🔬 Benchmarking External Converters (MarkItDown, Docling, Custom CLI)

You can benchmark any external CLI tool or custom script using the generic command template:

```bash
uv run aiready run \
  --dataset ./data/benchmark-suite \
  --converter custom \
  --name "my-custom-pipeline" \
  --custom-cmd "python my_converter.py {input} {output_dir}" \
  --output-json ./reports/run_custom.json
```

### Comparing Two Converters Side-by-Side
Compare scores, TEDS, table fidelity, link integrity, and latency:

```bash
uv run aiready compare \
  --run-a ./reports/run_reference.json \
  --run-b ./reports/run_custom.json
```

---

## 📊 Evaluation Scorecard Preview

```
                       Overall Suite Performance Summary                       
+-----------------------------------------------------------------------------+
| Metric                       |       Value | Status / Evaluation Target     |
|------------------------------+-------------+--------------------------------|
| Composite Score (ACI)        | 99.65 / 100 | Target: >= 85.0                |
| Structure Fidelity (TEDS)    |      99.82% | Target: >= 85.0%               |
| Table Fidelity               |      99.61% | Target: >= 85.0%               |
| Image Pipeline Overall       |      99.12% | Target: >= 80.0%               |
| Kebab-case Naming Compliance |     100.00% | Target: 100.0%                 |
| Markdown Link Integrity      |     100.00% | Target: 100.0% (Zero broken)   |
| Cleanliness / Anti-Noise     |     100.00% | Target: >= 90.0%               |
| Mean Latency                 |      8.6 ms | Processing speed per document  |
| Peak Memory (RSS)            |    170.2 MB | Resident Memory Footprint      |
| Suite Output Tokens (cl100k) |         848 | BPE Token volume               |
+-----------------------------------------------------------------------------+
```

---

## 📚 Documentation

- [Architecture Design & Mathematics](docs/ARCHITECTURE.md)
- [Metrics Guide & Formulas](docs/METRICS_GUIDE.md)
- [Multi-Persona Review & System Polish Report](docs/PERSONA_REVIEWS.md)

---

## 🧪 Testing

Run the full automated test suite with pytest:

```bash
uv run pytest -v
```

---

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
