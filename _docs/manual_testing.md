# Manual testing

How a human clicking through the running app turns into groomed backlog
issues, feeding into the normal lifecycle in `_docs/process.md`.

Who does what

- Tester (human) - runs the app and describes what they see
- Orchestrator (this session) - listens live, logs findings, files issues,
  triggers grooming
- PM - grooms each filed issue, follows `_docs/team/pm.md` (unchanged)

No new team role is needed. The live back-and-forth while testing has to
happen in the interactive session, not a subagent - a subagent can't hold
a running conversation with the tester. Grooming afterward reuses the
existing PM role exactly as `_docs/process.md` step 2 already does.

Process

1. Tester runs the app (see README's "Run on the LAN" section, or
   `manage.py runserver` locally) and describes findings as they go: what
   they did, what they expected, what happened instead.
2. The orchestrator keeps a running scratch log of findings during the
   session - not committed anywhere.
3. When the tester says they're done, the orchestrator files each finding
   as its own raw GitHub issue (title + steps/expected/actual), picking
   whichever existing label fits (bug, enhancement, accessibility, etc.).
4. Immediately after filing, the orchestrator runs the PM role on each new
   issue, same as `_docs/process.md` step 2, so issues land in the backlog
   already groomed and ready for an engineer.
5. Nothing is implemented automatically. Grooming is the stopping point,
   same as every other issue in the backlog.
