"""Comic retrieval, benchmarking, and optional embedding workers."""

from .benchmark import Retriever, run_benchmark
from .embedding_worker import EmbeddingWorkerResult, ExternalEmbeddingWorker
from .hybrid import fuse_scores
from .lexical import LexicalRetriever, tokenize
from .metrics import calculate_metrics
from .models import (
    BenchmarkQuery,
    EvaluationSet,
    QueryRanking,
    RankedAsset,
    RelevanceJudgment,
    RetrievalBenchmarkReport,
    RetrievalMetrics,
    RetrievalRunConfig,
)
from .vector_store import VectorMatch, VectorPoint, VectorStore

__all__ = [
    "BenchmarkQuery",
    "EmbeddingWorkerResult",
    "EvaluationSet",
    "ExternalEmbeddingWorker",
    "LexicalRetriever",
    "QueryRanking",
    "RankedAsset",
    "RelevanceJudgment",
    "Retriever",
    "RetrievalBenchmarkReport",
    "RetrievalMetrics",
    "RetrievalRunConfig",
    "VectorMatch",
    "VectorPoint",
    "VectorStore",
    "calculate_metrics",
    "fuse_scores",
    "run_benchmark",
    "tokenize",
]
