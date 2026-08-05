#!/bin/sh
set -eu
DEST="${1:-/app/martini_ff}"
mkdir -p "$DEST"
BASE="https://raw.githubusercontent.com/maccallumlab/martini_openmm/master/tests/popc_m3/openmm"
for f in martini_v3.0.0.itp martini_v3.0.0_phospholipids_v1.itp martini_v3.0.0_solvents_v1.itp; do
  echo "Fetching $f..."
  n=0
  until curl -fsSL "$BASE/$f" -o "$DEST/$f"; do
    n=$((n + 1))
    if [ "$n" -ge 5 ]; then
      echo "Failed to download $f after 5 attempts" >&2
      exit 1
    fi
    echo "Retry $n/5 for $f..."
    sleep 2
  done
done
echo "Martini 3 force field files installed in $DEST"
