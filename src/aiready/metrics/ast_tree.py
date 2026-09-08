"""Markdown AST parsing and structural Tree Edit Distance (TEDS) evaluation."""

from typing import List, Optional, Tuple, Dict, Any
from markdown_it import MarkdownIt
from markdown_it.token import Token


class ASTNode:
    """Simplified AST node for structural comparison."""

    def __init__(self, tag: str, text: str = "", children: Optional[List["ASTNode"]] = None):
        self.tag = tag
        self.text = text.strip()
        self.children = children if children is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "text": self.text,
            "children": [c.to_dict() for c in self.children],
        }

    def node_count(self) -> int:
        return 1 + sum(c.node_count() for c in self.children)


def parse_markdown_to_ast(markdown_text: str) -> ASTNode:
    """Parse a Markdown string into a normalized AST tree using markdown-it-py."""
    md = MarkdownIt("commonmark", {"breaks": True, "html": True}).enable("table")
    tokens: List[Token] = md.parse(markdown_text)

    root = ASTNode(tag="root")
    stack: List[Tuple[ASTNode, Optional[str]]] = [(root, None)]

    for token in tokens:
        if token.type.endswith("_open"):
            tag_name = token.tag or token.type[:-5]
            new_node = ASTNode(tag=tag_name)
            stack[-1][0].children.append(new_node)
            closing_type = token.type[:-5] + "_close"
            stack.append((new_node, closing_type))

        elif token.type.endswith("_close"):
            if len(stack) > 1 and stack[-1][1] == token.type:
                stack.pop()

        elif token.type == "inline":
            # Extract text and embedded tags (like image or code)
            curr = stack[-1][0]
            if token.children:
                for child in token.children:
                    if child.type == "image":
                        alt = child.content or ""
                        src = child.attrs.get("src", "") if child.attrs else ""
                        img_node = ASTNode(tag="img", text=f"{alt}::{src}")
                        curr.children.append(img_node)
                    elif child.content:
                        curr.text = (curr.text + " " + child.content).strip()
            else:
                curr.text = (curr.text + " " + token.content).strip()

        elif token.type in ("fence", "code_block"):
            code_node = ASTNode(tag="pre", text=token.content.strip())
            stack[-1][0].children.append(code_node)

        elif token.type == "hr":
            stack[-1][0].children.append(ASTNode(tag="hr"))

    return root


def _flatten_ast(node: ASTNode, depth: int = 0) -> List[Tuple[int, str, str]]:
    """Flatten AST into a depth-annotated linear sequence for robust tree edit comparison."""
    items = [(depth, node.tag, node.text)]
    for child in node.children:
        items.extend(_flatten_ast(child, depth + 1))
    return items


def calculate_tree_similarity(ast_pred: ASTNode, ast_gold: ASTNode) -> float:
    """Calculate normalized Tree Edit Distance Similarity (TEDS: 0.0 - 1.0)

    Uses dynamic programming sequence alignment across depth-tagged AST tokens
    to provide a mathematically strict, deterministic structural similarity score.
    """
    seq_p = _flatten_ast(ast_pred)
    seq_g = _flatten_ast(ast_gold)

    len_p = len(seq_p)
    len_g = len(seq_g)

    if len_p == 0 and len_g == 0:
        return 1.0
    if len_p == 0 or len_g == 0:
        return 0.0

    # DP edit distance with structural weight
    # Match cost: 0 if tags match and depth matches
    dp = [[0.0] * (len_g + 1) for _ in range(len_p + 1)]

    for i in range(len_p + 1):
        dp[i][0] = float(i)
    for j in range(len_g + 1):
        dp[0][j] = float(j)

    for i in range(1, len_p + 1):
        depth_p, tag_p, text_p = seq_p[i - 1]
        for j in range(1, len_g + 1):
            depth_g, tag_g, text_g = seq_g[j - 1]

            if tag_p == tag_g:
                depth_diff = abs(depth_p - depth_g)
                # Content match modifier
                text_match = 1.0 if text_p == text_g else 0.5 if (text_p and text_g) else 0.8
                cost = (depth_diff * 0.2) + (1.0 - text_match) * 0.5
            else:
                cost = 1.0

            dp[i][j] = min(
                dp[i - 1][j] + 1.0,        # deletion
                dp[i][j - 1] + 1.0,        # insertion
                dp[i - 1][j - 1] + cost,    # substitution
            )

    max_dist = max(len_p, len_g)
    sim = max(0.0, 1.0 - (dp[len_p][len_g] / max_dist))
    return round(sim, 4)


def extract_heading_hierarchy(markdown_text: str) -> List[Tuple[int, str]]:
    """Extract (level, text) pairs for all markdown headings (#, ##, etc.)."""
    md = MarkdownIt("commonmark")
    tokens = md.parse(markdown_text)
    headings: List[Tuple[int, str]] = []

    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            level = int(token.tag[1]) if len(token.tag) > 1 and token.tag[1].isdigit() else 1
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                text = tokens[i + 1].content.strip()
            else:
                text = ""
            headings.append((level, text))

    return headings


def evaluate_heading_hierarchy(pred_md: str, gold_md: str) -> float:
    """Evaluate fidelity of heading depth and order."""
    pred_h = extract_heading_hierarchy(pred_md)
    gold_h = extract_heading_hierarchy(gold_md)

    if not gold_h and not pred_h:
        return 1.0
    if not gold_h or not pred_h:
        return 0.0

    # Count matching levels and texts
    matches = 0
    min_len = min(len(pred_h), len(gold_h))
    for i in range(min_len):
        lvl_p, txt_p = pred_h[i]
        lvl_g, txt_g = gold_h[i]
        if lvl_p == lvl_g:
            matches += 0.5
        if txt_p.lower() == txt_g.lower():
            matches += 0.5

    score = matches / max(len(pred_h), len(gold_h))
    return round(score, 4)
