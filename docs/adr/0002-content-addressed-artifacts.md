# ADR 0002: Content-addressed managed artifacts

Status: accepted

## Decision

Derived files are immutable and stored below a Miller-managed workspace by
SHA-256 content identity. Stage fingerprints include the stage and implementation
versions, canonical configuration, and dependency content identities.

User source files are referenced read-only and never treated as cache storage.

## Consequences

- Repeated work reuses verified outputs.
- Changed inputs invalidate only dependent stages.
- File renames can preserve page/content identity.
- Cache cleanup must operate on references and protected paths rather than age alone.
