"""Text cleanliness, noise ratio, and boilerplate penalty evaluation."""

import re
from typing import Dict, Any


RAW_HTML_PATTERN = re.compile(r"<(?!\/?(table|tr|th|td|br|p|b|i|strong|em|code)\b)[^>]+>", re.IGNORECASE)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
EXCESSIVE_NEWLINES_PATTERN = re.compile(r"\n{4,}")


def evaluate_cleanliness(markdown_text: str) -> Dict[str, Any]:
    """Evaluate cleanliness and absence of noise in the generated Markdown.

    Penalizes:
    - Raw unhandled HTML tags (e.g. <span style="...">, <div>, <font>)
    - Control characters or broken binary junk
    - Excessive blank lines (> 3 consecutive newlines)
    """
    total_len = len(markdown_text)
    if total_len == 0:
        return {
            "noise_ratio": 1.0,
            "raw_html_count": 0,
            "control_chars_count": 0,
            "cleanliness_score": 0.0,
        }

    raw_html_matches = RAW_HTML_PATTERN.findall(markdown_text)
    control_matches = CONTROL_CHAR_PATTERN.findall(markdown_text)
    excessive_nl_matches = EXCESSIVE_NEWLINES_PATTERN.findall(markdown_text)

    penalty_points = (
        len(raw_html_matches) * 5 +
        len(control_matches) * 10 +
        len(excessive_nl_matches) * 3
    )

    noise_ratio = min(1.0, penalty_points / (total_len / 50.0 + 1.0))
    cleanliness_score = round(max(0.0, 1.0 - noise_ratio), 4)

    return {
        "noise_ratio": round(noise_ratio, 4),
        "raw_html_count": len(raw_html_matches),
        "control_chars_count": len(control_matches),
        "excessive_newlines_count": len(excessive_nl_matches),
        "cleanliness_score": cleanliness_score,
    }
