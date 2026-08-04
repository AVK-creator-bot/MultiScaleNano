"""Simple JSON file persistence for local dev (survives API reloads)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from multiscale_core.paths import ARTIFACT_DIR

STORE_DIR = ARTIFACT_DIR.parent / "store"
STORE_DIR.mkdir(parents=True, exist_ok=True)

T = TypeVar("T", bound=BaseModel)


class JsonStore(Generic[T]):
    def __init__(self, name: str, model: type[T]):
        self.path = STORE_DIR / f"{name}.json"
        self.model = model
        self._cache: dict[UUID, T] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._cache = {UUID(k): self.model.model_validate(v) for k, v in raw.items()}

    def _save(self) -> None:
        raw = {str(k): v.model_dump(mode="json") for k, v in self._cache.items()}
        self.path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    def get(self, id: UUID) -> T | None:
        self._load()
        return self._cache.get(id)

    def set(self, id: UUID, value: T) -> None:
        self._load()
        self._cache[id] = value
        self._save()

    def values(self) -> list[T]:
        self._load()
        return list(self._cache.values())

    def __contains__(self, id: UUID) -> bool:
        self._load()
        return id in self._cache
