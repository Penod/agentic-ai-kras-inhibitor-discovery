"""Generate static SVG figures from saved project outputs.

The visualization layer intentionally uses only the Python standard library.
That keeps figure regeneration available in a clean checkout even when plotting
libraries are not installed, and it makes the reports suitable for archival
project snapshots.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

BLUE = "#2f6fbd"
GREEN = "#2f9e44"
ORANGE = "#f08c00"
RED = "#d9480f"
PURPLE = "#7048e8"
GRAY = "#495057"
LIGHT_GRAY = "#e9ecef"
INK = "#212529"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: object, default: int = 0) -> int:
    return int(round(to_float(value, float(default))))


def fmt_model(name: str) -> str:
    return name.replace("_", " ").title().replace("Svm", "SVM").replace("Rbf", "RBF").replace("Xgboost", "XGBoost")


def svg(width: int, height: int, body: Iterable[str]) -> str:
    content = "\n".join(body)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>
text {{ font-family: Arial, Helvetica, sans-serif; fill: {INK}; }}
.title {{ font-size: 22px; font-weight: 700; }}
.subtitle {{ font-size: 12px; fill: {GRAY}; }}
.axis {{ stroke: {GRAY}; stroke-width: 1; }}
.grid {{ stroke: {LIGHT_GRAY}; stroke-width: 1; }}
.label {{ font-size: 12px; }}
.tick {{ font-size: 11px; fill: {GRAY}; }}
</style>
{content}
</svg>
"""


def write_svg(path: Path, width: int, height: int, body: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg(width, height, body), encoding="utf-8")


def nice_max(values: Iterable[float]) -> float:
    max_value = max([0.0, *values])
    if max_value <= 1:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(max_value))
    return math.ceil(max_value / magnitude) * magnitude


def bar_chart(path: Path, title: str, labels: list[str], values: list[float], color: str = BLUE) -> None:
    width, height = 900, 520
    left, right, top, bottom = 90, 40, 80, 100
    plot_w, plot_h = width - left - right, height - top - bottom
    y_max = nice_max(values)
    body = [
        f'<text class="title" x="{width/2}" y="34" text-anchor="middle">{esc(title)}</text>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
    ]
    for i in range(6):
        y = top + plot_h - (plot_h * i / 5)
        value = y_max * i / 5
        body.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}"/>')
        body.append(f'<text class="tick" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{value:,.0f}</text>')
    gap = 34
    bar_w = max(24, (plot_w - gap * (len(values) + 1)) / max(1, len(values)))
    for idx, (label, value) in enumerate(zip(labels, values)):
        x = left + gap + idx * (bar_w + gap)
        bar_h = 0 if y_max == 0 else (value / y_max) * plot_h
        y = top + plot_h - bar_h
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}" rx="3"/>')
        body.append(f'<text class="label" x="{x + bar_w/2:.1f}" y="{y - 8:.1f}" text-anchor="middle">{value:,.0f}</text>')
        body.append(f'<text class="tick" x="{x + bar_w/2:.1f}" y="{top + plot_h + 24}" text-anchor="middle">{esc(label)}</text>')
    write_svg(path, width, height, body)


def grouped_metric_chart(path: Path, title: str, rows: list[dict[str, str]], metrics: list[str]) -> None:
    width, height = 980, 560
    left, right, top, bottom = 90, 230, 80, 90
    plot_w, plot_h = width - left - right, height - top - bottom
    colors = [PURPLE, BLUE, GREEN, ORANGE, RED, GRAY, "#868e96"]
    body = [
        f'<text class="title" x="{width/2}" y="34" text-anchor="middle">{esc(title)}</text>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
    ]
    for i in range(6):
        y = top + plot_h - (plot_h * i / 5)
        value = i / 5
        body.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}"/>')
        body.append(f'<text class="tick" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{value:.1f}</text>')
    cluster_w = plot_w / len(metrics)
    bar_w = min(18, cluster_w / (len(rows) + 2))
    for metric_idx, metric in enumerate(metrics):
        center = left + cluster_w * metric_idx + cluster_w / 2
        start = center - (bar_w * len(rows)) / 2
        for row_idx, row in enumerate(rows):
            value = to_float(row.get(metric))
            bar_h = value * plot_h
            x = start + row_idx * bar_w
            y = top + plot_h - bar_h
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w - 2:.1f}" height="{bar_h:.1f}" fill="{colors[row_idx % len(colors)]}"/>')
        body.append(f'<text class="tick" x="{center:.1f}" y="{top + plot_h + 24}" text-anchor="middle">{esc(metric.upper().replace("_", " "))}</text>')
    legend_x, legend_y = left + plot_w + 35, top + 8
    for idx, row in enumerate(rows):
        y = legend_y + idx * 24
        body.append(f'<rect x="{legend_x}" y="{y - 10}" width="14" height="14" fill="{colors[idx % len(colors)]}"/>')
        body.append(f'<text class="label" x="{legend_x + 22}" y="{y + 2}">{esc(fmt_model(row.get("model", "")))}</text>')
    write_svg(path, width, height, body)


def cv_error_chart(path: Path, rows: list[dict[str, str]]) -> None:
    width, height = 900, 540
    left, right, top, bottom = 90, 60, 80, 120
    plot_w, plot_h = width - left - right, height - top - bottom
    rows = [row for row in rows if row.get("model") != "dummy_most_frequent"]
    body = [
        f'<text class="title" x="{width/2}" y="34" text-anchor="middle">Cross-Validation ROC-AUC by Model</text>',
        f'<text class="subtitle" x="{width/2}" y="56" text-anchor="middle">Bars show five-fold mean; error bars show standard deviation.</text>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
    ]
    y_min, y_max = 0.75, 1.0
    for i in range(6):
        value = y_min + (y_max - y_min) * i / 5
        y = top + plot_h - ((value - y_min) / (y_max - y_min)) * plot_h
        body.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}"/>')
        body.append(f'<text class="tick" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{value:.2f}</text>')
    gap = 28
    bar_w = (plot_w - gap * (len(rows) + 1)) / len(rows)
    for idx, row in enumerate(rows):
        mean_value = to_float(row.get("roc_auc_mean"))
        std_value = to_float(row.get("roc_auc_std"))
        x = left + gap + idx * (bar_w + gap)
        y = top + plot_h - ((mean_value - y_min) / (y_max - y_min)) * plot_h
        base_y = top + plot_h
        err_top = top + plot_h - (((mean_value + std_value) - y_min) / (y_max - y_min)) * plot_h
        err_bottom = top + plot_h - (((mean_value - std_value) - y_min) / (y_max - y_min)) * plot_h
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{base_y - y:.1f}" fill="{BLUE}" rx="3"/>')
        body.append(f'<line x1="{x + bar_w/2:.1f}" y1="{err_top:.1f}" x2="{x + bar_w/2:.1f}" y2="{err_bottom:.1f}" stroke="{INK}" stroke-width="1.5"/>')
        body.append(f'<line x1="{x + bar_w/2 - 8:.1f}" y1="{err_top:.1f}" x2="{x + bar_w/2 + 8:.1f}" y2="{err_top:.1f}" stroke="{INK}" stroke-width="1.5"/>')
        body.append(f'<line x1="{x + bar_w/2 - 8:.1f}" y1="{err_bottom:.1f}" x2="{x + bar_w/2 + 8:.1f}" y2="{err_bottom:.1f}" stroke="{INK}" stroke-width="1.5"/>')
        body.append(f'<text class="label" x="{x + bar_w/2:.1f}" y="{y - 10:.1f}" text-anchor="middle">{mean_value:.3f}</text>')
        body.append(f'<text class="tick" x="{x + bar_w/2:.1f}" y="{top + plot_h + 24}" text-anchor="middle">{esc(fmt_model(row.get("model", "")))}</text>')
    write_svg(path, width, height, body)


def histogram_counts(values: list[float], bins: int = 18) -> tuple[list[float], list[int], float, float]:
    if not values:
        return [], [], 0, 0
    low, high = min(values), max(values)
    if low == high:
        high = low + 1
    width = (high - low) / bins
    counts = [0] * bins
    for value in values:
        idx = min(bins - 1, max(0, int((value - low) / width)))
        counts[idx] += 1
    centers = [low + width * (i + 0.5) for i in range(bins)]
    return centers, counts, low, high


def descriptor_panel(path: Path, rows: list[dict[str, str]]) -> None:
    descriptors = [
        ("mol_wt", "Molecular Weight"),
        ("mol_logp", "LogP"),
        ("tpsa", "TPSA"),
        ("rotatable_bonds", "Rotatable Bonds"),
    ]
    width, height = 1100, 760
    panel_w, panel_h = 480, 280
    body = [f'<text class="title" x="{width/2}" y="34" text-anchor="middle">Molecular Property Distributions by Activity Class</text>']
    for idx, (column, label) in enumerate(descriptors):
        x0 = 70 + (idx % 2) * 520
        y0 = 80 + (idx // 2) * 330
        active = [to_float(row.get(column)) for row in rows if row.get("activity_label") == "1" and row.get(column)]
        inactive = [to_float(row.get(column)) for row in rows if row.get("activity_label") == "0" and row.get(column)]
        values = active + inactive
        if not values:
            continue
        _, active_counts, low, high = histogram_counts(active, 18)
        _, inactive_counts, _, _ = histogram_counts(inactive, 18)
        max_count = max([1, *active_counts, *inactive_counts])
        body.append(f'<text class="label" x="{x0 + panel_w/2}" y="{y0 - 18}" text-anchor="middle">{esc(label)}</text>')
        body.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + panel_h}"/>')
        body.append(f'<line class="axis" x1="{x0}" y1="{y0 + panel_h}" x2="{x0 + panel_w}" y2="{y0 + panel_h}"/>')
        bar_w = panel_w / 18
        for i in range(18):
            active_h = active_counts[i] / max_count * panel_h
            inactive_h = inactive_counts[i] / max_count * panel_h
            x = x0 + i * bar_w
            body.append(f'<rect x="{x:.1f}" y="{y0 + panel_h - active_h:.1f}" width="{bar_w/2 - 1:.1f}" height="{active_h:.1f}" fill="{GREEN}" opacity="0.72"/>')
            body.append(f'<rect x="{x + bar_w/2:.1f}" y="{y0 + panel_h - inactive_h:.1f}" width="{bar_w/2 - 1:.1f}" height="{inactive_h:.1f}" fill="{ORANGE}" opacity="0.72"/>')
        body.append(f'<text class="tick" x="{x0}" y="{y0 + panel_h + 22}" text-anchor="start">{low:.1f}</text>')
        body.append(f'<text class="tick" x="{x0 + panel_w}" y="{y0 + panel_h + 22}" text-anchor="end">{high:.1f}</text>')
    body.append(f'<rect x="780" y="704" width="14" height="14" fill="{GREEN}" opacity="0.72"/><text class="label" x="802" y="716">Active</text>')
    body.append(f'<rect x="870" y="704" width="14" height="14" fill="{ORANGE}" opacity="0.72"/><text class="label" x="892" y="716">Inactive</text>')
    write_svg(path, width, height, body)


def confusion_matrix_panel(path: Path, matrix_dir: Path) -> None:
    files = sorted(matrix_dir.glob("*.csv"))
    if not files:
        return
    width, height = 1120, 760
    cell = 96
    body = [f'<text class="title" x="{width/2}" y="34" text-anchor="middle">Holdout Confusion Matrices</text>']
    for idx, file_path in enumerate(files):
        rows = read_csv_rows(file_path)
        if len(rows) < 2:
            continue
        vals = [
            [to_int(rows[0].get("predicted_inactive_0")), to_int(rows[0].get("predicted_active_1"))],
            [to_int(rows[1].get("predicted_inactive_0")), to_int(rows[1].get("predicted_active_1"))],
        ]
        x0 = 70 + (idx % 3) * 350
        y0 = 80 + (idx // 3) * 300
        max_val = max(1, *[item for row in vals for item in row])
        body.append(f'<text class="label" x="{x0 + cell}" y="{y0 - 18}" text-anchor="middle">{esc(fmt_model(file_path.stem))}</text>')
        for r in range(2):
            for c in range(2):
                value = vals[r][c]
                shade = 245 - int(140 * value / max_val)
                fill = f"rgb({shade},{shade + 5},{255})"
                body.append(f'<rect x="{x0 + c*cell}" y="{y0 + r*cell}" width="{cell}" height="{cell}" fill="{fill}" stroke="white" stroke-width="2"/>')
                body.append(f'<text class="label" x="{x0 + c*cell + cell/2}" y="{y0 + r*cell + cell/2 + 5}" text-anchor="middle">{value}</text>')
        body.append(f'<text class="tick" x="{x0 + cell/2}" y="{y0 + 2*cell + 20}" text-anchor="middle">Pred 0</text>')
        body.append(f'<text class="tick" x="{x0 + 1.5*cell}" y="{y0 + 2*cell + 20}" text-anchor="middle">Pred 1</text>')
        body.append(f'<text class="tick" x="{x0 - 10}" y="{y0 + cell/2}" text-anchor="end">Actual 0</text>')
        body.append(f'<text class="tick" x="{x0 - 10}" y="{y0 + 1.5*cell}" text-anchor="end">Actual 1</text>')
    write_svg(path, width, height, body)


def scatter_plot(path: Path, rows: list[dict[str, str]]) -> None:
    points = [
        (to_float(row.get("kras_probability_active")), to_float(row.get("admet_score")), row.get("recommendation", ""))
        for row in rows
        if row.get("kras_probability_active") not in (None, "")
    ]
    if not points:
        return
    width, height = 860, 560
    left, right, top, bottom = 80, 50, 70, 80
    plot_w, plot_h = width - left - right, height - top - bottom
    body = [
        f'<text class="title" x="{width/2}" y="34" text-anchor="middle">ZINC22 Screening: KRAS Probability vs ADMET Score</text>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
        f'<text class="label" x="{left + plot_w/2}" y="{height - 22}" text-anchor="middle">Predicted KRAS-active probability</text>',
        f'<text class="label" x="22" y="{top + plot_h/2}" transform="rotate(-90 22 {top + plot_h/2})" text-anchor="middle">ADMET score</text>',
    ]
    for i in range(6):
        x = left + plot_w * i / 5
        y = top + plot_h - plot_h * i / 5
        body.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}"/>')
        body.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}"/>')
    for prob, admet, rec in points:
        x = left + prob * plot_w
        y = top + plot_h - admet * plot_h
        color = GREEN if rec == "Advance" else ORANGE if rec == "Advance with review" else "#adb5bd"
        radius = 4 if rec in {"Advance", "Advance with review"} else 2
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" opacity="0.65"/>')
    write_svg(path, width, height, body)


def curve_points(labels: list[int], scores: list[float], curve_type: str) -> tuple[list[tuple[float, float]], float]:
    grouped: dict[float, list[int]] = {}
    for score, label in zip(scores, labels):
        grouped.setdefault(score, []).append(label)
    grouped_items = sorted(grouped.items(), reverse=True)
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return [], 0.0

    if curve_type == "roc":
        points = [(0.0, 0.0)]
        tp = fp = 0
        for _, group_labels in grouped_items:
            tp += sum(1 for label in group_labels if label == 1)
            fp += sum(1 for label in group_labels if label == 0)
            points.append((fp / negatives, tp / positives))
        points.append((1.0, 1.0))
        auc = 0.0
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            auc += (x2 - x1) * (y1 + y2) / 2
    else:
        points = [(0.0, 1.0)]
        tp = fp = 0
        previous_recall = 0.0
        auc = 0.0
        for _, group_labels in grouped_items:
            tp += sum(1 for label in group_labels if label == 1)
            fp += sum(1 for label in group_labels if label == 0)
            recall = tp / positives
            precision = tp / max(1, tp + fp)
            points.append((recall, precision))
            auc += (recall - previous_recall) * precision
            previous_recall = recall
    return points, auc


def line_curve_chart(path: Path, title: str, prediction_rows: list[dict[str, str]], curve_type: str) -> None:
    width, height = 900, 620
    left, right, top, bottom = 90, 250, 80, 90
    plot_w, plot_h = width - left - right, height - top - bottom
    colors = [PURPLE, BLUE, GREEN, ORANGE, RED, GRAY, "#15aabf"]
    models = list(dict.fromkeys(row.get("model", "") for row in prediction_rows))
    body = [
        f'<text class="title" x="{width/2}" y="34" text-anchor="middle">{esc(title)}</text>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
    ]
    for i in range(6):
        x = left + plot_w * i / 5
        y = top + plot_h - plot_h * i / 5
        body.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}"/>')
        body.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}"/>')
        body.append(f'<text class="tick" x="{x:.1f}" y="{top + plot_h + 22}" text-anchor="middle">{i/5:.1f}</text>')
        body.append(f'<text class="tick" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{i/5:.1f}</text>')
    x_label = "False Positive Rate" if curve_type == "roc" else "Recall"
    y_label = "True Positive Rate" if curve_type == "roc" else "Precision"
    body.append(f'<text class="label" x="{left + plot_w/2}" y="{height - 26}" text-anchor="middle">{x_label}</text>')
    body.append(f'<text class="label" x="24" y="{top + plot_h/2}" transform="rotate(-90 24 {top + plot_h/2})" text-anchor="middle">{y_label}</text>')
    legend_x, legend_y = left + plot_w + 35, top + 8
    for idx, model in enumerate(models):
        model_rows = [row for row in prediction_rows if row.get("model") == model]
        labels = [to_int(row.get("actual_label")) for row in model_rows]
        scores = [to_float(row.get("positive_score")) for row in model_rows]
        points, auc = curve_points(labels, scores, curve_type)
        if not points:
            continue
        coords = " ".join(f"{left + x * plot_w:.1f},{top + plot_h - y * plot_h:.1f}" for x, y in points)
        color = colors[idx % len(colors)]
        body.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        y = legend_y + idx * 24
        metric_label = "AUC" if curve_type == "roc" else "AP"
        body.append(f'<rect x="{legend_x}" y="{y - 10}" width="14" height="14" fill="{color}"/>')
        body.append(f'<text class="label" x="{legend_x + 22}" y="{y + 2}">{esc(fmt_model(model))} ({metric_label} {auc:.3f})</text>')
    write_svg(path, width, height, body)


def generate_figures(processed_dir: Path = PROCESSED_DIR, figures_dir: Path = FIGURES_DIR) -> dict[str, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    curation = read_json(processed_dir / "kras_curation_summary.json")
    if curation:
        path = figures_dir / "activity_class_balance.svg"
        bar_chart(
            path,
            "KRAS Training Set Activity-Class Balance",
            ["Active", "Inactive"],
            [
                to_int(curation.get("active_training_rows")),
                to_int(curation.get("inactive_training_rows")),
            ],
            GREEN,
        )
        outputs["Activity-class balance"] = path

        path = figures_dir / "curation_funnel.svg"
        bar_chart(
            path,
            "ChEMBL Curation Funnel",
            ["Raw", "Labeled", "Active", "Inactive"],
            [
                to_int(curation.get("raw_records")),
                to_int(curation.get("training_rows")),
                to_int(curation.get("active_training_rows")),
                to_int(curation.get("inactive_training_rows")),
            ],
            BLUE,
        )
        outputs["ChEMBL curation funnel"] = path

        path = figures_dir / "variant_distribution.svg"
        bar_chart(
            path,
            "Training Records by KRAS Pathway Subset",
            ["G12C", "G12D", "G12V", "SOS1", "KRAS other"],
            [
                to_int(curation.get("g12c_training_rows")),
                to_int(curation.get("g12d_training_rows")),
                to_int(curation.get("g12v_training_rows")),
                to_int(curation.get("sos1_training_rows")),
                to_int(curation.get("kras_unspecified_training_rows")),
            ],
            GREEN,
        )
        outputs["Target and mutation distribution"] = path

    druglike = read_json(processed_dir / "kras_druglikeness_summary.json")
    if druglike:
        path = figures_dir / "druglikeness_filter_summary.svg"
        bar_chart(
            path,
            "Drug-Likeness Filter Summary",
            ["All", "Lipinski", "Veber", "Project drug-like"],
            [
                to_int(druglike.get("rows")),
                to_int(druglike.get("passes_lipinski")),
                to_int(druglike.get("passes_veber")),
                to_int(druglike.get("passes_project_druglike")),
            ],
            ORANGE,
        )
        outputs["Drug-likeness filter summary"] = path

    matrix_rows = read_csv_rows(processed_dir / "kras_model_matrix.csv")
    if matrix_rows:
        path = figures_dir / "molecular_property_distributions.svg"
        descriptor_panel(path, matrix_rows)
        outputs["Molecular property distributions"] = path

    druglike_rows = read_csv_rows(processed_dir / "kras_model_matrix_druglikeness_report.csv")
    if druglike_rows:
        violation_counts = Counter(str(to_int(row.get("lipinski_violations"))) for row in druglike_rows)
        labels = sorted(violation_counts, key=lambda value: int(value))
        path = figures_dir / "lipinski_violation_counts.svg"
        bar_chart(path, "Lipinski Rule-of-Five Violation Counts", labels, [violation_counts[label] for label in labels], GREEN)
        outputs["Lipinski violation counts"] = path

    model_rows = read_csv_rows(processed_dir / "model_metrics.csv")
    if model_rows:
        path = figures_dir / "model_metric_comparison.svg"
        grouped_metric_chart(path, "Holdout Model Performance Comparison", model_rows, ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"])
        outputs["Holdout model metric comparison"] = path

    cv_rows = read_csv_rows(processed_dir / "cross_validation_metrics.csv")
    if cv_rows:
        path = figures_dir / "cross_validation_roc_auc.svg"
        cv_error_chart(path, cv_rows)
        outputs["Cross-validation ROC-AUC comparison"] = path

    holdout_rows = read_csv_rows(processed_dir / "holdout_predictions.csv")
    if holdout_rows:
        path = figures_dir / "holdout_roc_curves.svg"
        line_curve_chart(path, "Holdout ROC Curves", holdout_rows, "roc")
        outputs["Holdout ROC curves"] = path

        path = figures_dir / "holdout_precision_recall_curves.svg"
        line_curve_chart(path, "Holdout Precision-Recall Curves", holdout_rows, "pr")
        outputs["Holdout precision-recall curves"] = path

    matrix_dir = processed_dir / "confusion_matrices"
    if matrix_dir.exists():
        path = figures_dir / "confusion_matrices.svg"
        confusion_matrix_panel(path, matrix_dir)
        outputs["Holdout confusion matrices"] = path

    importance_rows = read_csv_rows(processed_dir / "interpretation" / "feature_importance.csv")[:15]
    if importance_rows:
        path = figures_dir / "top_feature_importance.svg"
        bar_chart(
            path,
            "Top Model Features by Importance",
            [row.get("feature", "") for row in importance_rows],
            [to_float(row.get("importance")) for row in importance_rows],
            PURPLE,
        )
        outputs["Top model feature importance"] = path

    triage = read_json(processed_dir / "batch_screening" / "hit_triage" / "hit_triage_summary.json")
    if triage:
        path = figures_dir / "zinc22_hit_triage_funnel.svg"
        bar_chart(
            path,
            "ZINC22 Hit Triage Funnel",
            ["Screened", "Hit candidates", "Reported"],
            [
                to_int(triage.get("total_screened")),
                to_int(triage.get("total_hit_candidates")),
                to_int(triage.get("reported_top_n")),
            ],
            GREEN,
        )
        outputs["ZINC22 hit triage funnel"] = path

    screening_rows = read_csv_rows(processed_dir / "batch_screening" / "ranked_screening_results.csv")
    if screening_rows:
        path = figures_dir / "zinc22_probability_vs_admet.svg"
        scatter_plot(path, screening_rows)
        outputs["ZINC22 probability versus ADMET"] = path

        recommendations = Counter(row.get("recommendation", "Unknown") for row in screening_rows)
        path = figures_dir / "zinc22_recommendation_distribution.svg"
        labels = sorted(recommendations)
        bar_chart(path, "ZINC22 Screening Recommendation Distribution", labels, [recommendations[label] for label in labels], RED)
        outputs["ZINC22 recommendation distribution"] = path

    return outputs


def write_summary(outputs: dict[str, Path], processed_dir: Path = PROCESSED_DIR, reports_dir: Path = REPORTS_DIR) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "statistical_exploration_summary.md"
    curation = read_json(processed_dir / "kras_curation_summary.json")
    druglike = read_json(processed_dir / "kras_druglikeness_summary.json")
    triage = read_json(processed_dir / "batch_screening" / "hit_triage" / "hit_triage_summary.json")
    cv_rows = read_csv_rows(processed_dir / "cross_validation_metrics.csv")
    xgb_cv = next((row for row in cv_rows if row.get("model") == "xgboost"), {})
    metrics_rows = read_csv_rows(processed_dir / "model_metrics.csv")
    best = metrics_rows[0] if metrics_rows else {}

    lines = [
        "# Statistical Exploration and Model Evidence Summary",
        "",
        "This report collects reproducible figures generated from saved project outputs. It is intended to support scientific review by showing how compounds moved through curation, feature engineering, model evaluation, and ZINC22 hit triage.",
        "",
        "## Source Files",
        "",
        "- `data/processed/kras_curation_summary.json`",
        "- `data/processed/kras_model_matrix.csv`",
        "- `data/processed/kras_druglikeness_summary.json`",
        "- `data/processed/model_metrics.csv`",
        "- `data/processed/holdout_predictions.csv`",
        "- `data/processed/cross_validation_metrics.csv`",
        "- `data/processed/confusion_matrices/*.csv`",
        "- `data/processed/interpretation/feature_importance.csv`",
        "- `data/processed/batch_screening/ranked_screening_results.csv`",
        "- `data/processed/batch_screening/hit_triage/hit_triage_summary.json`",
        "",
        "## Key Counts",
        "",
        f"- ChEMBL raw records curated: `{to_int(curation.get('raw_records')):,}`",
        f"- Labeled active/inactive training records: `{to_int(curation.get('training_rows')):,}`",
        f"- Active training records: `{to_int(curation.get('active_training_rows')):,}`",
        f"- Inactive training records: `{to_int(curation.get('inactive_training_rows')):,}`",
        f"- Project drug-like records: `{to_int(druglike.get('passes_project_druglike')):,}`",
        f"- ZINC22 compounds screened: `{to_int(triage.get('total_screened')):,}`",
        f"- ZINC22 candidates passing hit-triage criteria: `{to_int(triage.get('total_hit_candidates')):,}`",
        "",
        "## Model Evidence",
        "",
        f"The best holdout model in the saved comparison is `{best.get('model', 'not available')}` with ROC-AUC `{to_float(best.get('roc_auc')):.3f}`, PR-AUC `{to_float(best.get('pr_auc')):.3f}`, F1 `{to_float(best.get('f1')):.3f}`, and recall `{to_float(best.get('recall')):.3f}`.",
        f"Five-fold cross-validation for XGBoost produced mean ROC-AUC `{to_float(xgb_cv.get('roc_auc_mean')):.3f}` with standard deviation `{to_float(xgb_cv.get('roc_auc_std')):.3f}`.",
        "",
        "## Generated Figures",
        "",
    ]
    for title, path in outputs.items():
        rel_path = path.relative_to(reports_dir).as_posix()
        lines.extend([f"### {title}", "", f"![{title}]({rel_path})", ""])
    lines.extend(
        [
            "## Notes and Limitations",
            "",
            "- These figures are generated from saved project artifacts, not from a fresh ChEMBL or ZINC22 download.",
            "- ROC and precision-recall curves are generated when `data/processed/holdout_predictions.csv` is available. Rerun model training first if that file is missing.",
            "- The ZINC22 hit triage results are computational predictions and should be treated as prioritization evidence for docking, molecular dynamics, medicinal chemistry review, and experimental validation.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "python -m kras_discovery.visualization.static_plots",
            "```",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SVG figures from saved KRAS discovery outputs.")
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args()

    outputs = generate_figures(args.processed_dir, args.figures_dir)
    report_path = write_summary(outputs, args.processed_dir, args.reports_dir)
    print(json.dumps({"figures": {key: str(value) for key, value in outputs.items()}, "report": str(report_path)}, indent=2))


if __name__ == "__main__":
    main()
