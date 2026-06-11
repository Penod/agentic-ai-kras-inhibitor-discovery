import tempfile
import unittest
from pathlib import Path

from kras_discovery.screening.zinc_prepare import convert_zinc_smi_to_csv, parse_smi_line


class ZincPrepareTest(unittest.TestCase):
    def test_parse_smi_line(self) -> None:
        self.assertEqual(parse_smi_line("CCO ZINC000001\n"), ("ZINC000001", "CCO"))
        self.assertIsNone(parse_smi_line(""))
        self.assertIsNone(parse_smi_line("CCO"))

    def test_convert_zinc_smi_to_csv_with_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "sample.smi"
            output_path = tmp_path / "sample.csv"
            input_path.write_text("CCO ZINC000001\nCCC ZINC000002\nCCN ZINC000003\n", encoding="utf-8")

            count = convert_zinc_smi_to_csv(input_path=input_path, output_path=output_path, limit=2)

            self.assertEqual(count, 2)
            rows = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(rows[0], "compound,smiles,library,notes")
            self.assertIn("ZINC000001,CCO,ZINC,lead-like screening candidate", rows)
            self.assertIn("ZINC000002,CCC,ZINC,lead-like screening candidate", rows)


if __name__ == "__main__":
    unittest.main()
