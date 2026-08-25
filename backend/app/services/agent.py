"""
agent.py  (service)
===================
DeveloperAgent — the core of DevOs Intelligence.

Capabilities
------------
* ANALYZE_CODE   – explain what a piece of code does
* DEBUG          – identify why something might fail
* EXPLAIN        – explain a concept/flow from the repo
* FIND_BUGS      – static analysis for potential issues
* IMPROVE_CODE   – suggest improvements
* PLAN_CHANGE    – generate a safe, structured change plan
* ARCHITECTURE   – answer dependency/architecture questions
* OVERVIEW       – answer "what is this project?" questions

Intent detection uses deterministic keyword rules first.
The LLM is used only for the actual analysis — never for intent routing.

Safety
------
* Never executes repository code.
* Never modifies files (read-only service).
* Never returns secrets found in content.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.file import File
from app.models.repository import Repository
from app.services.architecture import ArchitectureService
from app.services.llm import LLMService
from app.services.overview import RepositoryOverviewService
from app.services.search import CodeSearchService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

_OVERVIEW_SIGNALS = [
    "what is this project", "explain this project", "give me an overview",
    "project overview", "what does this repo do", "what does this repository do",
    "project summary", "codebase overview", "tell me about this project",
    "what is this codebase",
]

_ARCHITECTURE_SIGNALS = [
    "architecture", "dependency", "dependencies", "depends on", "depend on",
    "what calls", "who calls", "flow", "how does", "component", "components",
    "what files", "which files", "structure", "how is the project structured",
    "main components", "backend structure", "service layer",
]

_DEBUG_SIGNALS = [
    "bug", "error", "exception", "fail", "crash", "500", "traceback",
    "why does", "why is", "not working", "broken", "issue", "wrong",
    "returns null", "returns none", "undefined", "fix",
]

_FIND_BUGS_SIGNALS = [
    "find bugs", "find issues", "find problems", "code review",
    "potential bugs", "security", "vulnerability", "vulnerabilities",
    "smell", "code smell", "review",
]

_IMPROVE_SIGNALS = [
    "improve", "optimize", "refactor", "better", "cleaner", "faster",
    "performance", "suggestion", "suggest",
]

_PLAN_SIGNALS = [
    "add", "implement", "create", "build", "integrate", "how should i",
    "how do i", "plan", "change plan", "modification", "modify",
]

_EXPLAIN_SIGNALS = [
    "explain", "how does", "what is", "describe", "walk me through",
    "what happens when", "what does",
]

_ANALYZE_SIGNALS = [
    "analyze", "analyse", "look at", "check",
]


def classify_intent(query: str) -> str:
    """
    Deterministic intent classification based on keyword matching.
    Returns one of: OVERVIEW | ARCHITECTURE | DEBUG | FIND_BUGS |
                    IMPROVE_CODE | PLAN_CHANGE | EXPLAIN | ANALYZE_CODE
    """
    q = query.lower()

    # Priority order matters — more specific signals first
    if any(s in q for s in _OVERVIEW_SIGNALS):
        return "OVERVIEW"
    if any(s in q for s in _FIND_BUGS_SIGNALS):
        return "FIND_BUGS"
    if any(s in q for s in _DEBUG_SIGNALS):
        return "DEBUG"
    if any(s in q for s in _ARCHITECTURE_SIGNALS):
        return "ARCHITECTURE"
    if any(s in q for s in _IMPROVE_SIGNALS):
        return "IMPROVE_CODE"
    if any(s in q for s in _PLAN_SIGNALS):
        return "PLAN_CHANGE"
    if any(s in q for s in _EXPLAIN_SIGNALS):
        return "EXPLAIN"
    if any(s in q for s in _ANALYZE_SIGNALS):
        return "ANALYZE_CODE"

    return "EXPLAIN"   # safe default


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class DeveloperAgent:
    """
    Orchestrates context retrieval and LLM calls for repository analysis.
    READ-ONLY — this class never modifies files.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.search = CodeSearchService(db)
        self.llm = LLMService()
        self.overview_svc = RepositoryOverviewService(db)
        self.arch_svc = ArchitectureService(db)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        project_id: int,
        repository_id: int,
        query: str,
        limit: int = 8,
    ) -> dict[str, Any]:
        """
        Analyze a query against a repository and return structured findings.
        """
        intent = classify_intent(query)
        logger.info("Agent intent for query %r: %s", query[:80], intent)

        repo = (
            self.db.query(Repository)
            .filter(
                Repository.id == repository_id,
                Repository.project_id == project_id,
            )
            .first()
        )
        if not repo:
            return self._error("Repository not found.", intent)

        files: list[File] = (
            self.db.query(File)
            .filter(File.repository_id == repository_id)
            .all()
        )
        if not files:
            return self._error("Repository has not been indexed yet.", intent)

        try:
            if intent == "OVERVIEW":
                return self._handle_overview(project_id, repository_id, query, repo)

            if intent == "ARCHITECTURE":
                return self._handle_architecture(project_id, repository_id, query, repo)

            if intent == "FIND_BUGS":
                return self._handle_find_bugs(repository_id, query, repo, files, limit)

            if intent == "PLAN_CHANGE":
                return self._handle_plan_change(repository_id, query, repo, files, limit)

            # For DEBUG, IMPROVE_CODE, EXPLAIN, ANALYZE_CODE — use RAG
            return self._handle_rag(intent, repository_id, query, repo, limit)

        except Exception as exc:
            logger.exception("Agent error for intent %s", intent)
            return self._error(f"Analysis failed: {exc}", intent)

    # ------------------------------------------------------------------
    # Intent handlers
    # ------------------------------------------------------------------

    def _handle_overview(
        self, project_id: int, repository_id: int, query: str, repo: Repository
    ) -> dict[str, Any]:
        try:
            overview = self.overview_svc.get_overview(project_id, repository_id)
        except ValueError as exc:
            return self._error(str(exc), "OVERVIEW")

        context = self.overview_svc.build_llm_context(overview)
        # Also pull representative semantic chunks for richer answer
        chunks = self._get_representative_chunks(repository_id, limit=6)
        if chunks:
            context += "\n\nSample indexed code context:\n" + self._format_chunks(chunks)

        answer = self.llm.generate_overview(query=query, context=context)
        sources = self._chunks_to_sources(chunks)

        return {
            "query": query,
            "intent": "OVERVIEW",
            "analysis": answer,
            "findings": [],
            "recommendations": [],
            "sources": sources,
            "overview": overview,
        }

    def _handle_architecture(
        self, project_id: int, repository_id: int, query: str, repo: Repository
    ) -> dict[str, Any]:
        try:
            arch = self.arch_svc.get_architecture(project_id, repository_id)
        except ValueError as exc:
            return self._error(str(exc), "ARCHITECTURE")

        arch_context = self.arch_svc.build_llm_context(arch)

        # Also get semantically relevant chunks
        chunks = self.search.search(query=query, limit=6)
        semantic_context = self._format_chunks(chunks)

        context = arch_context + "\n\n" + semantic_context
        answer = self.llm.generate_architecture(query=query, context=context)

        sources = self._chunks_to_sources(chunks)
        # Add architecture file sources
        seen_paths = {s["file_path"] for s in sources}
        for f_info in arch["files"][:5]:
            if f_info["path"] not in seen_paths:
                sources.append({
                    "file_path": f_info["path"],
                    "language": f_info["language"],
                    "start_line": None,
                    "end_line": None,
                    "score": None,
                    "repository_full_name": repo.full_name,
                    "repository_url": repo.url,
                })

        return {
            "query": query,
            "intent": "ARCHITECTURE",
            "analysis": answer,
            "findings": [],
            "recommendations": [],
            "sources": sources,
            "architecture": arch,
        }

    def _handle_find_bugs(
        self,
        repository_id: int,
        query: str,
        repo: Repository,
        files: list[File],
        limit: int,
    ) -> dict[str, Any]:
        chunks = self.search.search(query=query, limit=limit)
        context = self._format_chunks(chunks)
        answer = self.llm.generate_bug_analysis(query=query, context=context)
        findings = self._extract_findings_from_answer(answer, chunks)

        return {
            "query": query,
            "intent": "FIND_BUGS",
            "analysis": answer,
            "findings": findings,
            "recommendations": self._extract_recommendations(answer),
            "sources": self._chunks_to_sources(chunks),
        }

    def _handle_plan_change(
        self,
        repository_id: int,
        query: str,
        repo: Repository,
        files: list[File],
        limit: int,
    ) -> dict[str, Any]:
        chunks = self.search.search(query=query, limit=limit)
        arch_context = ""
        try:
            arch = self.arch_svc.get_architecture(
                project_id=repo.project_id, repository_id=repository_id
            )
            arch_context = self.arch_svc.build_llm_context(arch)
        except Exception:
            pass

        context = arch_context + "\n\n" + self._format_chunks(chunks)
        answer = self.llm.generate_change_plan(query=query, context=context)

        import json
        try:
            plan_data = json.loads(answer)
        except Exception:
            plan_data = {"summary": "Error parsing plan JSON.", "changes": []}

        plan_steps = []
        for i, chg in enumerate(plan_data.get("changes", []), 1):
            fp = chg.get("file")
            plan_steps.append({
                "step": i,
                "file": fp,
                "start_line": chg.get("start_line"),
                "end_line": chg.get("end_line"),
                "proposed_change": chg.get("proposed_change", ""),
                "reason": chg.get("reason", "Identified from repository evidence."),
            })

        summary_text = plan_data.get("summary", "No changes suggested or insufficient context.")

        return {
            "query": query,
            "intent": "PLAN_CHANGE",
            "analysis": summary_text,
            "findings": [],
            "recommendations": plan_steps,
            "sources": self._chunks_to_sources(chunks),
            "plan": {
                "summary": summary_text,
                "steps": plan_steps,
                "risks": [],
                "tests": self._suggest_tests(files),
            },
        }

    def _handle_rag(
        self,
        intent: str,
        repository_id: int,
        query: str,
        repo: Repository,
        limit: int,
    ) -> dict[str, Any]:
        """
        General RAG pipeline for DEBUG, IMPROVE_CODE, EXPLAIN, ANALYZE_CODE.
        """
        chunks = self.search.search(query=query, limit=limit)
        context = self._format_chunks(chunks)
        answer = self.llm.generate_agent(intent=intent, query=query, context=context)

        return {
            "query": query,
            "intent": intent,
            "analysis": answer,
            "findings": [],
            "recommendations": [],
            "sources": self._chunks_to_sources(chunks),
        }

    # ------------------------------------------------------------------
    # Helper: representative code chunks (diverse files)
    # ------------------------------------------------------------------

    def _get_representative_chunks(
        self, repository_id: int, limit: int = 8
    ) -> list[dict]:
        """
        Return chunks that cover diverse files — entry points, configs, services.
        Uses semantic search with a broad "project overview" query, then
        deduplicates by file so no single file dominates.
        """
        candidates = self.search.search(
            query="project main entry point architecture overview services models",
            limit=30,
        )
        # Filter to this repository
        repo_chunks = [c for c in candidates if c.get("repository_id") == repository_id]

        # Deduplicate: keep best chunk per file
        seen_files: dict[int, dict] = {}
        for chunk in sorted(repo_chunks, key=lambda x: x["score"], reverse=True):
            fid = chunk.get("file_id")
            if fid and fid not in seen_files:
                seen_files[fid] = chunk
            if len(seen_files) >= limit:
                break

        return list(seen_files.values())

    # ------------------------------------------------------------------
    # Helper: format chunk list into LLM context
    # ------------------------------------------------------------------

    @staticmethod
    def _format_chunks(chunks: list[dict]) -> str:
        parts = []
        for chunk in chunks:
            parts.append(
                f"File: {chunk.get('file_path') or 'N/A'}\n"
                f"Language: {chunk.get('language') or 'N/A'}\n"
                f"Lines: {chunk.get('start_line')}-{chunk.get('end_line')}\n"
                f"Relevance: {chunk.get('score', 0):.2f}\n\n"
                f"{chunk.get('content', '')}\n---"
            )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Helper: sources list
    # ------------------------------------------------------------------

    @staticmethod
    def _chunks_to_sources(chunks: list[dict]) -> list[dict]:
        seen: set[tuple] = set()
        sources = []
        for c in chunks:
            key = (c.get("file_path"), c.get("start_line"))
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file_id": c.get("file_id"),
                    "repository_name": c.get("repository_name"),
                    "repository_full_name": c.get("repository_full_name"),
                    "repository_url": c.get("repository_url"),
                    "file_path": c.get("file_path"),
                    "file_name": c.get("file_name"),
                    "language": c.get("language"),
                    "start_line": c.get("start_line"),
                    "end_line": c.get("end_line"),
                    "score": c.get("score"),
                })
        return sources

    # ------------------------------------------------------------------
    # Helper: extract file paths mentioned in LLM output
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_file_mentions(
        text: str, file_path_map: dict[str, File]
    ) -> list[str]:
        """Return actual repository file paths mentioned in the LLM text."""
        found = []
        for path in file_path_map:
            # Match the path or just the filename
            filename = path.split("/")[-1]
            if path in text or filename in text:
                if path not in found:
                    found.append(path)
        return found[:10]

    # ------------------------------------------------------------------
    # Helper: suggest relevant test files
    # ------------------------------------------------------------------

    @staticmethod
    def _suggest_tests(files: list[File]) -> list[str]:
        test_files = [
            f.path for f in files
            if "test" in f.path.lower() or f.name.startswith("test_")
        ]
        return test_files[:5]

    # ------------------------------------------------------------------
    # Helper: very lightweight finding extraction (heuristic)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_findings_from_answer(answer: str, chunks: list[dict]) -> list[dict]:
        """
        Attach the most relevant chunk as evidence for each finding-like sentence.
        This is best-effort — the full LLM analysis is always the primary output.
        """
        findings = []
        # Look for sentences that sound like findings
        lines = [line.strip() for line in answer.split("\n") if line.strip()]
        severity_map = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}
        for line in lines:
            lower = line.lower()
            sev = "medium"  # default
            for word, level in severity_map.items():
                if word in lower:
                    sev = level
                    break
            if any(kw in lower for kw in ("bug", "issue", "problem", "risk", "insecure", "missing")):
                source = chunks[0] if chunks else {}
                findings.append({
                    "severity": sev,
                    "title": line[:100],
                    "description": line,
                    "file_path": source.get("file_path"),
                    "start_line": source.get("start_line"),
                    "end_line": source.get("end_line"),
                    "evidence": source.get("content", "")[:200],
                    "recommendation": "See full analysis above.",
                })
                if len(findings) >= 8:
                    break
        return findings

    @staticmethod
    def _extract_recommendations(answer: str) -> list[str]:
        recs = []
        for line in answer.split("\n"):
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "• ")) and len(stripped) > 10:
                recs.append(stripped.lstrip("-*• "))
        return recs[:10]

    @staticmethod
    def _error(message: str, intent: str) -> dict[str, Any]:
        return {
            "query": "",
            "intent": intent,
            "analysis": message,
            "findings": [],
            "recommendations": [],
            "sources": [],
            "error": message,
        }
