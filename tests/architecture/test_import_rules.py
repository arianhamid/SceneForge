"""
Architecture tests that enforce the REAL dependency graph of SceneForge.

These tests use AST parsing to extract imports from Python files and
verify that the dependency rules are not violated. They are designed
to match the actual codebase, not an idealized version.

Rules enforced:
1. core must not import contrib
2. core must not import knowledge
3. media must not import core
4. media must not import runtime
5. knowledge may import contrib artifact types (ADR-0016) — but NOT contrib providers
6. Pipeline must not import knowledge
7. core has no external dependencies (stdlib only)

Known real dependencies that are NOT violations:
- core/pipeline.py imports ProcessingContext from runtime (ADR-backed)
- knowledge builders import contrib artifact types for isinstance() checks
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Project root and package paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "sceneforge"

# Allowed knowledge → contrib artifact imports (ADR-0016)
ALLOWED_KNOWLEDGE_CONTRIB_IMPORTS: frozenset[str] = frozenset(
    {
        "sceneforge.contrib.ffmpeg.frame_extraction_artifact",
        "sceneforge.contrib.scenedetect.scene_cut_artifact",
        "sceneforge.contrib.whisper.transcript_artifact",
        "sceneforge.contrib.opencv.face_detection_artifact",
        "sceneforge.contrib.tesseract.ocr_artifact",
    }
)

# Standard library modules (Python 3.12)
STDLIB_MODULES: frozenset[str] = frozenset(sys.stdlib_module_names)


def _extract_imports(filepath: Path) -> list[str]:
    """Extract all imported module names from a Python file using AST.

    Returns a list of top-level module names (e.g., 'sceneforge.core.artifact'
    becomes 'sceneforge', 'sceneforge.core.artifact' is returned as is).
    """
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    return imports


def _get_module_files(subpackage: str) -> list[Path]:
    """Get all .py files in a sceneforge subpackage."""
    pkg_dir = PACKAGE_ROOT / subpackage
    if not pkg_dir.exists():
        return []
    return sorted(pkg_dir.rglob("*.py"))


def _is_sceneforge_import(module_name: str) -> bool:
    """Check if a module name is a sceneforge internal import."""
    return module_name.startswith("sceneforge.")


def _is_contrib_import(module_name: str) -> bool:
    """Check if a module name is a contrib import."""
    return module_name.startswith("sceneforge.contrib.")


def _is_knowledge_import(module_name: str) -> bool:
    """Check if a module name is a knowledge import."""
    return module_name.startswith("sceneforge.knowledge.")


def _is_core_import(module_name: str) -> bool:
    """Check if a module name is a core import."""
    return module_name.startswith("sceneforge.core.")


def _is_media_import(module_name: str) -> bool:
    """Check if a module name is a media import."""
    return module_name.startswith("sceneforge.media.")


def _is_runtime_import(module_name: str) -> bool:
    """Check if a module name is a runtime import."""
    return module_name.startswith("sceneforge.runtime.")


def _collect_imports_for_package(
    subpackage: str,
) -> dict[str, list[str]]:
    """Collect all imports from all files in a subpackage.

    Returns a dict mapping filepath -> list of imported module names.
    """
    result: dict[str, list[str]] = {}
    for filepath in _get_module_files(subpackage):
        imports = _extract_imports(filepath)
        if imports:
            rel_path = str(filepath.relative_to(PROJECT_ROOT))
            result[rel_path] = imports
    return result


# ─── Rule 1: core must not import contrib ─────────────────────────────


class TestCoreMustNotImportContrib:
    """Rule 1: sceneforge.core must not import sceneforge.contrib."""

    def test_no_contrib_imports(self) -> None:
        imports_by_file = _collect_imports_for_package("core")
        violations: list[tuple[str, str]] = []

        for filepath, imports in imports_by_file.items():
            for module in imports:
                if _is_contrib_import(module):
                    violations.append((filepath, module))

        assert not violations, (
            "core must not import contrib. Violations:\n"
            + "\n".join(f"  {f}: {m}" for f, m in violations)
        )


# ─── Rule 2: core must not import knowledge ───────────────────────────


class TestCoreMustNotImportKnowledge:
    """Rule 2: sceneforge.core must not import sceneforge.knowledge."""

    def test_no_knowledge_imports(self) -> None:
        imports_by_file = _collect_imports_for_package("core")
        violations: list[tuple[str, str]] = []

        for filepath, imports in imports_by_file.items():
            for module in imports:
                if _is_knowledge_import(module):
                    violations.append((filepath, module))

        assert not violations, (
            "core must not import knowledge. Violations:\n"
            + "\n".join(f"  {f}: {m}" for f, m in violations)
        )


# ─── Rule 3: media must not import core ────────────────────────────────


class TestMediaMustNotImportCore:
    """Rule 3: sceneforge.media must not import sceneforge.core."""

    def test_no_core_imports(self) -> None:
        imports_by_file = _collect_imports_for_package("media")
        violations: list[tuple[str, str]] = []

        for filepath, imports in imports_by_file.items():
            for module in imports:
                if _is_core_import(module):
                    violations.append((filepath, module))

        assert not violations, "media must not import core. Violations:\n" + "\n".join(
            f"  {f}: {m}" for f, m in violations
        )


# ─── Rule 4: media must not import runtime ─────────────────────────────


class TestMediaMustNotImportRuntime:
    """Rule 4: sceneforge.media must not import sceneforge.runtime."""

    def test_no_runtime_imports(self) -> None:
        imports_by_file = _collect_imports_for_package("media")
        violations: list[tuple[str, str]] = []

        for filepath, imports in imports_by_file.items():
            for module in imports:
                if _is_runtime_import(module):
                    violations.append((filepath, module))

        assert not violations, (
            "media must not import runtime. Violations:\n"
            + "\n".join(f"  {f}: {m}" for f, m in violations)
        )


# ─── Rule 5: knowledge may import contrib artifacts but not providers ──


class TestKnowledgeContribImports:
    """Rule 5: knowledge may import contrib artifact types (ADR-0016)
    but NOT contrib providers."""

    def test_only_allowed_contrib_imports(self) -> None:
        imports_by_file = _collect_imports_for_package("knowledge")
        violations: list[tuple[str, str]] = []

        for filepath, imports in imports_by_file.items():
            for module in imports:
                is_bad = (
                    _is_contrib_import(module)
                    and module not in ALLOWED_KNOWLEDGE_CONTRIB_IMPORTS
                )
                if is_bad:
                    violations.append((filepath, module))

        assert not violations, (
            "knowledge may only import these contrib artifact types:\n"
            + "\n".join(f"  {a}" for a in sorted(ALLOWED_KNOWLEDGE_CONTRIB_IMPORTS))
            + "\n\nViolations found:\n"
            + "\n".join(f"  {f}: {m}" for f, m in violations)
        )

    def test_allowed_imports_are_actually_used(self) -> None:
        """Verify the allowlist entries still exist in the codebase."""
        imports_by_file = _collect_imports_for_package("knowledge")
        all_knowledge_imports: set[str] = set()
        for imports in imports_by_file.values():
            for module in imports:
                all_knowledge_imports.add(module)

        orphaned = ALLOWED_KNOWLEDGE_CONTRIB_IMPORTS - all_knowledge_imports
        assert not orphaned, (
            "These allowlist entries are no longer imported by knowledge:\n"
            + "\n".join(f"  {a}" for a in sorted(orphaned))
            + "\n\nRemove them from ALLOWED_KNOWLEDGE_CONTRIB_IMPORTS."
        )


# ─── Rule 6: Pipeline must not import knowledge ───────────────────────


class TestPipelineMustNotImportKnowledge:
    """Rule 6: sceneforge.core.pipeline and async_pipeline must not
    import sceneforge.knowledge."""

    PIPELINE_FILES = (
        "sceneforge/core/pipeline.py",
        "sceneforge/core/async_pipeline.py",
    )

    def test_pipeline_no_knowledge_imports(self) -> None:
        violations: list[tuple[str, str]] = []

        for rel_path in self.PIPELINE_FILES:
            filepath = PROJECT_ROOT / rel_path
            if not filepath.exists():
                continue
            imports = _extract_imports(filepath)
            for module in imports:
                if _is_knowledge_import(module):
                    violations.append((rel_path, module))

        assert not violations, (
            "Pipeline must not import knowledge. Violations:\n"
            + "\n".join(f"  {f}: {m}" for f, m in violations)
        )


# ─── Rule 7: core has no external dependencies (stdlib only) ──────────


class TestCoreStdlibOnly:
    """Rule 7: core must only use stdlib modules, not third-party packages."""

    def test_no_external_dependencies(self) -> None:
        imports_by_file = _collect_imports_for_package("core")
        violations: list[tuple[str, str]] = []

        for filepath, imports in imports_by_file.items():
            for module in imports:
                top_level = module.split(".")[0]
                # Skip sceneforge internal imports
                if top_level == "sceneforge":
                    continue
                if top_level not in STDLIB_MODULES:
                    violations.append((filepath, module))

        assert not violations, "core must only use stdlib. Violations:\n" + "\n".join(
            f"  {f}: {m}" for f, m in violations
        )


# ─── Sanity: known ADR-backed dependencies exist and are not flagged ───


class TestKnownDependencies:
    """Verify that the known ADR-backed dependencies are correctly
    accounted for and not accidentally flagged."""

    def test_core_pipeline_imports_runtime(self) -> None:
        """core/pipeline.py imports ProcessingContext from runtime (ADR-backed)."""
        filepath = PROJECT_ROOT / "sceneforge/core/pipeline.py"
        imports = _extract_imports(filepath)
        assert any("sceneforge.runtime.processing_context" in m for m in imports), (
            "core/pipeline.py should import ProcessingContext from runtime"
        )

    def test_core_async_pipeline_imports_runtime(self) -> None:
        """core/async_pipeline.py imports ProcessingContext from runtime."""
        filepath = PROJECT_ROOT / "sceneforge/core/async_pipeline.py"
        imports = _extract_imports(filepath)
        assert any("sceneforge.runtime.processing_context" in m for m in imports), (
            "core/async_pipeline.py should import ProcessingContext from runtime"
        )

    def test_knowledge_imports_contrib_artifacts(self) -> None:
        """knowledge builders import contrib artifact types for isinstance() checks."""
        imports_by_file = _collect_imports_for_package("knowledge")
        all_knowledge_imports: set[str] = set()
        for imports in imports_by_file.values():
            for module in imports:
                if _is_contrib_import(module):
                    all_knowledge_imports.add(module)

        assert all_knowledge_imports, (
            "Expected knowledge to import contrib artifact types, but none found"
        )
        # Should contain the known artifact imports
        ffmpeg = "sceneforge.contrib.ffmpeg.frame_extraction_artifact"
        scenedetect = "sceneforge.contrib.scenedetect.scene_cut_artifact"
        tesseract = "sceneforge.contrib.tesseract.ocr_artifact"
        assert ffmpeg in all_knowledge_imports
        assert scenedetect in all_knowledge_imports
        assert tesseract in all_knowledge_imports
