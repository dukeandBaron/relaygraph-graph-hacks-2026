# Scope and acceptance

Created: 2026-10-18 Asia/Shanghai, after the event began.

One bounded product: investigate how a revised requirement changes an activity
plan, then prepare review actions. A single Codex conversation owns the work;
there are no external coding agents, task queues or coordination bridges.

## Required evidence

- FalkorDB is the only application state store. No in-memory or JSON fallback.
- Cypher traversals determine affected tasks and stale acknowledgements/receipts.
- Every prepared action cites source, requirement and dependency path.
- Adoption binds an immutable preview to a graph revision and rejects stale plans.
- A distinct tenant graph cannot read or change the demo graph.
- Restart retains graph data; a missing database stops operations visibly.
- Non-idempotent commands have operation identifiers and conflict checks.
- Synthetic data is explicit; no private documents or login data enter the graph.
- A public repository, complete local setup, model disclosure and real video are
  prepared before claiming official submission readiness.

## User contribution boundary

The user chooses whether to enter and must understand and verify the graph model,
queries and architecture. AI assistance is disclosed. No fabricated signature,
human review, genuine customer usage, award or platform receipt is permitted.

## Design plan

Audience: a small activity organizer handling a changed deadline and extra form.
Page job: show who and what needs a fresh review, and explain every result.

Palette: paper blue #f2f6fa, slate ink #18364b, graph teal #007f88,
change coral #d9543f, quiet gray #6e8190, surface white #ffffff.
Type: Georgia for the restrained product title, Segoe UI for controls and prose,
Consolas for query and record details. No external font dependency.
Layout: a wide relationship canvas beside a compact change inspector, with a
bottom evidence drawer; on mobile the inspector follows the graph.
Signature: selecting a proposed review illuminates its precise source-to-task
path. Colors encode changed, stale and current state, not decorative metrics.

Initial generic dashboard concepts were discarded because unrelated counters and
charts obscure the single change-response decision this product supports.
