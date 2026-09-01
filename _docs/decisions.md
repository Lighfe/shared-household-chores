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

## LAN access is enforced by network boundary, not application code
`ALLOWED_HOSTS` needs updating from its empty default so LAN requests
aren't rejected, and the README must carry an explicit warning against
exposing the app beyond the LAN (no port forwarding, no tunnels). There is
no code-level enforcement (e.g. IP-restricting middleware) — the app
relies on the household's network boundary plus the documented warning,
consistent with `_docs/plan.md`'s "no auth, trusted household devices
only" (#14).
