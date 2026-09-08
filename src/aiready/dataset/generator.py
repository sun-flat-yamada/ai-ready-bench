"""Deterministic synthetic test dataset generator across Office, PDF, and Image formats."""

import io
import json
import os
import shutil
import sqlite3
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont

import docx
from docx.shared import Inches, Pt, RGBColor
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
import pptx
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGBColor
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from aiready.dataset.schema import GroundTruthMetadata, ExpectedImageInfo


def _create_synthetic_image(text: str, subtitle: str, filename: str, width: int = 640, height: int = 360, bg_color=(41, 128, 185)) -> bytes:
    """Create a synthetic PNG chart/diagram image with clear rendered text."""
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw border and banner
    draw.rectangle([10, 10, width - 10, height - 10], outline=(236, 240, 241), width=3)
    draw.rectangle([20, 20, width - 20, 70], fill=(52, 73, 94))

    # Basic text rendering (default font to guarantee 100% portability)
    draw.text((30, 35), f"[CHART/DIAGRAM] {text}", fill=(255, 255, 255))
    draw.text((30, 85), subtitle, fill=(236, 240, 241))

    # Draw some mock chart elements
    draw.rectangle([50, 150, 120, 300], fill=(46, 204, 113))
    draw.text((55, 310), "2023", fill=(255, 255, 255))

    draw.rectangle([160, 120, 230, 300], fill=(52, 152, 219))
    draw.text((165, 310), "2024", fill=(255, 255, 255))

    draw.rectangle([270, 80, 340, 300], fill=(231, 76, 60))
    draw.text((275, 310), "2025", fill=(255, 255, 255))

    draw.rectangle([380, 50, 450, 300], fill=(241, 196, 15))
    draw.text((385, 310), "2026", fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class SyntheticDatasetGenerator:
    """Generates deterministic benchmark documents with matching ground truth."""

    def __init__(self, output_root: Path):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> List[Path]:
        """Generate all 8 supported document categories."""
        generated = [
            self.generate_word_suite(),
            self.generate_excel_suite(),
            self.generate_powerpoint_suite(),
            self.generate_visio_suite(),
            self.generate_project_suite(),
            self.generate_database_suite(),
            self.generate_pdf_suite(),
            self.generate_image_suite(),
        ]
        return generated

    def _save_ground_truth(self, case_dir: Path, expected_md: str, metadata: GroundTruthMetadata, images: Dict[str, bytes]):
        """Save expected markdown, metadata.json, and ground truth expected_images."""
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "expected.md").write_text(expected_md, encoding="utf-8")
        (case_dir / "metadata.json").write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

        expected_images_dir = case_dir / "expected_images"
        expected_images_dir.mkdir(parents=True, exist_ok=True)
        for fname, img_bytes in images.items():
            (expected_images_dir / fname).write_bytes(img_bytes)

    # -------------------------------------------------------------
    # 1. Word Document (.docx)
    # -------------------------------------------------------------
    def generate_word_suite(self) -> Path:
        case_dir = self.output_root / "01_word_annual_report"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.docx"

        doc = docx.Document()
        doc.add_heading("Global Enterprise AI Ingestion Report", level=1)
        doc.add_paragraph("This executive document benchmarks multimodal ingestion fidelity for enterprise knowledge bases.")

        doc.add_heading("1. Executive Summary", level=2)
        doc.add_paragraph("Document conversion pipelines must preserve structured tables, deep heading hierarchies, and contextual figure references.")

        # Embedded chart image
        img_filename = "quarterly-revenue-breakdown-2025.png"
        img_bytes = _create_synthetic_image(
            text="Quarterly Revenue Breakdown 2025",
            subtitle="Comparing Cloud vs On-Premises Ingestion Growth",
            filename=img_filename,
        )
        img_stream = io.BytesIO(img_bytes)
        doc.add_picture(img_stream, width=Inches(5.0))
        doc.add_paragraph("Figure 1: Quarterly Revenue Breakdown 2025 - Cloud vs On-Premises")

        doc.add_heading("2. Benchmark Performance Metrics", level=2)
        table = doc.add_table(rows=4, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Pipeline Name"
        hdr_cells[1].text = "TEDS Score"
        hdr_cells[2].text = "Latency (ms)"

        data = [
            ("Native-AST", "0.94", "120"),
            ("Docling-Core", "0.91", "450"),
            ("MarkItDown-Std", "0.85", "180"),
        ]
        for idx, (p, t, l) in enumerate(data, start=1):
            row_cells = table.rows[idx].cells
            row_cells[0].text = p
            row_cells[1].text = t
            row_cells[2].text = l

        doc.save(input_path)

        expected_md = (
            "# Global Enterprise AI Ingestion Report\n\n"
            "This executive document benchmarks multimodal ingestion fidelity for enterprise knowledge bases.\n\n"
            "## 1. Executive Summary\n\n"
            "Document conversion pipelines must preserve structured tables, deep heading hierarchies, and contextual figure references.\n\n"
            f"![quarterly-revenue-breakdown-2025](images/{img_filename})\n\n"
            "Figure 1: Quarterly Revenue Breakdown 2025 - Cloud vs On-Premises\n\n"
            "## 2. Benchmark Performance Metrics\n\n"
            "| Pipeline Name | TEDS Score | Latency (ms) |\n"
            "| --- | --- | --- |\n"
            "| Native-AST | 0.94 | 120 |\n"
            "| Docling-Core | 0.91 | 450 |\n"
            "| MarkItDown-Std | 0.85 | 180 |\n"
        )

        meta = GroundTruthMetadata(
            doc_id="word-annual-report-01",
            format="docx",
            category="office-word",
            description="Word document with hierarchical headings, embedded revenue chart image, and structured metrics table.",
            expected_headings_count=3,
            expected_tables_count=1,
            expected_images_count=1,
            expected_images=[
                ExpectedImageInfo(
                    image_id="img-01",
                    expected_filename=img_filename,
                    summary="quarterly-revenue-breakdown-2025",
                    keywords=["revenue", "quarterly", "breakdown", "2025"],
                    source_context="Figure 1: Quarterly Revenue Breakdown 2025",
                )
            ],
            tags=["word", "office", "table", "image", "headings"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {img_filename: img_bytes})
        return case_dir

    # -------------------------------------------------------------
    # 2. Excel Spreadsheet (.xlsx)
    # -------------------------------------------------------------
    def generate_excel_suite(self) -> Path:
        case_dir = self.output_root / "02_excel_financial_model"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.xlsx"

        wb = openpyxl.Workbook()
        ws_overview = wb.active
        ws_overview.title = "Consolidated_Metrics"

        headers = ["Department", "Headcount", "Budget (USD)", "Efficiency Ratio"]
        ws_overview.append(headers)
        rows = [
            ["Engineering", 120, 15000000, 0.92],
            ["Data Science", 45, 7500000, 0.88],
            ["Product Operations", 30, 3200000, 0.95],
        ]
        for r in rows:
            ws_overview.append(r)

        ws_regional = wb.create_sheet(title="Regional_Breakdown")
        ws_regional.append(["Region", "Active Clusters", "Monthly Ingestion (TB)"])
        ws_regional.append(["APAC-Tokyo", 16, 240.5])
        ws_regional.append(["US-East", 32, 680.2])
        ws_regional.append(["EU-Frankfurt", 24, 450.0])

        wb.save(input_path)

        expected_md = (
            "# Financial Model: Consolidated Metrics\n\n"
            "## Sheet: Consolidated_Metrics\n\n"
            "| Department | Headcount | Budget (USD) | Efficiency Ratio |\n"
            "| --- | --- | --- | --- |\n"
            "| Engineering | 120 | 15000000 | 0.92 |\n"
            "| Data Science | 45 | 7500000 | 0.88 |\n"
            "| Product Operations | 30 | 3200000 | 0.95 |\n\n"
            "## Sheet: Regional_Breakdown\n\n"
            "| Region | Active Clusters | Monthly Ingestion (TB) |\n"
            "| --- | --- | --- |\n"
            "| APAC-Tokyo | 16 | 240.5 |\n"
            "| US-East | 32 | 680.2 |\n"
            "| EU-Frankfurt | 24 | 450.0 |\n"
        )

        meta = GroundTruthMetadata(
            doc_id="excel-financial-model-02",
            format="xlsx",
            category="office-excel",
            description="Multi-sheet Excel financial model with department budgets and regional ingestion statistics.",
            expected_headings_count=3,
            expected_tables_count=2,
            expected_images_count=0,
            tags=["excel", "office", "tables", "multi-sheet"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {})
        return case_dir

    # -------------------------------------------------------------
    # 3. PowerPoint Presentation (.pptx)
    # -------------------------------------------------------------
    def generate_powerpoint_suite(self) -> Path:
        case_dir = self.output_root / "03_powerpoint_roadmap"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.pptx"

        prs = pptx.Presentation()
        blank_slide_layout = prs.slide_layouts[6]

        # Slide 1: Title
        slide1 = prs.slides.add_slide(blank_slide_layout)
        tx_box = slide1.shapes.add_textbox(PptInches(1), PptInches(1.5), PptInches(8), PptInches(2))
        tf = tx_box.text_frame
        p = tf.paragraphs[0]
        p.text = "Q3 Product Strategy & AI Integration"
        p.font.size = PptPt(36)
        p.font.bold = True

        p2 = tf.add_paragraph()
        p2.text = "Enterprise Architecture & Document Transformation Roadmap"
        p2.font.size = PptPt(20)

        # Slide 2: Architecture with embedded diagram
        slide2 = prs.slides.add_slide(blank_slide_layout)
        title_box = slide2.shapes.add_textbox(PptInches(0.8), PptInches(0.5), PptInches(8), PptInches(1))
        title_box.text_frame.paragraphs[0].text = "Cloud-Native Parsing Topology"
        title_box.text_frame.paragraphs[0].font.size = PptPt(24)

        img_filename = "cloud-native-parsing-topology.png"
        img_bytes = _create_synthetic_image(
            text="Cloud-Native Ingestion Topology",
            subtitle="Queue -> Worker -> AST Parser -> Markdown Storage",
            filename=img_filename,
            bg_color=(39, 174, 96),
        )
        img_stream = io.BytesIO(img_bytes)
        slide2.shapes.add_picture(img_stream, PptInches(1), PptInches(1.8), width=PptInches(6.5))

        prs.save(input_path)

        expected_md = (
            "# Q3 Product Strategy & AI Integration\n\n"
            "Enterprise Architecture & Document Transformation Roadmap\n\n"
            "## Slide 2: Cloud-Native Parsing Topology\n\n"
            f"![cloud-native-parsing-topology](images/{img_filename})\n"
        )

        meta = GroundTruthMetadata(
            doc_id="powerpoint-roadmap-03",
            format="pptx",
            category="office-ppt",
            description="PowerPoint deck containing title slide and architecture slide with embedded diagram.",
            expected_headings_count=2,
            expected_tables_count=0,
            expected_images_count=1,
            expected_images=[
                ExpectedImageInfo(
                    image_id="img-ppt-01",
                    expected_filename=img_filename,
                    summary="cloud-native-parsing-topology",
                    keywords=["cloud", "native", "parsing", "topology"],
                    source_context="Cloud-Native Parsing Topology",
                )
            ],
            tags=["powerpoint", "office", "slides", "diagram"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {img_filename: img_bytes})
        return case_dir

    # -------------------------------------------------------------
    # 4. Visio Architecture (.vsdx)
    # -------------------------------------------------------------
    def generate_visio_suite(self) -> Path:
        """Create a synthetic .vsdx package (OPC Zip structure with XML and embedded media)."""
        case_dir = self.output_root / "04_visio_datacenter_network"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.vsdx"

        img_filename = "core-datacenter-switch.png"
        img_bytes = _create_synthetic_image(
            text="Core Datacenter Switch Fabric",
            subtitle="Spine-Leaf Arista/Cisco 400G Interconnect",
            filename=img_filename,
            bg_color=(142, 68, 173),
        )

        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="png" ContentType="image/png"/>\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Override PartName="/visio/document.xml" ContentType="application/vnd.ms-visio.drawing.main+xml"/>\n'
            '  <Override PartName="/visio/pages/page1.xml" ContentType="application/vnd.ms-visio.page+xml"/>\n'
            '</Types>'
        )

        page1_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<PageContents xmlns="http://schemas.microsoft.com/office/visio/2012/main">\n'
            '  <Shapes>\n'
            '    <Shape ID="1" Name="Spine Switch A" Type="Shape">\n'
            '      <Text>Primary Core Spine Switch (400Gbps Backbone)</Text>\n'
            '    </Shape>\n'
            '    <Shape ID="2" Name="Spine Switch B" Type="Shape">\n'
            '      <Text>Secondary Core Spine Switch (HA Failover)</Text>\n'
            '    </Shape>\n'
            '    <Shape ID="3" Name="Leaf Rack 01" Type="Shape">\n'
            '      <Text>Compute Node Cluster A - Kubernetes Worker Pool</Text>\n'
            '    </Shape>\n'
            '  </Shapes>\n'
            '  <Connects>\n'
            '    <Connect FromSheet="4" ToSheet="1" FromCell="BeginX" ToCell="PinX"/>\n'
            '    <Connect FromSheet="4" ToSheet="3" FromCell="EndX" ToCell="PinX"/>\n'
            '  </Connects>\n'
            '</PageContents>'
        )

        with zipfile.ZipFile(input_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types_xml)
            zf.writestr("visio/document.xml", "<VisioDocument/>")
            zf.writestr("visio/pages/page1.xml", page1_xml)
            zf.writestr(f"visio/media/{img_filename}", img_bytes)

        expected_md = (
            "# Visio Diagram: Datacenter Network Architecture\n\n"
            "## Page 1: Network Topology & Spine-Leaf Fabric\n\n"
            f"![core-datacenter-switch](images/{img_filename})\n\n"
            "### Diagram Entities\n\n"
            "- **Spine Switch A**: Primary Core Spine Switch (400Gbps Backbone)\n"
            "- **Spine Switch B**: Secondary Core Spine Switch (HA Failover)\n"
            "- **Leaf Rack 01**: Compute Node Cluster A - Kubernetes Worker Pool\n\n"
            "### Connections\n\n"
            "- `Spine Switch A` connects to `Leaf Rack 01` (400G Uplink)\n"
        )

        meta = GroundTruthMetadata(
            doc_id="visio-datacenter-04",
            format="vsdx",
            category="office-visio",
            description="Visio network architecture diagram with spine-leaf switches, shapes, and embedded switch image.",
            expected_headings_count=3,
            expected_tables_count=0,
            expected_images_count=1,
            expected_images=[
                ExpectedImageInfo(
                    image_id="img-visio-01",
                    expected_filename=img_filename,
                    summary="core-datacenter-switch",
                    keywords=["datacenter", "switch", "core", "network"],
                    source_context="Core Datacenter Switch Fabric",
                )
            ],
            tags=["visio", "office", "diagram", "vsdx", "network"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {img_filename: img_bytes})
        return case_dir

    # -------------------------------------------------------------
    # 5. MS Project Schedule (.xml)
    # -------------------------------------------------------------
    def generate_project_suite(self) -> Path:
        case_dir = self.output_root / "05_project_wbs_schedule"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.xml"

        project_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Project xmlns="http://schemas.microsoft.com/project">\n'
            '  <Title>Enterprise LLM Gateway Migration</Title>\n'
            '  <Author>Program Management Office</Author>\n'
            '  <Tasks>\n'
            '    <Task>\n'
            '      <UID>1</UID>\n'
            '      <ID>1</ID>\n'
            '      <Name>Phase 1: Architecture Evaluation</Name>\n'
            '      <Duration>PT80H</Duration>\n'
            '      <PercentComplete>100</PercentComplete>\n'
            '    </Task>\n'
            '    <Task>\n'
            '      <UID>2</UID>\n'
            '      <ID>2</ID>\n'
            '      <Name>Phase 2: Converter Benchmark Suite Implementation</Name>\n'
            '      <Duration>PT120H</Duration>\n'
            '      <PercentComplete>75</PercentComplete>\n'
            '    </Task>\n'
            '    <Task>\n'
            '      <UID>3</UID>\n'
            '      <ID>3</ID>\n'
            '      <Name>Phase 3: Production Rollout &amp; Gateway Cutover</Name>\n'
            '      <Duration>PT40H</Duration>\n'
            '      <PercentComplete>0</PercentComplete>\n'
            '    </Task>\n'
            '  </Tasks>\n'
            '</Project>'
        )
        input_path.write_text(project_xml, encoding="utf-8")

        expected_md = (
            "# Project Schedule: Enterprise LLM Gateway Migration\n\n"
            "**Author**: Program Management Office\n\n"
            "## Work Breakdown Structure (WBS)\n\n"
            "| ID | Task Name | Duration | Progress |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | Phase 1: Architecture Evaluation | PT80H | 100% |\n"
            "| 2 | Phase 2: Converter Benchmark Suite Implementation | PT120H | 75% |\n"
            "| 3 | Phase 3: Production Rollout & Gateway Cutover | PT40H | 0% |\n"
        )

        meta = GroundTruthMetadata(
            doc_id="project-wbs-05",
            format="xml",
            category="office-project",
            description="MS Project WBS XML file with tasks, durations, and completion percentages.",
            expected_headings_count=2,
            expected_tables_count=1,
            expected_images_count=0,
            tags=["project", "office", "wbs", "xml", "schedule"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {})
        return case_dir

    # -------------------------------------------------------------
    # 6. Database / Relational Records (.sqlite)
    # -------------------------------------------------------------
    def generate_database_suite(self) -> Path:
        case_dir = self.output_root / "06_access_relational_registry"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.sqlite"

        if input_path.exists():
            input_path.unlink()

        conn = sqlite3.connect(input_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                tier TEXT NOT NULL,
                contract_val_kusd INTEGER NOT NULL
            )
        """)
        cur.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?)",
            [
                (101, "Acme AI Labs", "Enterprise-Gold", 450),
                (102, "Nexus Robotics", "Enterprise-Platinum", 1200),
                (103, "BioTech Innovations", "Standard-Silver", 180),
            ],
        )
        conn.commit()
        conn.close()

        expected_md = (
            "# Relational Database Schema & Data: Customer Registry\n\n"
            "## Table: customers\n\n"
            "| customer_id | company_name | tier | contract_val_kusd |\n"
            "| --- | --- | --- | --- |\n"
            "| 101 | Acme AI Labs | Enterprise-Gold | 450 |\n"
            "| 102 | Nexus Robotics | Enterprise-Platinum | 1200 |\n"
            "| 103 | BioTech Innovations | Standard-Silver | 180 |\n"
        )

        meta = GroundTruthMetadata(
            doc_id="db-registry-06",
            format="sqlite",
            category="office-db",
            description="Relational database table containing enterprise customer accounts and contract values.",
            expected_headings_count=2,
            expected_tables_count=1,
            expected_images_count=0,
            tags=["database", "access", "sqlite", "relational", "table"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {})
        return case_dir

    # -------------------------------------------------------------
    # 7. PDF Document (.pdf)
    # -------------------------------------------------------------
    def generate_pdf_suite(self) -> Path:
        case_dir = self.output_root / "07_pdf_research_paper"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.pdf"

        img_filename = "transformer-attention-map.png"
        img_bytes = _create_synthetic_image(
            text="Multi-Head Attention Distribution",
            subtitle="Cross-Layer Self-Attention Heatmap",
            filename=img_filename,
            bg_color=(192, 57, 43),
        )

        # Temporary file for ReportLab image inclusion
        tmp_img = case_dir / "_temp_pdf_chart.png"
        tmp_img.write_bytes(img_bytes)

        pdf_doc = SimpleDocTemplate(str(input_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20, leading=24)
        h2_style = ParagraphStyle("H2Style", parent=styles["Heading2"], fontSize=14, leading=18)
        body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=14)

        story.append(Paragraph("Evaluating AST Precision in Document AI Parsers", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Abstract: We formulate document structural conversion as an exact tree edit distance optimization problem.", body_style))
        story.append(Spacer(1, 14))

        story.append(Paragraph("1. Attention Mechanisms and Representation", h2_style))
        story.append(Spacer(1, 10))
        story.append(RLImage(str(tmp_img), width=360, height=200))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Figure 1: Transformer Multi-Head Attention Map across Context Layers", body_style))
        story.append(Spacer(1, 14))

        story.append(Paragraph("2. Experimental Results", h2_style))
        story.append(Spacer(1, 8))
        data = [
            ["Model", "F1 Score", "TEDS"],
            ["Doc-AI-Bench", "0.96", "0.95"],
            ["Baseline-Heuristic", "0.78", "0.71"],
        ]
        table = Table(data, colWidths=[150, 100, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)

        pdf_doc.build(story)
        if tmp_img.exists():
            tmp_img.unlink()

        expected_md = (
            "# Evaluating AST Precision in Document AI Parsers\n\n"
            "Abstract: We formulate document structural conversion as an exact tree edit distance optimization problem.\n\n"
            "## 1. Attention Mechanisms and Representation\n\n"
            f"![transformer-attention-map](images/{img_filename})\n\n"
            "Figure 1: Transformer Multi-Head Attention Map across Context Layers\n\n"
            "## 2. Experimental Results\n\n"
            "| Model | F1 Score | TEDS |\n"
            "| --- | --- | --- |\n"
            "| Doc-AI-Bench | 0.96 | 0.95 |\n"
            "| Baseline-Heuristic | 0.78 | 0.71 |\n"
        )

        meta = GroundTruthMetadata(
            doc_id="pdf-research-paper-07",
            format="pdf",
            category="pdf",
            description="Academic PDF with abstract, section headings, attention heatmap figure, and results table.",
            expected_headings_count=3,
            expected_tables_count=1,
            expected_images_count=1,
            expected_images=[
                ExpectedImageInfo(
                    image_id="img-pdf-01",
                    expected_filename=img_filename,
                    summary="transformer-attention-map",
                    keywords=["transformer", "attention", "map", "heatmap"],
                    source_context="Figure 1: Transformer Multi-Head Attention Map",
                )
            ],
            tags=["pdf", "paper", "table", "image", "academic"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {img_filename: img_bytes})
        return case_dir

    # -------------------------------------------------------------
    # 8. Standalone Image Infographic (.png)
    # -------------------------------------------------------------
    def generate_image_suite(self) -> Path:
        case_dir = self.output_root / "08_image_infographic"
        case_dir.mkdir(parents=True, exist_ok=True)
        img_filename = "infra-cost-reduction-metrics.png"
        input_path = case_dir / f"input.png"

        img_bytes = _create_synthetic_image(
            text="Cloud Infrastructure Optimization",
            subtitle="72% Compute Savings Realized in Q4",
            filename=img_filename,
            width=800,
            height=450,
            bg_color=(22, 160, 133),
        )
        input_path.write_bytes(img_bytes)

        expected_md = (
            "# Cloud Infrastructure Optimization\n\n"
            f"![infra-cost-reduction-metrics](images/{img_filename})\n\n"
            "**Key Highlight**: 72% Compute Savings Realized in Q4.\n"
        )

        meta = GroundTruthMetadata(
            doc_id="image-infographic-08",
            format="png",
            category="image",
            description="Standalone visual infographic presenting Q4 compute cost reduction statistics.",
            expected_headings_count=1,
            expected_tables_count=0,
            expected_images_count=1,
            expected_images=[
                ExpectedImageInfo(
                    image_id="img-standalone-01",
                    expected_filename=img_filename,
                    summary="infra-cost-reduction-metrics",
                    keywords=["infra", "cost", "reduction", "metrics", "compute"],
                    source_context="Cloud Infrastructure Optimization",
                )
            ],
            tags=["image", "infographic", "visual", "kebab-case"],
        )

        self._save_ground_truth(case_dir, expected_md, meta, {img_filename: img_bytes})
        return case_dir
