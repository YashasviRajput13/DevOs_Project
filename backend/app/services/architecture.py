"""
architecture.py
===============
Builds a structured architecture map from indexed repository files and
CodeDependency records stored in PostgreSQL.

The analysis runs statically on file content stored in the DB —
no repository code is ever executed.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models.dependency import CodeDependency
from app.models.file import File
from app.models.repository import Repository
from app.services.code_analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)


class ArchitectureService:
    """Builds a full architecture map for a repository."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.analyzer = CodeAnalyzer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_architecture(self, project_id: int, repository_id: int) -> dict[str, Any]:
        """Return structured architecture data or raise ValueError."""

        repo = (
            self.db.query(Repository)
            .filter(
                Repository.id == repository_id,
                Repository.project_id == project_id,
            )
            .first()
        )
        if not repo:
            raise ValueError("repository_not_found")

        files: list[File] = (
            self.db.query(File)
            .filter(File.repository_id == repository_id)
            .all()
        )
        if not files:
            raise ValueError("repository_not_indexed")

        deps: list[CodeDependency] = (
            self.db.query(CodeDependency)
            .filter(CodeDependency.repository_id == repository_id)
            .all()
        )

        # Build file_id → path index
        file_map: dict[int, File] = {f.id: f for f in files}

        # Re-analyze files on demand (fast — content already in DB)
        analyses = {}
        components: list[dict] = []
        api_routes: list[dict] = []
        db_models: list[dict] = []
        service_classes: list[dict] = []

        for f in files:
            if not f.content:
                continue
            analysis = self.analyzer.analyze(f.path, f.content, f.language)
            analyses[f.id] = analysis

            for cls in analysis.classes:
                entry: dict[str, Any] = {
                    "file_path": f.path,
                    "file_id": f.id,
                    "name": cls.name,
                    "start_line": cls.start_line,
                    "end_line": cls.end_line,
                    "bases": cls.bases,
                    "methods": cls.methods,
                }
                components.append(entry)
                if cls.name in analysis.service_classes:
                    service_classes.append(entry)

            for route in analysis.routes:
                api_routes.append({
                    "file_path": f.path,
                    "file_id": f.id,
                    "method": route.method,
                    "path": route.path,
                    "handler": route.handler,
                    "line": route.line,
                })

            for model_name in analysis.db_models:
                db_models.append({
                    "file_path": f.path,
                    "file_id": f.id,
                    "name": model_name,
                })

        # Build dependency list
        dep_list: list[dict] = []
        for dep in deps:
            src_path = file_map[dep.source_file_id].path if dep.source_file_id in file_map else None
            tgt_path = file_map[dep.target_file_id].path if dep.target_file_id and dep.target_file_id in file_map else None
            dep_list.append({
                "id": dep.id,
                "source_file": src_path,
                "target_file": tgt_path,
                "target_module": dep.target_module,
                "dependency_type": dep.dependency_type,
                "symbol_name": dep.symbol_name,
                "line_number": dep.line_number,
            })

        # Summarise files with their detected structure
        file_summaries: list[dict] = []
        for f in files:
            a = analyses.get(f.id)
            file_summaries.append({
                "id": f.id,
                "path": f.path,
                "language": f.language,
                "classes": [c["name"] for c in components if c["file_id"] == f.id],
                "routes": len([r for r in api_routes if r["file_id"] == f.id]),
                "import_count": len(a.imports) if a else 0,
            })

        return {
            "repository": {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.url,
            },
            "components": components,
            "files": file_summaries,
            "dependencies": dep_list,
            "api_routes": api_routes,
            "models": db_models,
            "services": service_classes,
        }

    def build_llm_context(self, architecture: dict[str, Any], max_items: int = 15) -> str:
        """Convert architecture data into a compact text block for LLM prompts."""
        repo = architecture["repository"]
        lines = [
            f"=== Architecture: {repo['full_name']} ===",
            f"URL: {repo['url']}",
            "",
        ]

        if architecture["api_routes"]:
            lines.append("API Routes:")
            for r in architecture["api_routes"][:max_items]:
                lines.append(
                    f"  {r['method']} {r['path']} → {r['handler']} "
                    f"[{r['file_path']}:{r['line']}]"
                )

        if architecture["models"]:
            lines.append("\nDatabase Models:")
            for m in architecture["models"][:max_items]:
                lines.append(f"  {m['name']} [{m['file_path']}]")

        if architecture["services"]:
            lines.append("\nService Classes:")
            for s in architecture["services"][:max_items]:
                lines.append(
                    f"  {s['name']} [{s['file_path']}:{s['start_line']}-{s['end_line']}]"
                )

        if architecture["dependencies"]:
            lines.append("\nKey Dependencies:")
            for d in architecture["dependencies"][:max_items]:
                src = d["source_file"] or "?"
                tgt = d["target_file"] or d["target_module"] or "?"
                sym = f" ({d['symbol_name']})" if d["symbol_name"] else ""
                lines.append(f"  {src} → {tgt}{sym} [{d['dependency_type']}]")

        return "\n".join(lines)

    def build_dependency_context(
        self, repository_id: int, symbol: str
    ) -> str:
        """
        Build focused context for dependency questions like
        'Which files depend on RepositoryIndexer?'
        """
        deps: list[CodeDependency] = (
            self.db.query(CodeDependency)
            .filter(
                CodeDependency.repository_id == repository_id,
                CodeDependency.symbol_name.ilike(f"%{symbol}%"),
            )
            .limit(30)
            .all()
        )

        if not deps:
            return f"No dependency records found referencing '{symbol}'."

        file_map: dict[int, File] = {
            f.id: f
            for f in self.db.query(File)
            .filter(File.repository_id == repository_id)
            .all()
        }

        lines = [f"Files referencing '{symbol}':"]
        for d in deps:
            src = file_map.get(d.source_file_id)
            src_path = src.path if src else "unknown"
            line_info = f" line {d.line_number}" if d.line_number else ""
            lines.append(f"  {src_path}{line_info} [{d.dependency_type}]")
        return "\n".join(lines)
