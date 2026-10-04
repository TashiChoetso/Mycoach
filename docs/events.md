# Event schema

Table: `user_events`. Append-only. Services emit via `EventBus.emit(...)` after the domain write commits (same transaction).

## Envelope

| Field | Type | Required |
|---|---|---|
| id | uuid | yes |
| user_id | uuid | yes |
| event_type | text | yes |
| occurred_at | timestamptz | yes (user-facing time of the action) |
| entity_type | text | when tied to a row |
| entity_id | uuid | when tied to a row |
| idempotency_key | text | for complete/skip retries |
| metadata | jsonb | small; no secrets, no raw passwords |
| request_id | text | from logging middleware |
| created_at | timestamptz | insert time |

## Event types

| Type | metadata (typical) |
|---|---|
| LOGIN | `{ "method": "password" }` |
| AREA_CREATED | `{ "name", "is_custom" }` |
| AREA_SELECTED | `{ "area_id" }` |
| GOAL_CREATED / GOAL_UPDATED | `{ "status?" }` |
| HABIT_COMPLETED | `{ "date", "value?", "streak" }` |
| HABIT_SKIPPED / HABIT_MISSED | `{ "date" }` |
| TASK_CREATED | `{ "recurrence_type" }` |
| TASK_COMPLETED / TASK_SKIPPED | `{ "date" }` |
| EXPENSE_ADDED | `{ "amount", "category" }` |
| BUDGET_EXCEEDED | `{ "budget_id", "spent", "limit" }` |
| DAILY_REVIEW_VIEWED | `{ "score_date" }` |
| WEEKLY_REVIEW_VIEWED | `{ "week_start" }` |
| AI_CHAT_TURN | `{ "conversation_id" }` — no message body |

Product analytics (DAU, completion rate, retention) are queries over this table plus domain tables — not a second tracking vendor in MVP.
