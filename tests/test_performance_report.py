import unittest

from kras_discovery.modeling.performance_report import build_performance_report


class PerformanceReportTest(unittest.TestCase):
    def test_build_performance_report_includes_best_model_and_cv(self) -> None:
        report = build_performance_report(
            {
                "model_matrix": "matrix.csv",
                "row_count": 10,
                "feature_count": 3,
                "class_counts": {"active": 6, "inactive": 4},
                "test_size": 0.2,
                "random_state": 42,
                "selection_metric": "roc_auc",
                "cv_folds_used": 5,
                "best_model": "xgboost",
                "metrics": [
                    {
                        "model": "xgboost",
                        "accuracy": "0.9",
                        "precision": "0.9",
                        "recall": "0.9",
                        "f1": "0.9",
                        "roc_auc": "0.95",
                        "pr_auc": "0.96",
                    }
                ],
                "cross_validation": [
                    {
                        "model": "xgboost",
                        "folds": "5",
                        "accuracy_mean": "0.9",
                        "accuracy_std": "0.01",
                        "f1_mean": "0.9",
                        "f1_std": "0.01",
                        "roc_auc_mean": "0.95",
                        "roc_auc_std": "0.01",
                        "pr_auc_mean": "0.96",
                        "pr_auc_std": "0.01",
                    }
                ],
            }
        )

        self.assertIn("KRAS Bioactivity Model Performance Summary", report)
        self.assertIn("Xgboost", report)
        self.assertIn("cross-validated", report)


if __name__ == "__main__":
    unittest.main()
