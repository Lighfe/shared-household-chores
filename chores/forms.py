from django import forms

from chores.models import OneOffTask, RecurringChore


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


class RecurringChoreEditForm(forms.ModelForm):
    """Edit form for an existing RecurringChore's name/interval_days/next_due_date (#12, #16).

    Exposes name, interval_days, and next_due_date -- excludes
    last_done_date. Per the "editing doesn't touch the current cycle"
    decision, editing name/interval_days alone edits the schedule going
    forward only: next_due_date is left untouched unless the user
    explicitly changes it here, and last_done_date is never touched by
    this form regardless of which fields change (#16). next_due_date uses
    the model's own required DateField validation -- no hand-rolled date
    parsing, and no "must be today or later" restriction, since a
    deliberately past date (marking a chore overdue) is a valid, truthful
    value.
    """

    class Meta:
        model = RecurringChore
        fields = ["name", "interval_days", "next_due_date"]
        labels = {
            "interval_days": "Interval (days)",
            "next_due_date": "Next due date",
        }
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 255}),
            "interval_days": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "next_due_date": forms.DateInput(attrs={"type": "date"}),
        }


class OneOffTaskForm(forms.ModelForm):
    """Create form for OneOffTask (#9).

    Only exposes name and due_date -- the fields a user sets when creating
    a one-off task. due_date is optional (null=True, blank=True on the
    model), matching due_date=None being a valid, non-overdue state (#4).
    Validation is entirely the model field's own (blank=False on name,
    optional DateField on due_date) -- no hand-rolled validation logic,
    per #9's constraints.
    """

    class Meta:
        model = OneOffTask
        fields = ["name", "due_date"]
        labels = {
            "due_date": "Due date (optional)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 255}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
