from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Priority(models.TextChoices):
    """Fixed priority levels for RecurringChore/OneOffTask (#22).

    Display-only for now: a fixed three-value enum (not free-form text or
    an open numeric field), consistent with the plain-enum `Status`
    pattern in `chores/status.py`. Does not affect sort order, filtering,
    or status classification -- see `_docs/decisions.md` (follow-up #32
    covers priority-based sort/grouping).
    """

    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class RecurringChore(models.Model):
    name = models.CharField(max_length=255, blank=False)
    interval_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    next_due_date = models.DateField()
    last_done_date = models.DateField(null=True, blank=True, default=None)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    def clean(self):
        super().clean()
        if self.interval_days is not None and self.interval_days <= 0:
            raise ValidationError(
                {"interval_days": "interval_days must be a positive integer."}
            )

    def __str__(self):
        return self.name


class OneOffTask(models.Model):
    name = models.CharField(max_length=255, blank=False)
    due_date = models.DateField(null=True, blank=True, default=None)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    def __str__(self):
        return self.name
