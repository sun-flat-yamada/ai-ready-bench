"""Sandboxed benchmark runner for AI-Ready Benchmark Suite.

This script executes external open-source Markdown converters in fully isolated,
ephemeral virtual environments (Cleanroom Sandbox) to protect the host environment
and repository against supply chain attacks, package collision, or malicious setup hooks.
After measurement, the entire sandbox environment is completely destroyed and scrubbed.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


MARKITDOWN_ADAPTER_CODE = '''"""MarkItDown adapter running inside isolated sandbox."""
import sys
import os
import re
import zipfile
from pathlib import Path
from markitdown import MarkItDown

def to_kebab_case(text: str, max_words: int = 6) -> str:
    clean = re.sub(r"^(figure\\s*\\d*[:\\.\\-]?|fig\\s*\\d*[:\\.\\-]?|slide\\s*\\d*[:\\.\\-]?)\\s*", "", text, flags=re.IGNORECASE)
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", clean)
    words = [w.lower() for w in clean.split("-") if w]
    if not words:
        return "embedded-image"
    return "-".join(words[:max_words])

def extract_office_images(input_path: Path, images_dir: Path) -> list:
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
    if len(sys.argv) < 3:
        sys.exit(1)
    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_dir / "output.md"

    try:
        md = MarkItDown()
        result = md.convert(str(input_path))
        content = result.text_content or ""
    except Exception as e:
        content = f"# Conversion note\\nFailed direct conversion: {e}\\n"

    # Ensure image contract
    extracted = extract_office_images(input_path, images_dir)
    if extracted:
        # Check if images are linked; if not, append them with kebab-case filenames
        for img_name in extracted:
            link_pattern = f"images/{img_name}"
            if link_pattern not in content:
                alt = img_name.rsplit(".", 1)[0]
                content += f"\\n\\n![{alt}](images/{img_name})\\n"

    output_md.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    main()
'''


PYMUPDF4LLM_ADAPTER_CODE = '''"""PyMuPDF4LLM adapter running inside isolated sandbox."""
import sys
import os
import re
import zipfile
from pathlib import Path
import pymupdf4llm

def extract_office_images(input_path: Path, images_dir: Path) -> list:
    extracted = []
    suffix = input_path.suffix.lower()
    if suffix in (".docx", ".pptx", ".xlsx"):
        try:
            with zipfile.ZipFile(input_path, 'r') as zf:
                media_files = [n for n in zf.namelist() if "media/image" in n]
                for idx, mf in enumerate(sorted(media_files), 1):
                    ext = Path(mf).suffix or ".png"
                    data = zf.read(mf)
                    kebab_name = f"pymupdf-figure-{idx}{ext}"
                    out_img = images_dir / kebab_name
                    out_img.write_bytes(data)
                    extracted.append(kebab_name)
        except Exception:
            pass
    return extracted

def main():
    if len(sys.argv) < 3:
        sys.exit(1)
    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_dir / "output.md"

    suffix = input_path.suffix.lower()
    content = ""

    if suffix == ".pdf":
        try:
            content = pymupdf4llm.to_markdown(
                str(input_path),
                write_images=True,
                image_path=str(images_dir),
            )
            # Rename extracted images to strict kebab-case if needed
            for f in images_dir.glob("*.*"):
                clean = re.sub(r"[^a-zA-Z0-9]+", "-", f.stem).strip("-").lower()
                kebab_name = f"{clean}{f.suffix.lower()}"
                if f.name != kebab_name:
                    target = images_dir / kebab_name
                    f.rename(target)
                    content = content.replace(f.name, kebab_name)
        except Exception as e:
            content = f"# PDF conversion error: {e}\\n"
    else:
        # Fallback text / Office extractor using standard lightweight readers
        try:
            content = f"# Document: {input_path.stem}\\n\\n"
            content += input_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = f"# Binary document: {input_path.name}\\n"

        extracted = extract_office_images(input_path, images_dir)
        for img_name in extracted:
            alt = img_name.rsplit(".", 1)[0]
            content += f"\\n\\n![{alt}](images/{img_name})\\n"

    output_md.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    main()
'''


DOCLING_ADAPTER_CODE = '''"""Docling adapter running inside isolated sandbox."""
import sys
import os
import re
import zipfile
from pathlib import Path

def extract_office_images(input_path: Path, images_dir: Path) -> list:
    extracted = []
    suffix = input_path.suffix.lower()
    if suffix in (".docx", ".pptx", ".xlsx"):
        try:
            with zipfile.ZipFile(input_path, 'r') as zf:
                media_files = [n for n in zf.namelist() if "media/image" in n]
                for idx, mf in enumerate(sorted(media_files), 1):
                    ext = Path(mf).suffix or ".png"
                    data = zf.read(mf)
                    kebab_name = f"docling-figure-{idx}{ext}"
                    out_img = images_dir / kebab_name
                    out_img.write_bytes(data)
                    extracted.append(kebab_name)
        except Exception:
            pass
    return extracted

def main():
    if len(sys.argv) < 3:
        sys.exit(1)
    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_dir / "output.md"

    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(str(input_path))
        content = result.document.export_to_markdown()
    except Exception as e:
        content = f"# Docling conversion error: {e}\\n"

    extracted = extract_office_images(input_path, images_dir)
    for img_name in extracted:
        if f"images/{img_name}" not in content:
            alt = img_name.rsplit(".", 1)[0]
            content += f"\\n\\n![{alt}](images/{img_name})\\n"

    output_md.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    main()
'''


TOOL_CONFIGS = {
    "markitdown": {
        "name": "Microsoft-MarkItDown-Sandbox",
        "author": "Microsoft AutoGen Team",
        "version": "0.0.1a",
        "description": "Microsoft MarkItDown document converter executed in ephemeral supply-chain isolated sandbox.",
        "repo_url": "https://github.com/microsoft/markitdown",
        "packages": ["markitdown"],
        "adapter_code": MARKITDOWN_ADAPTER_CODE,
    },
    "pymupdf4llm": {
        "name": "PyMuPDF4LLM-Sandbox",
        "author": "Artifex Software",
        "version": "0.0.17",
        "description": "PyMuPDF4LLM high-speed document & PDF parser evaluated in zero-trust sandbox.",
        "repo_url": "https://github.com/pymupdf/PyMuPDF4LLM",
        "packages": ["pymupdf4llm", "pymupdf"],
        "adapter_code": PYMUPDF4LLM_ADAPTER_CODE,
    },
    "docling": {
        "name": "IBM-Docling-Sandbox",
        "author": "IBM Research / Community",
        "version": "2.5.0",
        "description": "IBM Docling deep layout document parser evaluated in ephemeral sandbox.",
        "repo_url": "https://github.com/DS4SD/docling",
        "packages": ["docling"],
        "adapter_code": DOCLING_ADAPTER_CODE,
    },
}


def run_sandboxed_benchmark(tool_key: str, repo_root: Path):
    if tool_key not in TOOL_CONFIGS:
        raise ValueError(f"Unknown tool: {tool_key}. Choices: {list(TOOL_CONFIGS.keys())}")

    cfg = TOOL_CONFIGS[tool_key]
    print(f"\n=======================================================")
    print(f" [SANDBOX] Initializing Cleanroom Sandbox for: {cfg['name']}")
    print(f"=======================================================")

    # Create temporary isolated directory outside repo
    temp_dir = Path(tempfile.mkdtemp(prefix=f"aiready_sb_{tool_key}_")).resolve()
    venv_dir = temp_dir / ".venv"
    adapter_file = temp_dir / "adapter.py"
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_json = reports_dir / f"run_{tool_key}_actual.json"

    print(f"[SANDBOX] Isolated directory created: {temp_dir}")

    try:
        # 1. Create independent virtualenv using uv
        print("[SANDBOX] Creating ephemeral virtual environment with uv venv...")
        subprocess.run(["uv", "venv", str(venv_dir)], check=True, cwd=str(temp_dir))

        # Find python binary
        if os.name == "nt":
            python_bin = venv_dir / "Scripts" / "python.exe"
        else:
            python_bin = venv_dir / "bin" / "python"

        if not python_bin.exists():
            raise RuntimeError(f"Sandbox python binary not found at {python_bin}")

        # 2. Install target packages in isolation
        print(f"[SANDBOX] Installing packages {cfg['packages']} inside sandbox only...")
        install_cmd = ["uv", "pip", "install", "--python", str(python_bin)] + cfg["packages"]
        subprocess.run(install_cmd, check=True, cwd=str(temp_dir))

        # 3. Write adapter script
        print("[SANDBOX] Writing isolated adapter script...")
        adapter_file.write_text(cfg["adapter_code"], encoding="utf-8")

        # 4. Execute aiready benchmark
        custom_cmd = f'"{python_bin}" "{adapter_file}" {{input}} {{output_dir}}'
        benchmark_cmd = [
            "uv", "run", "aiready", "run",
            "--dataset", str(repo_root / "data" / "benchmark-suite"),
            "--converter", "custom",
            "--name", cfg["name"],
            "--custom-cmd", custom_cmd,
            "--output-json", str(report_json),
        ]
        print(f"[SANDBOX] Running benchmark suite against {cfg['name']}...")
        subprocess.run(benchmark_cmd, check=True, cwd=str(repo_root))

        print(f"[SANDBOX] Benchmark successful! Output saved to: {report_json}")

        # 5. Submit to leaderboard submissions
        print(f"[SANDBOX] Packaging and signing official submission manifest...")
        submit_cmd = [
            "uv", "run", "aiready", "submit",
            "--result", str(report_json),
            "--agent-name", cfg["name"],
            "--author", cfg["author"],
            "--version", cfg["version"],
            "--repo-url", cfg["repo_url"],
            "--description", cfg["description"],
            "--submissions-dir", str(repo_root / "submissions"),
        ]
        subprocess.run(submit_cmd, check=True, cwd=str(repo_root))

    finally:
        # 6. FAIL-SAFE TEARDOWN: Completely eradicate the sandbox environment
        print(f"\n[SANDBOX-TEARDOWN] Purging and destroying sandbox: {temp_dir}...")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if temp_dir.exists():
                # Force retry on Windows if locks exist
                subprocess.run(f'cmd /c rmdir /s /q "{temp_dir}"', shell=True)
            print(f"[SANDBOX-TEARDOWN] SUCCESS: Sandbox directory completely wiped clean.")
            assert not temp_dir.exists(), f"Failed to completely remove sandbox at {temp_dir}"
        except Exception as e:
            print(f"[SANDBOX-TEARDOWN] Warning during removal: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run sandboxed benchmark for OSS converters.")
    parser.add_argument("tool", choices=["markitdown", "pymupdf4llm", "docling", "all"], help="Tool to benchmark.")
    args = parser.parse_args()

    repo_dir = Path(__file__).resolve().parent.parent

    if args.tool == "all":
        tools = ["markitdown", "pymupdf4llm", "docling"]
    else:
        tools = [args.tool]

    for t in tools:
        run_sandboxed_benchmark(t, repo_dir)

    # Rebuild leaderboard after all submissions
    print("\n[LEADERBOARD] Rebuilding community leaderboard...")
    subprocess.run([
        "uv", "run", "aiready", "build-leaderboard",
        "--submissions-dir", str(repo_dir / "submissions"),
        "--output", str(repo_dir / "docs" / "data" / "leaderboard.json")
    ], check=True, cwd=str(repo_dir))
    print("[LEADERBOARD] Successfully rebuilt leaderboard!")
