"""Table structure and cell fidelity evaluation for Markdown tables."""

import re
from typing import List, Dict, Any, Tuple
from markdown_it import MarkdownIt


class ParsedTable:
    """Represents a Markdown table structure."""

    def __init__(self, headers: List[str], rows: List[List[str]]):
        self.headers = [h.strip() for h in headers]
        self.rows = [[cell.strip() for cell in r] for r in rows]

    @property
    def num_rows(self) -> int:
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        if self.headers:
            return len(self.headers)
        if self.rows:
            return len(self.rows[0])
        return 0


def extract_tables_from_markdown(markdown_text: str) -> List[ParsedTable]:
    """Parse GFM tables from markdown text into structured objects."""
    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(markdown_text)

    tables: List[ParsedTable] = []
    in_table = False
    in_thead = False
    in_tbody = False
    current_headers: List[str] = []
    current_rows: List[List[str]] = []
    current_row: List[str] = []

    for i, token in enumerate(tokens):
        if token.type == "table_open":
            in_table = True
            current_headers = []
            current_rows = []
        elif token.type == "table_close":
            in_table = False
            tables.append(ParsedTable(headers=current_headers, rows=current_rows))
        elif in_table:
            if token.type == "thead_open":
                in_thead = True
            elif token.type == "thead_close":
                in_thead = False
            elif token.type == "tbody_open":
                in_tbody = True
            elif token.type == "tbody_close":
                in_tbody = False
            elif token.type == "tr_open":
                current_row = []
            elif token.type == "tr_close":
                if in_thead:
                    current_headers = current_row
                elif in_tbody:
                    current_rows.append(current_row)
            elif token.type == "inline":
                current_row.append(token.content)

    return tables


def evaluate_table_fidelity(pred_tables: List[ParsedTable], gold_tables: List[ParsedTable]) -> Dict[str, Any]:
    """Calculate structural and content fidelity of tables."""
    if not gold_tables and not pred_tables:
        return {
            "table_count_score": 1.0,
            "dimension_score": 1.0,
            "content_overlap_score": 1.0,
            "overall_table_score": 1.0,
        }

    if not gold_tables or not pred_tables:
        return {
            "table_count_score": 0.0,
            "dimension_score": 0.0,
            "content_overlap_score": 0.0,
            "overall_table_score": 0.0,
        }

    count_score = min(len(pred_tables), len(gold_tables)) / max(len(pred_tables), len(gold_tables))

    dim_scores = []
    content_scores = []

    for idx in range(min(len(pred_tables), len(gold_tables))):
        p_tab = pred_tables[idx]
        g_tab = gold_tables[idx]

        # Dimension matching (rows and cols)
        row_diff = abs(p_tab.num_rows - g_tab.num_rows)
        col_diff = abs(p_tab.num_cols - g_tab.num_cols)
        dim_sim = max(0.0, 1.0 - (row_diff * 0.15 + col_diff * 0.25))
        dim_scores.append(dim_sim)

        # Cell content bag-of-words overlap
        pred_cells = set(c.lower() for r in p_tab.rows for c in r) | set(h.lower() for h in p_tab.headers)
        gold_cells = set(c.lower() for r in g_tab.rows for c in r) | set(h.lower() for h in g_tab.headers)

        if not gold_cells and not pred_cells:
            content_scores.append(1.0)
        elif not gold_cells or not pred_cells:
            content_scores.append(0.0)
        else:
            intersection = len(pred_cells.intersection(gold_cells))
            union = len(pred_cells.union(gold_cells))
            content_scores.append(intersection / union)

    avg_dim = sum(dim_scores) / len(dim_scores) if dim_scores else 0.0
    avg_content = sum(content_scores) / len(content_scores) if content_scores else 0.0

    overall = round(count_score * 0.3 + avg_dim * 0.3 + avg_content * 0.4, 4)

    return {
        "table_count_score": round(count_score, 4),
        "dimension_score": round(avg_dim, 4),
        "content_overlap_score": round(avg_content, 4),
        "overall_table_score": overall,
    }
