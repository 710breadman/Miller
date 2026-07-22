# Project and workspace format

SQLite is the authoritative project record. Files are immutable inputs or managed
artifacts referenced from that database.

```text
<workspace>/
├── projects/
│   └── <project-id>/
│       ├── artifacts/
│       ├── logs/
│       │   └── events.jsonl
│       └── tmp/
└── cache/
    ├── artifacts/<sha-prefix>/<sha>.<ext>
    └── comics/
        ├── pages/<sha-prefix>/<sha>.<source-ext>
        └── thumbnails/<sha-prefix>/<sha>.png
```

## Rules

- Project IDs are safe path components.
- Source comics, narration, scripts, music, and user media remain outside the
  workspace unless explicitly copied into a future portable export.
- Managed artifacts are addressed by SHA-256 content identity and verified on read.
- Temporary writes occur beside their final destination and are atomically replaced.
- JSON artifacts use canonical key ordering and UTF-8 encoding.
- A project export must include a manifest of every included file and hash.
- Cache entries are rebuildable and never the sole copy of user-authored state.
