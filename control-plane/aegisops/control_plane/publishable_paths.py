from __future__ import annotations

import pathlib
import re
from pathlib import PureWindowsPath


REDACTED_LOCAL_PATH_TOKEN = "<redacted-local-path>"
ALLOWLIST_MARKER = "publishable-path-hygiene: allowlist"
_MAC_HOME_PREFIX = "/" + "Users" + "/"

_WINDOWS_USER_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]+Users[\\/]+[^\\/]+(?:[\\/](?P<rest>.*))?$")
_UNIX_USER_PATH_IN_TEXT_RE = re.compile(r"/(?:Users|home)/[^/\s]+(?:/[^\s]*)?")
_WINDOWS_USER_PATH_IN_TEXT_RE = re.compile(
    r"(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+(?:[\\/][^\s]*)?"
)
_BLOCKED_TEXT_PATH_PREFIX_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./\\-"
)
_WINDOWS_DRIVE_PREFIX_RE = re.compile(r"(?:^|[^A-Za-z0-9_])[A-Za-z]:$")


def _is_relative_to(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_text_path_boundary(text: str, start: int) -> bool:
    return start == 0 or text[start - 1] not in _BLOCKED_TEXT_PATH_PREFIX_CHARACTERS


def _has_windows_drive_prefix(text: str, start: int) -> bool:
    return bool(_WINDOWS_DRIVE_PREFIX_RE.search(text[:start]))


def is_workstation_local_path(text: str) -> bool:
    for match in _WINDOWS_USER_PATH_IN_TEXT_RE.finditer(text):
        if _has_text_path_boundary(text, match.start()):
            return True

    for match in _UNIX_USER_PATH_IN_TEXT_RE.finditer(text):
        if not _has_text_path_boundary(text, match.start()):
            continue
        if match.group(0).startswith(_MAC_HOME_PREFIX) and _has_windows_drive_prefix(
            text, match.start()
        ):
            continue
        return True

    return False


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
