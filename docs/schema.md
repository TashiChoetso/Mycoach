# Database schema

PostgreSQL 16. UUID PKs (`gen_random_uuid()`). `created_at` / `updated_at` on mutable tables. All user data tables indexed on `user_id`.

## users

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| email | citext unique not null | |
| password_hash | text not null | argon2 |
| display_name | text not null | |
| timezone | text not null default `'UTC'` | IANA |
| locale | text not null default `'en'` | |
| currency | text not null default `'INR'` | ISO 4217, duplicated onto preferences |
| onboarding_completed_at | timestamptz | |
| is_active | boolean not null default true | |
| created_at, updated_at | timestamptz | |

## user_preferences

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid unique FK users | |
| theme | text default `'system'` | |
| week_starts_on | smallint default 1 | 0=Sun … 6=Sat |
| scoring_weights | jsonb not null | see scoring.md |
| dashboard_sections | jsonb not null | ordered visible section ids |
| quiet_hours_start / end | time | |
| notification_types | jsonb | enabled types |
| reminder_time | time | morning brief default |
| created_at, updated_at | timestamptz | |

## areas

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| slug | text unique | system catalog only |
| name | text not null | |
| description | text | |
| icon | text | lucide key |
| color | text | token name, not hex required |
| is_system | boolean not null | catalog vs custom |
| owner_user_id | uuid FK users | null for system |
| sort_order | int default 0 | |
| created_at, updated_at | timestamptz | |

Unique `(owner_user_id, lower(name))` where `owner_user_id is not null`.

## user_areas

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| area_id | uuid FK | |
| custom_name | text | rename overlay |
| is_enabled | boolean default true | |
| dashboard_visible | boolean default true | |
| sort_order | int | |
| created_at, updated_at | timestamptz | |
| unique (user_id, area_id) | | |

## goals

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| user_area_id | uuid FK user_areas | |
| title, description | text | |
| target_value | numeric | nullable qualitative goals |
| current_value | numeric default 0 | |
| unit | text | |
| start_date, target_date | date | |
| status | text | `active\|paused\|completed\|archived` |
| created_at, updated_at | timestamptz | |

## goal_milestones

id, goal_id, title, target_value, sort_order, reached_at, created_at, updated_at.

## habits

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id, user_area_id | uuid | |
| goal_id | uuid nullable | |
| name, description | text | |
| frequency_type | text | `daily\|weekly\|weekdays\|times_per_week\|monthly` |
| frequency_config | jsonb | `{ "days": [1,3,5], "times": 4 }` |
| target_value | numeric | e.g. 20 pages, 8000 steps |
| target_unit | text | |
| reminder_time | time | |
| start_date, end_date | date | |
| difficulty | text | `easy\|medium\|hard` |
| is_active | boolean default true | |
| created_at, updated_at | timestamptz | |

## habit_logs

id, user_id, habit_id, log_date (date), status (`completed\|skipped\|missed`), value numeric, note text, completed_at, unique (habit_id, log_date).

## tasks

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id, user_area_id | uuid | |
| goal_id, habit_id | uuid nullable | |
| title, description | text | |
| priority | text | `low\|medium\|high` |
| due_date | date | first due / anchor |
| recurrence_type | text | `none\|daily\|weekly\|monthly\|custom` |
| recurrence_config | jsonb | |
| estimated_duration_minutes | int | |
| status | text | definition status; one-time uses this too |
| completed_at, skipped_at | timestamptz | |
| created_at, updated_at | timestamptz | |

## task_completions

id, user_id, task_id, occurrence_date, status (`completed\|skipped`), completed_at, unique (task_id, occurrence_date).

## expense_categories

id, user_id nullable (null = system), name, parent_id, slug, is_system, created_at, updated_at.

## expenses

id, user_id, category_id, amount numeric(12,2), currency, type (`expense\|income`), occurred_on date, description, payment_method, user_area_id, notes, created_at, updated_at.

## budgets

id, user_id, category_id nullable (null = overall), period (`daily\|weekly\|monthly\|yearly`), amount, currency, start_date, user_area_id, created_at, updated_at.

## daily_scores

id, user_id, score_date, momentum int 0–100 nullable, breakdown jsonb, created_at, unique (user_id, score_date).

## area_scores

id, user_id, user_area_id, score_date, score int, breakdown jsonb, unique (user_area_id, score_date).

## daily_metrics / weekly_metrics / monthly_metrics

id, user_id, period_start, payload jsonb (pre-aggregated counters). Unique (user_id, period_start).

## detected_patterns

id, user_id, pattern_key, evidence jsonb, confidence numeric, detected_at, valid_until.

## user_events

id, user_id, event_type, occurred_at, entity_type, entity_id, idempotency_key, metadata jsonb, request_id, created_at. Index (user_id, occurred_at desc), unique (user_id, idempotency_key) where key present.

## notifications

id, user_id, type, title, body, scheduled_at, sent_at, read_at, payload jsonb.

## ai_conversations / ai_messages

conversation: id, user_id, title, created_at, updated_at.  
message: id, conversation_id, role (`user\|assistant\|tool`), content, tool_name, tool_payload jsonb, created_at.

## ai_insights

id, user_id, insight_type, title, body, evidence jsonb, period_start, period_end, created_at.

## custom_metrics / metric_logs

User-defined measures on an area (e.g. “pages written”). Logs are dated values.

## Indexes (required)

- `user_areas (user_id, is_enabled)`
- `goals (user_id, status)`
- `habits (user_id, is_active)`
- `habit_logs (user_id, log_date)`
- `tasks (user_id, due_date)`
- `task_completions (user_id, occurrence_date)`
- `expenses (user_id, occurred_on)`
- `daily_scores (user_id, score_date)`
- `user_events (user_id, event_type, occurred_at)`
