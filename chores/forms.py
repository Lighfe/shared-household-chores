from django import forms

from chores.models import OneOffTask, Priority, RecurringChore


class RecurringChoreForm(forms.ModelForm):
    """Create/edit form for RecurringChore.

    Deliberately only exposes name, interval_days, next_due_date, and
    priority -- the fields a user sets when creating a chore (#8, plus
    priority added by #22). last_done_date is never user-editable through
    this form; it stays unset on creation.

    Validation is entirely the model field's own (blank=False on name,
    MinValueValidator(1) + model.clean() on interval_days, required
    DateField on next_due_date, choices-restricted CharField on priority)
    -- no hand-rolled validation logic, per #8's constraints. priority's
    `choices` validation rejects anything outside Low/Medium/High, and the
    model's default (Medium) is used as the field's initial value on an
    unbound form, so submitting without touching the selector still saves
    Medium (#22).
    """

    class Meta:
        model = RecurringChore
        fields = ["name", "interval_days", "next_due_date", "priority"]
        labels = {
            "interval_days": "Interval (days)",
            "next_due_date": "Initial due date",
            "priority": "Priority",
        }
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 255}),
            "interval_days": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "next_due_date": forms.DateInput(attrs={"type": "date"}),
        }


class RecurringChoreEditForm(forms.ModelForm):
    """Edit form for an existing RecurringChore's name/interval_days/next_due_date/priority (#12, #16, #22).

    Exposes name, interval_days, next_due_date, and priority -- excludes
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
        fields = ["name", "interval_days", "next_due_date", "priority"]
        labels = {
            "interval_days": "Interval (days)",
            "next_due_date": "Next due date",
            "priority": "Priority",
        }
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 255}),
            "interval_days": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "next_due_date": forms.DateInput(attrs={"type": "date"}),
        }


class OneOffTaskForm(forms.ModelForm):
    """Create form for OneOffTask (#9).

    Exposes name, due_date, and priority (#22) -- the fields a user sets
    when creating a one-off task. due_date is optional (null=True,
    blank=True on the model), matching due_date=None being a valid,
    non-overdue state (#4). Validation is entirely the model field's own
    (blank=False on name, optional DateField on due_date, choices-
    restricted CharField on priority) -- no hand-rolled validation logic,
    per #9's constraints.
    """

    class Meta:
        model = OneOffTask
        fields = ["name", "due_date", "priority"]
        labels = {
            "due_date": "Due date (optional)",
            "priority": "Priority",
        }
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 255}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class AddItemForm(forms.Form):
    """Merged create form for either a RecurringChore or a OneOffTask (#23).

    Replaces the separate RecurringChoreForm/OneOffTaskForm disclosures on
    the home page with a single "Add" form: a "Recurring" checkbox picks
    which model gets created on submit. Field names/labels intentionally
    match the two underlying forms as closely as possible (`due_date`
    plays the role of `next_due_date` when recurring is checked) so the
    view's mapping from cleaned_data to model kwargs is direct.

    Requiredness mirrors the two original forms exactly, but is enforced
    here in clean() rather than via each field's own `required` flag,
    since which fields are required depends on the "recurring" checkbox's
    value -- not on the field in isolation. This runs on every submission
    server-side, so a bypassed/broken client (no JS, tampered POST) can't
    skip required fields by leaving "recurring" checked but omitting
    interval_days/due_date (#23's constraint: don't rely on client-side
    `required` attributes alone).

    - recurring unchecked: due_date optional, interval_days ignored
      entirely (not stored) -- matching OneOffTaskForm.
    - recurring checked: interval_days (>= 1) and due_date both required
      -- matching RecurringChoreForm.
    """

    name = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={"maxlength": 255})
    )
    recurring = forms.BooleanField(required=False, label="Recurring")
    interval_days = forms.IntegerField(
        required=False,
        min_value=1,
        label="Interval (days)",
        widget=forms.NumberInput(attrs={"min": 1, "step": 1}),
    )
    due_date = forms.DateField(
        required=False,
        label="Due date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    priority = forms.ChoiceField(
        choices=Priority.choices, initial=Priority.MEDIUM, label="Priority"
    )

    def clean(self):
        cleaned_data = super().clean()
        recurring = cleaned_data.get("recurring")
        interval_days = cleaned_data.get("interval_days")
        due_date = cleaned_data.get("due_date")

        if recurring:
            if interval_days is None:
                self.add_error("interval_days", "This field is required.")
            if due_date is None:
                self.add_error("due_date", "This field is required.")

        return cleaned_data
