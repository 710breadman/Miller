import json
import sys
from pathlib import Path

import pytest

from miller.analysis import (
    NormalizedBox,
    OcrResult,
    OcrSpan,
    PageAnalysis,
    PageDescription,
    PanelCandidate,
    PanelSource,
    TechnicalQuality,
)
from miller.artifacts import canonical_json_bytes, sha256_bytes
from miller.retrieval import (
    BenchmarkQuery,
    EvaluationSet,
    ExternalEmbeddingWorker,
    LexicalRetriever,
    RelevanceJudgment,
    calculate_metrics,
    fuse_scores,
    run_benchmark,
)


def page(letter: str, summary: str, ocr_text: str, character: str) -> PageAnalysis:
    page_id = "page_" + letter * 64
    return PageAnalysis(
        page_id=page_id,
        source_sha256=letter * 64,
        source_locator=f"Series/Issue/{letter}.png",
        image_width=800,
        image_height=1200,
        panels=(
            PanelCandidate(
                id=f"panel_{letter}_full",
                page_id=page_id,
                box=NormalizedBox(x=0, y=0, width=1, height=1),
                order=0,
                confidence=1,
                source=PanelSource.FULL_PAGE,
                is_full_page=True,
            ),
        ),
        ocr=OcrResult(
            engine="fixture",
            engine_version="1",
            language="eng",
            spans=(
                OcrSpan(
                    id=f"ocr_{letter}",
                    text=ocr_text,
                    box=NormalizedBox(x=0.1, y=0.1, width=0.4, height=0.1),
                    confidence=1,
                ),
            ),
        ),
        description=PageDescription(
            summary=summary,
            characters=(character,),
            confidence=1,
            generator="fixture",
        ),
        quality=TechnicalQuality(
            width=800,
            height=1200,
            aspect_ratio=2 / 3,
            brightness=0.5,
            contrast=0.5,
            sharpness=0.5,
            text_coverage=0.1,
            resolution_score=0.7,
            overall_score=0.6,
        ),
    )


def test_lexical_benchmark_metrics_are_reproducible() -> None:
    records = (
        page("a", "A hero accepts responsibility", "great power", "Peter"),
        page("b", "A detective watches the city", "vengeance", "Bruce"),
        page("c", "A cosmic battle begins", "stars collapse", "Nova"),
    )
    corpus_hash = "sha256:" + sha256_bytes(
        canonical_json_bytes([record.model_dump(mode="json") for record in records])
    )
    evaluation = EvaluationSet(
        name="fixture",
        corpus_hash=corpus_hash,
        queries=(
            BenchmarkQuery(
                id="query_responsibility",
                text="hero responsibility power",
                category="theme",
                judgments=(RelevanceJudgment(asset_id=records[0].page_id, relevance=3),),
            ),
            BenchmarkQuery(
                id="query_city",
                text="detective city vengeance",
                category="character",
                judgments=(RelevanceJudgment(asset_id=records[1].page_id, relevance=3),),
            ),
        ),
    )
    evaluation.validate_corpus({record.page_id for record in records})
    retriever = LexicalRetriever(records)
    report = run_benchmark(
        evaluation,
        retriever,
        name="bm25",
        version="1",
        top_k=3,
        parameters={"k1": 1.2, "b": 0.75},
    )
    assert report.metrics.recall_at[1] == 1
    assert report.metrics.mean_reciprocal_rank == 1
    assert report.metrics.ndcg_at[1] == 1
    recalculated = calculate_metrics(evaluation.queries, report.rankings)
    assert recalculated.recall_at == report.metrics.recall_at
    assert report.config.index_hash == retriever.index_hash


def test_evaluation_set_rejects_missing_assets() -> None:
    evaluation = EvaluationSet(
        name="fixture",
        corpus_hash="sha256:" + "a" * 64,
        queries=(
            BenchmarkQuery(
                id="query_missing",
                text="missing",
                category="fixture",
                judgments=(RelevanceJudgment(asset_id="page_missing", relevance=1),),
            ),
        ),
    )
    with pytest.raises(ValueError):
        evaluation.validate_corpus(set())


def test_hybrid_score_fusion_is_stable() -> None:
    records = (
        page("a", "hero responsibility", "power", "Peter"),
        page("b", "detective city", "vengeance", "Bruce"),
    )
    lexical = LexicalRetriever(records).search("hero", limit=10)
    fused = fuse_scores(
        lexical,
        {records[0].page_id: 0.4, records[1].page_id: 0.9},
        lexical_weight=0.8,
        semantic_weight=0.2,
    )
    assert fused[0].asset_id == records[0].page_id
    assert fused[0].rank == 1


def test_external_embedding_worker_contract(tmp_path: Path) -> None:
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import json, sys\n"
        "request = json.loads(sys.stdin.read())\n"
        "if request['operation'] == 'probe':\n"
        "    print(json.dumps({'name':'fixture','version':'1'}))\n"
        "else:\n"
        "    values = request.get('texts') or request.get('paths')\n"
        "    print(json.dumps({'model':'fixture','model_revision':'abc123',"
        "'dimensions':3,'vectors':[[1.0,0.0,0.0] for _ in values], 'warnings':[]}))\n",
        encoding="utf-8",
    )
    adapter = ExternalEmbeddingWorker((sys.executable, str(worker)))
    assert adapter.probe() == {"name": "fixture", "version": "1"}
    result = adapter.embed_text(("hero", "city"))
    assert result.dimensions == 3
    assert len(result.vectors) == 2
    assert json.loads(result.model_dump_json())["model_revision"] == "abc123"


def test_qdrant_vector_store_upsert_query_filter_and_rebuild() -> None:
    pytest.importorskip("qdrant_client")
    from miller.retrieval.qdrant_store import QdrantVectorStore
    from miller.retrieval.vector_store import VectorPoint

    store = QdrantVectorStore.memory()
    store.upsert(
        "comic_panels",
        (
            VectorPoint(
                id="panel_hero",
                vector=(1.0, 0.0, 0.0),
                payload={"series": "Alpha", "continuity": "main"},
            ),
            VectorPoint(
                id="panel_city",
                vector=(0.0, 1.0, 0.0),
                payload={"series": "Beta", "continuity": "main"},
            ),
            VectorPoint(
                id="panel_alt",
                vector=(0.9, 0.1, 0.0),
                payload={"series": "Alpha", "continuity": "alternate"},
            ),
        ),
    )

    all_matches = store.query("comic_panels", (1.0, 0.0, 0.0), limit=3)
    assert [match.id for match in all_matches][:2] == ["panel_hero", "panel_alt"]

    filtered = store.query(
        "comic_panels",
        (1.0, 0.0, 0.0),
        filters={"continuity": "alternate"},
    )
    assert [match.id for match in filtered] == ["panel_alt"]
    assert filtered[0].payload["series"] == "Alpha"

    store.upsert(
        "comic_panels",
        (
            VectorPoint(
                id="panel_city",
                vector=(1.0, 0.0, 0.0),
                payload={"series": "Beta", "continuity": "main"},
            ),
        ),
    )
    rebuilt = store.query("comic_panels", (1.0, 0.0, 0.0), limit=3)
    assert {match.id for match in rebuilt[:2]} == {"panel_hero", "panel_city"}
    assert store.delete_collection("comic_panels") is True
    assert store.delete_collection("comic_panels") is False
