from datetime import date

from django.shortcuts import render
from django.views.decorators.http import require_POST

from chores.dates import get_today
from chores.forms import OneOffTaskForm, RecurringChoreForm
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
