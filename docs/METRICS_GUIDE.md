[ **English** | [日本語](METRICS_GUIDE.ja.md) ]

# Metrics Guide & Evaluation Standards

This guide explains each metric calculated by `aiready-benchmark`, the underlying algorithm, and target thresholds.

---

## 1. Metric Reference Table

| Metric Key | Category | Range | Target | Description |
| :--- | :--- | :---: | :---: | :--- |
| `composite_score_100` | Composite | 0.0 - 100.0 | **>= 85.0** | Weighted overall AI-Ready Index (ACI) |
| `teds` | Structure | 0.0 - 1.0 | **>= 0.85** | Normalized Tree Edit Distance Similarity on AST |
| `heading_hierarchy` | Structure | 0.0 - 1.0 | **>= 0.90** | Fidelity of heading levels (`#`, `##`, `###`) and sequence |
| `table_fidelity` | Tables | 0.0 - 1.0 | **>= 0.85** | Row, column, and cell content alignment |
| `image_integrity` | Multimodal | 0.0 - 1.0 | **>= 0.80** | Extraction rate, kebab naming, link integrity composite |
| `kebab_compliance` | Multimodal | 0.0 - 1.0 | **1.00** | Strict adherence to `^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$` |
| `link_integrity` | Multimodal | 0.0 - 1.0 | **1.00** | Percentage of Markdown image links resolving to disk files |
| `cleanliness` | Anti-Noise | 0.0 - 1.0 | **>= 0.90** | Absence of raw HTML junk, control chars, excessive blank lines |
| `latency_ms` | Performance | ms | - | Wall-clock execution time per document |
| `peak_memory_mb` | Performance | MB | **< 500 MB** | Maximum Resident Set Size (RSS) during processing |
| `tokens_cl100k` | Cost | count | - | Accurate BPE token volume (OpenAI / tiktoken) |

---

## 2. In-Depth Metric Details

### 1. Structural Fidelity (TEDS)
- **Problem Solved**: High BLEU or ROUGE text scores can occur even when document layout is completely scrambled (e.g. table cells flattened into a wall of unsegmented text).
- **Evaluation Mechanism**: The generated Markdown is parsed into an abstract syntax tree (AST) via `markdown-it-py`. Nodes are categorized into typed structural elements (`heading`, `table`, `thead`, `tr`, `td`, `img`, `paragraph`, `list`). A dynamic programming sequence alignment computes the minimum tree transformations needed to map the candidate AST into the gold AST.

### 2. Table Fidelity Score
- **Problem Solved**: Broken table borders or merged cell errors cause hallucinations in RAG retrieval.
- **Evaluation Mechanism**:
  1. **Table Count Match**: $\frac{\min(N_{\text{pred}}, N_{\text{gold}})}{\max(N_{\text{pred}}, N_{\text{gold}})}$
  2. **Dimension Match**: Penalizes differences in row and column dimensions.
  3. **Content Overlap**: Jaccard similarity of normalized cell text sets.

### 3. Image Pipeline & Kebab-case Semantic Linking
- **Problem Solved**: Text LLMs cannot inspect figures without metadata, and broken image paths break downstream multimodal ingestion.
- **Evaluation Mechanism**:
  - **Extraction Rate**: Verifies that figures embedded in containers (DOCX drawings, PPTX picture shapes, PDF XObjects, Visio media) are saved to disk.
  - **Kebab-Case Naming**: Stems must strictly match lower-case alphanumeric hyphenation. Arbitrary names like `img_001.png` or `Slide2.JPG` fail this test.
  - **Link Integrity Check**: Every `![alt](images/filename.png)` link in the Markdown is cross-checked against actual filesystem files. If a link points to a non-existent file, it is flagged as a broken link (penalty 100%).

### 4. Noise Ratio and Cleanliness
- **Problem Solved**: Some converters dump unparsed HTML blobs (`<div class="header">`, `<span style="...">`), which bloat token counts and confuse LLMs.
- **Evaluation Mechanism**: Detects unhandled HTML tags (excluding standard Markdown-compatible table tags), control characters (`\x00` through `\x1f`), and excessive blank lines.

### 5. Cost & Token Economic Modeling
- **Problem Solved**: An ingestion pipeline that inflates token counts by 40% will increase annual enterprise LLM API costs by 40%.
- **Evaluation Mechanism**: Measures exact token counts using `tiktoken` BPE encodings. Models the projected financial cost for 1,000 document ingestions across:
  - **GPT-4o**: \$2.50 / 1M input tokens
  - **Claude 3.5 Sonnet**: \$3.00 / 1M input tokens
  - **Gemini 2.0 Flash**: \$0.10 / 1M input tokens
  - **DeepSeek-V3**: \$0.14 / 1M input tokens
