#!/usr/bin/env python
"""Generate a compact, source-derived Tavola onboarding orientation scan."""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT_HINTS = ("AGENTS.md", "CONTEXT.md", "backend", "frontend")


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    function: str
    file: Path
    line: int


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]).resolve() if args else find_repo_root(Path.cwd())
    if root is None:
        print("Could not find Tavola repo root.", file=sys.stderr)
        return 1

    print(scan_repo(root))
    return 0


def find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if all((candidate / hint).exists() for hint in ROOT_HINTS):
            return candidate
    return None


def scan_repo(root: Path) -> str:
    backend_root = discover_backend_root(root)
    frontend_root = root / "frontend/src"
    backend_layers = discover_child_dirs(backend_root)
    frontend_sections = discover_child_dirs(frontend_root)
    frontend_features = discover_child_dirs(frontend_root / "features")

    lines: list[str] = []
    add = lines.append

    add("# Tavola Repository Scan")
    add("")
    add(f"Repository root: `{root}`")
    add("")
    add("This is an orientation index, not the final guide. Inspect the named files")
    add("before turning it into architecture prose.")
    add("")

    add("## Source Of Truth")
    add("")
    for rel_path in ("AGENTS.md", "CONTEXT.md"):
        add_existing(add, root, rel_path)
    for rel_path in key_docs(root):
        add(f"- `{rel_path}`")
    add("")

    add("## Backend Map")
    add("")
    if backend_root.exists():
        add(f"- backend package root: `{backend_root.relative_to(root)}`")
    for layer in backend_layers:
        add(f"- `{layer.relative_to(root)}`")
    for rel_path in backend_entry_points(root, backend_root):
        add(f"- `{rel_path}`")
    add("")

    add("### FastAPI Routes")
    add("")
    routes = collect_routes(root)
    if routes:
        for route in sorted(routes, key=lambda item: (item.path, item.method)):
            add(
                f"- `{route.method} {route.path}` -> `{route.function}` "
                f"({route.file.relative_to(root)}:{route.line})"
            )
    else:
        add("- No FastAPI routes found.")
    add("")

    add("## Frontend Map")
    add("")
    for rel_path in ("frontend/src/App.tsx", "frontend/src/pages/HomePage.tsx"):
        add_existing(add, root, rel_path)
    for section in frontend_sections:
        add(f"- `{section.relative_to(root)}`")
    if frontend_features:
        add("")
        add("Current feature areas:")
        for feature in frontend_features:
            add(f"- `{feature.relative_to(root)}`")
    add("")

    add("### Frontend API Paths")
    add("")
    api_paths = collect_frontend_api_paths(root)
    if api_paths:
        for rel_file, paths in sorted(api_paths.items()):
            rendered = ", ".join(f"`{path}`" for path in sorted(paths))
            add(f"- `{rel_file}`: {rendered}")
    else:
        add("- No frontend API path strings found.")
    add("")

    add("## Tests")
    add("")
    for label, count in test_counts(root).items():
        add(f"- {label}: {count} test files")
    add("")

    add("## Scripts And Commands")
    add("")
    for label, command in collect_commands(root):
        add(f"- {label}: `{command}`")
    add("")

    add("## Mermaid Starting Point")
    add("")
    add("```mermaid")
    add("flowchart LR")
    add('  User["Customer or operator"] --> Home["Frontend composition"]')
    if frontend_features:
        for feature in frontend_features:
            node_id = mermaid_id(feature.name)
            label = feature.name.replace("-", " ").title()
            add(f'  Home --> {node_id}["{label} feature"]')
            add(f'  {node_id} --> Client["Frontend API clients"]')
    else:
        add('  Home --> Client["Frontend API clients"]')
    add('  Client --> Routers["Backend routers + schemas"]')
    add('  Routers --> UseCases["Application use cases"]')
    add('  UseCases --> Domain["Domain rules"]')
    add('  UseCases --> Infra["Infrastructure adapters"]')
    add("```")

    return "\n".join(lines)


def discover_backend_root(root: Path) -> Path:
    src_root = root / "backend/src"
    if not src_root.exists():
        return src_root
    candidates = [path for path in src_root.iterdir() if path.is_dir()]
    package_candidates = [path for path in candidates if (path / "api").exists()]
    return package_candidates[0] if package_candidates else src_root


def discover_child_dirs(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(
        child
        for child in path.iterdir()
        if child.is_dir() and not child.name.startswith((".", "__"))
    )


def backend_entry_points(root: Path, backend_root: Path) -> list[str]:
    candidates = (
        backend_root / "api/main.py",
        backend_root / "api/dependencies.py",
        backend_root / "config/settings.py",
    )
    return [str(path.relative_to(root)) for path in candidates if path.exists()]


def collect_routes(root: Path) -> list[Route]:
    routes: list[Route] = []
    for routers_dir in sorted((root / "backend/src").glob("*/api/routers")):
        if not routers_dir.is_dir():
            continue
        for file in sorted(routers_dir.glob("*.py")):
            routes.extend(collect_routes_from_file(file))
    return routes


def collect_routes_from_file(file: Path) -> list[Route]:
    tree = parse_python(file)
    if tree is None:
        return []

    routes: list[Route] = []
    prefix = router_prefix(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            route = route_from_decorator(decorator, prefix)
            if route is not None:
                method, path = route
                routes.append(Route(method, path, node.name, file, node.lineno))
    return routes


def router_prefix(tree: ast.AST) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if name_of(node.value.func) != "APIRouter":
            continue
        for keyword in node.value.keywords:
            if keyword.arg == "prefix":
                return literal_string(keyword.value) or ""
    return ""


def route_from_decorator(node: ast.expr, prefix: str) -> tuple[str, str] | None:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    if not isinstance(node.func.value, ast.Name) or node.func.value.id != "router":
        return None
    method = node.func.attr.upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return None
    suffix = literal_string(node.args[0]) if node.args else ""
    return method, normalize_path(prefix, suffix or "")


def collect_frontend_api_paths(root: Path) -> dict[str, set[str]]:
    pattern = re.compile(r"[\"'](/[A-Za-z][^\"'`]*)[\"']")
    api_dir = root / "frontend/src/api"
    result: dict[str, set[str]] = {}
    for file in sorted(api_dir.glob("*.ts")):
        if ".test." in file.name:
            continue
        paths = {
            path
            for path in pattern.findall(file.read_text(encoding="utf-8"))
            if path != "/api" and not path.startswith(("/api/", "//"))
        }
        if paths:
            result[str(file.relative_to(root))] = paths
    return result


def key_docs(root: Path) -> list[str]:
    docs = [
        "docs/frontend-browser-approval-check.md",
        "docs/scaffold-smoke-check.md",
        "docs/adr/0001-desktop-first-demonstrator-ui.md",
        "docs/adr/0002-planning-first-live-planner-sessions.md",
    ]
    return [rel_path for rel_path in docs if (root / rel_path).exists()]


def test_counts(root: Path) -> dict[str, int]:
    return {
        "backend": len(list((root / "backend/tests").glob("test_*.py"))),
        "frontend": len(list((root / "frontend/src").rglob("*.test.ts*"))),
    }


def collect_commands(root: Path) -> list[tuple[str, str]]:
    commands = [
        ("backend install", "cd backend && uv sync"),
        ("backend tests", "cd backend && uv run pytest"),
        ("backend lint", "cd backend && uv run ruff check ."),
        ("frontend install", "cd frontend && npm install"),
    ]

    package_json = root / "frontend/package.json"
    if package_json.exists():
        scripts = json.loads(package_json.read_text(encoding="utf-8")).get(
            "scripts", {}
        )
        commands.extend(
            (f"frontend {name}", f"cd frontend && npm run {name}")
            for name in sorted(scripts)
        )

    pyproject = root / "backend/pyproject.toml"
    if pyproject.exists():
        project_name = tomllib.loads(pyproject.read_text(encoding="utf-8")).get(
            "project", {}
        ).get("name")
        if project_name:
            commands.insert(0, ("backend package", project_name))

    return commands


def add_existing(add: Callable[[str], None], root: Path, rel_path: str) -> None:
    if (root / rel_path).exists():
        add(f"- `{rel_path}`")


def parse_python(file: Path) -> ast.Module | None:
    try:
        return ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
    except SyntaxError:
        return None


def name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def normalize_path(prefix: str, suffix: str) -> str:
    path = f"{prefix.rstrip('/')}/{suffix.lstrip('/')}" if suffix else prefix
    return path if path.startswith("/") else f"/{path}"


def mermaid_id(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    return "".join(word.capitalize() for word in words) if words else "Feature"


if __name__ == "__main__":
    raise SystemExit(main())
