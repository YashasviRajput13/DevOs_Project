"""
code_analyzer.py
================
Extracts structural information from indexed source files using Python's
built-in AST for .py files and regex-based heuristics for other languages.

SAFETY: This module NEVER executes repository code.
All analysis is purely static (text / AST parse only).
"""
from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ImportInfo:
    module: str
    alias: str | None = None
    line: int = 0


@dataclass
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    is_async: bool = False
    decorators: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    name: str
    start_line: int
    end_line: int
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class RouteInfo:
    method: str          # GET, POST, PUT, DELETE, PATCH
    path: str
    handler: str
    line: int


@dataclass
class FileAnalysis:
    path: str
    language: str | None
    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    routes: list[RouteInfo] = field(default_factory=list)
    # SQLAlchemy model names detected in this file
    db_models: list[str] = field(default_factory=list)
    # Service class names detected in this file
    service_classes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex patterns for non-Python heuristics
# ---------------------------------------------------------------------------

_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)
_JS_ROUTE_RE = re.compile(
    r"""(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""",
    re.IGNORECASE | re.MULTILINE,
)
_FASTAPI_ROUTE_DECORATOR = re.compile(
    r"""@\w+\.(get|post|put|delete|patch)\s*\(\s*["']([^"']+)["']""",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Public analyzer
# ---------------------------------------------------------------------------

class CodeAnalyzer:
    """
    Analyzes a single source file and returns a FileAnalysis.
    Safe: never imports or executes code from the repository.
    """

    def analyze(self, path: str, content: str, language: str | None) -> FileAnalysis:
        result = FileAnalysis(path=path, language=language)

        if not content:
            return result

        lang = (language or "").lower()

        if lang == "python":
            self._analyze_python(result, content)
        elif lang in ("javascript", "typescript"):
            self._analyze_js(result, content)
        else:
            # For all other languages just try route detection
            self._detect_generic_routes(result, content)

        return result

    # ------------------------------------------------------------------
    # Python analysis (AST)
    # ------------------------------------------------------------------

    def _analyze_python(self, result: FileAnalysis, content: str) -> None:
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            result.errors.append(f"SyntaxError: {exc}")
            # Fall back to regex for what we can still get
            self._detect_generic_routes(result, content)
            return

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.imports.append(
                        ImportInfo(module=alias.name, alias=alias.asname, line=node.lineno)
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    result.imports.append(
                        ImportInfo(
                            module=f"{module}.{alias.name}" if module else alias.name,
                            alias=alias.asname,
                            line=node.lineno,
                        )
                    )

        # Top-level classes and functions (walk top-level body)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fi = self._extract_function(node)
                result.functions.append(fi)
                # Detect FastAPI route decorators
                for dec in node.decorator_list:
                    route = self._try_extract_fastapi_route(dec, node.name)
                    if route:
                        result.routes.append(route)

            elif isinstance(node, ast.ClassDef):
                ci = self._extract_class(node)
                result.classes.append(ci)
                # SQLAlchemy model: inherits from Base or DeclarativeBase
                if any(
                    self._base_name(b) in ("Base", "DeclarativeBase", "Model")
                    for b in node.bases
                ):
                    result.db_models.append(node.name)
                # Service class: name ends with Service or Agent
                if node.name.endswith(("Service", "Agent", "Manager", "Handler")):
                    result.service_classes.append(node.name)

                # Also scan methods inside classes for route decorators
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for dec in item.decorator_list:
                            route = self._try_extract_fastapi_route(dec, item.name)
                            if route:
                                result.routes.append(route)

    @staticmethod
    def _extract_function(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionInfo:
        decorators = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Attribute):
                decorators.append(f"{ast.unparse(d)}")
            elif isinstance(d, ast.Call):
                decorators.append(ast.unparse(d.func))

        end = getattr(node, "end_lineno", node.lineno)
        return FunctionInfo(
            name=node.name,
            start_line=node.lineno,
            end_line=end,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
        )

    @staticmethod
    def _extract_class(node: ast.ClassDef) -> ClassInfo:
        bases = []
        for b in node.bases:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                pass
        methods = [
            item.name
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        end = getattr(node, "end_lineno", node.lineno)
        return ClassInfo(
            name=node.name,
            start_line=node.lineno,
            end_line=end,
            bases=bases,
            methods=methods,
        )

    @staticmethod
    def _try_extract_fastapi_route(decorator: ast.expr, handler_name: str) -> RouteInfo | None:
        """
        Detect patterns like @router.get("/path") or @app.post("/path").
        Returns a RouteInfo if recognized, else None.
        """
        if not isinstance(decorator, ast.Call):
            return None
        func = decorator.func
        if not isinstance(func, ast.Attribute):
            return None
        method = func.attr.upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
            return None
        # Extract path argument
        if not decorator.args:
            return None
        path_arg = decorator.args[0]
        if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str):
            return RouteInfo(
                method=method,
                path=path_arg.value,
                handler=handler_name,
                line=decorator.lineno if hasattr(decorator, "lineno") else 0,
            )
        return None

    @staticmethod
    def _base_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    # ------------------------------------------------------------------
    # JS / TS analysis (regex)
    # ------------------------------------------------------------------

    def _analyze_js(self, result: FileAnalysis, content: str) -> None:
        for m in _JS_IMPORT_RE.finditer(content):
            module = m.group(1) or m.group(2)
            if module:
                line = content[: m.start()].count("\n") + 1
                result.imports.append(ImportInfo(module=module, line=line))
        for m in _JS_ROUTE_RE.finditer(content):
            line = content[: m.start()].count("\n") + 1
            result.routes.append(
                RouteInfo(
                    method=m.group(1).upper(),
                    path=m.group(2),
                    handler="",
                    line=line,
                )
            )

    # ------------------------------------------------------------------
    # Generic route detection (regex — used as fallback)
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_generic_routes(result: FileAnalysis, content: str) -> None:
        for m in _FASTAPI_ROUTE_DECORATOR.finditer(content):
            line = content[: m.start()].count("\n") + 1
            result.routes.append(
                RouteInfo(
                    method=m.group(1).upper(),
                    path=m.group(2),
                    handler="",
                    line=line,
                )
            )

    # ------------------------------------------------------------------
    # Serialization helper
    # ------------------------------------------------------------------

    @staticmethod
    def analysis_to_dict(analysis: FileAnalysis) -> dict[str, Any]:
        return {
            "path": analysis.path,
            "language": analysis.language,
            "imports": [
                {"module": i.module, "alias": i.alias, "line": i.line}
                for i in analysis.imports
            ],
            "functions": [
                {
                    "name": f.name,
                    "start_line": f.start_line,
                    "end_line": f.end_line,
                    "is_async": f.is_async,
                    "decorators": f.decorators,
                }
                for f in analysis.functions
            ],
            "classes": [
                {
                    "name": c.name,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "bases": c.bases,
                    "methods": c.methods,
                }
                for c in analysis.classes
            ],
            "routes": [
                {
                    "method": r.method,
                    "path": r.path,
                    "handler": r.handler,
                    "line": r.line,
                }
                for r in analysis.routes
            ],
            "db_models": analysis.db_models,
            "service_classes": analysis.service_classes,
            "errors": analysis.errors,
        }
