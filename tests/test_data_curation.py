import tempfile
import unittest
from pathlib import Path

from kras_discovery.data_curation.curation import (
    CURATED_FIELDS,
    TRAINING_FIELDS,
    build_training_set,
    curate_activity,
    infer_variant_or_node,
    read_csv,
    summarize_records,
    write_csv,
)


def activity(
    molecule_id: str,
    smiles: str,
    pchembl: str,
    description: str,
    *,
    target_id: str = "CHEMBL2189121",
    standard_type: str = "IC50",
) -> dict[str, str]:
    return {
        "molecule_chembl_id": molecule_id,
        "canonical_smiles": smiles,
        "standard_type": standard_type,
        "standard_relation": "=",
        "standard_value": "10",
        "standard_units": "nM",
        "pchembl_value": pchembl,
        "assay_chembl_id": "CHEMBLASSAY1",
        "assay_type": "B",
        "assay_description": description,
        "target_chembl_id": target_id,
        "target_pref_name": "GTPase KRas",
        "target_organism": "Homo sapiens",
        "document_chembl_id": "CHEMBLDOC1",
        "document_year": "2024",
        "src_id": "1",
        "bao_label": "single protein format",
        "data_validity_comment": "",
    }


class DataCurationTest(unittest.TestCase):
    def test_activity_labeling_and_variant_inference(self) -> None:
        active = curate_activity(activity("CHEMBL1", "CCO", "7.2", "KRAS G12C inhibitor assay"))
        inactive = curate_activity(activity("CHEMBL2", "CCN", "4.8", "KRAS G12D assay"))
        ambiguous = curate_activity(activity("CHEMBL3", "CCC", "6.1", "KRAS G12V assay"))

        self.assertEqual(active["activity_class"], "active")
        self.assertEqual(active["variant_or_node"], "G12C")
        self.assertEqual(inactive["activity_class"], "inactive")
        self.assertEqual(inactive["variant_or_node"], "G12D")
        self.assertEqual(ambiguous["activity_class"], "ambiguous")
        self.assertEqual(ambiguous["variant_or_node"], "G12V")

    def test_sos1_target_is_inferred_from_target_id(self) -> None:
        record = curate_activity(
            activity(
                "CHEMBL4",
                "CCCl",
                "7.8",
                "Exchange factor assay",
                target_id="CHEMBL4523334",
            )
        )

        self.assertEqual(record["target_label"], "SOS1")
        self.assertEqual(record["variant_or_node"], "SOS1")

    def test_training_set_excludes_ambiguous_and_conflicting_labels(self) -> None:
        curated = [
            curate_activity(activity("CHEMBL1", "CCO", "7.4", "KRAS G12C assay")),
            curate_activity(activity("CHEMBL1", "CCO", "7.1", "KRAS G12C assay")),
            curate_activity(activity("CHEMBL2", "CCN", "4.2", "KRAS G12D assay")),
            curate_activity(activity("CHEMBL3", "CCC", "6.2", "KRAS G12V assay")),
            curate_activity(activity("CHEMBL4", "CCCC", "7.3", "KRAS G12C assay")),
            curate_activity(activity("CHEMBL4", "CCCC", "4.9", "KRAS G12C assay")),
        ]

        training_rows = build_training_set(curated)

        self.assertEqual(len(training_rows), 2)
        self.assertEqual({row["molecule_chembl_id"] for row in training_rows}, {"CHEMBL1", "CHEMBL2"})
        self.assertEqual(next(row for row in training_rows if row["molecule_chembl_id"] == "CHEMBL1")["assay_count"], "2")

    def test_csv_round_trip_and_summary(self) -> None:
        curated = [
            curate_activity(activity("CHEMBL1", "CCO", "7.4", "KRAS G12C assay")),
            curate_activity(activity("CHEMBL2", "CCN", "4.2", "KRAS G12D assay")),
        ]
        training_rows = build_training_set(curated)

        with tempfile.TemporaryDirectory() as tmpdir:
            curated_path = Path(tmpdir) / "curated.csv"
            training_path = Path(tmpdir) / "training.csv"
            write_csv(curated_path, curated, CURATED_FIELDS)
            write_csv(training_path, training_rows, TRAINING_FIELDS)

            self.assertEqual(len(read_csv(curated_path)), 2)
            self.assertEqual(len(read_csv(training_path)), 2)

        summary = summarize_records(curated, training_rows)
        self.assertEqual(summary["active_training_rows"], 1)
        self.assertEqual(summary["inactive_training_rows"], 1)

    def test_unknown_variant_fallback(self) -> None:
        self.assertEqual(infer_variant_or_node({"assay_description": "", "target_pref_name": "", "bao_label": ""}), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
