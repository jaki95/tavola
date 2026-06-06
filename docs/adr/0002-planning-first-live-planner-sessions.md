# Planning-first live Planner sessions

Live Planner submissions create or return a **Planning** session immediately and
resolve asynchronously to a follow-up question, menu proposal, or failure.
Follow-up answers use the same lifecycle by returning the existing session to
**Planning**. Tavola uses this planning-first lifecycle instead of synchronous
blocking planner submissions because Codex SDK latency is variable, and
customers should be able to keep browsing the catalog while Tavola plans the
menu.

Planning progress is reported through backend-owned **Planning updates** on the
existing polled session resource, not through frontend elapsed-time phases or a
separate push channel. Customer-facing update copy stays in Tavola language;
Codex remains implementation technology and appears only as the Planner surface's
"powered by Codex" attribution. Terminal Planner states may keep update history
in the API for traceability, but the storefront should collapse back to the
follow-up, proposal, or failure experience rather than displaying a dashboard.
