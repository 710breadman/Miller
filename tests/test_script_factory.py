from pathlib import Path

import pytest

from miller.artifacts import sha256_bytes
from miller.db import Database
from miller.script_factory import (
    EvidenceClaim,
    EvidenceLedger,
    EvidenceSource,
    LocalTextProvider,
    ScriptFactory,
    ScriptFactoryRequest,
    ScriptFactoryService,
    SourceKind,
    StubGenerator,
    SupportLevel,
)


def ledger() -> EvidenceLedger:
    source = EvidenceSource(
        id="source_asm50",
        kind=SourceKind.COMIC,
        title="Amazing Spider-Man 50",
        locator="ASM 50 pages 17-19",
        excerpt="Peter quits, the city worsens, and responsibility pulls him back.",
        content_hash="sha256:" + "a" * 64,
    )
    claim = EvidenceClaim(
        id="claim_responsibility",
        statement="Peter returns because responsibility outweighs his desire to quit.",
        source_ids=(source.id,),
        support=SupportLevel.STRONG,
        confidence=0.95,
    )
    return EvidenceLedger(sources=(source,), claims=(claim,))


def responses() -> list[dict[str, object]]:
    return [
        {
            "candidates": [
                {
                    "id": "frame_01",
                    "thesis": "Responsibility keeps pulling Peter back.",
                    "viewer_promise": "Explain why quitting cannot free him.",
                    "claim_ids": ["claim_responsibility"],
                    "confidence": 0.9,
                }
            ]
        },
        {
            "title": "Why Peter Cannot Quit",
            "thesis": "Responsibility keeps pulling Peter back.",
            "sections": [
                {
                    "id": "section_01",
                    "title": "The attempt to leave",
                    "purpose": "Set up the conflict.",
                    "claim_ids": ["claim_responsibility"],
                    "target_words": 300,
                }
            ],
        },
        {
            "text": "Peter tries to quit, but responsibility pulls him back.",
            "claim_ids_used": ["claim_responsibility"],
        },
        {
            "text": "Peter tries to quit, but responsibility pulls him back.",
            "claim_ids_used": ["claim_responsibility"],
            "findings": [],
        },
        {
            "text": "Peter wants out. Responsibility will not let him stay gone.",
            "claim_ids_used": ["claim_responsibility"],
        },
    ]


def test_local_text_provider_is_read_only_and_ranked(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    text = "Peter Parker learns that responsibility keeps calling him back."
    path.write_text(text, encoding="utf-8")
    before = path.read_bytes()
    results = LocalTextProvider((tmp_path,)).search("Peter responsibility")
    assert len(results) == 1
    assert results[0].score == 2
    assert results[0].content_hash == "sha256:" + sha256_bytes(before)
    assert path.read_bytes() == before


def test_script_factory_validates_and_persists_every_stage(tmp_path: Path) -> None:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Script", tmp_path / "workspace", "project_script")
    factory = ScriptFactory(StubGenerator(responses()))
    service = ScriptFactoryService(database, factory)
    package = service.run(
        "project_script",
        ScriptFactoryRequest(
            briefing="Explain why Peter can never really leave the role.",
            ledger=ledger(),
            target_words=1200,
        ),
    )
    assert package.final.text.startswith("Peter wants out")
    assert database.get_document("project_script", "script.final").revision == 1
    assert len(database.list_events("project_script")) >= 7


def test_unknown_generated_claim_is_rejected() -> None:
    bad = responses()
    bad[0] = {
        "candidates": [
            {
                "id": "frame_01",
                "thesis": "Invented",
                "viewer_promise": "Invented",
                "claim_ids": ["claim_fake"],
                "confidence": 1,
            }
        ]
    }
    with pytest.raises(ValueError, match="unknown claims"):
        ScriptFactory(StubGenerator(bad)).run(
            ScriptFactoryRequest(briefing="Test", ledger=ledger())
        )
