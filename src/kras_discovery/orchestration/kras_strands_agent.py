"""
kras_strands_agent.py

Strands SDK orchestration agent for KRAS inhibitor candidate triage
and virtual screening.

IMPORTANT ARCHITECTURE NOTE:
Your existing src/kras_discovery/agents/orchestrator.py already runs
all 9 agents (Validation, Feature, KRASTargetFit, MutantSelectivity,
ADMET, Toxicity, Literature, Manufacturability, ClinicalRelevance) in
a fixed sequence over a shared CandidateContext. That sequencing is
deterministic and correct as-is -- this file does NOT re-wrap each
individual agent as a separate LLM-callable tool, because doing so
would require re-implementing the CandidateContext plumbing
(target_panel, features dict passed agent-to-agent) outside of
AgentOrchestrator, which risks drifting out of sync with the real
pipeline.

Instead, the LLM orchestrates at the WORKFLOW level -- the decision
that's actually novel versus your existing CLI:
    - "evaluate this one SMILES"      -> evaluate_candidate
    - "prepare this ZINC .smi file"   -> prepare_zinc_library
    - "screen this CSV library"       -> run_batch_screen
    - "triage these screening results" -> triage_hits
    - chaining these correctly for a full "screen this raw ZINC
      tranche end to end" request

This keeps the underlying scientific pipeline (evaluate_candidates,
AgentOrchestrator, the trained XGBoost model) completely unchanged --
only the entry points the LLM can call are new.

Install:
    pip install strands-agents boto3

Requires AWS credentials with Bedrock model access configured, and
must run with the repo's src/ on the Python path (e.g. from the repo
root with `pip install -e .` done, or PYTHONPATH=src).
"""

import logging
from pathlib import Path

from strands import Agent, tool
from strands.models import BedrockModel

from kras_discovery.models.schemas import MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates
from kras_discovery.screening.zinc_prepare import convert_zinc_smi_to_csv
from kras_discovery.screening.batch_screen import run_batch_screening
from kras_discovery.screening.hit_triage import triage_hits as _triage_hits


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kras_agent")


SYSTEM_PROMPT = """You are a research orchestration agent for KRAS-pathway
inhibitor discovery, sitting on top of an existing 9-agent evaluation
pipeline (validation, feature computation, KRAS target-fit scoring via
a trained XGBoost classifier at ROC-AUC 0.9845, mutant selectivity,
ADMET, toxicity, literature, manufacturability, and clinical
relevance). That pipeline's internal sequencing is fixed and already
correct -- your job is to decide which WORKFLOW to run and in what
order, and to explain your reasoning and the results in natural
language.

## Workflows available to you
1. SINGLE-MOLECULE EVALUATION -- evaluate_candidate(smiles, name).
   Runs the full 9-agent pipeline on one molecule and returns a
   complete report with every agent's finding.
2. LIBRARY PREPARATION -- prepare_zinc_library(input_smi_path,
   output_csv_path, limit). Converts a raw ZINC .smi tranche file
   into the CSV format the batch screener needs. Only needed when
   starting from a raw .smi file rather than an existing CSV.
3. BATCH VIRTUAL SCREENING -- run_batch_screen(input_csv_path,
   output_dir, top_n). Runs the full 9-agent pipeline across every
   compound in a CSV library and writes ranked results.
4. HIT TRIAGE -- triage_screening_hits(ranked_results_csv_path,
   output_dir, min_kras_probability, min_admet_score, top_n). Filters
   batch-screening output down to Advance / Advance-with-review hits
   using: kras_probability_active >= 0.70, admet_score >= 0.60,
   toxicity_label = Low risk, inference_mode = trained_model (unless
   told otherwise).

## Scope
You operate over compounds under consideration as KRAS G12C, G12D,
or G12V inhibitor candidates (SOS1 as a pathway node, not yet a
separately trained target). Your job is candidate triage and virtual
screening -- not diagnosis, treatment guidance, or claims of
confirmed inhibition. You do not design, generate, or optimize novel
molecular structures; you evaluate and rank compounds that already
exist in the input.

## Reasoning requirements
- State which workflow(s) you're invoking and why, before acting.
- For a raw .smi file, run prepare_zinc_library before
  run_batch_screen. For a request to find hits (not just scores),
  run triage_screening_hits after run_batch_screen -- raw ranked
  scores are not a usable recommendation on their own.
- Every finding in a report is already labeled with its
  inference_mode (trained_model vs heuristic_fallback) -- always
  surface this, and treat heuristic-derived findings as lower
  confidence.
- When individual agent findings disagree (e.g. high target fit but
  a toxicity flag), surface that disagreement explicitly rather than
  letting the single overall_score hide it.

## Output requirements
- Every recommendation must be traceable: name the workflow(s)
  invoked and the concrete outputs (or, for large batches, summary
  statistics and file paths) that produced your conclusion.
- This system produces computational hit candidates for scientific
  review. It does not claim confirmed KRAS inhibition, does not
  perform docking or molecular dynamics, and does not replace
  medicinal chemistry review or experimental validation.
- If asked something outside compound triage/screening (general
  medical advice, clinical guidance, molecule generation/
  optimization, non-KRAS chemistry), say so and decline rather than
  answering outside your evaluated scope.
"""


# ---------------------------------------------------------------------------
# Tools -- thin, faithful wrappers around your existing pipeline entry
# points. None of these re-implement or bypass AgentOrchestrator.
# ---------------------------------------------------------------------------

@tool
def evaluate_candidate(smiles: str, name: str = "Candidate-1") -> dict:
    """Run the full 9-agent evaluation pipeline on a single SMILES
    string (validation, features, KRAS target fit, mutant
    selectivity, ADMET, toxicity, literature, manufacturability,
    clinical relevance). Returns the complete CandidateReport,
    including every agent's individual finding, score, and label, so
    you can reason about and explain each one.
    """
    logger.info("evaluate_candidate called | name=%s smiles=%s", name, smiles)
    candidate = MoleculeCandidate(smiles=smiles, name=name)
    reports = evaluate_candidates([candidate])
    result = reports[0].model_dump()
    logger.info(
        "evaluate_candidate result | compound=%s overall_score=%s recommendation=%s",
        result.get("compound"), result.get("overall_score"), result.get("recommendation"),
    )
    return result


@tool
def prepare_zinc_library(input_smi_path: str, output_csv_path: str, limit: int = 5000) -> dict:
    """Convert a raw ZINC .smi tranche file into the CSV format the
    batch screener expects (columns: compound, smiles, library,
    notes). Call this before run_batch_screen if the input is a raw
    .smi file rather than an already-prepared CSV. limit caps the
    number of compounds pulled (defaults to 5000, matching the
    original research screen).
    """
    logger.info(
        "prepare_zinc_library called | input=%s output=%s limit=%d",
        input_smi_path, output_csv_path, limit,
    )
    count = convert_zinc_smi_to_csv(
        input_path=Path(input_smi_path),
        output_path=Path(output_csv_path),
        limit=limit,
    )
    result = {"compounds_written": count, "output_csv_path": output_csv_path}
    logger.info("prepare_zinc_library result | %s", result)
    return result


@tool
def run_batch_screen(
    input_csv_path: str,
    output_dir: str,
    name_column: str = "compound",
    smiles_column: str = "smiles",
    top_n: int | None = None,
) -> dict:
    """Run the full 9-agent pipeline across every compound in a CSV
    library and write ranked results (ranked_screening_results.csv
    and agent_screening_reports.json) to output_dir. This is the
    batch equivalent of evaluate_candidate -- use this for libraries,
    not a loop of single-molecule calls. top_n optionally caps the
    number of top-ranked results written.
    """
    logger.info(
        "run_batch_screen called | input=%s output_dir=%s top_n=%s",
        input_csv_path, output_dir, top_n,
    )
    summary_rows, reports = run_batch_screening(
        input_path=Path(input_csv_path),
        output_dir=Path(output_dir),
        name_column=name_column,
        smiles_column=smiles_column,
        top_n=top_n,
    )
    result = {
        "compounds_scored": len(reports),
        "output_csv_path": str(Path(output_dir) / "ranked_screening_results.csv"),
        "output_json_path": str(Path(output_dir) / "agent_screening_reports.json"),
        "top_result_preview": summary_rows[:5],
    }
    logger.info(
        "run_batch_screen result | compounds_scored=%d output=%s",
        result["compounds_scored"], result["output_csv_path"],
    )
    return result


@tool
def triage_screening_hits(
    ranked_results_csv_path: str,
    output_dir: str,
    min_kras_probability: float = 0.70,
    min_admet_score: float = 0.60,
    top_n: int = 25,
    require_low_toxicity: bool = True,
    require_trained_model: bool = True,
) -> dict:
    """Filter a batch-screening run's ranked results down to the top
    hit candidates using the standard criteria (kras_probability_active
    >= 0.70, admet_score >= 0.60, toxicity_label = Low risk,
    inference_mode = trained_model, recommendation in {Advance,
    Advance with review}) unless told to relax them. Always call this
    after run_batch_screen -- raw ranked scores are not a usable
    output on their own.
    """
    logger.info(
        "triage_screening_hits called | input=%s min_kras_probability=%.2f min_admet_score=%.2f top_n=%d",
        ranked_results_csv_path, min_kras_probability, min_admet_score, top_n,
    )
    hits, summary = _triage_hits(
        input_path=Path(ranked_results_csv_path),
        output_dir=Path(output_dir),
        min_kras_probability=min_kras_probability,
        min_admet_score=min_admet_score,
        top_n=top_n,
        require_low_toxicity=require_low_toxicity,
        require_trained_model=require_trained_model,
    )
    result = {"summary": summary, "hits": hits}
    logger.info(
        "triage_screening_hits result | total_screened=%s total_hit_candidates=%s reported_top_n=%s",
        summary.get("total_screened"), summary.get("total_hit_candidates"), summary.get("reported_top_n"),
    )
    return result


# ---------------------------------------------------------------------------
# Agent assembly
# ---------------------------------------------------------------------------

def build_agent(model_id: str = "us.amazon.nova-lite-v1:0",
                 region: str = "us-east-1") -> Agent:
    """Build the KRAS triage + virtual screening orchestration agent.

    Defaults to Nova Lite on Bedrock -- unlike Anthropic models, Nova
    does not require submitting a "use case details" form before a
    new AWS account can invoke it, so this avoids the
    ResourceNotFoundException new accounts hit on first Claude call.
    Swap back to a Claude model id (e.g.
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0") once that form is
    submitted and access clears, if you prefer Claude's reasoning.
    """
    model = BedrockModel(model_id=model_id, region_name=region)

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            evaluate_candidate,
            prepare_zinc_library,
            run_batch_screen,
            triage_screening_hits,
        ],
    )
    return agent


if __name__ == "__main__":
    agent = build_agent()

    # --- Smoke test 1: single-molecule mode, known-inhibitor positive control ---
    sotorasib_smiles = "CC1=C2CN(C(=O)C3=C(N=CC=N3)NC4=C(C=CC(=C4)N5CCN(CC5)C)OC)CCN2C6=C1C(=NC=N6)N7CCCC7C(=O)N"

    single_response = agent(
        f"Evaluate this candidate as a KRAS G12C inhibitor: {sotorasib_smiles}. "
        f"Walk through what the pipeline found for each agent, then give a "
        f"final recommendation with confidence level."
    )
    print("=== Single-molecule mode ===")
    print(single_response)

    # --- Smoke test 2: batch/virtual screening mode ---
    # Adjust this path to an actual prepared library CSV on disk before running,
    # e.g. data/external/example_screening_library.csv from your repo.
    screen_response = agent(
        "Screen the compound library at data/external/example_screening_library.csv "
        "against KRAS, then triage it down to the real hits, and give me your reasoning."
    )
    print("\n=== Virtual screening mode ===")
    print(screen_response)
