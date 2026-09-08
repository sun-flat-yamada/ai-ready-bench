"""Tests for AST tree parsing and TEDS structural similarity metric."""

from aiready.metrics.ast_tree import (
    parse_markdown_to_ast,
    calculate_tree_similarity,
    extract_heading_hierarchy,
    evaluate_heading_hierarchy,
)


def test_ast_parsing_and_identical_similarity():
    md = "# Title\n\nIntro paragraph.\n\n## Section 1\n\n- Bullet 1\n- Bullet 2\n"
    ast1 = parse_markdown_to_ast(md)
    ast2 = parse_markdown_to_ast(md)

    sim = calculate_tree_similarity(ast1, ast2)
    assert sim == 1.0


def test_ast_structural_divergence_penalty():
    gold_md = "# Title\n\nParagraph text.\n\n| H1 | H2 |\n| --- | --- |\n| A | B |\n"
    degraded_md = "# Title\n\nRaw unstructured text without table."

    ast_gold = parse_markdown_to_ast(gold_md)
    ast_deg = parse_markdown_to_ast(degraded_md)

    sim = calculate_tree_similarity(ast_deg, ast_gold)
    assert 0.0 < sim < 0.90


def test_heading_hierarchy_evaluation():
    gold = "# Main\n\n## Sub 1\n\n### Detail 1\n"
    pred = "# Main\n\n## Sub 1\n\n### Detail 1\n"
    pred_broken = "# Main\n\n# Sub 1\n\n# Detail 1\n"

    assert evaluate_heading_hierarchy(pred, gold) == 1.0
    assert evaluate_heading_hierarchy(pred_broken, gold) < 1.0
