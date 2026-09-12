---
name: benchmark-participant
description: >-
  Guide and execute benchmark evaluations and official leaderboard submissions for
  ai-ready-bench participants, utilizing Docker-first container sandboxing with
  user-confirmed local fallback.
---

# Benchmark Participant & Submission Agent Runbook

This skill equips AI agents with the knowledge and execution protocols necessary to guide participants through benchmarking their document converters (e.g. Docling, MarkItDown, PyMuPDF4LLM, or proprietary pipelines) and submitting verified results to the **AI-Ready Benchmark Suite** leaderboard.

---

## 🛡️ Core Security Principle: Docker-First Sandboxing

When benchmarking external converters, untrusted packages or arbitrary CLI adapters pose significant supply chain risks:
- Pre/post-install code execution.
- Reading environment variables, credentials, or host filesystem files.
- Memory bombs or resource starvation.

### The Standard Execution Rules:
1. **DEFAULT (Docker Container Sandbox)**:
   - Benchmark runs MUST default to executing inside an isolated Docker container (`ai-ready-bench:latest`).
   - The container runs as unprivileged user `benchuser` (UID 10001).
   - Linux capabilities are dropped (`--cap-drop=ALL`).
   - Privilege escalation is disabled (`no-new-privileges:true`).
   - CPU and memory limits are enforced (`--memory=4g`, `--cpus=2.0`).
   - Dataset is mounted strictly read-only (`./data:/workspace/data:ro`).
2. **FALLBACK (Local Ephemeral Virtualenv)**:
   - If Docker is **not available or not running**, the agent MUST NOT silently run un-isolated local code.
   - The agent MUST **prompt the user for explicit confirmation** before proceeding with host execution.
   - When confirmed, execution uses an ephemeral cleanroom directory (`$TEMP/aiready_sb_*`) that is scrubbed and purged immediately after measurement.

---

## 🚀 End-to-End Participant Workflow

Follow this sequence whenever a user asks to benchmark a tool, evaluate a converter, or submit results:

### Step 1: Pre-flight Verification & Dataset Generation
Ensure benchmark test cases are generated:
```bash
uv run aiready generate-dataset --output-dir ./data/benchmark-suite
```

### Step 2: Execute Benchmark (Docker-First)
Run the sandboxed runner:
```bash
# Auto mode: Uses Docker if available; prompts user before local fallback
uv run python scripts/sandboxed_benchmark.py <tool_name> --mode auto
```
Available built-in presets:
- `reference`: The built-in pure-software reference converter.
- `markitdown`: Microsoft MarkItDown.
- `pymupdf4llm`: PyMuPDF4LLM PDF and layout reader.
- `docling`: IBM Docling deep layout engine.

#### For Custom Converters:
Participants with custom pipelines can provide an adapter script following the **AI-Ready Contract** (see section below) and run:
```bash
# In Docker (recommended):
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
      --name "MyCustomAgent" \
      --custom-cmd "python /workspace/runs/my_adapter.py {input} {output_dir}" \
      --output-json /workspace/reports/run_my_agent.json
```

### Step 3: Verify Output Contract & Link Integrity
Verify that output documents satisfy all structural and image integrity checks:
```bash
uv run aiready verify \
  --markdown ./runs/<tool>/01_word_annual_report/output.md \
  --images-dir ./runs/<tool>/01_word_annual_report/images
```
Ensure:
- Zero broken Markdown image links (`![alt](images/kebab-name.png)`).
- Strict kebab-case image naming (`^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$`).
- Zero orphan images on disk.

### Step 4: Package & Sign Official Submission
Generate a collision-free signed manifest:
```bash
uv run aiready submit \
  --result ./reports/run_<tool>_actual.json \
  --agent-name "AgentName" \
  --author "author-github-username" \
  --version "1.0.0" \
  --description "Description of layout analysis, OCR engine, or table fidelity" \
  --submissions-dir ./submissions
```
This saves an atomic, signed JSON payload under:
`submissions/runs/<author-slug>/<agent-slug>_v<version>_<sha8>.json`

### Step 5: Verify Leaderboard Compilation
Preview the updated leaderboard locally:
```bash
uv run aiready build-leaderboard \
  --submissions-dir ./submissions \
  --output ./docs/data/leaderboard.json
```

### Step 6: Submit Pull Request
Guide the participant in opening their GitHub PR:
```bash
git checkout -b submit/<agent-slug>-v<version>
git add submissions/runs/<author-slug>/
git commit -m "feat(submission): add <agent-name> v<version>"
git push origin submit/<agent-slug>-v<version>
```

---

## 📝 The AI-Ready Image Contract for Adapters

Any custom adapter script must adhere to this interface:

```python
import sys
from pathlib import Path

def main():
    input_file = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_dir / "output.md"

    # 1. Parse input_file and extract text to markdown
    markdown_content = "# Converted Title\n..."

    # 2. Extract embedded figures to images/ with strict kebab-case names
    # e.g., images/figure-1-sales-trend.png

    # 3. Reference images in Markdown
    # e.g., ![Sales Trend](images/figure-1-sales-trend.png)

    output_md.write_text(markdown_content, encoding="utf-8")

if __name__ == "__main__":
    main()
```

---

## 💬 Agent Interaction Guidelines

When assisting a user with benchmarking:
1. **Inquire about the Converter**: Ask the participant what tool, model, or script they wish to evaluate.
2. **Explain the Sandboxing**: Inform them that tests are executed in a Docker sandbox by default to protect their host environment.
3. **If Docker is Missing**: State clearly:
   > "Docker is not detected on your system. To protect your machine from unverified dependencies, benchmarking normally runs in a container. Would you like me to proceed with an ephemeral local sandbox on your machine?"
   Only proceed after receiving confirmation.
4. **Present the Evaluation Scorecard**: Summarize Composite ACI Score, TEDS, Table Fidelity, Image Integrity, and Projected Cost.
5. **Facilitate Submission**: Guide the user through signing the submission file and creating the Pull Request.
