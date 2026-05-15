#!/usr/bin/env bash
set -euo pipefail

uv run python control-plane/tests/test_phase61_7_record_search_filter.py
npm run test --workspace @aegisops/operator-ui -- OperatorRoutes.test.tsx
