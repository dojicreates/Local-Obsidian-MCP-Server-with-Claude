import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration – reads vault path from env var or config.json
# ---------------------------------------------------------------------------

def _load_vault_path() -> Path:
    """Return the Obsidian vault root, checking env var then config.json."""
    env = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env:
        return Path(env).expanduser().resolve()

    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        data = json.loads(config_file.read_text(encoding="utf-8"))
        raw = data.get("vault_path", "")
        if raw:
            return Path(raw).expanduser().resolve()

    raise RuntimeError(
        "Obsidian vault path not set.\n"
        "Either set the OBSIDIAN_VAULT_PATH environment variable or add it to config.json."
    )


VAULT: Path = _load_vault_path()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve(relative: str) -> Path:
    """Resolve a vault-relative path and make sure it stays inside the vault."""
    target = (VAULT / relative).resolve()
    if not str(target).startswith(str(VAULT)):
        raise ValueError(f"Path '{relative}' escapes the vault root – access denied.")
    return target


def _md_path(relative: str) -> Path:
    """Ensure the path ends with .md."""
    p = Path(relative)
    if p.suffix.lower() != ".md":
        p = p.with_suffix(".md")
    return p


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="obsidian",
    instructions=(
        "This server gives you access to an Obsidian markdown vault. "
        "You can read, write, search, list, and delete notes. "
        "All paths are relative to the vault root."
    ),
)


# ── READ ────────────────────────────────────────────────────────────────────

@mcp.tool()
def read_note(path: str) -> str:
    """
    Read the full content of a note.

    Args:
        path: Vault-relative path to the note (e.g. 'Ideas/Project Alpha.md').
              The .md extension is added automatically if omitted.
    """
    full = _resolve(str(_md_path(path)))
    if not full.exists():
        return f"ERROR: Note not found: {path}"
    return full.read_text(encoding="utf-8")


# ── WRITE (create / overwrite) ───────────────────────────────────────────────

@mcp.tool()
def write_note(path: str, content: str) -> str:
    """
    Create or completely overwrite a note.

    Args:
        path:    Vault-relative path (e.g. 'Daily/2024-01-01.md').
        content: Full markdown content to write.
    """
    full = _resolve(str(_md_path(path)))
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return f"OK: Written {full.relative_to(VAULT)}"


# ── APPEND ──────────────────────────────────────────────────────────────────

@mcp.tool()
def append_to_note(path: str, content: str) -> str:
    """
    Append text to the end of an existing note (creates the note if absent).

    Args:
        path:    Vault-relative path.
        content: Text to append.
    """
    full = _resolve(str(_md_path(path)))
    full.parent.mkdir(parents=True, exist_ok=True)
    with full.open("a", encoding="utf-8") as fh:
        fh.write("\n" + content)
    return f"OK: Appended to {full.relative_to(VAULT)}"


# ── DELETE ───────────────────────────────────────────────────────────────────

@mcp.tool()
def delete_note(path: str) -> str:
    """
    Permanently delete a note from the vault.

    Args:
        path: Vault-relative path.
    """
    full = _resolve(str(_md_path(path)))
    if not full.exists():
        return f"ERROR: Note not found: {path}"
    full.unlink()
    return f"OK: Deleted {path}"


# ── LIST ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_notes(folder: str = "") -> str:
    """
    List all markdown notes inside a folder (defaults to vault root).

    Args:
        folder: Vault-relative folder path. Leave empty for the whole vault.
    """
    base = _resolve(folder) if folder else VAULT
    if not base.exists():
        return f"ERROR: Folder not found: {folder}"

    notes = sorted(base.rglob("*.md"))
    if not notes:
        return "No notes found."

    lines = [str(n.relative_to(VAULT)).replace("\\", "/") for n in notes]
    return "\n".join(lines)


# ── SEARCH ───────────────────────────────────────────────────────────────────

@mcp.tool()
def search_notes(query: str, folder: str = "", case_sensitive: bool = False) -> str:
    """
    Full-text search across all notes and return matching file paths with
    the first matching line from each file.

    Args:
        query:          Text or regex to search for.
        folder:         Restrict search to this vault-relative folder (optional).
        case_sensitive: Whether the search is case-sensitive (default False).
    """
    base = _resolve(folder) if folder else VAULT
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error as exc:
        return f"ERROR: Invalid regex – {exc}"

    results = []
    for note in sorted(base.rglob("*.md")):
        try:
            text = note.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                rel = str(note.relative_to(VAULT)).replace("\\", "/")
                results.append(f"{rel}:{lineno}: {line.strip()}")
                break  # one hit per file

    if not results:
        return f"No notes matching '{query}'."
    return "\n".join(results)


# ── VAULT STRUCTURE ──────────────────────────────────────────────────────────

@mcp.tool()
def get_vault_structure(max_depth: int = 3) -> str:
    """
    Return a tree view of the vault's folder/file structure.

    Args:
        max_depth: How many levels deep to show (default 3).
    """
    lines: list[str] = ["VAULT: (root)"]

    def _walk(path: Path, depth: int, prefix: str) -> None:
        if depth > max_depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return
        for i, child in enumerate(children):
            connector = "└── " if i == len(children) - 1 else "├── "
            lines.append(prefix + connector + child.name)
            if child.is_dir():
                extension = "    " if i == len(children) - 1 else "│   "
                _walk(child, depth + 1, prefix + extension)

    _walk(VAULT, 1, "")
    return "\n".join(lines)


# ── MOVE / RENAME ────────────────────────────────────────────────────────────

@mcp.tool()
def move_note(source: str, destination: str) -> str:
    """
    Move or rename a note within the vault.

    Args:
        source:      Current vault-relative path.
        destination: New vault-relative path.
    """
    src = _resolve(str(_md_path(source)))
    dst = _resolve(str(_md_path(destination)))
    if not src.exists():
        return f"ERROR: Source not found: {source}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return f"OK: Moved '{source}' → '{destination}'"


# ── DAILY NOTE ───────────────────────────────────────────────────────────────

@mcp.tool()
def get_or_create_daily_note(date: Optional[str] = None) -> str:
    """
    Return the content of today's daily note (or a specific date's note),
    creating it with a template if it doesn't exist yet.

    Args:
        date: Date string in YYYY-MM-DD format. Defaults to today.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    path = Path("Daily") / f"{date}.md"
    full = _resolve(str(path))

    if full.exists():
        return full.read_text(encoding="utf-8")

    template = f"# {date}\n\n## Tasks\n- [ ] \n\n## Notes\n\n## Journal\n"
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(template, encoding="utf-8")
    return template


# ── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
