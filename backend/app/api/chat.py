"""
chat.py  — API
==========================
POST /api/chat

Detects overview/architecture intent and routes to appropriate context.
Existing RAG behaviour for normal code questions is unchanged.

Embed-on-demand: the SentenceTransformer model is only loaded if the
caller provides a scoped repository (project_id + repository_id that are
non-zero) OR if real code chunks exist in the database.  A plain
"Hello" / test query with project_id=0 / repository_id=0 goes straight
to the LLM without touching the embedding model.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.architecture import ArchitectureService
from app.services.llm import LLMService
from app.services.overview import RepositoryOverviewService

logger = logging.getLogger(__name__)

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
    provider: str = Field(default="devos_auto")
    conversation_id: int | None = None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _has_repo_context(data: ChatRequest) -> bool:
    """Return True only when the caller provides a real (non-zero) repo scope."""
    return bool(data.project_id) and bool(data.repository_id)


def _search_chunks(db: Session, query: str, limit: int) -> list[dict]:
    """
    Run semantic search.  Imports EmbeddingService lazily so the
    SentenceTransformer model is never loaded unless this function is
    actually called.  Returns an empty list on any error.
    """
    try:
        from app.services.search import CodeSearchService  # noqa: PLC0415
        svc = CodeSearchService(db)
        return svc.search(query=query, limit=limit)
    except MemoryError:
        logger.error("OOM during embedding search — returning empty results.")
        return []
    except Exception as exc:
        logger.warning("Embedding search failed (%s) — returning empty results.", exc)
        return []


# ── Endpoint ───────────────────────────────────────────────────────────────
from app.models.user import User, RoleEnum
from app.services.auth import get_current_user, verify_project_access

@router.post("")
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if _has_repo_context(data):
        verify_project_access(db, current_user.id, data.project_id)
        
    logger.info(
        "chat: request received — query=%r project_id=%s repository_id=%s",
        data.query[:80],
        data.project_id,
        data.repository_id,
    )

    intent = _detect_intent(data.query)
    has_repo = _has_repo_context(data)

    # ── Overview intent ─────────────────────────────────────────────────────
    if intent == "overview" and has_repo:
        logger.info("chat: dispatching to overview path")
        logger.info("chat: database operation started (overview)")
        svc = RepositoryOverviewService(db)
        try:
            overview = svc.get_overview(data.project_id, data.repository_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        context = svc.build_llm_context(overview)
        logger.info("chat: database operation completed (overview)")

        # Augment with semantic chunks (only if model is available)
        chunks = _search_chunks(db, "project structure overview main entry point", 4)
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

        logger.info("chat: LLM request started (overview)")
        try:
            llm = LLMService(provider=data.provider)
            answer = llm.generate_overview(query=data.query, context=context)
        except Exception as exc:
            logger.error("chat: LLM request failed — %s", exc)
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")

        logger.info("chat: LLM response received (overview)")
        sources = _build_sources(chunks)
        logger.info("chat: request completed (overview)")
        return _save_and_return_chat(db, current_user, data, {
            "query": data.query, "intent": "overview", "answer": answer, "sources": sources
        })

    # ── Architecture intent ─────────────────────────────────────────────────
    if intent == "architecture" and has_repo:
        logger.info("chat: dispatching to architecture path")
        logger.info("chat: database operation started (architecture)")
        arch_svc = ArchitectureService(db)
        try:
            arch = arch_svc.get_architecture(data.project_id, data.repository_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        arch_context = arch_svc.build_llm_context(arch)
        logger.info("chat: database operation completed (architecture)")

        chunks = _search_chunks(db, data.query, data.limit)
        if chunks:
            semantic_ctx = _format_chunk_context(chunks)
            context = arch_context + "\n\n" + semantic_ctx
        else:
            context = arch_context

        logger.info("chat: LLM request started (architecture)")
        try:
            llm = LLMService(provider=data.provider)
            answer = llm.generate_architecture(query=data.query, context=context)
        except Exception as exc:
            logger.error("chat: LLM request failed — %s", exc)
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")

        logger.info("chat: LLM response received (architecture)")
        sources = _build_sources(chunks)
        logger.info("chat: request completed (architecture)")
        return _save_and_return_chat(db, current_user, data, {
            "query": data.query, "intent": "architecture", "answer": answer, "sources": sources
        })

    # ── Standard RAG path ───────────────────────────────────────────────────
    #
    # Only perform embedding-based search when a real repository is scoped.
    # Without a repository scope (project_id=0 / None) there are no chunks
    # to search, so we skip the model load and answer directly with the LLM.
    #
    if has_repo:
        logger.info("chat: database operation started (RAG search)")
        results = _search_chunks(db, data.query, data.limit)
        logger.info(
            "chat: database operation completed (RAG search, %d chunks)", len(results)
        )

        # Deduplicate by file + line range
        seen: set = set()
        unique_results = []
        for r in results:
            key = (r.get("file_id"), r.get("start_line"), r.get("end_line"))
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
    else:
        # No repository scoped — skip embedding entirely
        logger.info(
            "chat: no repository scope — skipping embedding search, answering directly"
        )
        unique_results = []

    if not unique_results:
        # No chunks — answer the question without code context.
        context = (
            "(No repository code has been indexed or no repository was selected. "
            "Answer based on general software engineering knowledge where possible.)"
        )
        logger.info("chat: LLM request started (no-context path)")
        try:
            llm = LLMService(provider=data.provider)
            answer = llm.generate(question=data.query, context=context)
        except Exception as exc:
            logger.error("chat: LLM request failed — %s", exc)
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")
        logger.info("chat: LLM response received (no-context path)")
        logger.info("chat: request completed (no-context path)")
        return _save_and_return_chat(db, current_user, data, {
            "query": data.query,
            "intent": "rag",
            "answer": answer,
            "sources": [],
        })

    context = _format_chunk_context(unique_results)

    logger.info("chat: LLM request started (RAG path)")
    try:
        llm = LLMService(provider=data.provider)
        answer = llm.generate(question=data.query, context=context)
    except Exception as exc:
        logger.error("chat: LLM request failed — %s", exc)
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {exc}")

    logger.info("chat: LLM response received (RAG path)")
    sources = _build_sources(unique_results)
    logger.info("chat: request completed (RAG path)")
    
    # === Save to Conversation History (Final Wrapper) ===
    # For any intent (we just put it here since it's the common exit point for most, wait!
    # Overview and Architecture exit early. We need to save those too.
    # We should actually wrap all return calls. Let's write a helper and call it.)
    #
    # Instead of refactoring all distinct returns, I will inject the DB logic directly before returning.
    ans_data = {
        "query": data.query,
        "intent": "rag",
        "answer": answer,
        "sources": sources,
    }
    
    return _save_and_return_chat(db, current_user, data, ans_data)

from app.models.chat import Conversation, Message

def _save_and_return_chat(db: Session, user: User, req: ChatRequest, result: dict):
    if not req.project_id:
        return result
        
    conv_id = req.conversation_id
    if not conv_id:
        conv = Conversation(
            user_id=user.id,
            project_id=req.project_id,
            repository_id=req.repository_id,
            title=req.query[:50] + "..." if len(req.query) > 50 else req.query
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id
        
    db.add(Message(
        conversation_id=conv_id,
        role="user",
        content=req.query,
        context_files=None
    ))
    db.commit()
    
    db.add(Message(
        conversation_id=conv_id,
        role="assistant",
        content=result["answer"],
        context_files=result.get("sources")
    ))
    db.commit()
    
    result["conversation_id"] = conv_id
    return result

@router.get("/conversations")
def list_conversations(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(db, current_user.id, project_id)
    convs = db.query(Conversation).filter(Conversation.project_id == project_id, Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc()).all()
    return [{
        "id": c.id, "title": c.title, "repository_id": c.repository_id, "updated_at": c.updated_at.isoformat()
    } for c in convs]


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()
    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": m.context_files,
            "created_at": m.created_at.isoformat()
        } for m in msgs]
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