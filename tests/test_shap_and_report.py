import unittest

from kras_discovery.interpretation.report import build_report, format_metric
from kras_discovery.interpretation.shap_analysis import build_shap_rows


class ShapAndReportTest(unittest.TestCase):
    def test_build_shap_rows_ranks_features(self) -> None:
        rows = build_shap_rows(["a", "b", "c"], [0.1, 0.5, 0.2])

        self.assertEqual(rows[0]["feature"], "b")
        self.assertEqual(rows[0]["rank"], "1")
        self.assertAlmostEqual(sum(float(row["normalized_mean_abs_shap"]) for row in rows), 1.0)

    def test_format_metric(self) -> None:
        self.assertEqual(format_metric("0.984467"), "0.984")
        self.assertEqual(format_metric(None), "n/a")

    def test_build_report_includes_core_sections(self) -> None:
        comparison = {
            "best_model": "xgboost",
            "row_count": 10,
            "feature_count": 3,
            "class_counts": {"active": 6, "inactive": 4},
            "metrics": [
                {
                    "model": "xgboost",
                    "accuracy": "0.900",
                    "precision": "0.910",
                    "recall": "0.920",
                    "f1": "0.915",
                    "roc_auc": "0.950",
                    "pr_auc": "0.970",
                }
            ],
        }
        importance = {
            "top_features": [{"feature": "morgan_1"}, {"feature": "maccs_2"}],
            "group_importance": {"Morgan": 0.7, "MACCS": 0.3},
        }

        report = build_report(
            full_comparison=comparison,
            druglike_comparison=comparison,
            full_importance=importance,
            druglike_importance=importance,
            full_shap={},
            druglike_shap={},
        )

        self.assertIn("# KRAS Model Interpretation Report", report)
        self.assertIn("Model Performance", report)
        self.assertIn("SHAP outputs were not found", report)


if __name__ == "__main__":
    unittest.main()
