from __future__ import annotations

import argparse
import re
from pathlib import Path


def markdown_to_blocks(markdown: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    in_table = False
    table_lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("|"):
            in_table = True
            table_lines.append(line)
            continue
        if in_table:
            blocks.append(("table", "\n".join(table_lines)))
            table_lines = []
            in_table = False
        if not line:
            blocks.append(("space", ""))
        elif line.startswith("# "):
            blocks.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("heading", line[3:].strip()))
        elif line.startswith("### "):
            blocks.append(("subheading", line[4:].strip()))
        elif line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
        else:
            blocks.append(("paragraph", line.strip()))
    if table_lines:
        blocks.append(("table", "\n".join(table_lines)))
    return blocks


def clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text


def export_markdown_pdf(input_path: Path, output_path: Path) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF export requires reportlab. Install with `pip install reportlab`.") from exc

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="BulletBody", parent=styles["BodyText"], leftIndent=14, firstLineIndent=-8))

    story = []
    for kind, text in markdown_to_blocks(input_path.read_text(encoding="utf-8")):
        text = clean_inline(text)
        if kind == "space":
            story.append(Spacer(1, 0.08 * inch))
        elif kind == "title":
            story.append(Paragraph(text, styles["Title"]))
            story.append(Spacer(1, 0.15 * inch))
        elif kind == "heading":
            story.append(Spacer(1, 0.08 * inch))
            story.append(Paragraph(text, styles["Heading2"]))
        elif kind == "subheading":
            story.append(Paragraph(text, styles["Heading3"]))
        elif kind == "bullet":
            story.append(Paragraph(f"- {text}", styles["BulletBody"]))
        elif kind == "table":
            rows = []
            for table_line in text.splitlines():
                cells = [clean_inline(cell.strip()) for cell in table_line.strip("|").split("|")]
                if all(set(cell) <= {"-"} for cell in cells):
                    continue
                rows.append(cells)
            if rows:
                table = Table(rows, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111111")),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#999999")),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 0.12 * inch))
        else:
            story.append(Paragraph(text, styles["BodyText"]))

        if len(story) > 0 and len(story) % 120 == 0:
            story.append(PageBreak())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    doc.build(story)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a Markdown report to PDF.")
    parser.add_argument("--input", type=Path, required=True, help="Markdown input path.")
    parser.add_argument("--output", type=Path, required=True, help="PDF output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_markdown_pdf(input_path=args.input, output_path=args.output)
    print(f"Wrote PDF report to {args.output}")


if __name__ == "__main__":
    main()
