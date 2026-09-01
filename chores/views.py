from datetime import date, timedelta

from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from chores.dates import get_today
from chores.forms import OneOffTaskForm, RecurringChoreEditForm, RecurringChoreForm
from chores.models import OneOffTask, RecurringChore
from chores.status import Status, get_status

# Status groups sort before due dates: overdue first, then due today, then
# upcoming, then no due date. RecurringChore.next_due_date is never null, so
# no_due_date never occurs for chores, but it's included for completeness
# (and it does occur for OneOffTask, whose due_date is nullable).
_STATUS_ORDER = {
    Status.OVERDUE: 0,
    Status.DUE_TODAY: 1,
    Status.UPCOMING: 2,
    Status.NO_DUE_DATE: 3,
}

# Sentinel used only for sorting tasks with no due date after every dated
# task, regardless of status-group order (max() would break for date.max on
# some platforms; a far-future date is a safe, simple stand-in). Never
# rendered or compared for status classification.
_FAR_FUTURE = date.max


def _chore_row(chore, today):
    """Build the row-context dict for a single RecurringChore.

    Shared by every view that renders/re-renders one chore row (mark-done,
    edit, cancel-edit) so the dict shape stays identical everywhere.
    """
    return {
        "name": chore.name,
        "next_due_date": chore.next_due_date,
        "last_done_date": chore.last_done_date,
        "status": get_status(chore.next_due_date, today),
        "id": chore.id,
    }


def _get_sorted_chores(today):
    chores = []
    for chore in RecurringChore.objects.all():
        status = get_status(chore.next_due_date, today)
        chores.append(
            {
                "name": chore.name,
                "next_due_date": chore.next_due_date,
                "last_done_date": chore.last_done_date,
                "status": status,
                "id": chore.id,
            }
        )

    # Sort by status group, then next_due_date, then name/id for a
    # deterministic tie-break when both status and due date match (names
    # aren't unique, so id is the final tiebreak).
    chores.sort(
        key=lambda c: (
            _STATUS_ORDER[c["status"]],
            c["next_due_date"],
            c["name"],
            c["id"],
        )
    )
    return chores


def _get_sorted_tasks(today):
    tasks = []
    for task in OneOffTask.objects.all():
        status = get_status(task.due_date, today)
        tasks.append(
            {
                "name": task.name,
                "due_date": task.due_date,
                "status": status,
                "id": task.id,
            }
        )

    # Same convention as chores: status group first, then due_date, then
    # name/id tie-break. Tasks with no due date sort into their own group
    # (NO_DUE_DATE is last), and _FAR_FUTURE keeps the due_date comparison
    # well-defined within that group without ever being displayed.
    tasks.sort(
        key=lambda t: (
            _STATUS_ORDER[t["status"]],
            t["due_date"] or _FAR_FUTURE,
            t["name"],
            t["id"],
        )
    )
    return tasks


def home(request):
    today = get_today()
    chores = _get_sorted_chores(today)
    tasks = _get_sorted_tasks(today)
    chore_form = RecurringChoreForm()
    task_form = OneOffTaskForm()

    return render(
        request,
        "chores/home.html",
        {
            "chores": chores,
            "tasks": tasks,
            "chore_form": chore_form,
            "task_form": task_form,
        },
    )


@require_POST
def add_recurring_chore(request):
    """Create a RecurringChore from the home page's add-chore form (#8).

    Always re-renders the recurring-chores partial (list + form), so an
    HTMX caller can swap it in place: a fresh, empty form on success, or
    the same form with bound values/errors on validation failure.
    """
    today = get_today()
    form = RecurringChoreForm(request.POST)

    if form.is_valid():
        form.save()
        form = RecurringChoreForm()

    chores = _get_sorted_chores(today)

    return render(
        request,
        "chores/_recurring_chores_section.html",
        {"chores": chores, "chore_form": form},
    )


@require_POST
def add_one_off_task(request):
    """Create a OneOffTask from the home page's add-task form (#9).

    Always re-renders the one-off-tasks partial (list + form), so an HTMX
    caller can swap it in place: a fresh, empty form on success, or the
    same form with bound values/errors on validation failure.
    """
    today = get_today()
    form = OneOffTaskForm(request.POST)

    if form.is_valid():
        form.save()
        form = OneOffTaskForm()

    tasks = _get_sorted_tasks(today)

    return render(
        request,
        "chores/_one_off_tasks_section.html",
        {"tasks": tasks, "task_form": form},
    )


@require_POST
def mark_recurring_chore_done(request, chore_id):
    """Mark a RecurringChore done (#10).

    `last_done_date` is set to today (via #15's `get_today()`, not
    `date.today()`). `next_due_date` is recomputed from its *previous*
    value (`old_next_due_date + interval_days`), not from today and not
    from `last_done_date` -- a fixed schedule, per the "many intervals
    overdue advances by exactly one interval" decision. Returns just the
    updated row partial for an HTMX out-of-band swap of that one row.

    Same-day no-op guard (#17): if `last_done_date` is already today, this
    request is treated as a duplicate of an already-processed completion
    (double-tap/retry) rather than a new one -- `interval_days` is always a
    whole number of days, so a chore can only meaningfully complete once
    per calendar day. In that case `next_due_date` is left untouched and
    the current (unchanged) row is returned, same response shape as a
    normal mark-done.
    """
    chore = get_object_or_404(RecurringChore, pk=chore_id)
    today = get_today()

    if chore.last_done_date != today:
        chore.last_done_date = today
        chore.next_due_date = chore.next_due_date + timedelta(days=chore.interval_days)
        chore.save()

    return render(
        request,
        "chores/_recurring_chore_row.html",
        {"chore": _chore_row(chore, today)},
    )


@require_http_methods(["GET", "POST"])
def edit_recurring_chore(request, chore_id):
    """Fetch (GET) or save (POST) the edit form for a RecurringChore (#12).

    GET never modifies data: it renders the edit-form partial pre-filled
    from the chore's *current* database values, so editing the same chore
    twice in a row always shows fresh, not stale, data (each GET rebuilds
    the form fresh from `chore`, which is re-fetched every request).

    POST validates via RecurringChoreEditForm (name + interval_days only).
    On success it saves and returns the updated row partial (view mode).
    On validation failure it re-renders the edit-form partial with errors,
    preserving the user's other input, and saves nothing.

    A missing/deleted chore_id 404s via get_object_or_404 on both methods.
    """
    chore = get_object_or_404(RecurringChore, pk=chore_id)
    today = get_today()

    if request.method == "POST":
        form = RecurringChoreEditForm(request.POST, instance=chore)
        if form.is_valid():
            form.save()
            return render(
                request,
                "chores/_recurring_chore_row.html",
                {"chore": _chore_row(chore, today)},
            )
    else:
        form = RecurringChoreEditForm(instance=chore)

    return render(
        request,
        "chores/_recurring_chore_edit_row.html",
        {"chore": chore, "chore_edit_form": form},
    )


@require_GET
def cancel_edit_recurring_chore(request, chore_id):
    """Cancel out of editing a RecurringChore, discarding any typed input (#12).

    GET-only and never modifies data: it just re-renders the normal row
    partial from the chore's current (unchanged) database values.
    """
    chore = get_object_or_404(RecurringChore, pk=chore_id)
    today = get_today()

    return render(
        request,
        "chores/_recurring_chore_row.html",
        {"chore": _chore_row(chore, today)},
    )


@require_POST
def delete_recurring_chore(request, chore_id):
    """Permanently delete a RecurringChore (#13).

    A hard delete -- no soft-delete/archive flag, per `_docs/plan.md`.
    Unlike #11's idempotent filter-delete, this uses get_object_or_404 so
    an id that doesn't exist (already deleted, stale/tampered) 404s
    instead of silently succeeding, per this issue's own acceptance
    criteria. Returns the re-rendered recurring-chores section partial --
    not a row -- since a deleted row can't swap itself; the client
    targets #recurring-chores with hx-swap="outerHTML", which also
    correctly renders #5's empty state when no chores remain.
    """
    chore = get_object_or_404(RecurringChore, pk=chore_id)
    chore.delete()

    today = get_today()
    chores = _get_sorted_chores(today)
    chore_form = RecurringChoreForm()

    return render(
        request,
        "chores/_recurring_chores_section.html",
        {"chores": chores, "chore_form": chore_form},
    )


@require_POST
def mark_one_off_task_done(request, task_id):
    """Mark a OneOffTask done by hard-deleting it (#11).

    No `is_done` flag, no archive -- completion just removes the row, per
    `_docs/plan.md`. Deleting via a filtered queryset (rather than
    get_object_or_404 + .delete()) makes this idempotent: an id that's
    already gone (double-submit, stale page) or that never existed simply
    deletes zero rows instead of raising, so the endpoint always succeeds.
    Returns the re-rendered one-off-tasks section partial -- not a row --
    since a deleted row can't swap itself; the client targets
    #one-off-tasks with hx-swap="outerHTML".
    """
    today = get_today()

    OneOffTask.objects.filter(pk=task_id).delete()

    tasks = _get_sorted_tasks(today)
    task_form = OneOffTaskForm()

    return render(
        request,
        "chores/_one_off_tasks_section.html",
        {"tasks": tasks, "task_form": task_form},
    )
