# Planning-first live Planner sessions

Live Planner submissions create or return a **Planning** session immediately and
resolve asynchronously to a follow-up question, menu proposal, or failure.
Follow-up answers use the same lifecycle by returning the existing session to
**Planning**. Tavola uses this planning-first lifecycle instead of synchronous
blocking planner submissions because Codex SDK latency is variable, and
customers should be able to keep browsing the catalog while Tavola plans the
menu.
