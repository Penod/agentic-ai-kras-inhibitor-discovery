from __future__ import annotations

from kras_discovery.models.schemas import TargetNode, TargetPanel


KRAS_TARGET_PANEL = TargetPanel(
    family="KRAS pathway",
    indication_focus="pancreatic cancer and lung adenocarcinoma",
    nodes=(
        TargetNode(
            name="KRAS G12C",
            gene="KRAS",
            mutation="G12C",
            role="clinically validated covalent inhibitor target",
            disease_context="non-small cell lung cancer and colorectal cancer",
        ),
        TargetNode(
            name="KRAS G12D",
            gene="KRAS",
            mutation="G12D",
            role="high-priority pancreatic cancer mutation",
            disease_context="pancreatic ductal adenocarcinoma",
        ),
        TargetNode(
            name="KRAS G12V",
            gene="KRAS",
            mutation="G12V",
            role="common solid-tumor KRAS mutation",
            disease_context="lung, colorectal, and pancreatic cancer",
        ),
        TargetNode(
            name="SOS1",
            gene="SOS1",
            mutation="wild-type pathway node",
            role="guanine nucleotide exchange factor upstream of KRAS activation",
            disease_context="KRAS pathway modulation",
        ),
    ),
)
