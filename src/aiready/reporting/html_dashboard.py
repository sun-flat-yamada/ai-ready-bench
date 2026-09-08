"""Standalone interactive HTML dashboard for benchmark evaluation."""

from pathlib import Path
from aiready.evaluators.benchmark_runner import BenchmarkRunResult


def generate_html_dashboard(result: BenchmarkRunResult) -> str:
    """Generate an interactive, responsive standalone HTML dashboard with embedded charts."""
    case_rows = []
    for c in result.cases:
        if not c.success:
            case_rows.append(f"""
            <tr class="failed-row">
                <td><strong>{c.case_name}</strong></td>
                <td><span class="badge badge-format">{c.format}</span></td>
                <td><span class="badge badge-fail">FAILED</span></td>
                <td colspan="7"><em>{c.error_message or 'Error during conversion'}</em></td>
            </tr>
            """)
            continue

        case_rows.append(f"""
        <tr>
            <td><strong>{c.case_name}</strong></td>
            <td><span class="badge badge-format">{c.format}</span></td>
            <td><span class="badge badge-score">{c.composite_score_100:.1f}</span></td>
            <td>{c.scores.get('teds', 0.0):.2f}</td>
            <td>{c.scores.get('table_fidelity', 0.0):.2f}</td>
            <td>{c.scores.get('image_integrity', 0.0):.2f}</td>
            <td>{c.scores.get('kebab_compliance', 0.0):.2f}</td>
            <td>{c.scores.get('link_integrity', 0.0):.2f}</td>
            <td>{c.cost_metrics.get('latency_ms', 0.0):.0f} ms</td>
            <td>{c.cost_metrics.get('tokens_cl100k', 0):,}</td>
        </tr>
        """)

    cost_cards = []
    rate_map = {
        "gpt-4o": "$2.50 / 1M in",
        "claude-3-5-sonnet": "$3.00 / 1M in",
        "gemini-2-0-flash": "$0.10 / 1M in",
        "deepseek-v3": "$0.14 / 1M in",
    }
    for model_name, cost in result.projected_cost_per_1k_suite_usd.items():
        cost_cards.append(f"""
        <div class="card cost-card">
            <div class="card-title">{model_name.upper()}</div>
            <div class="cost-value">${cost:.4f}</div>
            <div class="cost-rate">{rate_map.get(model_name, '')}</div>
            <div class="card-sub">per 1,000 document suite runs</div>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Ready Document Conversion Benchmark - {result.converter_name}</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-purple: #a855f7;
            --accent-yellow: #fbbf24;
            --accent-red: #f87171;
            --border-color: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 2rem;
            line-height: 1.5;
        }}
        .header {{
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 1.8rem; color: var(--accent-blue); }}
        .header-meta {{ color: var(--text-secondary); font-size: 0.9rem; }}
        .grid-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
            transition: transform 0.2s ease;
        }}
        .card:hover {{ transform: translateY(-2px); }}
        .card-title {{ font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.5rem; }}
        .card-value {{ font-size: 2rem; font-weight: 700; color: var(--text-primary); }}
        .card-value.highlight {{ color: var(--accent-yellow); }}
        .card-value.green {{ color: var(--accent-green); }}
        .card-sub {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem; }}
        .cost-card {{ text-align: center; border-top: 3px solid var(--accent-purple); }}
        .cost-value {{ font-size: 1.6rem; font-weight: 700; color: var(--accent-purple); }}
        .cost-rate {{ font-size: 0.85rem; color: var(--accent-blue); margin: 0.25rem 0; }}
        .section-title {{ font-size: 1.3rem; margin: 2rem 0 1rem; color: var(--accent-blue); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-card);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }}
        th, td {{
            padding: 0.85rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: #1e293b;
            color: var(--accent-blue);
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        tr:hover {{ background-color: rgba(255, 255, 255, 0.03); }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-score {{ background: rgba(52, 211, 153, 0.2); color: var(--accent-green); }}
        .badge-format {{ background: rgba(56, 189, 248, 0.2); color: var(--accent-blue); }}
        .badge-fail {{ background: rgba(248, 113, 113, 0.2); color: var(--accent-red); }}
        .footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>AI-Ready Document Conversion Benchmark</h1>
            <div class="header-meta">Converter Target: <strong>{result.converter_name}</strong> | Run: {result.timestamp}</div>
        </div>
        <div>
            <span class="badge badge-score" style="font-size: 1.1rem; padding: 0.5rem 1rem;">
                ACI: {result.mean_composite_score:.2f} / 100
            </span>
        </div>
    </div>

    <div class="grid-stats">
        <div class="card">
            <div class="card-title">Structural Fidelity (TEDS)</div>
            <div class="card-value green">{result.mean_teds_score:.1%}</div>
            <div class="card-sub">Target: >= 85.0%</div>
        </div>
        <div class="card">
            <div class="card-title">Table Fidelity</div>
            <div class="card-value green">{result.mean_table_score:.1%}</div>
            <div class="card-sub">Rows, cols & cell content</div>
        </div>
        <div class="card">
            <div class="card-title">Image Pipeline</div>
            <div class="card-value green">{result.mean_image_score:.1%}</div>
            <div class="card-sub">Extraction & kebab-case linking</div>
        </div>
        <div class="card">
            <div class="card-title">Link Integrity</div>
            <div class="card-value green">{result.mean_link_integrity:.1%}</div>
            <div class="card-sub">Unbroken Markdown image links</div>
        </div>
        <div class="card">
            <div class="card-title">Cleanliness</div>
            <div class="card-value green">{result.mean_cleanliness_score:.1%}</div>
            <div class="card-sub">Noise & raw HTML suppression</div>
        </div>
        <div class="card">
            <div class="card-title">Mean Latency</div>
            <div class="card-value">{result.mean_latency_ms:.0f} <span style="font-size: 1rem;">ms</span></div>
            <div class="card-sub">Peak RAM: {result.mean_peak_memory_mb:.1f} MB</div>
        </div>
    </div>

    <h2 class="section-title">Projected Ingestion Cost (per 1,000 Suite Executions)</h2>
    <div class="grid-stats">
        {''.join(cost_cards)}
    </div>

    <h2 class="section-title">Test Cases Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Case Name</th>
                <th>Format</th>
                <th>ACI Score</th>
                <th>TEDS</th>
                <th>Table</th>
                <th>Image</th>
                <th>Kebab</th>
                <th>Link</th>
                <th>Latency</th>
                <th>Tokens</th>
            </tr>
        </thead>
        <tbody>
            {''.join(case_rows)}
        </tbody>
    </table>

    <div class="footer">
        Generated by <strong>aiready-benchmark</strong> | Designed for rigorous, software-driven AI-Ready evaluation
    </div>
</body>
</html>
"""
    return html


def save_html_dashboard(result: BenchmarkRunResult, output_path: Path):
    """Save HTML dashboard to file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_html_dashboard(result), encoding="utf-8")
