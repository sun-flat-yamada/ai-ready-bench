"""Image extraction, kebab-case naming, and link integrity metrics."""

import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from aiready.config import KEBAB_CASE_IMAGE_REGEX, MARKDOWN_IMAGE_REGEX
from aiready.dataset.schema import ExpectedImageInfo


def extract_markdown_image_links(markdown_text: str) -> List[Dict[str, str]]:
    """Find all image tags in Markdown text: ![alt](path "title")."""
    matches = []
    for m in MARKDOWN_IMAGE_REGEX.finditer(markdown_text):
        matches.append({
            "alt": m.group("alt").strip(),
            "path": m.group("path").strip(),
            "filename": Path(m.group("path").strip()).name,
        })
    return matches


def is_kebab_case_filename(filename: str) -> bool:
    """Validate if an image filename strictly matches semantic kebab-case naming.

    Examples of valid names:
      - 'quarterly-revenue-breakdown-2025.png'
      - 'cloud-native-parsing-topology.jpg'
      - 'core-datacenter-switch.webp'
    Examples of invalid names:
      - 'Image_1.png' (underscore, uppercase)
      - 'image1.png' (no semantic kebab hyphenation)
      - 'figure 1.png' (spaces)
    """
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()

    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        return False

    # Check against regex
    return bool(KEBAB_CASE_IMAGE_REGEX.match(filename))


def evaluate_image_pipeline(
    markdown_text: str,
    extracted_images_dir: Optional[Path],
    expected_images: List[ExpectedImageInfo],
) -> Dict[str, Any]:
    """Strictly evaluate image extraction, kebab-case naming, and Markdown link integrity."""
    markdown_links = extract_markdown_image_links(markdown_text)

    # 1. Discover physical extracted files
    physical_files: List[Path] = []
    if extracted_images_dir and extracted_images_dir.exists():
        physical_files = [
            p for p in extracted_images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".svg")
        ]

    physical_filenames = {p.name for p in physical_files}

    # 2. Expected Image Counts and Extraction Rate
    num_expected = len(expected_images)
    num_physical = len(physical_files)

    if num_expected == 0:
        extraction_rate = 1.0
    else:
        extraction_rate = min(1.0, num_physical / num_expected)

    # 3. Kebab-case Naming Compliance
    valid_kebab_files = [f for f in physical_filenames if is_kebab_case_filename(f)]
    kebab_compliance_rate = (
        len(valid_kebab_files) / len(physical_filenames) if physical_filenames else (1.0 if num_expected == 0 else 0.0)
    )

    # 4. Markdown Link Integrity (Zero Broken Links)
    # Every link in Markdown must resolve to an existing physical file
    valid_links = 0
    broken_links = []
    referenced_filenames = set()

    for link in markdown_links:
        fname = link["filename"]
        referenced_filenames.add(fname)
        if fname in physical_filenames:
            valid_links += 1
        else:
            broken_links.append(link["path"])

    if not markdown_links:
        link_integrity_score = 1.0 if num_expected == 0 else 0.0
    else:
        link_integrity_score = valid_links / len(markdown_links)

    # 5. Orphan Extracted Images (Extracted to disk but not linked inside Markdown)
    orphan_images = list(physical_filenames - referenced_filenames)

    # 6. Alt-text / Summary Semantic Keyword Matching
    keyword_scores = []
    for exp_img in expected_images:
        matched_alt = None
        for link in markdown_links:
            if link["filename"] == exp_img.expected_filename or exp_img.summary in link["alt"]:
                matched_alt = link["alt"].lower()
                break

        if matched_alt and exp_img.keywords:
            hit = sum(1 for kw in exp_img.keywords if kw.lower() in matched_alt)
            keyword_scores.append(hit / len(exp_img.keywords))
        elif exp_img.keywords:
            keyword_scores.append(0.0)

    avg_alt_score = sum(keyword_scores) / len(keyword_scores) if keyword_scores else 1.0

    # Composite Image Score
    if num_expected == 0:
        overall_image_score = 1.0
    else:
        overall_image_score = round(
            extraction_rate * 0.35 +
            kebab_compliance_rate * 0.25 +
            link_integrity_score * 0.30 +
            avg_alt_score * 0.10,
            4
        )

    return {
        "expected_image_count": num_expected,
        "extracted_image_count": num_physical,
        "markdown_image_links_count": len(markdown_links),
        "extraction_rate": round(extraction_rate, 4),
        "kebab_compliance_rate": round(kebab_compliance_rate, 4),
        "link_integrity_score": round(link_integrity_score, 4),
        "alt_keyword_score": round(avg_alt_score, 4),
        "broken_links": broken_links,
        "orphan_images": orphan_images,
        "overall_image_score": overall_image_score,
    }
