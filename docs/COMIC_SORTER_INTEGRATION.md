# Comic Sorter bundle import

Miller accepts the file contract `comic-sorter.miller-bundle` major version 1:

```powershell
miller --db .miller/miller.sqlite3 import-comic-sorter `
  --project-id project_example `
  --bundle .\miller-bundle.json
```

The importer validates the complete bundle against Miller's packaged copy of Comic Sorter's JSON Schema before opening a transaction. It never opens Comic Sorter's SQLite database. One transaction stores the bundle checksum, original payload, candidate provenance IDs, narrative rank, evidence IDs, and technical hints. Reimporting identical content with the same bundle ID is a no-op; conflicting content is rejected.

Comic Sorter's narrative score remains a separate input. `ComicSorterBundleImporter.narrative_scores` supplies page-level values to `StoryboardBuilder`; the resulting `SceneScore` records narrative and technical quality separately. `combine_candidate_score` handles the fuller crop, text-mask, continuity, reuse, and narration-alignment comparison. Miller remains responsible for panel analysis, crops, masks, asset reuse, storyboards, and video production. Bundle provenance is also stored as a revisioned project document so portable project export retains it.
