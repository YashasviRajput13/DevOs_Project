"""
indexer.py (updated)
====================
Indexes repository files, creates CodeChunks with embeddings,
and extracts CodeDependency records via CodeAnalyzer.
Re-indexing is safe: existing dependency records are deleted and
recreated per file to avoid duplicates.
"""
from sqlalchemy.orm import Session

from app.models.chunk import CodeChunk
from app.models.dependency import CodeDependency
from app.models.file import File
from app.models.repository import Repository
from app.services.chunker import CodeChunker
from app.services.code_analyzer import CodeAnalyzer
from app.services.github import GitHubService


class RepositoryIndexer:

    def __init__(self, db: Session):
        self.db = db
        self.github = GitHubService()
        self.chunker = CodeChunker(db)
        self.analyzer = CodeAnalyzer()

    async def index_repository(self, repository: Repository):
        files = await self.github.get_repository_tree(
            repository.owner,
            repository.name,
            repository.default_branch,
        )

        indexed = 0
        chunks_created = 0

        # --- Build a path→file_id map for dependency resolution ---
        existing_files: dict[str, File] = {
            f.path: f
            for f in self.db.query(File)
            .filter(File.repository_id == repository.id)
            .all()
        }

        for item in files:
            path = item.get("path")

            if not path or self._should_ignore(path):
                continue

            try:
                data = await self.github.get_text_file(
                    repository.owner,
                    repository.name,
                    path,
                )

                if not data:
                    continue

                extension = self._get_extension(path)
                language = self._get_language(extension)

                existing = existing_files.get(path)

                if existing:
                    existing.name = path.split("/")[-1]
                    existing.extension = extension
                    existing.language = language
                    existing.content = data["content"]
                    existing.size = data.get("size")
                    existing.sha = data.get("sha")
                    file = existing
                else:
                    file = File(
                        repository_id=repository.id,
                        path=path,
                        name=path.split("/")[-1],
                        extension=extension,
                        language=language,
                        content=data["content"],
                        size=data.get("size"),
                        sha=data.get("sha"),
                    )
                    self.db.add(file)
                    self.db.flush()
                    existing_files[path] = file

                chunks_created += self.chunker.chunk_file(file)
                indexed += 1

            except Exception as e:
                print(f"Failed to index {path}: {e}")
                self.db.rollback()

        # Flush so all file IDs are stable before analysis
        self.db.flush()

        # Rebuild path→file_id after indexing
        all_files: dict[str, File] = {
            f.path: f
            for f in self.db.query(File)
            .filter(File.repository_id == repository.id)
            .all()
        }

        # --- Code analysis & dependency extraction ---
        deps_created = self._extract_dependencies(repository, all_files)

        self.db.commit()

        return {
            "repository_id": repository.id,
            "files_indexed": indexed,
            "chunks_created": chunks_created,
            "dependencies_extracted": deps_created,
        }

    def _extract_dependencies(
        self,
        repository: Repository,
        all_files: dict[str, File],
    ) -> int:
        """
        Run CodeAnalyzer on every indexed file and persist CodeDependency
        records.  Deletes existing records first so re-indexing is idempotent.
        """
        # Delete existing dependency records for this repository
        self.db.query(CodeDependency).filter(
            CodeDependency.repository_id == repository.id
        ).delete(synchronize_session=False)

        deps_created = 0

        for path, file_obj in all_files.items():
            if not file_obj.content:
                continue

            try:
                analysis = self.analyzer.analyze(
                    path=path,
                    content=file_obj.content,
                    language=file_obj.language,
                )
            except Exception as exc:
                print(f"Analysis failed for {path}: {exc}")
                continue

            # --- Import dependencies ---
            for imp in analysis.imports:
                # Try to resolve to a known file
                target_file_id = self._resolve_module(imp.module, all_files)
                dep = CodeDependency(
                    repository_id=repository.id,
                    source_file_id=file_obj.id,
                    target_file_id=target_file_id,
                    target_module=imp.module[:500],
                    dependency_type="import",
                    symbol_name=imp.alias[:255] if imp.alias else None,
                    line_number=imp.line,
                )
                self.db.add(dep)
                deps_created += 1

            # --- API routes ---
            for route in analysis.routes:
                dep = CodeDependency(
                    repository_id=repository.id,
                    source_file_id=file_obj.id,
                    target_file_id=None,
                    target_module=None,
                    dependency_type="api_route",
                    symbol_name=f"{route.method} {route.path}"[:255],
                    line_number=route.line,
                )
                self.db.add(dep)
                deps_created += 1

            # --- Class declarations (helps answer "what classes exist?") ---
            for cls in analysis.classes:
                dep = CodeDependency(
                    repository_id=repository.id,
                    source_file_id=file_obj.id,
                    target_file_id=None,
                    target_module=None,
                    dependency_type="class",
                    symbol_name=cls.name[:255],
                    line_number=cls.start_line,
                )
                self.db.add(dep)
                deps_created += 1

            # --- SQLAlchemy models ---
            for model_name in analysis.db_models:
                dep = CodeDependency(
                    repository_id=repository.id,
                    source_file_id=file_obj.id,
                    target_file_id=None,
                    target_module=None,
                    dependency_type="model_reference",
                    symbol_name=model_name[:255],
                    line_number=None,
                )
                self.db.add(dep)
                deps_created += 1

        return deps_created

    @staticmethod
    def _resolve_module(module: str, all_files: dict[str, File]) -> int | None:
        """
        Try to resolve a Python import string to an indexed file path.
        e.g. "app.services.indexer" → "app/services/indexer.py"
        Returns the file ID if found, else None.
        """
        candidate = module.replace(".", "/") + ".py"
        file_obj = all_files.get(candidate)
        if file_obj:
            return file_obj.id
        # Try without the last segment (from X import Y)
        parts = module.rsplit(".", 1)
        if len(parts) == 2:
            parent = parts[0].replace(".", "/") + ".py"
            f = all_files.get(parent)
            if f:
                return f.id
        return None

    @staticmethod
    def _get_extension(path: str):
        filename = path.split("/")[-1]
        if "." not in filename:
            return None
        return filename.rsplit(".", 1)[1].lower()

    @staticmethod
    def _get_language(extension: str | None):
        languages = {
            "py": "Python", "js": "JavaScript", "jsx": "JavaScript",
            "ts": "TypeScript", "tsx": "TypeScript", "java": "Java",
            "cpp": "C++", "c": "C", "h": "C/C++", "hpp": "C++",
            "cs": "C#", "go": "Go", "rs": "Rust", "php": "PHP",
            "rb": "Ruby", "kt": "Kotlin", "swift": "Swift",
            "html": "HTML", "css": "CSS", "scss": "SCSS",
            "sql": "SQL", "json": "JSON", "yaml": "YAML",
            "yml": "YAML", "md": "Markdown", "xml": "XML",
            "sh": "Shell",
        }
        return languages.get(extension)

    @staticmethod
    def _should_ignore(path: str):
        ignored = [
            ".git/", "__pycache__/", "node_modules/",
            ".venv/", "venv/", "dist/", "build/",
            "package-lock.json", "poetry.lock", "yarn.lock"
        ]
        if any(item in path for item in ignored):
            return True
            
        ext = path.split(".")[-1].lower() if "." in path else ""
        if ext in ["png", "jpg", "jpeg", "gif", "webp", "pdf", "zip", "tar", "gz", "mp3", "mp4", "wav", "sqlite3", "pyc", "pkl"]:
            return True
            
        return False