# Threat model

## Scope

Miller is a local application that reads user-selected comics, scripts,
narration, music, model files, and project data. It launches local tools such as
FFmpeg and later isolated AI workers. The computer owner is trusted; imported
files and third-party tools are not automatically trusted.

## Protected assets

- Original comic archives and image folders
- Narration, scripts, music, and user media
- Project state, edit decisions, provenance, and render history
- Credentials or API keys used by optional research providers
- Local machine availability, storage, GPU time, and private library metadata

## Trust boundaries

1. User-selected source paths → read-only ingestion code
2. CBZ/ZIP contents → decompression and image decoders
3. Miller core → FFmpeg and future worker subprocesses
4. Worker output → core validation and transactional state commit
5. Local web UI → localhost API
6. SQLite source of truth → rebuildable caches and vector stores
7. Downloaded models/tools → provenance, checksums, licenses, and capability probes

## Required controls

### Filesystem

- Never write below a source root.
- Resolve and verify every managed output remains below the configured workspace.
- Reject archive paths that are absolute, contain `..`, use Windows drive syntax,
  contain backslashes, or normalize to duplicates.
- Treat symlinks and junctions as possible escape paths.
- Use atomic writes followed by integrity verification.
- Cache deletion must support dry-run and protected-path checks.

### Archives and images

- Bound archive entry count, individual expanded size, total expanded size, and
  compression ratio.
- Reject encrypted members and unsupported image types.
- Validate decoded image dimensions and content before accepting page records.
- Run risky or historically vulnerable decoders in isolated workers when practical.
- Keep synthetic malicious fixtures for ZIP-slip, duplicate paths, oversized files,
  corrupt images, and suspicious compression ratios.

### Subprocesses

- Pass argument arrays directly; never concatenate user input into a shell command.
- Record exact executable path, version, arguments, timeout, exit code, and stderr.
- Use bounded timeouts and cooperative cancellation followed by forced termination.
- Workers receive scoped input/output directories, not unrestricted project control.
- Worker output cannot complete a stage without the current attempt ID and lease token.

### State and database

- Enable SQLite foreign keys and busy timeout on every connection.
- Use one core-owned transition layer and `BEGIN IMMEDIATE` for state mutation.
- Preserve immutable attempts and append-only events.
- Mark interrupted attempts abandoned during startup recovery.
- Do not place SQLite WAL databases on SMB/network storage.
- Pin a SQLite build with current WAL fixes before enabling concurrent WAL use.

### Local services

- Bind the future API, Qdrant, and worker control ports to loopback by default.
- Do not expose unauthenticated Qdrant or development servers to a LAN.
- Protect state-changing API routes against cross-site requests.
- Use a per-launch local authorization secret if browser-origin isolation is not enough.
- Separate secrets from project manifests, exported projects, prompts, and logs.

### Models and AI

- Record model repository, revision, weight checksum, license, quantization, and runtime.
- AI output is untrusted structured input until parsed and validated.
- Never accept invented source provenance.
- Bound repair, research, and agent loops.
- Heavy models run outside the core environment and cannot mutate files or state directly.

### Logging and export

- Redact secrets and avoid dumping full copyrighted sources into logs.
- Preserve short evidence locators and hashes rather than unnecessary full copies.
- Portable exports include only managed assets explicitly selected for export.
- Verify manifests before import and reject path escapes or hash mismatches.

## Known residual risks

- Image and media decoder vulnerabilities cannot be eliminated entirely.
- Local malware or an already-compromised user account is outside the primary model.
- Copyright and model-weight permissions require review separate from software security.
- External GPL tools may create distribution obligations if bundled or tightly linked.

## Security acceptance gates

- Malicious archive fixtures fail without writing outside temporary/managed paths.
- Source-tree byte hashes remain unchanged after ingestion, thumbnails, and rendering.
- Stale attempt tokens cannot commit artifacts.
- Cancellation and crashes leave recoverable database state.
- Logs contain no configured secret values.
- Cache prune dry-runs never identify source files as deletion candidates.

## Implemented additional controls

- Render, normalize, portable-export, and timeline-export operations refuse existing
  output paths instead of overwriting them.
- Web binding is restricted to loopback values by schema and CLI choices.
- Scene edits use revision checks so stale browser state cannot silently overwrite
  newer work.
- Durable queue claims are transactional and interrupted jobs are explicitly recovered.
- Qdrant point identity is deterministic but SQLite remains authoritative; vector
  collections may be deleted and rebuilt without project-state loss.
- Qdrant's local in-memory/persisted modes are used only for tests; production is
  expected to use a pinned loopback service.
