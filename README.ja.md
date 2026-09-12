[ [English](README.md) | **日本語** ]

# AI-Ready ドキュメント変換ベンチマークスイート (`aiready`)

[![CI](https://github.com/sun-flat-yamada/ai-ready-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/sun-flat-yamada/ai-ready-bench/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-Live%20on%20GitHub%20Pages-brightgreen.svg)](https://sun-flat-yamada.github.io/ai-ready-bench/)
[![Tests](https://img.shields.io/badge/pytest-20%20passed-brightgreen.svg)]()

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/sun.flat.yamada)

ドキュメントから「AI-Ready（AI活用に最適化された）Markdown」への変換器を評価するための、ソフトウェア駆動・決定論的なベンチマークフレームワークです。Office スイート（Word、Excel、PowerPoint、Visio、Project、Access/DB）、PDF、画像に対応し、厳格な AST 構造忠実度（TEDS）、ケバブケース（kebab-case）による意味的命名を伴う決定論的画像抽出、リンク整合性の相互検証、トークン経済性のプロファイリングを検証・保証します。

インタラクティブな公開リーダーボード: **[https://sun-flat-yamada.github.io/ai-ready-bench/](https://sun-flat-yamada.github.io/ai-ready-bench/)**

---

## 🚀 主なハイライト

- **マルチフォーマットのエンタープライズ対応**:
  - **Word (`.docx`)**: 見出し階層、スタイル付きテーブル、埋め込み図表。
  - **Excel (`.xlsx`)**: 複数シートのワークブック、整形された財務諸表テーブル、グラフ。
  - **PowerPoint (`.pptx`)**: 複数カラムのスライド、テキストボックス、ダイアグラム。
  - **Visio (`.vsdx`)**: OPC XML シェイプ、ネットワークやフローチャートの接続トポロジー、埋め込みメディア。
  - **Project (`.xml`)**: 作業分解図（WBS）、タスク期間、進捗率。
  - **Database (`.sqlite` / `.accdb`)**: リレーショナルテーブル、スキーマ、構造化レコード。
  - **PDF (`.pdf`)**: 学術論文レイアウト、複数ページにまたがる表、埋め込み図版。
  - **Images (`.png`, `.jpg`)**: 単体のインフォグラフィックやダイアグラム。
- **AI-Ready 画像規約（The AI-Ready Image Contract）**:
  - 図表を物理的に `images/` ディレクトリへ自動抽出。
  - 厳格なケバブケース（kebab-case）の意味的命名規則（`^[a-z0-9]+(-[a-z0-9]+)*\.(png|jpe?g|webp|svg)$`）を検証。
  - Markdown 内のリンク（`![alt](images/kebab-name.png)`）にリンク切れが一切ないこと、および参照されていない孤立画像がないことを検証。
- **決定論的ソフトウェア評価（安易なLLMプロンプトの排除）**:
  - パースされた Markdown AST に対する **Tree Edit Distance Similarity (TEDS)**。
  - **テーブル構造忠実度**（行/列の次元一致度およびセル内容の F1 スコア）。
  - **クリーン度 / ノイズ耐性比**（未処理の生 HTML タグや制御文字などのゴミをペナルティ評価）。
- **処理性能とトークン経済性**:
  - `tiktoken` による正確な BPE トークンカウント（`cl100k_base` および `o200k_base`）。
  - 最大メモリ使用量（Peak RSS: MB）と処理レイテンシのプロファイリング。
  - **GPT-4o**、**Claude 3.5 Sonnet**、**Gemini 2.0 Flash**、**DeepSeek-V3** におけるドキュメント 1,000 件あたりの想定入力コスト試算。
- **100% 再現可能なテストスイート**:
  - 外部ダウンロードを一切必要とせず、全 8 種類のドキュメント形式と正解（ground-truth）Markdown・画像をオンデマンドで生成する決定論的合成ジェネレータ。
- **マルチペルソナレビューによる洗練**:
  - RAG アーキテクト、エンタープライズセキュリティ監査人、MLOps エンジニア、OSS 研究者からのフィードバックに基づいて共同設計（[docs/PERSONA_REVIEWS.ja.md](docs/PERSONA_REVIEWS.ja.md) / [英語版](docs/PERSONA_REVIEWS.md)）。

---

## 📦 インストール

Python 3.10 以降が必要です。[`uv`](https://github.com/astral-sh/uv) の使用を推奨します：

```bash
# リポジトリのクローン
git clone https://github.com/sun-flat-yamada/ai-ready-bench.git
cd ai-ready-bench

# 仮想環境の作成とアクティベート
uv venv .venv
# Windows の場合:
.venv\Scripts\activate
# Linux/macOS の場合:
source .venv/bin/activate

uv pip install -e ".[dev]"
```

---

## ⚡ クイックスタート

### 1. 決定論的テストケースの生成
8 つの標準ベンチマークドキュメントと対応する正解データを生成します：

```bash
uv run aiready generate-dataset --output-dir ./data/benchmark-suite
```

### 2. 組み込みリファレンスパーサーでのベンチマーク実行
ベンチマークハーネスを実行し、Rich ターミナル、Markdown、HTML、JSON レポートを出力します：

```bash
uv run aiready run \
  --dataset ./data/benchmark-suite \
  --converter reference \
  --work-dir ./runs \
  --output-json ./reports/run_reference.json \
  --output-md ./reports/report.md \
  --output-html ./reports/dashboard.html
```

### 3. 出力ドキュメントの画像およびリンク整合性の検証
生成された Markdown ファイルと抽出された画像ディレクトリを即座に検証します：

```bash
uv run aiready verify \
  --markdown ./runs/reference-software/01_word_annual_report/output.md \
  --images-dir ./runs/reference-software/01_word_annual_report/images
```

---

## 🏆 公開リーダーボード＆コミュニティレビュー (GitHub Pages)

本リポジトリでは、**GitHub Pages**（`/docs` ディレクトリ）へ直接デプロイ可能な自動化されたインタラクティブリーダーボードをホストしています：

- **ライブランキング表**: 総合 ACI スコア、TEDS、テーブル忠実度、画像整合性、レイテンシ、取り込みコスト順でソート可能なリアルタイムランキング。
- **⭐️ スター評価＆クチコミレビュー**: コミュニティメンバーが各エージェントを評価（1〜5 つ星）し、多様なエンジニアリングペルソナ（RAG アーキテクト、MLOps、エンタープライズセキュリティ、AI 研究者）の視点から詳細なフィードバックを投稿可能。
- **GitHub Issue との同期**: レビューは Web UI から直接送信でき、リポジトリの恒久的な記録として GitHub Issue にミラーリングされます。

ローカルでプレビューする場合:
```bash
python -m http.server --directory docs 8000
# ブラウザで http://localhost:8000 を開く
```

---

## 🤖 カスタムエージェント / ツールの配布と提出

参加者は、独自のオープンソースまたはプロプライエタリなコンバーターをベンチマークし、安全にコミュニティリーダーボードへ結果を提出できます。

### 🧠 ベンチマーク参加 AI エージェント
AI ペアプログラミング（Antigravity、Cursor、Claude Code）向けに、このワークフローは **[`benchmark-participant`](.agents/skills/benchmark-participant/SKILL.md)** スキルおよびリポジトリルール（[`AGENTS.md`](AGENTS.md)）にカプセル化されています。以下のように指示するだけです：
> *「私のコンバーター [名前] をベンチマークして、リーダーボードへの提出準備をして。」*

エージェントが Docker の検出、安全な実行、リンク/画像の検証、Pull Request の作成を代行します。

### 🛡️ 安全な実行: Docker 優先サンドボックス (Docker-First Sandboxing)
外部コンバーターは任意のコードを実行する可能性があります。ベンチマークの実行は、ケーパビリティを破棄し、非 root ユーザー（`benchuser:10001`）、メモリ/CPU 制限を課した隔離 Docker コンテナをデフォルトとします：

```bash
# 1. Docker 優先サンドボックスで実行（Docker がない場合は対話形式でローカルフォールバックを確認）
python scripts/sandboxed_benchmark.py docling

# 2. 非対話型 CI、または確認プロンプトなしでローカルフォールバックを許可する場合:
python scripts/sandboxed_benchmark.py docling --allow-local-fallback

# 3. リーダーボードをローカルでビルド、または Pull Request を作成
uv run aiready build-leaderboard --submissions-dir ./submissions --output ./docs/data/leaderboard.json
```

`submissions/runs/<author>/` に新しいファイルを含む Pull Request が作成されると、自動化された GitHub Actions ワークフローが SHA256 ペイロードチェックサムを検証し、リーダーボードをコンパイルして GitHub Pages にデプロイします。

---

## 🔬 外部コンバーターのベンチマーク (MarkItDown, Docling, カスタム CLI)

汎用のコマンドテンプレートを使用して、任意の外部 CLI ツールやカスタムスクリプトをベンチマークできます：

```bash
uv run aiready run \
  --dataset ./data/benchmark-suite \
  --converter custom \
  --name "my-custom-pipeline" \
  --custom-cmd "python my_converter.py {input} {output_dir}" \
  --output-json ./reports/run_custom.json
```

### 2 つのコンバーターの並行比較
スコア、TEDS、テーブル忠実度、リンク整合性、レイテンシを直接比較します：

```bash
uv run aiready compare \
  --run-a ./reports/run_reference.json \
  --run-b ./reports/run_custom.json
```

---

## 📊 評価スコアカードのプレビュー

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

## 📚 ドキュメント

- [アーキテクチャ設計と数理モデル](docs/ARCHITECTURE.ja.md) ([English](docs/ARCHITECTURE.md))
- [メトリクスガイドと計算式](docs/METRICS_GUIDE.ja.md) ([English](docs/METRICS_GUIDE.md))
- [マルチペルソナレビューとシステム改善レポート](docs/PERSONA_REVIEWS.ja.md) ([English](docs/PERSONA_REVIEWS.md))

---

## 🧪 テスト

pytest を使用して自動テストスイート全体を実行します：

```bash
uv run pytest -v
```

---

## 📄 ライセンス

MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) を参照してください。

---

## 🤝 Contribution & Support

Contributions are welcome! If you find this tool useful, please consider supporting its development.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/sun.flat.yamada)
