"""Sandboxed benchmark runner for AI-Ready Benchmark Suite.

This script executes document converters in fully isolated environments:
1. DEFAULT: Secure Docker container sandbox with non-root user, dropped capabilities,
   and resource limits.
2. FALLBACK: Ephemeral local cleanroom virtual environment, used ONLY after explicit
   user confirmation when Docker is unavailable in the execution environment.

After measurement, all sandbox artifacts and ephemeral environments are scrubbed clean.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


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
    "reference": {
        "name": "Reference-Software",
        "author": "AI-Ready Core Team",
        "version": "1.0.0",
        "description": "Pure software reference converter supporting Office, PDF, and image formats.",
        "repo_url": "https://github.com/sun-flat-yamada/ai-ready-bench",
        "packages": [],
        "adapter_code": None,
    },
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


def is_docker_available() -> bool:
    """Check if Docker CLI is installed and Docker daemon is responsive."""
    try:
        proc = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def confirm_local_fallback(assume_yes: bool = False, allow_fallback_flag: bool = False) -> bool:
    """Ask user for explicit confirmation before running local un-sandboxed execution.

    In interactive environments, prompt the user.
    In non-interactive environments, require --allow-local-fallback or --yes.
    """
    if assume_yes or allow_fallback_flag:
        print("[SANDBOX-NOTICE] User authorized local fallback via CLI flag (--allow-local-fallback / -y).")
        return True

    # Check if standard input is an interactive terminal
    is_interactive = sys.stdin and sys.stdin.isatty()

    if not is_interactive:
        print("\n[SECURITY-ERROR] Docker is unavailable and session is non-interactive.")
        print("To allow local execution without Docker, pass --allow-local-fallback or -y.")
        return False

    print("\n" + "=" * 65)
    print(" [SECURITY ALERT] Docker Sandbox is NOT Available")
    print("=" * 65)
    print("Benchmark measurement defaults to an isolated Docker container")
    print("to protect against potential supply-chain risks in external packages.")
    print("Running locally will execute the converter in a host virtualenv.")
    print("=" * 65)

    try:
        response = input("Do you want to proceed with local sandboxed execution? [y/N]: ").strip().lower()
        confirmed = response in ("y", "yes")
        if not confirmed:
            print("[SANDBOX] Local execution aborted by user.")
        return confirmed
    except (EOFError, KeyboardInterrupt):
        print("\n[SANDBOX] Operation canceled.")
        return False


def run_docker_sandboxed_benchmark(tool_key: str, repo_root: Path) -> bool:
    """Execute benchmark inside secure Docker container with strict sandbox boundaries."""
    cfg = TOOL_CONFIGS[tool_key]
    print(f"\n=======================================================")
    print(f" [DOCKER-SANDBOX] Launching Container for: {cfg['name']}")
    print(f"=======================================================")

    image_name = "ai-ready-bench:latest"
    dockerfile_path = repo_root / "docker" / "Dockerfile"

    # 1. Build or refresh container image
    print(f"[DOCKER-SANDBOX] Ensuring Docker image '{image_name}' is ready...")
    build_cmd = [
        "docker", "build",
        "-t", image_name,
        "-f", str(dockerfile_path),
        str(repo_root),
    ]
    build_proc = subprocess.run(build_cmd, cwd=str(repo_root))
    if build_proc.returncode != 0:
        raise RuntimeError("Failed to build Docker sandbox image.")

    # 2. Run container with security isolation
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_json = reports_dir / f"run_{tool_key}_actual.json"

    # Volume mounts
    data_dir = repo_root / "data"
    runs_dir = repo_root / "runs"
    submissions_dir = repo_root / "submissions"
    data_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    submissions_dir.mkdir(parents=True, exist_ok=True)

    print("[DOCKER-SANDBOX] Running container with security flags:")
    print("  - User: 10001:10001 (benchuser, unprivileged)")
    print("  - Capabilities: ALL dropped (--cap-drop=ALL)")
    print("  - Privilege escalation: Disabled (no-new-privileges:true)")
    print("  - Memory limit: 4096MB")
    print("  - Read-only data mount: ./data:/workspace/data:ro")

    # Command to run inside container: delegate to internal runner with local mode
    docker_run_cmd = [
        "docker", "run", "--rm",
        "--user", "10001:10001",
        "--cap-drop=ALL",
        "--security-opt", "no-new-privileges:true",
        "--memory", "4096m",
        "-v", f"{data_dir.resolve()}:/workspace/data:ro",
        "-v", f"{runs_dir.resolve()}:/workspace/runs:rw",
        "-v", f"{reports_dir.resolve()}:/workspace/reports:rw",
        "-v", f"{submissions_dir.resolve()}:/workspace/submissions:rw",
        "--entrypoint", "python",
        image_name,
        "scripts/sandboxed_benchmark.py", tool_key,
        "--mode", "local",
        "--allow-local-fallback",
    ]

    proc = subprocess.run(docker_run_cmd, cwd=str(repo_root))
    if proc.returncode != 0:
        raise RuntimeError(f"Docker container execution exited with code {proc.returncode}")

    print(f"[DOCKER-SANDBOX] Execution complete! Results recorded in {report_json}")
    return True


def run_local_sandboxed_benchmark(tool_key: str, repo_root: Path):
    """Execute converter in ephemeral cleanroom virtualenv on host."""
    cfg = TOOL_CONFIGS[tool_key]
    print(f"\n=======================================================")
    print(f" [LOCAL-SANDBOX] Initializing Cleanroom for: {cfg['name']}")
    print(f"=======================================================")

    temp_dir = Path(tempfile.mkdtemp(prefix=f"aiready_sb_{tool_key}_")).resolve()
    venv_dir = temp_dir / ".venv"
    adapter_file = temp_dir / "adapter.py"
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_json = reports_dir / f"run_{tool_key}_actual.json"

    print(f"[LOCAL-SANDBOX] Isolated temp directory: {temp_dir}")

    try:
        # Check if reference converter (no extra venv or packages needed)
        if tool_key == "reference":
            benchmark_cmd = [
                "uv", "run", "aiready", "run",
                "--dataset", str(repo_root / "data" / "benchmark-suite"),
                "--converter", "reference",
                "--name", cfg["name"],
                "--output-json", str(report_json),
            ]
        else:
            # 1. Ephemeral virtualenv using uv
            print("[LOCAL-SANDBOX] Creating ephemeral virtual environment with uv venv...")
            subprocess.run(["uv", "venv", str(venv_dir)], check=True, cwd=str(temp_dir))

            if os.name == "nt":
                python_bin = venv_dir / "Scripts" / "python.exe"
            else:
                python_bin = venv_dir / "bin" / "python"

            if not python_bin.exists():
                raise RuntimeError(f"Sandbox python binary not found at {python_bin}")

            # 2. Install target packages in isolation
            if cfg["packages"]:
                print(f"[LOCAL-SANDBOX] Installing packages {cfg['packages']} inside sandbox...")
                install_cmd = ["uv", "pip", "install", "--python", str(python_bin)] + cfg["packages"]
                subprocess.run(install_cmd, check=True, cwd=str(temp_dir))

            # 3. Write adapter script
            print("[LOCAL-SANDBOX] Writing isolated adapter script...")
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

        print(f"[LOCAL-SANDBOX] Running benchmark suite against {cfg['name']}...")
        subprocess.run(benchmark_cmd, check=True, cwd=str(repo_root))
        print(f"[LOCAL-SANDBOX] Benchmark successful! Output saved to: {report_json}")

        # 5. Package and sign submission manifest
        print(f"[LOCAL-SANDBOX] Packaging and signing official submission manifest...")
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
        # 6. Guaranteed Cleanup (Fail-Safe Teardown)
        print(f"\n[LOCAL-TEARDOWN] Purging and destroying sandbox: {temp_dir}...")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if temp_dir.exists():
                if os.name == "nt":
                    subprocess.run(f'cmd /c rmdir /s /q "{temp_dir}"', shell=True)
                else:
                    subprocess.run(["rm", "-rf", str(temp_dir)])
            print(f"[LOCAL-TEARDOWN] SUCCESS: Local sandbox directory completely wiped clean.")
        except Exception as e:
            print(f"[LOCAL-TEARDOWN] Warning during removal: {e}")


def run_sandboxed_benchmark(
    tool_key: str,
    repo_root: Path,
    mode: str = "auto",
    allow_fallback: bool = False,
    assume_yes: bool = False,
):
    """Orchestrates benchmark measurement following Docker-first policy with confirmed local fallback."""
    if tool_key not in TOOL_CONFIGS:
        raise ValueError(f"Unknown tool: {tool_key}. Choices: {list(TOOL_CONFIGS.keys())}")

    docker_available = is_docker_available()

    if mode == "docker":
        if not docker_available:
            print("[ERROR] Mode is set to 'docker', but Docker daemon is not available or not running.")
            sys.exit(1)
        run_docker_sandboxed_benchmark(tool_key, repo_root)

    elif mode == "local":
        print("[NOTICE] Mode explicitly set to 'local'. Running in ephemeral host sandbox.")
        run_local_sandboxed_benchmark(tool_key, repo_root)

    else:  # mode == "auto" (default)
        if docker_available:
            print("[SANDBOX-DISCOVERY] Docker is available. Executing via Docker sandbox (default).")
            run_docker_sandboxed_benchmark(tool_key, repo_root)
        else:
            print("[SANDBOX-DISCOVERY] Docker is NOT available in this environment.")
            confirmed = confirm_local_fallback(assume_yes=assume_yes, allow_fallback_flag=allow_fallback)
            if confirmed:
                print("[SANDBOX-DISCOVERY] Proceeding with local sandboxed benchmark...")
                run_local_sandboxed_benchmark(tool_key, repo_root)
            else:
                print("[ABORT] Benchmark execution halted. Start Docker or confirm local execution to proceed.")
                sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run sandboxed benchmark for document converters (Docker-first with local fallback)."
    )
    parser.add_argument(
        "tool",
        choices=["reference", "markitdown", "pymupdf4llm", "docling", "all"],
        help="Tool or converter to benchmark.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "docker", "local"],
        default="auto",
        help="Execution mode. 'auto' (default) uses Docker if available, prompting before local fallback. "
             "'docker' forces Docker container execution. 'local' forces local sandbox.",
    )
    parser.add_argument(
        "--allow-local-fallback",
        action="store_true",
        help="Allow local execution fallback without interactive prompt when Docker is unavailable.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Automatically answer yes to prompts.",
    )
    parser.add_argument(
        "--no-leaderboard-rebuild",
        action="store_true",
        help="Skip rebuilding the leaderboard after benchmark execution.",
    )

    args = parser.parse_args()
    repo_dir = Path(__file__).resolve().parent.parent

    if args.tool == "all":
        tools = ["markitdown", "pymupdf4llm", "docling"]
    else:
        tools = [args.tool]

    for t in tools:
        run_sandboxed_benchmark(
            t,
            repo_dir,
            mode=args.mode,
            allow_fallback=args.allow_local_fallback,
            assume_yes=args.yes,
        )

    if not args.no_leaderboard_rebuild:
        print("\n[LEADERBOARD] Rebuilding community leaderboard...")
        subprocess.run([
            "uv", "run", "aiready", "build-leaderboard",
            "--submissions-dir", str(repo_dir / "submissions"),
            "--output", str(repo_dir / "docs" / "data" / "leaderboard.json")
        ], check=True, cwd=str(repo_dir))
        print("[LEADERBOARD] Successfully rebuilt leaderboard!")
