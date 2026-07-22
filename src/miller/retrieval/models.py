"""Versioned retrieval benchmark records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RetrievalModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RelevanceJudgment(RetrievalModel):
    asset_id: str = Field(min_length=1)
    relevance: int = Field(ge=0, le=3)


class BenchmarkQuery(RetrievalModel):
    id: str = Field(pattern=r"^query_[A-Za-z0-9_.-]+$")
    text: str = Field(min_length=1, max_length=2000)
    category: str = Field(min_length=1, max_length=100)
    judgments: tuple[RelevanceJudgment, ...]
    notes: str = Field(default="", max_length=2000)

    @field_validator("judgments")
    @classmethod
    def validate_judgments(
        cls, value: tuple[RelevanceJudgment, ...]
    ) -> tuple[RelevanceJudgment, ...]:
        ids = [judgment.asset_id for judgment in value]
        if len(ids) != len(set(ids)):
            raise ValueError("query judgments must have unique asset IDs")
        if not any(judgment.relevance > 0 for judgment in value):
            raise ValueError("query requires at least one relevant asset")
        return value


class EvaluationSet(RetrievalModel):
    schema_version: int = Field(default=1, ge=1)
    name: str = Field(min_length=1, max_length=200)
    corpus_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    queries: tuple[BenchmarkQuery, ...]

    @field_validator("queries")
    @classmethod
    def validate_queries(cls, value: tuple[BenchmarkQuery, ...]) -> tuple[BenchmarkQuery, ...]:
        if not value:
            raise ValueError("evaluation set must contain queries")
        ids = [query.id for query in value]
        if len(ids) != len(set(ids)):
            raise ValueError("evaluation query IDs must be unique")
        return value

    def validate_corpus(self, asset_ids: set[str]) -> None:
        missing = sorted(
            {
                judgment.asset_id
                for query in self.queries
                for judgment in query.judgments
                if judgment.asset_id not in asset_ids
            }
        )
        if missing:
            raise ValueError(f"evaluation set references missing assets: {missing}")


class RankedAsset(RetrievalModel):
    asset_id: str = Field(min_length=1)
    score: float
    rank: int = Field(ge=1)
    components: dict[str, float] = Field(default_factory=dict)


class QueryRanking(RetrievalModel):
    query_id: str = Field(pattern=r"^query_[A-Za-z0-9_.-]+$")
    results: tuple[RankedAsset, ...]
    latency_ms: float = Field(ge=0.0)

    @field_validator("results")
    @classmethod
    def validate_ranks(cls, value: tuple[RankedAsset, ...]) -> tuple[RankedAsset, ...]:
        if [item.rank for item in value] != list(range(1, len(value) + 1)):
            raise ValueError("result ranks must be contiguous and one-based")
        ids = [item.asset_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("ranked assets must be unique")
        return value


class RetrievalMetrics(RetrievalModel):
    recall_at: dict[int, float]
    mean_reciprocal_rank: float = Field(ge=0.0, le=1.0)
    ndcg_at: dict[int, float]
    mean_latency_ms: float = Field(ge=0.0)


class RetrievalRunConfig(RetrievalModel):
    retriever: str = Field(min_length=1, max_length=200)
    retriever_version: str = Field(min_length=1, max_length=200)
    top_k: int = Field(default=20, ge=1, le=1000)
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    index_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class RetrievalBenchmarkReport(RetrievalModel):
    schema_version: int = Field(default=1, ge=1)
    evaluation_name: str = Field(min_length=1)
    corpus_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    config: RetrievalRunConfig
    rankings: tuple[QueryRanking, ...]
    metrics: RetrievalMetrics

    @model_validator(mode="after")
    def validate_query_count(self) -> RetrievalBenchmarkReport:
        if not self.rankings:
            raise ValueError("benchmark report must contain rankings")
        return self
