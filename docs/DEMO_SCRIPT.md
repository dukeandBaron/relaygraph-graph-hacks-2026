# Working UI demo

The final video uses edited captures from the actual local application backed by
FalkorDB. It is not an uninterrupted user session. People, notices and receipts
are synthetic. Narration, if present, is synthesized and does not impersonate the
participant or a customer. Failed raw screencast attempts are excluded.

1. **Connected work.** RelayGraph follows changed requirements to the work that
   needs a fresh review. This synthetic activity has owners, source notices,
   requirements, tasks, acknowledgements and a receipt stored in FalkorDB.
2. **Trace before acting.** The deadline moves forward and a declaration is
   added. The real graph traversal finds registration, travel and catering, with
   three dependency hops for catering. Accessibility remains current.
3. **Review-bound adoption.** Explicit adoption binds the correction to this
   graph revision. The old receipt is retained as needing recheck, and three
   owner-linked review actions are stored in the graph.
4. **Explain the result.** Each action exposes its dependency path and original
   source revisions. Historical source text is separate from current values, and
   the underlying parameterized Cypher is inspectable.
5. **A graph dependency, not decoration.** Real database outage testing returns
   unavailable, and restarting the database preserves the same graph hash.
   Read-only MCP context tools are available for the caller's own AI assistant.

Disclosure: AI-assisted development; deterministic default runtime; no online
model calls; no claim of real customer outcomes or official submission success.
