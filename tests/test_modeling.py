import tempfile
import unittest
from pathlib import Path

from kras_discovery.modeling.dataset import class_counts, is_numeric_feature_column, read_model_matrix
from kras_discovery.modeling.train_models import (
    ModelingDependencyError,
    effective_cv_folds,
    import_modeling_dependencies,
    molecule_group_keys,
    scaffold_group_keys,
    split_indices,
)


class ModelingDatasetTest(unittest.TestCase):
    def test_read_model_matrix_identifies_features_and_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matrix.csv"
            path.write_text(
                "\n".join(
                    [
                        "molecule_chembl_id,canonical_smiles,target_label,variant_or_node,activity_class,activity_label,best_pchembl_value,feature_a,feature_b",
                        "CHEMBL1,CCO,KRAS,G12C,active,1,7.2,0.1,1",
                        "CHEMBL2,CCN,KRAS,G12D,inactive,0,4.8,0.2,0",
                    ]
                ),
                encoding="utf-8",
            )

            matrix = read_model_matrix(path)

        self.assertEqual(matrix.feature_columns, ["feature_a", "feature_b"])
        self.assertEqual(matrix.labels, [1, 0])
        self.assertEqual(class_counts(matrix.labels), {"inactive": 1, "active": 1})

    def test_missing_model_matrix_has_actionable_error(self) -> None:
        with self.assertRaises(FileNotFoundError) as context:
            read_model_matrix(Path("missing_model_matrix.csv"))

        self.assertIn("Run `python -m kras_discovery.feature_engineering.rdkit_pipeline` first", str(context.exception))

    def test_read_model_matrix_ignores_quality_annotation_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matrix.csv"
            path.write_text(
                "\n".join(
                    [
                        "molecule_chembl_id,canonical_smiles,target_label,variant_or_node,activity_class,activity_label,best_pchembl_value,feature_a,passes_lipinski,druglike_notes",
                        "CHEMBL1,CCO,KRAS,G12C,active,1,7.2,0.1,True,",
                        "CHEMBL2,CCN,KRAS,G12D,inactive,0,4.8,0.2,False,MW > 500",
                    ]
                ),
                encoding="utf-8",
            )

            matrix = read_model_matrix(path)

        self.assertEqual(matrix.feature_columns, ["feature_a"])

    def test_numeric_feature_detection(self) -> None:
        rows = [{"a": "1.0", "b": "True"}, {"a": "2", "b": "False"}]

        self.assertTrue(is_numeric_feature_column(rows, "a"))
        self.assertFalse(is_numeric_feature_column(rows, "b"))

    def test_modeling_dependency_contract(self) -> None:
        try:
            deps = import_modeling_dependencies()
        except ModelingDependencyError:
            self.skipTest("scikit-learn modeling dependencies are not installed")

        self.assertIn("RandomForestClassifier", deps)
        self.assertIn("LogisticRegression", deps)

    def test_effective_cv_folds_respects_smallest_class(self) -> None:
        self.assertEqual(effective_cv_folds([0, 0, 1, 1, 1], requested_folds=5), 2)
        self.assertEqual(effective_cv_folds([0, 1, 1], requested_folds=5), 0)
        self.assertEqual(effective_cv_folds([0, 0, 1, 1], requested_folds=1), 0)

    def test_molecule_group_keys_use_smiles_to_keep_duplicates_together(self) -> None:
        rows = [
            {"molecule_chembl_id": "CHEMBL1", "canonical_smiles": "CCO"},
            {"molecule_chembl_id": "CHEMBL2", "canonical_smiles": "CCO"},
            {"molecule_chembl_id": "CHEMBL3", "canonical_smiles": "CCN"},
        ]

        self.assertEqual(molecule_group_keys(rows), ["CCO", "CCO", "CCN"])

    def test_grouped_split_prevents_exact_molecule_overlap(self) -> None:
        try:
            deps = import_modeling_dependencies()
        except ModelingDependencyError:
            self.skipTest("scikit-learn modeling dependencies are not installed")

        np = deps["np"]
        rows = [
            {"molecule_chembl_id": "CHEMBL1", "canonical_smiles": "CCO"},
            {"molecule_chembl_id": "CHEMBL2", "canonical_smiles": "CCO"},
            {"molecule_chembl_id": "CHEMBL3", "canonical_smiles": "CCN"},
            {"molecule_chembl_id": "CHEMBL4", "canonical_smiles": "CCN"},
            {"molecule_chembl_id": "CHEMBL5", "canonical_smiles": "CCC"},
            {"molecule_chembl_id": "CHEMBL6", "canonical_smiles": "CCCC"},
        ]
        y = np.asarray([1, 1, 0, 0, 1, 0], dtype=int)

        train_indices, test_indices, groups = split_indices(
            y=y,
            deps=deps,
            rows=rows,
            test_size=0.34,
            random_state=42,
            split_strategy="molecule",
        )

        self.assertIsNotNone(groups)
        train_groups = {groups[int(index)] for index in train_indices}
        test_groups = {groups[int(index)] for index in test_indices}
        self.assertFalse(train_groups & test_groups)

    def test_scaffold_group_keys_group_related_aromatic_compounds(self) -> None:
        try:
            groups = scaffold_group_keys(
                [
                    {"molecule_chembl_id": "CHEMBL1", "canonical_smiles": "Cc1ccccc1"},
                    {"molecule_chembl_id": "CHEMBL2", "canonical_smiles": "Oc1ccccc1"},
                ]
            )
        except ModelingDependencyError:
            self.skipTest("RDKit is not installed")

        self.assertEqual(groups[0], groups[1])


if __name__ == "__main__":
    unittest.main()
