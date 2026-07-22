"""Validate Miller's definitive planning-control files and sprint graph."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'PROJECT_CHARTER.md','CURRENT_STATE.md','ARCHITECTURE.md','DECISIONS.md',
    'ROADMAP.md','SPRINT_INDEX.md','SPRINT_STATE.json','BLOCKERS.md',
    'RESEARCH_CATALOG.md','EXTERNAL_PROJECTS.md','EVALUATION_PLAN.md',
    'TEST_MATRIX.md','RISKS.md','HANDOFF.md','CHANGELOG_PLANNING.md',
    'docs/PLANNING_INDEX.md','docs/BOARD_REVIEWS.md','docs/SPRINT_CARDS.md',
    'docs/AGENT_ORCHESTRATION.md','docs/CONTEXT_PROTOCOL.md',
    'docs/REVIEW_PASSES.md','docs/LOCAL_ACCEPTANCE_TEST.md','docs/OWNER_DECISIONS.md',
}
CARD = re.compile(r'^## ([A-Z]{2,3}-\d{3}) — (.+)$', re.MULTILINE)
REQUIRED_CARD_FIELDS = (
    '**Parent roadmap item:**','**Exact objective:**','**Why it matters:**',
    '**Files allowed to inspect:**','**Files allowed to change:**',
    '**Files that must not be changed:**','**Required context:**','**Prerequisites:**',
    '**Inputs:**','**Detailed task sequence:**','**Expected outputs:**',
    '**Tests to add or run:**','**Acceptance criteria:**','**Failure conditions:**',
    '**Recovery instructions:**','**Logging requirements:**','**Documentation updates:**',
    '**Git checkpoint:**','**Estimated context load:**','**Recommended model:**',
    '**Codex review requirement:**','**Next unblocked sprint options:**',
)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def main() -> int:
    missing=sorted(path for path in REQUIRED if not (ROOT/path).is_file())
    require(not missing, f'missing planning files: {missing}')
    state=json.loads((ROOT/'SPRINT_STATE.json').read_text(encoding='utf-8'))
    require(state['schema_version']==2,'unexpected sprint state schema')
    entries=state['sprints']
    ids=[entry['id'] for entry in entries]
    require(len(ids)==len(set(ids)),'duplicate sprint IDs in state')
    known=set(ids)
    for entry in entries:
        require(set(entry['dependencies']) <= known, f"unknown dependency for {entry['id']}")
        require(entry['id'] not in entry['dependencies'],f"self dependency: {entry['id']}")
    active=state['active_sprint']
    require(active in known,'active sprint unknown')
    require(active not in state['completed_sprints'],'active sprint already completed')
    require(active not in state['blocked_sprints'],'active sprint also blocked')
    require(set(state['completed_sprints']) <= known,'unknown completed sprint')
    require(set(state['blocked_sprints']) <= known,'unknown blocked sprint')
    require(set(state['next_unblocked']) <= known,'unknown next-unblocked sprint')
    card_dir=ROOT/'docs/sprints'
    require(card_dir.is_dir(),'missing docs/sprints directory')
    card_files=sorted(card_dir.glob('*.md'))
    by_id={path.stem:path for path in card_files}
    require(set(by_id)==known,'card files differ from machine state')
    for sid in ids:
        block=by_id[sid].read_text(encoding='utf-8')
        heading=re.search(r'^# ([A-Z]{2,3}-\d{3}) — (.+)$',block,re.MULTILINE)
        require(heading is not None and heading.group(1)==sid,f'{sid} heading mismatch')
        for field in REQUIRED_CARD_FIELDS:
            require(field in block,f'{sid} missing field {field}')
    cards=(ROOT/'docs/SPRINT_CARDS.md').read_text(encoding='utf-8')
    require(all(f'sprints/{sid}.md' in cards for sid in ids),'card index missing link')
    index=(ROOT/'SPRINT_INDEX.md').read_text(encoding='utf-8')
    require(all(f'`{sid}`' in index for sid in ids),'sprint index missing ID')
    print(f'Planning verified: {len(ids)} sprint cards; active={active}; files={len(REQUIRED)}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
