# ==============================================================================
# AI-Ready Document Conversion Benchmark Suite (aiready)
# Secure Isolated Docker Sandbox Environment
# ==============================================================================
# Requirement:
# 1. Zero-trust isolation against supply chain attacks from external converters.
# 2. Non-root unprivileged execution (benchuser: 10001).
# 3. System libraries for PDF, OCR, Image, and Office document parsing.
# 4. Fast, deterministic dependency management using uv.
# ==============================================================================

FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    PATH="/home/benchuser/.local/bin:/workspace/.venv/bin:$PATH"

# Install essential system libraries for multimodal document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install uv for deterministic dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create secure unprivileged user and directories
RUN groupadd -g 10001 benchuser && \
    useradd -u 10001 -g benchuser -m -s /bin/bash benchuser

WORKDIR /workspace

# Create standard directory layout and assign ownership
RUN mkdir -p /workspace/data /workspace/runs /workspace/reports /workspace/submissions /workspace/scripts && \
    chown -R benchuser:benchuser /workspace

# Switch to unprivileged user for build and execution
USER benchuser

# Pre-initialize virtualenv in workspace
RUN uv venv /workspace/.venv

# Copy dependency specifications first for caching
COPY --chown=benchuser:benchuser pyproject.toml README.md /workspace/

# Install benchmark harness dependencies
COPY --chown=benchuser:benchuser src/ /workspace/src/
RUN uv pip install --no-cache -e .

# Copy benchmark helper scripts
COPY --chown=benchuser:benchuser scripts/ /workspace/scripts/

# Default working volume paths
VOLUME ["/workspace/data", "/workspace/runs", "/workspace/reports", "/workspace/submissions"]

# Default entrypoint
ENTRYPOINT ["aiready"]
CMD ["--help"]
