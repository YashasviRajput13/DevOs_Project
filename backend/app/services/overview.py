"""
overview.py
===========
Derives a structured repository overview from database records only.
No data is invented; everything is computed from Repository, File, and
CodeChunk rows that already exist in PostgreSQL.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chunk import CodeChunk
from app.models.file import File
from app.models.repository import Repository

logger = logging.getLogger(__name__)

# Files whose names strongly suggest they are important entry points or configs
_IMPORTANT_FILENAMES = {
    "main.py", "app.py", "server.py", "index.py", "wsgi.py", "asgi.py",
    "manage.py", "run.py", "cli.py",
    "index.js", "index.ts", "app.js", "app.ts", "server.js", "server.ts",
    "main.js", "main.ts",
    "index.html", "index.jsx", "index.tsx",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt", "Pipfile", "Cargo.toml", "go.mod",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "README.md", "readme.md",
    "alembic.ini", "settings.py", "config.py", "configuration.py",
    ".env.example",
}

# Framework/library detection: if any indexed file path contains a key, we add the label
_FRAMEWORK_SIGNALS: list[tuple[str, str]] = [
    ("fastapi", "FastAPI"),
    ("flask", "Flask"),
    ("django", "Django"),
    ("sqlalchemy", "SQLAlchemy"),
    ("alembic", "Alembic"),
    ("pydantic", "Pydantic"),
    ("starlette", "Starlette"),
    ("celery", "Celery"),
    ("redis", "Redis"),
    ("groq", "Groq"),
    ("openai", "OpenAI"),
    ("sentence_transformers", "SentenceTransformers"),
    ("torch", "PyTorch"),
    ("react", "React"),
    ("vue", "Vue"),
    ("angular", "Angular"),
    ("next", "Next.js"),
    ("vite", "Vite"),
    ("express", "Express"),
    ("prisma", "Prisma"),
    ("mongoose", "Mongoose"),
    ("pytest", "pytest"),
    ("unittest", "unittest"),
]


class RepositoryOverviewService:
    """Builds a structured overview from indexed repository records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_overview(self, project_id: int, repository_id: int) -> dict[str, Any]:
        """Return a structured overview dict or raise ValueError."""

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

        chunk_count: int = (
            self.db.query(func.count(CodeChunk.id))
            .join(File, CodeChunk.file_id == File.id)
            .filter(File.repository_id == repository_id)
            .scalar()
            or 0
        )

        languages = self._compute_languages(files)
        directories = self._compute_directories(files)
        important_files = self._compute_important_files(files)
        frameworks = self._detect_frameworks(files)
        summary_ctx = self._build_summary_context(repo, files, languages, directories, frameworks)

        return {
            "repository": {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.url,
                "default_branch": repo.default_branch,
            },
            "statistics": {
                "files": len(files),
                "chunks": chunk_count,
            },
            "languages": languages,
            "directories": directories,
            "important_files": important_files,
            "frameworks": frameworks,
            "summary_context": summary_ctx,
        }

    def build_llm_context(self, overview: dict[str, Any]) -> str:
        """Convert an overview dict into a plain-text block for LLM prompts."""
        repo = overview["repository"]
        stats = overview["statistics"]
        lines = [
            f"Repository: {repo['full_name']}",
            f"GitHub URL: {repo['url']}",
            f"Default branch: {repo['default_branch']}",
            f"Indexed files: {stats['files']}",
            f"Code chunks: {stats['chunks']}",
        ]

        if overview["languages"]:
            lang_str = ", ".join(
                f"{l['name']} ({l['files']} files)" for l in overview["languages"]
            )
            lines.append(f"Languages: {lang_str}")

        if overview["frameworks"]:
            lines.append(f"Detected frameworks/libraries: {', '.join(overview['frameworks'])}")

        if overview["directories"]:
            dirs = [d["path"] for d in overview["directories"][:10]]
            lines.append(f"Top directories: {', '.join(dirs)}")

        if overview["important_files"]:
            ifiles = [f["path"] for f in overview["important_files"][:10]]
            lines.append(f"Key files: {', '.join(ifiles)}")

        lines.append("")
        lines.append(overview.get("summary_context", ""))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_languages(files: list[File]) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for f in files:
            if f.language:
                counter[f.language] += 1
        return [{"name": lang, "files": cnt} for lang, cnt in counter.most_common()]

    @staticmethod
    def _compute_directories(files: list[File]) -> list[dict[str, Any]]:
        dir_counter: Counter[str] = Counter()
        for f in files:
            parts = f.path.split("/")
            if len(parts) > 1:
                dir_counter[parts[0]] += 1
        return [
            {"path": d, "file_count": cnt}
            for d, cnt in dir_counter.most_common(20)
        ]

    @staticmethod
    def _compute_important_files(files: list[File]) -> list[dict[str, Any]]:
        important = []
        for f in files:
            if f.name.lower() in _IMPORTANT_FILENAMES:
                important.append({"path": f.path, "name": f.name, "language": f.language})
        return important

    @staticmethod
    def _detect_frameworks(files: list[File]) -> list[str]:
        """Detect frameworks by scanning file paths and content snippets."""
        all_paths = " ".join(f.path.lower() for f in files)
        # Also sample first 500 chars of content for import clues
        all_content = " ".join(
            (f.content or "")[:500].lower() for f in files
        )
        combined = all_paths + " " + all_content

        detected: list[str] = []
        seen: set[str] = set()
        for signal, label in _FRAMEWORK_SIGNALS:
            if signal in combined and label not in seen:
                detected.append(label)
                seen.add(label)
        return detected

    @staticmethod
    def _build_summary_context(
        repo: Repository,
        files: list[File],
        languages: list[dict],
        directories: list[dict],
        frameworks: list[str],
    ) -> str:
        """Build a compact factual summary paragraph for the LLM."""
        lang_names = [l["name"] for l in languages[:4]]
        dir_names = [d["path"] for d in directories[:5]]
        parts = [
            f"The repository '{repo.full_name}' contains {len(files)} indexed files.",
        ]
        if lang_names:
            parts.append(f"Primary languages detected: {', '.join(lang_names)}.")
        if frameworks:
            parts.append(f"Frameworks/libraries identified: {', '.join(frameworks[:6])}.")
        if dir_names:
            parts.append(f"Main directories: {', '.join(dir_names)}.")
        return " ".join(parts)
