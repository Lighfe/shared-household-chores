"""Pure, model-independent chore/task status classification.

This module intentionally does not import anything from ``chores.models``
and does not call ``date.today()`` internally, so it works standalone with
plain ``datetime.date`` values passed in explicitly.
"""

from datetime import date
from enum import Enum


class Status(str, Enum):
    """The possible states a due date can classify to."""

    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    UPCOMING = "upcoming"
    NO_DUE_DATE = "no_due_date"


def get_status(due_date: date | None, today: date) -> Status:
    """Classify ``due_date`` relative to ``today``.

    - ``due_date`` is ``None`` -> ``Status.NO_DUE_DATE``, regardless of ``today``.
    - ``due_date`` before ``today`` -> ``Status.OVERDUE``.
    - ``due_date`` equal to ``today`` -> ``Status.DUE_TODAY``.
    - ``due_date`` after ``today`` -> ``Status.UPCOMING``.
    """
    if due_date is None:
        return Status.NO_DUE_DATE
    if due_date < today:
        return Status.OVERDUE
    if due_date == today:
        return Status.DUE_TODAY
    return Status.UPCOMING
