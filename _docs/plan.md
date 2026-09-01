# Shared Household Chores — Scope

## Purpose
A personal chore-tracking tool. It tracks the user's own chore
responsibilities within a shared household — it is not a multi-user
or collaborative tool. Other household members do not log in or
interact with the app; the user tracks their own tasks independently.

## Scope decisions

- **Users**: single-user. No accounts, no login, no multi-user state.
- **Platform**: mobile-friendly web app (usable from a phone browser
  around the house, not a native app).
- **Chore types**:
  - Recurring chores on a fixed schedule (e.g. "vacuum every 7 days").
    The next due date is computed from the fixed schedule, not from
    the completion date — marking a chore done late does not push
    later occurrences back.
  - One-off tasks (e.g. "clean out the fridge this weekend"). Deleted
    on completion; not kept around as a done/archived record.
- **Reminders**: passive only. No push notifications, no digests.
  The app shows what's due/overdue when opened; the user checks in on
  their own schedule.
- **Timezone**: fixed to Europe/Berlin. No per-user or configurable
  timezone/locale settings.
- **Persistence**: a database (not a flat file). Choice of database
  engine deferred to the tech stack decision.
- **Access**: reachable only on the trusted home LAN; not exposed to
  the public internet. No auth, since only trusted household devices
  can reach it.
- **History/stats**: none. The app tracks current state only — what's
  due, what's overdue, when each chore was last done. No completion
  logs, streaks, or analytics.

## Explicitly out of scope
- Multi-user accounts or shared/collaborative views
- Push notifications or scheduled reminders
- Cloud hosting/deployment
- History, streaks, or analytics dashboards

## Status
Scope agreed with user on 2026-09-01. Next step: propose implementation
approaches (tech stack, data model) and produce a full design before
any implementation.
