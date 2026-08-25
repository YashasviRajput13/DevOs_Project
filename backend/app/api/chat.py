"""
chat.py  — API  (updated)
==========================
POST /api/chat

Detects overview/architecture intent and routes to appropriate context.
Existing RAG behaviour for normal code questions is unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.architecture import ArchitectureService
from app.services.llm import LLMService
from app.services.overview import RepositoryOverviewService
from app.services.search import CodeSearchService

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# ── Intent signals ─────────────────────────────────────────────────────────

_OVERVIEW_SIGNALS = [
    "what is this project", "explain this project", "give me an overview",
    "project overview", "what does this repo", "project summary",
    "codebase overview", "tell me about this project", "what is this codebase",
    "overview of this", "summarize this",
]

_ARCHITECTURE_SIGNALS = [
    "architecture", "dependency", "dependencies", "depends on", "depend on",
    "what calls", "who calls", "components", "what files", "which files",
    "how does the api", "how does the backend", "service layer",
    "database model", "what are the main", "folder structure",
    "project structure", "how is the project structured",
]


def _detect_intent(query: str) -> str:
    q = query.lower()
    if any(s in q for s in _OVERVIEW_SIGNALS):
        return "overview"
    if any(s in q for s in _ARCHITECTURE_SIGNALS):
        return "architecture"
    return "rag"


# ── Request model ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)
    # Optional repository scoping (enables overview/architecture answers)
    project_id: int | None = None
    repository_id: int | None = None


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    intent = _detect_intent(data.query)

    # ── Overview intent ────────────────────────────────────────────────────
    if intent == "overview" and data.project_id and data.repository_id:
        svc = RepositoryOverviewService(db)
        try:
            overview = svc.get_overview(data.project_id, data.repository_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        context = svc.build_llm_context(overview)
        # Augment with semantic chunks
        search_svc = CodeSearchService(db)
        chunks = search_svc.search(
            query="project structure overview main entry point",
            limit=4,
        )
        if chunks:
            context += "\n\nSample code context:\n"
            for c in chunks:
                context += (
                    f"\nFile: {c.get('file_path')} "
                    f"Lines {c.get('start_line')}-{c.get('end_line')}\n"
                    f"{c.get('content','')[:300]}\n---"
                )
        else:
            context += "\n\n(No specific code snippets found)"

        llm = LLMService()
        try:
            answer = llm.generate_overview(query=data.query, context=context)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")

        sources = _build_sources(chunks)
        return {"query": data.query, "intent": "overview", "answer": answer, "sources": sources}

    # ── Architecture intent ────────────────────────────────────────────────
    if intent == "architecture" and data.project_id and data.repository_id:
        arch_svc = ArchitectureService(db)
        try:
            arch = arch_svc.get_architecture(data.project_id, data.repository_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        arch_context = arch_svc.build_llm_context(arch)
        search_svc = CodeSearchService(db)
        chunks = search_svc.search(query=data.query, limit=data.limit)
        if chunks:
            semantic_ctx = _format_chunk_context(chunks)
            context = arch_context + "\n\n" + semantic_ctx
        else:
            context = arch_context

        llm = LLMService()
        try:
            answer = llm.generate_architecture(query=data.query, context=context)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")

        sources = _build_sources(chunks)
        return {"query": data.query, "intent": "architecture", "answer": answer, "sources": sources}

    # ── Standard RAG (unchanged behaviour) ────────────────────────────────
    search_svc = CodeSearchService(db)
    results = search_svc.search(query=data.query, limit=data.limit)

    # Deduplicate by file + line range
    seen: set = set()
    unique_results = []
    for r in results:
        key = (r.get("file_id"), r.get("start_line"), r.get("end_line"))
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    if not unique_results:
        return {
            "query": data.query,
            "intent": "rag",
            "answer": "No relevant code was found in this repository.",
            "sources": [],
        }

    context = _format_chunk_context(unique_results)

    llm = LLMService()
    try:
        answer = llm.generate(question=data.query, context=context)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")

    sources = _build_sources(unique_results)
    return {
        "query": data.query,
        "intent": "rag",
        "answer": answer,
        "sources": sources,
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def _format_chunk_context(results: list[dict]) -> str:
    parts = []
    for r in results:
        parts.append(
            f"Repository: {r.get('repository_full_name') or 'N/A'}\n"
            f"GitHub URL: {r.get('repository_url') or 'N/A'}\n"
            f"File: {r.get('file_path') or 'N/A'}\n"
            f"Language: {r.get('language') or 'N/A'}\n"
            f"Lines: {r.get('start_line')}-{r.get('end_line')}\n"
            f"Similarity: {r.get('score', 0):.2f}\n\n"
            f"Code:\n{r.get('content', '')}\n---"
        )
    return "\n\n".join(parts)


def _build_sources(results: list[dict]) -> list[dict]:
    seen: set = set()
    sources = []
    for r in results:
        key = (r.get("file_path"), r.get("start_line"))
        if key not in seen:
            seen.add(key)
            sources.append({
                "file_id": r.get("file_id"),
                "repository_name": r.get("repository_name"),
                "repository_full_name": r.get("repository_full_name"),
                "repository_url": r.get("repository_url"),
                "file_path": r.get("file_path"),
                "file_name": r.get("file_name"),
                "language": r.get("language"),
                "start_line": r.get("start_line"),
                "end_line": r.get("end_line"),
                "score": r.get("score"),
            })
    return sources