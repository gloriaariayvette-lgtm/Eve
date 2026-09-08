# ops — the archaeology

Five hundred single-use scripts, written one at a time against the live house on
Aegis: reconnaissance to find out what a handler actually does, a patch to change
it, a test to see whether the change held. They are kept because the reasoning in
them is the record of how the system got to be the way it is, and because a
question like "when did the journal stop using grok" is answerable here and
nowhere else.

Nothing in this directory is imported by `server/`, `client/` or `air3/`. Nothing
here runs as part of the product. They were moved out of the repository root so
that the three things that *are* the product can be seen.

- `recon/` — read-only: dump a handler, trace a call, find which copy is live
- `patches/` — one-shot edits applied to files on Aegis
- `tests/` — one-shot verification after a patch
- `tools/` — everything else: modules, daemons, experiments, installers

The operational truth these were written against lives in `docs/VINTOS-OPS.md`.
Read that before running anything here; several of these scripts assume paths and
port numbers that have since changed.
