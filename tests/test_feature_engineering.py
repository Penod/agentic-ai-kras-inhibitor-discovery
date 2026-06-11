import unittest
from pathlib import Path

from kras_discovery.feature_engineering.rdkit_features import (
    DESCRIPTOR_FIELDS,
    MACCS_FIELDS,
    MORGAN_FIELDS,
    RDKitUnavailableError,
    activity_class_to_label,
    import_rdkit,
    metadata_row,
    run_rdkit_feature_pipeline,
)


class FeatureEngineeringTest(unittest.TestCase):
    def test_activity_class_to_label(self) -> None:
        self.assertEqual(activity_class_to_label("active"), "1")
        self.assertEqual(activity_class_to_label("inactive"), "0")

        with self.assertRaises(ValueError):
            activity_class_to_label("ambiguous")

    def test_metadata_row_encodes_binary_label(self) -> None:
        row = {
            "molecule_chembl_id": "CHEMBL1",
            "canonical_smiles": "CCO",
            "target_label": "KRAS",
            "variant_or_node": "G12C",
            "activity_class": "active",
            "best_pchembl_value": "7.300",
        }

        metadata = metadata_row(row)

        self.assertEqual(metadata["activity_label"], "1")
        self.assertEqual(metadata["variant_or_node"], "G12C")

    def test_feature_field_counts(self) -> None:
        self.assertEqual(len(DESCRIPTOR_FIELDS), 12)
        self.assertEqual(len(MACCS_FIELDS), 166)
        self.assertEqual(len(MORGAN_FIELDS), 2048)

    def test_missing_training_file_has_actionable_error(self) -> None:
        with self.assertRaises(FileNotFoundError) as context:
            run_rdkit_feature_pipeline(Path("missing_training_set.csv"), Path("."))

        self.assertIn("Run `python -m kras_discovery.data_curation.chembl_pipeline` first", str(context.exception))

    def test_rdkit_import_contract(self) -> None:
        try:
            modules = import_rdkit()
        except RDKitUnavailableError:
            self.skipTest("RDKit is not installed in this environment")

        self.assertIn("Chem", modules)
        self.assertIn("MACCSkeys", modules)


if __name__ == "__main__":
    unittest.main()
