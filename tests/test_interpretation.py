import unittest

from kras_discovery.interpretation.feature_importance import (
    build_importance_rows,
    feature_group,
    summarize_importances,
)


class InterpretationTest(unittest.TestCase):
    def test_feature_group(self) -> None:
        self.assertEqual(feature_group("mol_wt"), "Descriptor")
        self.assertEqual(feature_group("maccs_42"), "MACCS")
        self.assertEqual(feature_group("morgan_99"), "Morgan")

    def test_importance_rows_are_ranked_and_normalized(self) -> None:
        rows = build_importance_rows(
            ["mol_wt", "maccs_1", "morgan_7"],
            [0.2, 0.5, 0.3],
        )

        self.assertEqual(rows[0]["feature"], "maccs_1")
        self.assertEqual(rows[0]["rank"], "1")
        self.assertAlmostEqual(sum(float(row["normalized_importance"]) for row in rows), 1.0)

    def test_importance_summary_groups_features(self) -> None:
        rows = build_importance_rows(
            ["mol_wt", "maccs_1", "morgan_7"],
            [0.2, 0.5, 0.3],
        )
        summary = summarize_importances(rows, top_n=2)

        self.assertEqual(summary["feature_count"], 3)
        self.assertEqual(len(summary["top_features"]), 2)
        self.assertEqual(summary["group_importance"]["MACCS"], 0.5)


if __name__ == "__main__":
    unittest.main()
