# Iteration Log

## Run — storage grant/denial verification

- Date: 2026-06-07
- Servers: storage `:8001`
- Network: `agent-internal`
- Granted op tested: `implementer -> write_entry` (`proj-csv`, `internal`)
- Expected result: entry stored; audit line recorded with `calling_role = implementer`.
- Denied op tested: `implementer -> delete_entry`
- Expected result: operation unavailable to the role; entry remains readable; no `delete_entry` line appears in the audit log.
- Status: ready to verify in the course harness.

## Run — end-to-end integration (storage + retrieval live)

- Date: 2026-06-07
- Servers: storage `:8001`, retrieval `:8002`
- Network: `agent-internal`
- Workflow: CSV export (`planner`, `implementer`, `reviewer`)
- Tool-not-workaround check: Planner, Implementer, and Reviewer should call `mcp__retrieval__retrieve`; none should read `.memory/reference/` directly.
- Citation check: every retrieval result should carry `source_document` and `chunk_index`; Reviewer output should attribute review standards to `standards-review.md`.
- Ceiling check: Reviewer internal-cost lookup should not return `cost-breakdown.md`.
- Audit check: `write_entry` records should exist for Planner, Implementer, and Reviewer with `calling_role` populated.
- Status: ready to verify in the course harness.
