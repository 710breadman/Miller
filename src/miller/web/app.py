# ruff: noqa: E501
"""Local-only FastAPI service and minimal storyboard editor."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from ..db import Database, DocumentConflict
from ..editor import (
    ReplaceAssetCommand,
    SaveStoryboardCommand,
    SetFocusCommand,
    SetLockCommand,
    SetMotionCommand,
    SetMusicCommand,
    SetTransitionCommand,
    StoryboardEditor,
    StoryboardSnapshot,
)
from ..models import Project

T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CreateProjectRequest(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    workspace: str = Field(min_length=1)
    project_id: str | None = Field(default=None, min_length=1, max_length=128)


class HealthResponse(ApiModel):
    status: str
    database: str


def _call(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except DocumentConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        message = exc.args[0] if exc.args else str(exc)
        raise HTTPException(status_code=404, detail=str(message)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def create_app(db_path: Path | str = ".miller/miller.sqlite3") -> FastAPI:
    """Create the local Miller API application."""

    database = Database(Path(db_path).expanduser().resolve())
    database.initialize()
    editor = StoryboardEditor(database)
    app = FastAPI(
        title="Miller",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", database=str(database.path))

    @app.post("/api/projects", response_model=Project, status_code=201)
    def create_project(request: CreateProjectRequest) -> Project:
        return _call(
            lambda: database.create_project(
                request.name,
                request.workspace,
                request.project_id,
            )
        )

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str) -> dict[str, object]:
        project = _call(lambda: database.get_project(project_id))
        stages = database.list_stage_runs(project_id)
        return {
            "project": project.model_dump(mode="json"),
            "stages": [stage.model_dump(mode="json") for stage in stages],
        }

    @app.get(
        "/api/projects/{project_id}/storyboard",
        response_model=StoryboardSnapshot,
    )
    def get_storyboard(project_id: str) -> StoryboardSnapshot:
        return _call(lambda: editor.get(project_id))

    @app.put(
        "/api/projects/{project_id}/storyboard",
        response_model=StoryboardSnapshot,
    )
    def save_storyboard(
        project_id: str, command: SaveStoryboardCommand
    ) -> StoryboardSnapshot:
        return _call(lambda: editor.save(project_id, command))

    @app.get(
        "/api/projects/{project_id}/storyboard/history",
        response_model=tuple[StoryboardSnapshot, ...],
    )
    def storyboard_history(project_id: str) -> tuple[StoryboardSnapshot, ...]:
        return _call(lambda: editor.history(project_id))

    @app.post(
        "/api/projects/{project_id}/commands/replace-asset",
        response_model=StoryboardSnapshot,
    )
    def replace_asset(
        project_id: str, command: ReplaceAssetCommand
    ) -> StoryboardSnapshot:
        return _call(lambda: editor.replace_asset(project_id, command))

    @app.post(
        "/api/projects/{project_id}/commands/motion",
        response_model=StoryboardSnapshot,
    )
    def set_motion(project_id: str, command: SetMotionCommand) -> StoryboardSnapshot:
        return _call(lambda: editor.set_motion(project_id, command))

    @app.post(
        "/api/projects/{project_id}/commands/focus",
        response_model=StoryboardSnapshot,
    )
    def set_focus(project_id: str, command: SetFocusCommand) -> StoryboardSnapshot:
        return _call(lambda: editor.set_focus(project_id, command))

    @app.post(
        "/api/projects/{project_id}/commands/transition",
        response_model=StoryboardSnapshot,
    )
    def set_transition(
        project_id: str, command: SetTransitionCommand
    ) -> StoryboardSnapshot:
        return _call(lambda: editor.set_transition(project_id, command))

    @app.post(
        "/api/projects/{project_id}/commands/lock",
        response_model=StoryboardSnapshot,
    )
    def set_lock(project_id: str, command: SetLockCommand) -> StoryboardSnapshot:
        return _call(lambda: editor.set_lock(project_id, command))

    @app.post(
        "/api/projects/{project_id}/commands/music",
        response_model=StoryboardSnapshot,
    )
    def set_music(project_id: str, command: SetMusicCommand) -> StoryboardSnapshot:
        return _call(lambda: editor.set_music(project_id, command))

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> HTMLResponse:
        return HTMLResponse(_EDITOR_HTML)

    return app


_EDITOR_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Miller Storyboard Editor</title>
<style>
:root { color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; }
body { margin: 0; background: #111318; color: #eef1f5; }
header { position: sticky; top: 0; z-index: 2; padding: 14px 18px; background: #171a20; border-bottom: 1px solid #303641; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
input, select, button { background: #222731; color: inherit; border: 1px solid #3b4350; border-radius: 7px; padding: 8px 10px; }
button { cursor: pointer; } button:hover { background: #303744; }
main { max-width: 1200px; margin: 0 auto; padding: 18px; }
#status { min-height: 1.5em; color: #aeb8c8; }
.scene { display: grid; grid-template-columns: 110px 1fr; gap: 14px; margin: 12px 0; padding: 14px; background: #191d24; border: 1px solid #303641; border-radius: 10px; }
.time { color: #9fb0c8; font-variant-numeric: tabular-nums; }
.narration { font-size: 1.05rem; line-height: 1.45; margin-bottom: 10px; }
.asset { font-family: ui-monospace, Consolas, monospace; overflow-wrap: anywhere; }
.controls, .alternatives { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
.locked { border-color: #b48b39; }
.badge { padding: 3px 7px; border-radius: 99px; background: #283140; font-size: .78rem; }
@media (max-width: 650px) { .scene { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <div class="toolbar">
    <strong>Miller</strong>
    <input id="project" placeholder="project ID" value="project_demo">
    <button onclick="loadStoryboard()">Load storyboard</button>
    <span id="revision" class="badge">revision —</span>
  </div>
</header>
<main>
  <div id="status">Enter a project ID whose storyboard is already generated.</div>
  <div id="scenes"></div>
</main>
<script>
let snapshot = null;
const motions = ["static","slow_push","slow_pull","pan_left","pan_right"];
const transitions = ["cut","crossfade","dip_black"];
const projectId = () => document.getElementById("project").value.trim();
const status = (message, bad=false) => {
  const node = document.getElementById("status"); node.textContent = message;
  node.style.color = bad ? "#ff9b9b" : "#aeb8c8";
};
const escapeHtml = value => String(value).replace(/[&<>'"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]));
async function api(path, options={}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data;
}
async function loadStoryboard() {
  try {
    status("Loading…");
    snapshot = await api(`/api/projects/${encodeURIComponent(projectId())}/storyboard`);
    render(); status(`Loaded ${snapshot.storyboard.scenes.length} scenes.`);
  } catch (error) { status(error.message, true); }
}
async function command(name, sceneId, values={}) {
  try {
    const payload = {expected_revision:snapshot.revision, scene_id:sceneId, ...values};
    snapshot = await api(`/api/projects/${encodeURIComponent(projectId())}/commands/${name}`, {method:"POST", body:JSON.stringify(payload)});
    render(); status(`Saved revision ${snapshot.revision}.`);
  } catch (error) { status(error.message, true); if (String(error.message).includes("revision")) loadStoryboard(); }
}
function options(values, selected) { return values.map(v => `<option ${v===selected?'selected':''}>${v}</option>`).join(""); }
function render() {
  document.getElementById("revision").textContent = `revision ${snapshot.revision}`;
  document.getElementById("scenes").innerHTML = snapshot.storyboard.scenes.map(scene => `
    <section class="scene ${scene.locked?'locked':''}">
      <div><div class="time">${scene.start.toFixed(2)}–${scene.end.toFixed(2)}s</div><div class="badge">${escapeHtml(scene.id)}</div></div>
      <div>
        <div class="narration">${escapeHtml(scene.narration)}</div>
        <div>Primary: <span class="asset">${escapeHtml(scene.primary_asset)}</span></div>
        <div class="alternatives">${scene.alternatives.map(a => `<button ${scene.locked?'disabled':''} onclick="command('replace-asset','${scene.id}',{asset_id:'${escapeHtml(a)}'})">Use ${escapeHtml(a)}</button>`).join("")}</div>
        <div class="controls">
          <select ${scene.locked?'disabled':''} onchange="command('motion','${scene.id}',{preset:this.value})">${options(motions, scene.camera.preset)}</select>
          <select ${scene.locked?'disabled':''} onchange="command('transition','${scene.id}',{transition:this.value})">${options(transitions, scene.transition)}</select>
          <input ${scene.locked?'disabled':''} value="${escapeHtml(scene.music_state)}" aria-label="music state" onchange="command('music','${scene.id}',{music_state:this.value})">
          <button onclick="command('lock','${scene.id}',{locked:${!scene.locked}})">${scene.locked?'Unlock':'Lock'}</button>
        </div>
      </div>
    </section>`).join("");
}
const query = new URLSearchParams(location.search).get("project");
if (query) { document.getElementById("project").value = query; loadStoryboard(); }
</script>
</body>
</html>"""
