"""Active MD force-field selection."""

from __future__ import annotations

import os


def requested_force_field() -> str:
    return os.environ.get("MULTISCALE_FORCE_FIELD", "martini3").strip().lower()


def prefer_martini3() -> bool:
    return requested_force_field() not in ("lj", "legacy", "lj_coarse_grained")


def provenance_force_field(use_martini: bool) -> str:
    return "martini3" if use_martini else "lj_coarse_grained"
