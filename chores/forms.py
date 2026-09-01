from django import forms

from chores.models import RecurringChore


class RecurringChoreForm(forms.ModelForm):
    """Create/edit form for RecurringChore.

    Deliberately only exposes name, interval_days, next_due_date -- the
    fields a user sets when creating a chore (#8). last_done_date is never
    user-editable through this form; it stays unset on creation.

    Validation is entirely the model field's own (blank=False on name,
    MinValueValidator(1) + model.clean() on interval_days, required
    DateField on next_due_date) -- no hand-rolled validation logic, per
    #8's constraints.
    """

    class Meta:
        model = RecurringChore
        fields = ["name", "interval_days", "next_due_date"]
        labels = {
            "interval_days": "Interval (days)",
            "next_due_date": "Initial due date",
        }
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 255}),
            "interval_days": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "next_due_date": forms.DateInput(attrs={"type": "date"}),
        }
