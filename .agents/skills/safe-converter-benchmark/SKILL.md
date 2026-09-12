---
name: safe-converter-benchmark
description: >-
  Execute and benchmark external open-source document converters in fully isolated,
  ephemeral sandboxes to defend against supply chain attacks, measure AST & image integrity,
  package official submissions, and update the ai-ready-bench leaderboard.
---

# Safe Converter Benchmark & Ephemeral Sandbox Runbook

This skill outlines the complete protocol for discovering, adapting, benchmarking, and submitting open-source document-to-Markdown converters within `ai-ready-bench`, with **Zero Trust & Cleanroom Sandbox Isolation** to prevent supply-chain attacks.

---

## 1. Supply Chain Threat Model & Sandbox Architecture

When installing and evaluating external open-source packages (especially newly released converters or deep neural pipelines), host environments face significant security risks:
- **Malicious `setup.py` / Wheel Hooks**: Pre/post-install arbitrary code execution.
- **Environment & Credential Exfiltration**: Reading environment variables or SSH/Git keys.
- **Dependency Confusion / Namespace Collisions**: Polluting the project's primary virtual environment.

### The Cleanroom Sandbox Protocol
1. **Isolated Ephemeral Directory**:
   - Always allocate a temporary working space in system temp (`$env:TEMP/aiready_sb_<tool>_<uuid>`).
   - Never install external packages into the project's root `.venv`.
2. **Ephemeral Virtualenv**:
   - Spin up a standalone environment with `uv venv <temp_dir>/.venv`.
   - Install only the required packages using `uv pip install --python <sandbox_python> <packages>`.
3. **Execution Boundary**:
   - External code only interacts with `{input}` and `{output_dir}`.
   - Outputs must conform to the **AI-Ready Contract**:
     - Main text saved to `{output_dir}/output.md`.
     - Extracted figures stored in `{output_dir}/images/` with strict kebab-case naming (`^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$`).
     - Markdown references must match (`![alt](images/kebab-name.png)`).
4. **Guaranteed Cleanup (Fail-Safe Teardown)**:
   - Use `try...finally` in Python or defensive PowerShell scripts to forcefully purge the sandbox directory upon completion, regardless of execution outcome.

---

## 2. Automated Benchmark Execution

Use the dedicated runner script:

```bash
# Run a specific converter in its isolated sandbox
uv run python scripts/sandboxed_benchmark.py markitdown
uv run python scripts/sandboxed_benchmark.py pymupdf4llm
uv run python scripts/sandboxed_benchmark.py docling

# Or run all configured converters sequentially
uv run python scripts/sandboxed_benchmark.py all
```

### What the Script Executes:
1. Allocates `$env:TEMP/aiready_sb_<tool>_<uuid>`.
2. Creates isolated virtual environment.
3. Installs specified packages (e.g. `markitdown`, `pymupdf4llm`, or `docling`).
4. Generates an adapter script enforcing image extraction and kebab-case naming.
5. Invokes `aiready run --converter custom --custom-cmd "<sandbox_python> <adapter> {input} {output_dir}"`.
6. Packages and signs the submission manifest into `submissions/runs/<author>/<agent>.json`.
7. Purges the sandbox directory completely.
8. Rebuilds `docs/data/leaderboard.json` automatically.

---

## 3. Custom Converter Adapter Template

When adding a new converter, implement an adapter following this pattern:

```python
import sys
import os
import re
import zipfile
from pathlib import Path

def extract_office_images(input_path: Path, images_dir: Path) -> list:
    """Extract embedded figures from Office containers with kebab-case naming."""
    extracted = []
    suffix = input_path.suffix.lower()
    if suffix in (".docx", ".pptx", ".xlsx"):
        try:
            with zipfile.ZipFile(input_path, 'r') as zf:
                media_files = [n for n in zf.namelist() if "media/image" in n]
                for idx, mf in enumerate(sorted(media_files), 1):
                    ext = Path(mf).suffix or ".png"
                    data = zf.read(mf)
                    kebab_name = f"extracted-figure-{idx}{ext}"
                    out_img = images_dir / kebab_name
                    out_img.write_bytes(data)
                    extracted.append(kebab_name)
        except Exception:
            pass
    return extracted

def main():
    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_dir / "output.md"

    # 1. Execute primary conversion logic
    content = "" # Your converter output here

    # 2. Enforce Image Contract
    extracted = extract_office_images(input_path, images_dir)
    for img_name in extracted:
        if f"images/{img_name}" not in content:
            alt = img_name.rsplit(".", 1)[0]
            content += f"\n\n![{alt}](images/{img_name})\n"

    output_md.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    main()
```

---

## 4. Verification & Inspection Runbook

After running a benchmark:

```bash
# Verify image and link integrity for a generated document
uv run aiready verify \
  --markdown ./runs/custom-converter/01_word_annual_report/output.md \
  --images-dir ./runs/custom-converter/01_word_annual_report/images

# Compare results side-by-side against the reference converter
uv run aiready compare \
  --run-a ./reports/run_reference.json \
  --run-b ./reports/run_docling_actual.json

# Check that the sandbox directory has been completely deleted
powershell -Command "Get-ChildItem -Path $env:TEMP -Filter 'aiready_sb_*'"
```
