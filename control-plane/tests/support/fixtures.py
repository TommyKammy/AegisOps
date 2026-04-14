from __future__ import annotations

import json
import pathlib


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "wazuh"


def load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))

