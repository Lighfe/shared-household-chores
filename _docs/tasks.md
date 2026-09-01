# Shared Household Chores — Task Backlog

Each task is scoped to be finishable in one session and understandable
without reading the others. Built on the design in `_docs/plan.md`:
Django + SQLite, server-rendered templates with HTMX for interactivity.

## 1. Project setup with a passing test
Goal: An empty, runnable Django project with a green test suite.
Description: Scaffold a new Django project and a `chores` app inside it, configure `TIME_ZONE = "Europe/Berlin"` and `USE_TZ = False` in settings, and add one trivial test (e.g. asserting the test runner works, or a smoke test on the admin/health path) that passes with `manage.py test`.

## 2. RecurringChore model
Goal: Persist recurring chores with the fields the fixed-schedule logic needs.
Description: Add a `RecurringChore` model to the `chores` app with `name`, `interval_days`, `next_due_date`, and nullable `last_done_date`, plus a migration. Add model-level tests confirming a chore can be created and saved with these fields.

## 3. OneOffTask model
Goal: Persist one-off tasks separately from recurring chores.
Description: Add a `OneOffTask` model with `name` and a nullable `due_date`, plus a migration. Add model-level tests confirming creation and that deleting a task removes it (no archive/history to preserve).

## 4. Chore status logic
Goal: A pure function that classifies a chore/task as overdue, due today, or upcoming.
Description: Write a small function (e.g. `chores/status.py`) that takes a due date and today's date and returns one of `overdue` / `due_today` / `upcoming`. Cover edge cases (due date is exactly today, one day before, one day after) with unit tests — this logic is shared by both models but should not live inside either.

## 5. Home page: list recurring chores
Goal: A view showing all recurring chores with their computed status.
Description: Add a view and template that lists all `RecurringChore` rows, sorted by urgency (overdue first), showing name, next due date, last done date, and status label using the logic from task 4. No interactivity yet — plain read-only page.

## 6. Home page: list one-off tasks
Goal: Extend the home page to also show pending one-off tasks.
Description: Add the `OneOffTask` list to the same home page template (or a second section on it), showing name and due date if set, with overdue tasks flagged using the status logic from task 4. Still read-only.

## 7. Mobile-friendly base styling
Goal: The app is comfortably usable on a phone browser.
Description: Add a base template with a lightweight, mobile-first CSS setup (plain CSS or a small framework like Pico.css — no build step), and apply it to the home page so text, spacing, and tap targets work on a small screen.

## 8. Add a recurring chore
Goal: Users can create a new recurring chore from the UI.
Description: Add a form and view for creating a `RecurringChore` (name, interval in days, initial due date), wired up via HTMX so submitting returns the updated chore list partial without a full page reload.

## 9. Add a one-off task
Goal: Users can create a new one-off task from the UI.
Description: Add a form and view for creating a `OneOffTask` (name, optional due date), wired up via HTMX the same way as task 8, returning the updated task list partial.

## 10. Mark a recurring chore done
Goal: Completing a recurring chore updates it per the fixed-schedule rule.
Description: Add an HTMX endpoint that, on "mark done", sets `last_done_date` to today and advances `next_due_date` by `interval_days` from its *previous* value (not from today), then returns the updated row partial. Include a test proving a late completion does not shift the next occurrence.

## 11. Mark a one-off task done
Goal: Completing a one-off task removes it from the list.
Description: Add an HTMX endpoint that deletes the given `OneOffTask` on completion and returns the updated task list partial, with no record kept afterward.

## 12. Edit a recurring chore
Goal: Users can correct a recurring chore's name or interval after creating it.
Description: Add a form and view to edit a `RecurringChore`'s name or interval, wired up via HTMX so submitting returns the updated row/list partial without a full page reload.

## 13. Delete a recurring chore
Goal: Users can remove a recurring chore that's no longer wanted.
Description: Add an HTMX endpoint to delete a `RecurringChore` outright, returning the updated list partial.

## 14. LAN-accessible run configuration
Goal: The app can be opened from a phone on the home network.
Description: Document (e.g. in a README) and configure how to run the dev server bound to the machine's LAN IP (`manage.py runserver 0.0.0.0:8000`) rather than localhost-only, so it's reachable from other devices on the home LAN, with a note that it must never be exposed beyond the LAN.
