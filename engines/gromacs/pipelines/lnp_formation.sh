#!/bin/bash
# LNP self-assembly pipeline (GROMACS Martini CG) — NOT USED IN PRODUCTION
# Production runs OpenMM via simulation_worker. This script must not emit canned results.

set -euo pipefail
RUN_ID="${1:?run_id required}"
DESIGN="${2:?design_json required}"

echo "[lnp_formation] ERROR: GROMACS pipeline not implemented for run ${RUN_ID}" >&2
echo "[lnp_formation] Design: ${DESIGN}" >&2
exit 1
