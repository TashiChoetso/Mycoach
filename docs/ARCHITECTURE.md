# MyCoach — Architecture

**Product:** AI-powered Personal Life Coach / Life Operating System  
**Loop:** Plan → Act → Track → Understand → Improve → Repeat  
**North star:** What should I do today? How am I doing? Where am I struggling? What should I do next?

This document is the source of truth for MVP architecture. Application code follows it incrementally.

---

## 1. System architecture

Modular monolith. No microservices in MVP.

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js web app (primary client)                           │
│  Calm, editorial UI · later: Expo mobile sharing the API    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / JSON  Bearer JWT
┌────────────────────────────▼────────────────────────────────┐
│  FastAPI modular monolith                                   │
│  api/  services/  repositories/  scoring/  analytics/  ai/  │
└─┬───────────┬───────────┬───────────┬───────────┬───────────┘
  │           │           │           │           │
  ▼           ▼           ▼           ▼           ▼
Postgres    Redis     Workers      LLM         Push
(source     (rate     (scores,     (reason     (later)
 of truth)   limit,    reviews,     only)
             jobs)     notify)
```

**Client choice:** Next.js web first so the full journey can be verified in a browser. The API is client-agnostic; Expo can be added without changing domain logic.

**AI path (never skip the data layer):**

```
User message → intent → tool selection → structured retrieval
  → deterministic analytics → LLM reasoning → validated response
```

The LLM never computes scores, streaks, totals, or budget math.

---

## 2. Database ERD

PostgreSQL. UUID primary keys. `timestamptz` in UTC. `date` columns are calendar dates in the **user's timezone**. Every user-owned row has `user_id` and is queried only through that scope.

```
users 1──1 user_preferences
  │
  ├──* user_areas *──1 areas          (catalog + user-owned custom)
  │        │
  │        ├──* goals ──* goal_milestones
  │        ├──* habits ──* habit_logs
  │        ├──* tasks  ──* task_completions
  │        └──* custom_metrics ──* metric_logs
  │
  ├──* expenses *──1 expense_categories
  ├──* budgets
  ├──* daily_scores ──* area_scores
  ├──* daily_metrics / weekly_metrics / monthly_metrics
  ├──* detected_patterns
  ├──* user_events
  ├──* notifications
  ├──* ai_conversations ──* ai_messages
  └──* ai_insights
```

Full column definitions: [schema.md](./schema.md).

**Timezone rule:** store instants as UTC. Convert to `users.timezone` (IANA) before deciding “today”, recurrence, streaks, and daily scores. Tests must cover `America/New_York` vs `Asia/Kolkata` around midnight.

---

## 3. Domain model

| Entity | Role |
|---|---|
| **User** | Account, timezone, locale, onboarding state |
| **Area** | Life domain. System catalog *or* user-created. Never assume a fixed set. |
| **UserArea** | Membership, rename, sort, dashboard visibility |
| **Goal** | Outcome in an area, optional numeric target + milestones |
| **Habit** | Recurring practice linked to an area and optional goal |
| **Task** | One-time or recurring action. Completions live on `task_completions` so recurrence does not mutate history |
| **Expense / Budget** | Only meaningful when Finance (or a custom money area) is enabled |
| **DailyScore / AreaScore** | Snapshots from the scoring engine — not from the LLM |
| **UserEvent** | Append-only behavioral log for analytics and AI context |
| **DetectedPattern** | Output of statistical analysis, later passed to the coach |
| **AiInsight** | Grounded recommendation with evidence JSON |

---

## 4. API contracts

REST, `/api/v1`. JSON. Cursor pagination (`limit`, `cursor`) on lists. All mutation bodies validated with Pydantic. Every resource endpoint is **user-scoped** in the repository layer, not only in the router.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Access + refresh JWT |
| POST | `/auth/refresh` | Rotate access token |
| POST | `/auth/logout` | Revoke refresh token |
| GET | `/me` | Profile + preferences |
| PATCH | `/me` | Name, timezone, locale |
| PATCH | `/me/preferences` | Scoring weights, dashboard, currency |
| GET/POST | `/areas` | List selected + catalog; add/create |
| PATCH/DELETE | `/areas/{id}` | Rename, hide, leave, delete custom |
| GET/POST | `/goals` | Goals in selected areas |
| PATCH | `/goals/{id}` | Update progress / status |
| GET/POST | `/habits` | Habits |
| POST | `/habits/{id}/complete` | Log completion for a date |
| POST | `/habits/{id}/skip` | Skip without breaking compassion copy |
| GET/POST | `/tasks` | Tasks |
| POST | `/tasks/{id}/complete` | Complete occurrence |
| POST | `/tasks/{id}/skip` | Skip occurrence |
| GET/POST | `/expenses` | Finance only |
| GET/POST | `/budgets` | Finance only |
| GET | `/dashboard/today` | Today screen payload |
| GET | `/scores/today` | Momentum + area scores |
| GET | `/analytics/daily\|weekly\|monthly` | Aggregates |
| POST | `/ai/chat` | Coach turn with tools |
| GET | `/ai/insights` | Stored grounded insights |
| GET/PATCH | `/notifications/preferences` | Quiet hours, types |

Auth: `Authorization: Bearer <access_token>`. Refresh token in httpOnly cookie (web) and returned in JSON for future mobile.

Errors: `{ "error": { "code": "NOT_FOUND", "message": "...", "request_id": "..." } }`  
401 unauthenticated · 403 forbidden · 404 not found *or* other user's id (same 404) · 409 conflict · 422 validation · 429 rate limit.

Full request/response shapes: [api.md](./api.md).

---

## 5. Frontend routes

| Route | Screen | MVP |
|---|---|---|
| `/` | Splash → redirect | yes |
| `/login` `/signup` | Auth | yes |
| `/onboarding/areas` | Multi-select + create custom | yes |
| `/onboarding/goals` | Per-area “what do you want?” | phase 2 |
| `/onboarding/habits` | Editable suggestions | phase 2 |
| `/today` | Primary home | yes (grows each phase) |
| `/tasks` `/habits` `/goals` | Domain screens | phase 2–3 |
| `/finance` | Hidden unless Finance selected | phase 7 |
| `/analytics` | Drill-down | phase 5 |
| `/coach` | AI coach | phase 8 |
| `/notifications` `/settings` `/profile` | Account | phase 1 profile/settings shell |

Dashboard sections are data-driven from `user_preferences.dashboard_sections` and enabled `user_areas`. Finance widgets never render unless that area is enabled.

---

## 6. Momentum Score algorithm

**Name:** Momentum Score · range 0–100 · **deterministic Python** in `app/scoring`. The LLM is forbidden from producing this number.

### 6.1 What it measures

Progress against **this user's plan for this local calendar day**. It is not a judgment of worth. A day with nothing planned is a rest day (`null` score), never a zero.

### 6.2 Per-area score

For each enabled area that has at least one planned signal:

| Component | When active | Formula |
|---|---|---|
| Tasks | ≥1 occurrence due today | `completed / (due − skipped)` × 100 |
| Habits | ≥1 habit due today | `completed / (due − skipped)` × 100 |
| Goals | ≥1 active goal with a target | on-track ratio, clamped 0–100: `actual_progress / expected_progress` |
| Consistency | ≥1 habit or task with 7-day history | 7-day completion rate × 100 |
| Finance | Finance area enabled **and** a budget exists | `100` if spent ≤ budget; else `100 × budget / spent` |

Skipped items are excluded from the denominator (a skip is not a miss). Missed items (day ended, neither complete nor skip) count as incomplete.

Default weights (stored on `user_preferences.scoring_weights`):

```
tasks 0.30 · habits 0.30 · goals 0.20 · consistency 0.10 · finance 0.10
```

Inactive components are dropped. Remaining weights are **renormalized to 1.0**. A user without Finance is never scored on Finance.

`area_score = round(Σ weight_i × component_i)` then clamp 0–100.

### 6.3 Overall Momentum

Equal-weight mean of **active** area scores (areas with no planned signals are omitted).

Optional consistency bonus: `+ floor(7_day_habit_rate × 5)`, then clamp at 100. Bonus is applied after the mean so it cannot hide a collapsed day.

### 6.4 Persistence

Nightly worker (and on-demand after completions) writes `daily_scores` + `area_scores`. The Today endpoint may compute live for “today” and read snapshots for history.

---

## 7. AI tool schema

Coach context is a **structured briefing**, not the database. Tools fetch more. Tools return analytics DTOs; they never return raw ORM rows.

```json
{
  "tools": [
    { "name": "get_today_summary", "args": {} },
    { "name": "get_weekly_summary", "args": { "week_start": "date?" } },
    { "name": "get_monthly_summary", "args": { "year": "int?", "month": "int?" } },
    { "name": "get_area_progress", "args": { "area_id": "uuid?" } },
    { "name": "get_goal_progress", "args": { "goal_id": "uuid?" } },
    { "name": "get_habit_history", "args": { "habit_id": "uuid", "days": "int=28" } },
    { "name": "get_task_history", "args": { "from": "date", "to": "date" } },
    { "name": "get_expense_summary", "args": { "from": "date", "to": "date" } },
    { "name": "get_budget_status", "args": { "period": "daily|weekly|monthly" } },
    { "name": "get_streak", "args": { "habit_id": "uuid" } },
    { "name": "get_behavior_patterns", "args": { "area_id": "uuid?" } }
  ]
}
```

Safety: never invent stats; if a tool returns empty, the model must say data is insufficient. No financial guarantees, no medical diagnosis, no data mutation without an explicit confirmed user action (mutation tools are out of MVP chat).

Full JSON Schema: [ai.md](./ai.md).

---

## 8. Event schema

Append-only. Written in the same request as the domain mutation (outbox-style function in the service layer).

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "event_type": "TASK_COMPLETED",
  "occurred_at": "timestamptz",
  "entity_type": "task",
  "entity_id": "uuid",
  "idempotency_key": "string?",
  "metadata": {},
  "request_id": "string?",
  "created_at": "timestamptz"
}
```

Core types: `TASK_CREATED|COMPLETED|SKIPPED`, `HABIT_COMPLETED|SKIPPED|MISSED`, `GOAL_CREATED|UPDATED`, `EXPENSE_ADDED`, `BUDGET_EXCEEDED`, `AREA_CREATED`, `LOGIN`, `DAILY_REVIEW_VIEWED`, `WEEKLY_REVIEW_VIEWED`, `AI_CHAT_TURN`.

---

## 9. MVP scope

**In (phases 1–5):** auth, areas (catalog + custom), goals, habits, tasks, Today dashboard, completions, Momentum Score, analytics (daily/weekly/monthly).

**Out of first ship (phases 6–10):** push notifications, finance, AI coach, pattern detection, advanced personalization.

Every phase must leave a runnable app. Phase 1 is already a complete slice: register → choose areas → see a personalized Today shell.

---

## 10. Risks and decisions

| Decision | Choice | Why |
|---|---|---|
| Client | Next.js web first | Browser-verifiable; API stays mobile-ready |
| Architecture | Modular monolith | MVP does not need service boundaries |
| Recurring tasks | Definition + `task_completions` by date | History stays immutable |
| Custom areas | Row in `areas` with `owner_user_id` | Unlimited custom domains, same hierarchy |
| Scoring | Dedicated Python module | Deterministic, testable, LLM-proof |
| AI | Tools over dumps | Grounding; cheaper; safer |
| Isolation | `user_id` in every repository query | IDOR returns 404 |
| Time | UTC storage, user TZ for “today” | Correct streaks and scores |
| Finance | Optional area | No penalty, no UI, no score weight |

| Risk | Mitigation |
|---|---|
| Timezone / DST bugs | Golden tests around midnight in multiple zones |
| Score feels like judgment | Copy, rest-day `null`, skip ≠ fail |
| LLM hallucination | Tools + “insufficient data” contract + no score from model |
| Notification spam | Later; prefs, quiet hours, caps |
| Scope explosion | Four north-star questions gate features |
| Recurrence edge cases | Completions table; never rewrite past rows |
