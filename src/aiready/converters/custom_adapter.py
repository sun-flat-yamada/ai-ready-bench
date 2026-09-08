"""Generic CLI / script adapter for benchmarking external converters."""

import subprocess
from pathlib import Path
from typing import List, Optional
from aiready.converters.base import BaseConverter, ConversionResult


class CustomCommandConverter(BaseConverter):
    """Executes a custom CLI command or script to convert documents.

    Template parameters:
      {input}: Path to input file
      {output_dir}: Path to output directory (where output.md and images/ are expected)
      {output_md}: Path to output.md
    """

    def __init__(self, name: str, command_template: str):
        super().__init__(name=name)
        self.command_template = command_template

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        output_md = output_dir / "output.md"

        cmd = self.command_template.format(
            input=str(input_path.resolve()),
            output_dir=str(output_dir.resolve()),
            output_md=str(output_md.resolve()),
        )

        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            return ConversionResult(
                markdown_content="",
                images_dir=images_dir,
                extracted_images_count=0,
                success=False,
                error_message=f"Command failed with exit code {proc.returncode}:\n{proc.stderr}",
            )

        if output_md.exists():
            md_content = output_md.read_text(encoding="utf-8", errors="replace")
        else:
            # Fallback: check stdout
            md_content = proc.stdout
            output_md.write_text(md_content, encoding="utf-8")

        extracted_images = list(images_dir.glob("*.*")) if images_dir.exists() else []

        return ConversionResult(
            markdown_content=md_content,
            images_dir=images_dir,
            extracted_images_count=len(extracted_images),
            success=True,
        )
