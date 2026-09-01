from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class RecurringChore(models.Model):
    name = models.CharField(max_length=255, blank=False)
    interval_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    next_due_date = models.DateField()
    last_done_date = models.DateField(null=True, blank=True, default=None)

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

    def __str__(self):
        return self.name
