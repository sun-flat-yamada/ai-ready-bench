# AI-Ready Document Conversion Benchmark Suite (`aiready`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/pytest-15%20passed-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-ruff%20%2F%20pep8-black.svg)]()

A software-driven, deterministic benchmark framework for evaluating document-to-AI-ready Markdown converters. It covers Office suites (Word, Excel, PowerPoint, Visio, Project, Access/DB), PDF, and Images, enforcing strict AST structural fidelity (TEDS), deterministic image extraction with kebab-case semantic naming, link integrity cross-checks, and token economic profiling.

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
git clone https://github.com/example/aiready-benchmark.git
cd aiready-benchmark

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
