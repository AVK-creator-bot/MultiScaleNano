#!/bin/bash
# Drug–LNP encapsulation pipeline (GROMACS) — NOT USED IN PRODUCTION
# Production runs OpenMM via simulation_worker. This script must not emit canned results.

set -euo pipefail
RUN_ID="${1:?run_id required}"
DESIGN="${2:?design_json required}"

echo "[drug_encapsulation] ERROR: GROMACS pipeline not implemented for run ${RUN_ID}" >&2
echo "[drug_encapsulation] Design: ${DESIGN}" >&2
exit 1
