"""Unit tests for the sandboxed benchmark runner and fallback logic."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts directory to sys.path
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import sandboxed_benchmark


def test_is_docker_available_true():
    """Verify is_docker_available returns True when docker info succeeds."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert sandboxed_benchmark.is_docker_available() is True


def test_is_docker_available_false_on_error():
    """Verify is_docker_available returns False when docker command fails or is missing."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert sandboxed_benchmark.is_docker_available() is False

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["docker", "info"], timeout=5)):
        assert sandboxed_benchmark.is_docker_available() is False


def test_confirm_local_fallback_with_flags():
    """Verify confirmation succeeds without prompting when flags are set."""
    assert sandboxed_benchmark.confirm_local_fallback(assume_yes=True) is True
    assert sandboxed_benchmark.confirm_local_fallback(allow_fallback_flag=True) is True


def test_confirm_local_fallback_non_interactive():
    """Verify confirmation fails in non-interactive environment without flags."""
    with patch("sys.stdin.isatty", return_value=False):
        assert sandboxed_benchmark.confirm_local_fallback(assume_yes=False, allow_fallback_flag=False) is False


def test_confirm_local_fallback_interactive_prompt_yes():
    """Verify user input 'y' or 'yes' confirms local fallback."""
    with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="y"):
        assert sandboxed_benchmark.confirm_local_fallback() is True

    with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="YES"):
        assert sandboxed_benchmark.confirm_local_fallback() is True


def test_confirm_local_fallback_interactive_prompt_no():
    """Verify user input 'n' or empty string aborts local fallback."""
    with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="n"):
        assert sandboxed_benchmark.confirm_local_fallback() is False

    with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
        assert sandboxed_benchmark.confirm_local_fallback() is False


def test_run_sandboxed_benchmark_auto_aborts_without_permission():
    """Verify auto mode exits when Docker is unavailable and fallback is denied."""
    repo_root = Path(__file__).resolve().parent.parent
    with patch("sandboxed_benchmark.is_docker_available", return_value=False), \
         patch("sandboxed_benchmark.confirm_local_fallback", return_value=False), \
         pytest.raises(SystemExit) as excinfo:
        sandboxed_benchmark.run_sandboxed_benchmark("reference", repo_root, mode="auto")

    assert excinfo.value.code == 1


def test_run_sandboxed_benchmark_docker_mode_fails_when_unavailable():
    """Verify docker mode exits with error when Docker is not running."""
    repo_root = Path(__file__).resolve().parent.parent
    with patch("sandboxed_benchmark.is_docker_available", return_value=False), \
         pytest.raises(SystemExit) as excinfo:
        sandboxed_benchmark.run_sandboxed_benchmark("reference", repo_root, mode="docker")

    assert excinfo.value.code == 1
