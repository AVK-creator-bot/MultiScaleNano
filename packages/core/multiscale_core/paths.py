"""Shared filesystem paths."""

import os
from pathlib import Path

# Project-root-relative artifact store (override via MULTISCALE_ARTIFACT_DIR)
ARTIFACT_DIR = Path(os.environ.get("MULTISCALE_ARTIFACT_DIR", "data/artifacts"))
