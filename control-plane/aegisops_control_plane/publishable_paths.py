from __future__ import annotations

import pathlib
import re
from pathlib import PureWindowsPath


REDACTED_LOCAL_PATH_TOKEN = "<redacted-local-path>"
ALLOWLIST_MARKER = "publishable-path-hygiene: allowlist"

_WINDOWS_USER_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]+Users[\\/]+[^\\/]+(?:[\\/](?P<rest>.*))?$")


def _is_relative_to(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def is_workstation_local_path(text: str) -> bool:
    return "/Users/" in text or "/home/" in text or bool(re.search(r"[A-Za-z]:\\Users\\", text))


def normalize_publishable_path(
    path: str | pathlib.Path,
    *,
    repo_root: str | pathlib.Path | None = None,
    home: str | pathlib.Path | None = None,
) -> str:
    raw = str(path).strip()
    if not raw:
        return raw

    windows_match = _WINDOWS_USER_PATH_RE.match(raw.replace("/", "\\"))
    if windows_match:
        rest = windows_match.group("rest") or ""
        rest = PureWindowsPath(rest).as_posix() if rest else ""
        return (
            f"{REDACTED_LOCAL_PATH_TOKEN}/{rest}"
            if rest
            else REDACTED_LOCAL_PATH_TOKEN
        )

    candidate = pathlib.Path(raw).expanduser()
    if not candidate.is_absolute():
        return candidate.as_posix() if isinstance(path, pathlib.Path) else raw

    resolved = candidate.resolve(strict=False)
    repo_root_path = pathlib.Path(repo_root).resolve(strict=False) if repo_root else None
    if repo_root_path and _is_relative_to(resolved, repo_root_path):
        return resolved.relative_to(repo_root_path).as_posix()

    home_path = pathlib.Path(home).expanduser().resolve(strict=False) if home else pathlib.Path.home().resolve(strict=False)
    if _is_relative_to(resolved, home_path):
        relative = resolved.relative_to(home_path).as_posix()
        return (
            f"{REDACTED_LOCAL_PATH_TOKEN}/{relative}"
            if relative and relative != "."
            else REDACTED_LOCAL_PATH_TOKEN
        )

    return REDACTED_LOCAL_PATH_TOKEN
