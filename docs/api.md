# API contracts (v1)

Base URL: `/api/v1`  
Auth: `Authorization: Bearer <access_token>` except register/login/refresh.

Pagination: `?limit=20&cursor=<opaque>`. Response: `{ "items": [...], "next_cursor": "..." | null }`.

## Auth

### POST `/auth/register`

```json
{ "email": "nick@example.com", "password": "min 10 chars", "display_name": "Nick", "timezone": "Asia/Kolkata" }
```

201 `{ "user": User, "access_token": "...", "token_type": "bearer", "expires_in": 900 }`  
Refresh token: httpOnly cookie `refresh_token` + body `refresh_token` for mobile.

### POST `/auth/login`

`{ "email", "password" }` → 200 same as register. 401 on mismatch (same message for unknown email).

### POST `/auth/refresh`

Cookie or `{ "refresh_token" }`. Rotates refresh token.

### POST `/auth/logout`

Revokes current refresh token.

## Profile

### GET `/me`

```json
{
  "id": "uuid",
  "email": "nick@example.com",
  "display_name": "Nick",
  "timezone": "Asia/Kolkata",
  "locale": "en",
  "currency": "INR",
  "onboarding_completed_at": null,
  "preferences": {
    "theme": "system",
    "week_starts_on": 1,
    "scoring_weights": { "tasks": 0.3, "habits": 0.3, "goals": 0.2, "consistency": 0.1, "finance": 0.1 },
    "dashboard_sections": ["quote", "momentum", "tasks", "habits", "areas", "coach"]
  },
  "areas": [{ "id": "uuid", "name": "Health & Fitness", "slug": "health", "is_system": true }]
}
```

### PATCH `/me` — `display_name`, `timezone`, `locale`, `currency`  
### PATCH `/me/preferences` — partial preferences  
### POST `/me/onboarding/complete` — stamps `onboarding_completed_at`

## Areas

### GET `/areas`

Query `?include=catalog|selected|all` (default `all`).

```json
{
  "catalog": [{ "id": "...", "slug": "health", "name": "Health & Fitness", "selected": false }],
  "selected": [{ "id": "user_area_id", "area_id": "...", "name": "Photography", "is_custom": true, "sort_order": 0 }]
}
```

### POST `/areas`

Select catalog: `{ "area_id": "uuid" }`  
Create custom: `{ "name": "Photography", "description": "optional" }`  
409 if already selected / duplicate custom name.

### PATCH `/areas/{user_area_id}` — `custom_name`, `is_enabled`, `dashboard_visible`, `sort_order`  
### DELETE `/areas/{user_area_id}` — leave area; custom areas with no other refs may be deleted

## Goals / Habits / Tasks (phase 2)

Standard CRUD. Complete/skip:

`POST /habits/{id}/complete` `{ "date": "2026-09-06", "value": 20 }`  
`POST /habits/{id}/skip` `{ "date": "2026-09-06" }`  
`POST /tasks/{id}/complete` `{ "date": "2026-09-06" }`

Idempotent per (entity, date). Re-complete updates timestamp. Returns `{ "momentum_delta": 10, "score": 86 }` when scoring exists.

## Dashboard

### GET `/dashboard/today`

Server computes “today” in the user timezone.

```json
{
  "greeting": { "name": "Nick", "period": "morning", "quote": "..." },
  "momentum": { "score": 86, "max": 100, "rest_day": false },
  "tasks": { "items": [], "completed": 0, "total": 0 },
  "habits": { "items": [], "completed": 0, "due": 0 },
  "finance": null,
  "areas": [{ "id": "...", "name": "Learning", "score": 92 }],
  "coach": { "message": "...", "cta": { "label": "Start workout", "habit_id": "..." } }
}
```

`finance` is `null` when Finance is not selected. `coach` is a template in phases 1–5, LLM in phase 8.

## Scores & analytics

`GET /scores/today` → `{ "momentum": 86, "areas": [...], "breakdown": {...}, "rest_day": false }`  
`GET /analytics/daily?from&to`  
`GET /analytics/weekly?weeks=8`  
`GET /analytics/monthly?months=12`

## AI (phase 8)

`POST /ai/chat` `{ "conversation_id": null, "message": "How was my week?" }`  
Response streams later; MVP can be non-stream JSON with `citations` from tool payloads.

`GET /ai/insights`

## Notifications (phase 6)

`GET|PATCH /notifications/preferences`  
`GET /notifications` list in-app.
