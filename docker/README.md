# AI-Ready Benchmark Docker Environment Specification

This directory contains the containerization definitions for the **AI-Ready Document Conversion Benchmark Suite** (`aiready`).

## 1. Architectural & Security Requirements

External document converters (especially third-party open-source libraries or experimental neural parsers) pose significant supply chain risks:
- **Arbitrary Code Execution**: Wheel/sdist post-install scripts or malicious parser code.
- **Credential & File Exfiltration**: Scanning environment variables, ssh keys, or cloud metadata.
- **Resource Exhaustion**: Unbounded memory allocation (zip bombs, unbounded OCR pipelines) crashing the host machine.

### Security Guarantees in Docker Configuration:
1. **Unprivileged User (`benchuser:10001`)**:
   - The container explicitly drops root privileges and executes as unprivileged UID 10001.
2. **Capability Dropping (`cap_drop: ALL`)**:
   - Drops all Linux kernel capabilities (`--cap-drop=ALL`).
3. **Privilege Escalation Prevention**:
   - Enforces `no-new-privileges:true`.
4. **Network Sandboxing (`network_mode: none`)**:
   - Benchmark runs default to zero network access, preventing any exfiltration of ground truth datasets, outputs, or host data.
5. **Resource Limits**:
   - Maximum 4GB RAM and 2.0 CPUs by default, preventing host memory exhaustion.
6. **Volume Segregation**:
   - Dataset directory `./data` is mounted strictly read-only (`:ro`).
   - Writable volumes are scoped exclusively to `./runs`, `./reports`, and `./submissions`.

---

## 2. Quick Usage

### Build the Image:
```bash
docker compose -f docker/docker-compose.yml build
```

### Run Benchmark inside Docker:
```bash
# Reference converter in network-isolated container
docker compose -f docker/docker-compose.yml run --rm benchmark

# Or run custom command directly with docker run
docker run --rm \
  --user 10001:10001 \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --memory=4g \
  --network=none \
  -v "$(pwd)/data:/workspace/data:ro" \
  -v "$(pwd)/runs:/workspace/runs" \
  -v "$(pwd)/reports:/workspace/reports" \
  -v "$(pwd)/submissions:/workspace/submissions" \
  ai-ready-bench:latest \
  run --dataset /workspace/data/benchmark-suite --converter reference
```

### Automatic Orchestration:
For automatic detection of Docker and fallback handling, participants should use:
```bash
python scripts/sandboxed_benchmark.py <tool>
```
If Docker is present, it will run inside the Docker container automatically. If Docker is unavailable, it will prompt the user before falling back to local cleanroom execution.
