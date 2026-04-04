#!/usr/bin/env python3

from __future__ import annotations

import json

from aegisops_control_plane.service import build_runtime_snapshot


def main() -> int:
    snapshot = build_runtime_snapshot()
    print(json.dumps(snapshot.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
