from pathlib import Path

from kras_discovery.visualization.static_plots import histogram_counts, to_float, write_svg


def test_to_float_handles_empty_and_boolean_like_values():
    assert to_float("") == 0.0
    assert to_float(None) == 0.0
    assert to_float("0.75") == 0.75
    assert to_float("not-a-number", default=-1.0) == -1.0


def test_histogram_counts_preserves_observation_count():
    _, counts, low, high = histogram_counts([1.0, 2.0, 3.0, 4.0], bins=4)

    assert sum(counts) == 4
    assert low == 1.0
    assert high == 4.0


def test_write_svg_creates_valid_svg_file(tmp_path: Path):
    output = tmp_path / "figure.svg"

    write_svg(output, 120, 80, ['<text x="10" y="20">Test</text>'])

    content = output.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert "Test" in content

