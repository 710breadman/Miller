# Sub-sprint template

Each sub-sprint should fit one focused Codex run and one reviewable commit.

```markdown
### X.Y — Short outcome name

Outcome: one concrete artifact or behavior.

Inputs:

- only prior artifacts required to begin

Work:

- 1–4 tightly related implementation items

Gate:

- exact command/test/artifact proving completion

Exclude:

- tempting adjacent work reserved for later sub-sprints
```

## Sizing rules

- One cohesive outcome.
- Prefer 1–4 production files plus focused tests; generated migrations/fixtures
  may exceed this.
- One primary failure mode.
- Verification runs locally without subjective completion claims.
- No hidden dependency on future sub-sprints.
- If estimated context exceeds one focused run, split before coding.

## Completion record

Update:

1. `STATUS.md`: completed result, evidence, decisions/failures, next exact step.
2. `SPRINT_STATE.json`: append completed ID; advance `active_sub_sprint` once.
3. Tests/artifact checks.
4. Commit with sub-sprint ID in message when committing is requested.
