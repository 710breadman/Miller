# Comic Sorter bundle import

Miller accepts the file contract `comic-sorter.miller-bundle` major version 1:

```powershell
miller --db .miller/miller.sqlite3 import-comic-sorter `
  --project-id project_example `
  --bundle .\miller-bundle.json
```

The importer validates the complete bundle against Miller's packaged copy of Comic Sorter's JSON Schema before opening a transaction. It never opens Comic Sorter's SQLite database. One transaction stores the bundle checksum, original payload, candidate provenance IDs, narrative rank, evidence IDs, and technical hints. Reimporting identical content with the same bundle ID is a no-op; conflicting content is rejected.

Comic Sorter's narrative score remains a separate input. `combine_candidate_score` combines it with Miller-owned technical quality, crop, text-mask, continuity, reuse, and narration-alignment components. Miller remains responsible for panel analysis, crops, masks, asset reuse, storyboards, and video production.
