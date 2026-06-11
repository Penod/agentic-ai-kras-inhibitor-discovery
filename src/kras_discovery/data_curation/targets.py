from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChEMBLTargetConfig:
    label: str
    target_chembl_id: str
    preferred_name: str
    target_type: str
    mutation_keywords: tuple[str, ...] = ()


CHEMBL_TARGETS = (
    ChEMBLTargetConfig(
        label="KRAS",
        target_chembl_id="CHEMBL2189121",
        preferred_name="GTPase KRas",
        target_type="single protein",
        mutation_keywords=("G12C", "G12D", "G12V", "KRAS"),
    ),
    ChEMBLTargetConfig(
        label="SOS1",
        target_chembl_id="CHEMBL4523334",
        preferred_name="Son of sevenless homolog 1",
        target_type="single protein",
        mutation_keywords=("SOS1",),
    ),
)


TARGETS_BY_ID = {target.target_chembl_id: target for target in CHEMBL_TARGETS}
