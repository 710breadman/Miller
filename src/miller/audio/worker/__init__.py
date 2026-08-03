"""Isolated, pinned worker environment for external alignment engines.

Nothing in this subpackage is imported by Miller's core at runtime; the
core only launches ``align_worker.py`` as a subprocess (see
``miller.audio.whisper_worker.ExternalAlignmentWorker``). See
``requirements.txt`` in this directory for the pinned, isolated environment
this worker is meant to run inside.
"""
