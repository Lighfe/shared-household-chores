from django.shortcuts import render

from chores.dates import get_today
from chores.models import RecurringChore
from chores.status import Status, get_status

# Status groups sort before due dates: overdue first, then due today, then
# upcoming. RecurringChore.next_due_date is never null, so no_due_date never
# occurs here, but it's included for completeness/safety.
_STATUS_ORDER = {
    Status.OVERDUE: 0,
    Status.DUE_TODAY: 1,
    Status.UPCOMING: 2,
    Status.NO_DUE_DATE: 3,
}


def home(request):
    today = get_today()

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

    return render(request, "chores/home.html", {"chores": chores})
