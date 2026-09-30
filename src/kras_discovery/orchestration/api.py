"""
api.py

FastAPI wrapper exposing the KRAS agentic pipeline over HTTP, for
deployment as a containerized service (e.g. AWS App Runner).

Two endpoints on purpose, at two different trust/latency levels:

    GET  /health    -> liveness check. No Bedrock call, no model load.
                        Used by App Runner's health check.
    POST /evaluate   -> direct call into the real 9-agent pipeline
                        (evaluate_candidates). No LLM involved.
                        Deterministic, fast, cheap.
    POST /chat       -> natural-language request routed through the
                        Strands agent (build_agent), which calls
                        Bedrock (Nova Lite) and decides which
                        pipeline tool(s) to invoke. Slower, costs a
                        Bedrock invocation, but is the actual
                        "agentic" entry point.

Run locally:
    uvicorn kras_discovery.orchestration.api:app --host 0.0.0.0 --port 8000

Both endpoints wrap the exact same pipeline code used by the CLI and
by kras_strands_agent.py -- nothing scientific is reimplemented here.
"""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from kras_discovery.models.schemas import MoleculeCandidate
from kras_discovery.pipelines.screening import evaluate_candidates
from kras_discovery.orchestration.kras_strands_agent import build_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kras_agent_api")

app = FastAPI(
    title="KRAS Agentic AI Discovery API",
    description=(
        "LLM-orchestrated KRAS inhibitor candidate evaluation, backed by a "
        "9-agent rule-based pipeline and a trained Random Forest classifier "
        "(ROC-AUC 0.980 molecule-grouped / 0.938 scaffold-split)."
    ),
    version="0.1.0",
)

# Built lazily on first /chat call so /health (and container startup /
# App Runner health checks) never require a Bedrock round trip.
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        logger.info("Building Strands agent on first /chat call")
        _agent = build_agent()
    return _agent


class EvaluateRequest(BaseModel):
    smiles: str
    name: str = "Candidate-1"


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    """Direct pipeline call, no LLM. Runs all 9 agents on one SMILES."""
    logger.info("evaluate called | name=%s smiles=%s", req.name, req.smiles)
    try:
        candidate = MoleculeCandidate(smiles=req.smiles, name=req.name)
        reports = evaluate_candidates([candidate])
        result = reports[0].model_dump()
        logger.info(
            "evaluate result | compound=%s overall_score=%s recommendation=%s",
            result.get("compound"), result.get("overall_score"), result.get("recommendation"),
        )
        return result
    except Exception as exc:
        logger.exception("evaluate failed")
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/chat")
def chat(req: ChatRequest):
    """Natural-language request, routed through the Bedrock-backed Strands agent."""
    logger.info("chat called | message=%s", req.message)
    try:
        agent = get_agent()
        response = agent(req.message)
        return {"response": str(response)}
    except Exception as exc:
        logger.exception("chat failed")
        raise HTTPException(status_code=502, detail=str(exc))
