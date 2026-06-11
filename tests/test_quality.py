import unittest

from kras_discovery.quality.assay_quality import add_assay_quality_flags
from kras_discovery.quality.druglikeness import (
    add_druglikeness_flags,
    lipinski_violations,
    passes_project_druglike,
    passes_veber,
)


class QualityFilterTest(unittest.TestCase):
    def test_druglike_row_passes_filters(self) -> None:
        row = {
            "mol_wt": "420",
            "mol_logp": "3.2",
            "tpsa": "82",
            "h_bond_donors": "2",
            "h_bond_acceptors": "7",
            "rotatable_bonds": "6",
            "activity_label": "1",
        }

        flagged = add_druglikeness_flags(row)

        self.assertEqual(lipinski_violations(row), [])
        self.assertTrue(passes_veber(row))
        self.assertTrue(passes_project_druglike(row))
        self.assertEqual(flagged["passes_project_druglike"], "True")

    def test_non_druglike_row_is_flagged(self) -> None:
        row = {
            "mol_wt": "780",
            "mol_logp": "7.2",
            "tpsa": "190",
            "h_bond_donors": "7",
            "h_bond_acceptors": "14",
            "rotatable_bonds": "18",
        }

        flagged = add_druglikeness_flags(row)

        self.assertGreaterEqual(int(flagged["lipinski_violations"]), 3)
        self.assertEqual(flagged["passes_veber"], "False")
        self.assertEqual(flagged["passes_project_druglike"], "False")

    def test_assay_quality_flags_problem_records(self) -> None:
        row = {
            "target_organism": "Homo sapiens",
            "assay_type": "B",
            "standard_type": "IC50",
            "data_validity_comment": "",
            "activity_class": "active",
            "canonical_smiles": "CCO",
        }
        bad_row = {
            "target_organism": "Mus musculus",
            "assay_type": "F",
            "standard_type": "Ratio",
            "data_validity_comment": "Outside typical range",
            "activity_class": "ambiguous",
            "canonical_smiles": "",
        }

        self.assertEqual(add_assay_quality_flags(row)["passes_assay_quality"], "True")
        flagged = add_assay_quality_flags(bad_row)
        self.assertEqual(flagged["passes_assay_quality"], "False")
        self.assertIn("non-human target organism", flagged["assay_quality_notes"])


if __name__ == "__main__":
    unittest.main()
