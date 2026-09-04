# Decisions

Product/design decisions made while grooming the backlog (2026-09-01) that
go beyond what `_docs/plan.md` already specified. Each was a judgment call
the original issue text left open; recorded here so they don't need to be
re-derived from issue threads later.

## Status logic gets a fourth state: `no_due_date`
The original spec for #4 only named three states (overdue / due today /
upcoming). `OneOffTask.due_date` is nullable (#3), so a fourth value,
`no_due_date`, was added — a task with no due date is never flagged
overdue or due-today (#4, #6).

## Editing a chore's interval doesn't touch its current cycle
Changing `interval_days` on an existing `RecurringChore` (#12) leaves
`next_due_date` and `last_done_date` untouched. The new interval only
applies starting from the *next* time the chore is marked done (#10).
Edit is forward-only, not a retroactive reschedule.

## Manual due-date correction is a field on the edit form, not a new flow
#16 (split out from #12): a user can directly correct `next_due_date`
(e.g. "push this out three weeks") by adding a field to #12's existing
edit form, rather than building a separate reschedule action/endpoint —
one extra field didn't justify a parallel form for a single-user app.
`last_done_date` was deliberately left non-editable — correcting a past
completion record is a different concern with no use case forcing it yet.

## Double-submit protection: client-side disable + one cheap server check, no idempotency layer
#17 (split out from #10/#11): guarding "mark done" against double-tap/retry
uses HTMX's `hx-disabled-elt` client-side, plus a same-day no-op check on
the recurring-chore endpoint (if `last_done_date` is already today, the
second POST is a no-op instead of advancing `next_due_date` again).
Database-level idempotency tokens/locking were explicitly rejected as
over-engineering for a single-user, LAN-only, low-traffic app.
This **changes** #10's original behavior: its test asserting two
back-to-back same-day mark-done calls advance the due date twice is
superseded and must be rewritten as part of implementing #17.

## Cancelling a one-off task is a distinct action from completing it
#18 (split out from #11): both "done" and "cancel/remove" hard-delete the
`OneOffTask` row with no history kept either way — the data-layer behavior
is identical. The decision was purely UI/UX: a separate, visually
de-emphasized "remove" control exists so a task the user decided against
isn't dishonestly marked "done" just to clear it from the list.

## Destructive actions require a confirmation step
Deleting a recurring chore (#13) and removing/completing a one-off task
(#11, #18) all require a client-side confirm (e.g. `hx-confirm`) before
the request fires, since none of these actions are undoable and the app
keeps no history (per `_docs/plan.md`).

## Duplicate chore/task names are allowed
No uniqueness constraint on `RecurringChore.name` or `OneOffTask.name` —
creating or renaming to a name that already exists succeeds (#8, #9, #12).

## Recurring chores that are many intervals overdue advance by exactly one interval on mark-done
Marking a far-overdue chore done adds exactly one `interval_days` to its
previous `next_due_date` and stops — it does not loop through missed
intervals to catch up to a future date, and does not snap to today (#10).
The chore may still show overdue/due-today afterward; that's expected.

## Mobile CSS must be vendored, not CDN-linked
Since the app is LAN-only, a phone on the home LAN isn't guaranteed to
also have general internet access — a CDN-hosted CSS framework risks an
unstyled page. The framework/CSS file is checked into the repo instead (#7).

## "Today" is computed once, in one place
Rather than every call site independently calling `date.today()` (which
would use the host's local timezone, not necessarily Europe/Berlin), a
single shared helper provides "today" and is reused everywhere a
completion date or status check needs it (#15, feeds into #4, #10, #17).

## Grooming judgment calls from the manual-testing backlog (#19-#30), 2026-09-02

A human testing session produced raw findings filed as issues #19-#30.
Grooming them (per `_docs/team/pm.md`) surfaced several judgment calls
beyond what each issue said, recorded here. Four follow-up issues were
filed for scope explicitly moved out of the original 12: #31 (drag-and-
drop reorder, out of #20), #32 (priority-based sort, out of #22), #33
(guaranteed date format/calendar via a custom picker, out of #24/#26),
#34 (custom confirm modal, out of #27).

## #20's "reorder" request is split: an alphabetical sort toggle now, drag-and-drop deferred
The raw finding's "sort chronologically" half was already satisfied by
the existing automatic status-then-due-date sort (#5) by the time this
was groomed. Rather than reject the issue outright, it was re-scoped to
add a lightweight "Default"/"Name (A-Z)" sort toggle -- an actionable,
small, checkable piece of the original ask. True manual drag-and-drop
reordering with a persisted custom order was judged too large and
product-ambiguous (how does a manual order interact with automatic
status grouping?) to bundle into the same issue, and was split out to
follow-up #31, not scheduled for the current backlog.

## #22's priority field is display-only; sort/grouping impact is a separate follow-up
Adding a `priority` field (Low/Medium/High, default Medium, on both
`RecurringChore` and `OneOffTask`) was kept to "store it and show it."
Whether/how priority should affect list ordering relative to the
existing status/due-date sort is a real product question (does priority
outrank due-date proximity? within a status group only or across
groups?) that would have expanded #22 substantially -- split out to
follow-up #32.

## #24/#26 (calendar start day, date format) are scoped to a best-effort `lang`-attribute fix; a guaranteed fix is a separate follow-up
Investigating `<input type="date">` behavior: the native calendar's
first day of week and displayed date format are governed largely by the
browser's own OS/browser locale handling, not reliably by the page's
`lang` attribute -- this varies by browser and isn't something plain
HTML/CSS can guarantee. Both issues were scoped to the best-effort fix
(setting `<html lang>` to a Monday-first, day-before-month locale like
`en-GB`), with an explicit note that this may not take effect on every
browser. Guaranteeing both properties regardless of the visiting
device's locale would require replacing the native date input with a
custom-rendered date-picker (a new JS component) -- out of scope for
these two issues, filed as a single shared follow-up, #33, since both
stem from the same root cause.

## #27's scope is the post-success animation only; replacing the native confirm() popup is a separate follow-up
The tester's finding described the current `hx-confirm` native browser
popup (used before one-off task "Done", per the "destructive actions
require confirmation" decision) as feeling out of place, but that's a
distinct, cross-cutting concern (also used by chore delete #13 and task
cancel #18) from #27's actual ask (a post-success completion animation).
Kept #27 scoped to the animation; replacing the native confirm dialogs
app-wide with a custom-styled modal was split out to follow-up #34.

## #19's scope was widened from "Recurring Chores" to both list sections
The raw finding named only the Recurring Chores screen, but the
One-off Tasks section shares the same layout/markup patterns
(`.form-row`, `.chore-list`/`.task-list`) -- fixing only one would leave
the two sections looking inconsistent side by side. #19 was groomed to
cover both sections.

## #21's form/list separation uses a native `<details>` disclosure, not a modal or new page
The raw finding offered several options ("different sections, a modal,
or a dedicated add view"). A native `<details>`/`<summary>` disclosure,
collapsed by default, was chosen over a modal or a new page/route: it
requires no new JS dependency, no new URL, and no accessibility
scaffolding (native semantics), consistent with the app's existing
"server-rendered templates + HTMX, no other JS framework" approach.

## #28/#29/#30 are groomed as normal but flagged deferred, not labeled
The tester explicitly flagged these three as future extension ideas,
not for the current backlog. The repo's label set (`enhancement`, `bug`,
`accessibility`, `documentation`, `duplicate`, `good first issue`,
`help wanted`, `invalid`, `question`, `wontfix`) has no priority/
deferred label, so each issue's body carries an explicit "Deferred /
future work" note in the Goal and a closing Note instead of a label
change. They were still groomed to the full template (checkable
acceptance criteria, out of scope, constraints) so they're ready to pick
up as-is if the product direction ever calls for them.

## QA gets a third verdict, NEEDS-HUMAN, for criteria only checkable in a real browser
#24/#26 were closed on "QA: PASS (with caveat)" for a criterion QA
structurally could not check (no GUI browser in the sandbox) — the
rendered calendar's actual first-day-of-week/date-format. Manual
testing on 2026-09-03 confirmed the calendar still shows Sunday-first
in the browser actually used, meaning the caveat's predicted failure
mode happened and the issue was closed prematurely. Root cause: QA
only had PASS/FAIL, and FAIL would have sent it back to an engineer who
could change nothing (the code was already correct — the gap was the
missing human check, not the implementation). `_docs/team/qa-engineer.md`
and `_docs/process.md` now define a third verdict, NEEDS-HUMAN, for
criteria observable only in a real rendered browser/device: it blocks
closing and must be surfaced plainly in any summary, not just left in
the issue thread as a caveat under a PASS.

## #24/#26 reopened; #33 is the actual fix needed
Per the decision above, #24 and #26 are reopened rather than left
closed with a stale PASS — the human check their own acceptance
criteria called for has now happened and shows the `lang`-attribute
best-effort fix did not take effect in the browser actually used. No
further code change belongs on #24/#26 themselves (their scope was
always best-effort, by design, per the entry above on #24/#26's
scoping) — the real remaining work is #33, the guaranteed custom
date-picker fix, which should be prioritized.

## LAN access is enforced by network boundary, not application code
`ALLOWED_HOSTS` needs updating from its empty default so LAN requests
aren't rejected, and the README must carry an explicit warning against
exposing the app beyond the LAN (no port forwarding, no tunnels). There is
no code-level enforcement (e.g. IP-restricting middleware) — the app
relies on the household's network boundary plus the documented warning,
consistent with `_docs/plan.md`'s "no auth, trusted household devices
only" (#14).
