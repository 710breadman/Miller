# Owner decisions still required

Only decisions that materially affect architecture, release, or acceptance are listed.

| ID | Decision | Recommended default | Why it matters | Needed by |
|---|---|---|---|---|
| OWN-001 | Confirm canonical local repo/workspace paths | repo `V:\AI\Miller`; managed workspace inside/alongside it, subject to local verification | removes stale `D:\_Codex\Miller` assumptions | `ENV-001` |
| OWN-002 | Approve private acceptance/evaluation corpus | 3–10 varied issues plus a 30–90 second fixture; never commit media | unlocks analysis, retrieval, and visual gates | `ENV-002`, `ANL-001` |
| OWN-003 | Choose default normal/deep-dive duration | normal 13–18 minutes, configurable; deep dive separate | affects beat count, render performance, UI defaults | `DOC-001`, `QAE-002` |
| OWN-004 | Select Miller software license | Apache-2.0 unless simplicity is preferred over patent grant, then MIT | required for public distribution/contributors | `REL-002` |
| OWN-005 | Approve public fixture policy | synthetic and freely licensed fixtures only; private corpus referenced by hashes | protects copyrighted media | `ANL-001`, `SEC-002` |
| OWN-006 | Define minimum visual acceptance | use rubric in `EVALUATION_PLAN.md`; relevance/emotional support outrank flashy effects | determines model/storyboard winner | `QAE-001` |
| OWN-007 | Decide quotation/subtitle policy | actual quotations only from user-provided/verified sources; no on-screen comic text by default | affects script evidence and cleanup | script/visual polish |
| OWN-008 | Confirm Resolve support importance | optional after polished v1 | avoids blocking on proprietary software | `ADV-003` |
| OWN-009 | Permit optional external model downloads | yes, explicit per-model install with recorded license/hash | enables capable local workers without bloating core | model sprints |
| OWN-010 | Feedback learning policy | store edits/ratings; train/tune only after explicit dataset approval | protects privacy and avoids silent degradation | post-v1 |
| OWN-011 | Choose subtitle default | off by default; optional per project/export | matches no-on-screen-text preference while preserving accessibility/export | `DOC-001`, `UX-001` |
| OWN-012 | Confirm public/commercial distribution intent | private/local development until explicitly approved | controls license, codec, model/data, and release obligations | `SEC-002`, `REL-002` |

Lower-impact choices should use the recorded defaults and remain configurable rather than interrupting work.
