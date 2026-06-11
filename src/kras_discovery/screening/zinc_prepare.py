from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_smi_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped:
        return None
    parts = stripped.split()
    if len(parts) < 2:
        return None
    smiles = parts[0]
    zinc_id = parts[1]
    return zinc_id, smiles


def convert_zinc_smi_to_csv(
    input_path: Path,
    output_path: Path,
    limit: int = 5000,
    library_name: str = "ZINC",
    notes: str = "lead-like screening candidate",
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with input_path.open("r", encoding="utf-8") as source, output_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=["compound", "smiles", "library", "notes"])
        writer.writeheader()
        for line in source:
            parsed = parse_smi_line(line)
            if parsed is None:
                continue
            zinc_id, smiles = parsed
            writer.writerow(
                {
                    "compound": zinc_id,
                    "smiles": smiles,
                    "library": library_name,
                    "notes": notes,
                }
            )
            count += 1
            if count >= limit:
                break

    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a ZINC .smi file into the batch-screening CSV format.")
    parser.add_argument("--input", type=Path, required=True, help="Input ZINC .smi file.")
    parser.add_argument("--output", type=Path, default=Path("data/external/zinc_screening_library.csv"), help="Output CSV.")
    parser.add_argument("--limit", type=int, default=5000, help="Maximum number of compounds to write.")
    parser.add_argument("--library", default="ZINC", help="Library label to write into the CSV.")
    parser.add_argument("--notes", default="lead-like screening candidate", help="Notes label to write into the CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = convert_zinc_smi_to_csv(
        input_path=args.input,
        output_path=args.output,
        limit=args.limit,
        library_name=args.library,
        notes=args.notes,
    )
    print(f"Wrote {count} compounds to {args.output}")


if __name__ == "__main__":
    main()
