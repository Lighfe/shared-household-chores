- Tasks are GitHub issues, one at a time
- Read the acceptance criteria before starting and before closing
- Commit regularly

Roles

- PM - grooms a task before anyone implements it, follows _docs/team/pm.md
- Engineer - implements one groomed task, follows _docs/team/software-engineer.md
- QA - checks the result against the acceptance criteria, follows _docs/team/qa-engineer.md

Orchestrator

The main session is the orchestrator. It launches the PM, the engineer
and QA as subagents. It does not groom, implement or test itself.

Lifecycle

1. Pick the next open issue from the backlog
2. PM grooms it
3. Engineer implements it
4. QA verifies it
5. On FAIL, back to step 3 with the QA comment as input
6. On PASS, read the engineer's "Worth keeping" line and apply it (see `_docs/meta.md`) before closing the issue
7. On NEEDS-HUMAN, do not close the issue. Leave it open with the QA
   comment naming exactly what a human needs to check, and say so
   plainly in any summary of the work (not just in the issue thread) —
   it is not done until that check happens
8. Repeat until the backlog is empty

Rules

- Do not skip step 2
- Do not skip step 6, even when the engineer's comment says "Worth keeping: none"
- The engineer does not close the issue
- QA does not fix the code, only outputs PASS, FAIL, or NEEDS-HUMAN
- The orchestrator closes the issue only after QA outputs PASS
- An issue QA marked NEEDS-HUMAN is not "done" in any summary the
  orchestrator gives the user, even if every code-checkable criterion
  passed
- When engineers work in parallel, do not `git stash`/`stash pop` across the whole working tree — it can pull in another engineer's uncommitted changes; extract only the intended files (e.g. `git show stash@{0}:<path>`)