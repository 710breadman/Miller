"""Qdrant implementation of Miller's rebuildable vector-store contract."""

from __future__ import annotations

import importlib
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .vector_store import FilterValues, Payload, VectorMatch, VectorPoint

_RESERVED_ID = "_miller_id"


def _qdrant_modules() -> tuple[Any, Any]:
    """Load the optional Qdrant dependency only when this adapter is used."""

    try:
        client_module = importlib.import_module("qdrant_client")
        models_module = importlib.import_module("qdrant_client.http.models")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Qdrant support is not installed; install Miller with the retrieval extra"
        ) from exc
    return client_module.QdrantClient, models_module


class QdrantVectorStore:
    """Metadata-aware cosine vector search through the official client.

    Use :meth:`memory` only for tests. Version 1 production should connect to a
    pinned Qdrant service bound to localhost.
    """

    def __init__(self, client: Any) -> None:
        self.client = client
        _, self.models = _qdrant_modules()

    @classmethod
    def service(
        cls,
        url: str = "http://127.0.0.1:6333",
        *,
        timeout_seconds: int = 30,
    ) -> QdrantVectorStore:
        client_type, _ = _qdrant_modules()
        return cls(client_type(url=url, timeout=timeout_seconds))

    @classmethod
    def persisted_test_store(cls, path: Path | str) -> QdrantVectorStore:
        client_type, _ = _qdrant_modules()
        return cls(client_type(path=str(Path(path).expanduser().resolve())))

    @classmethod
    def memory(cls) -> QdrantVectorStore:
        client_type, _ = _qdrant_modules()
        return cls(client_type(":memory:"))

    def ensure_collection(self, name: str, vector_size: int) -> None:
        self._validate_collection_name(name)
        if vector_size <= 0:
            raise ValueError("vector size must be positive")
        if not self.client.collection_exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=self.models.VectorParams(
                    size=vector_size,
                    distance=self.models.Distance.COSINE,
                ),
            )
            return
        info = self.client.get_collection(name)
        vectors = info.config.params.vectors
        if not isinstance(vectors, self.models.VectorParams):
            raise ValueError(f"collection {name!r} does not use one unnamed dense vector")
        if vectors.size != vector_size or vectors.distance != self.models.Distance.COSINE:
            raise ValueError(
                f"collection {name!r} configuration mismatch: "
                f"expected cosine/{vector_size}, got {vectors.distance}/{vectors.size}"
            )

    def upsert(self, collection: str, points: Sequence[VectorPoint]) -> None:
        self._validate_collection_name(collection)
        if not points:
            return
        expected_size = len(points[0].vector)
        if any(len(point.vector) != expected_size for point in points):
            raise ValueError("all vectors in one upsert must have equal dimensions")
        self.ensure_collection(collection, expected_size)
        qdrant_points = [
            self.models.PointStruct(
                id=self._point_id(point.id),
                vector=list(point.vector),
                payload={**point.payload, _RESERVED_ID: point.id},
            )
            for point in points
        ]
        self.client.upsert(collection_name=collection, points=qdrant_points, wait=True)

    def query(
        self,
        collection: str,
        vector: Sequence[float],
        *,
        limit: int = 20,
        filters: FilterValues | None = None,
    ) -> tuple[VectorMatch, ...]:
        self._validate_collection_name(collection)
        if not vector or any(not math.isfinite(float(component)) for component in vector):
            raise ValueError("query vector must be non-empty and finite")
        if limit <= 0 or limit > 1000:
            raise ValueError("query limit must be between 1 and 1000")
        response = self.client.query_points(
            collection_name=collection,
            query=[float(component) for component in vector],
            query_filter=self._filter(filters),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        matches: list[VectorMatch] = []
        for point in response.points:
            raw_payload = point.payload or {}
            asset_id = raw_payload.get(_RESERVED_ID)
            if not isinstance(asset_id, str) or not asset_id:
                raise RuntimeError("Qdrant result is missing Miller asset identity")
            payload = self._normalized_payload(raw_payload)
            matches.append(VectorMatch(id=asset_id, score=float(point.score), payload=payload))
        return tuple(matches)

    def delete_collection(self, name: str) -> bool:
        self._validate_collection_name(name)
        if not self.client.collection_exists(name):
            return False
        return bool(self.client.delete_collection(name))

    @staticmethod
    def _point_id(asset_id: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"miller-vector:{asset_id}"))

    def _filter(self, filters: FilterValues | None) -> Any:
        if not filters:
            return None
        conditions = [
            self.models.FieldCondition(key=key, match=self.models.MatchValue(value=value))
            for key, value in sorted(filters.items())
        ]
        return self.models.Filter(must=conditions)

    @staticmethod
    def _normalized_payload(payload: dict[str, Any]) -> Payload:
        normalized: Payload = {}
        for key, value in payload.items():
            if key == _RESERVED_ID:
                continue
            if value is None or isinstance(value, str | int | float | bool):
                normalized[key] = value
            else:
                raise RuntimeError(f"unsupported Qdrant payload value for {key!r}")
        return normalized

    @staticmethod
    def _validate_collection_name(name: str) -> None:
        if not name or len(name) > 255:
            raise ValueError("collection name must contain 1 to 255 characters")
