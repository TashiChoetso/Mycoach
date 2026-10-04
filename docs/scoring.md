# Momentum Score

Computed only in `backend/app/scoring`. Unit-tested. Never produced by an LLM.

## Rest days

If the user has **no** tasks due and **no** habits due on that local date, and no finance budget for that day:

- `momentum = null`
- `rest_day = true`
- UI copy: “Nothing planned — that’s okay.”

Do not write `0`. Zero means a planned day with no follow-through.

## Skip vs miss

| Status | In numerator | In denominator |
|---|---|---|
| completed | yes | yes |
| skipped | no | no |
| missed / still open | no | yes |

## Goal on-track ratio

```
elapsed = max(1, days from start_date to score_date)
span    = max(elapsed, days from start_date to target_date)
expected = (elapsed / span) * target_value
actual   = current_value
ratio    = actual / expected          # expected 0 → treat as 1.0 if actual ≥ 0
score    = clamp(round(ratio * 100), 0, 100)
```

Qualitative goals (no `target_value`): omitted from the goals component.

## Finance

Only if a selected area is Finance (slug `finance`) **or** a user area flagged as money-tracking in later customization, **and** a budget covers the day.

- `spent <= budget` → 100 × (1 is too generous if they spent 0 against a budget — still 100; under-budget is success)
- `spent > budget` → `round(100 * budget / spent)`

No budget → component inactive (not a penalty).

## Weight renormalization

```
active = {k: w[k] for k in components if component_is_active}
total  = sum(active.values())
norm   = {k: v / total for k, v in active.items()}
area   = round(sum(norm[k] * scores[k] for k in norm))
```

## Overall

```
active_areas = [a for a in enabled_areas if a.has_signal_today]
if not active_areas: rest day
momentum = round(mean(area.score for area in active_areas))
momentum = min(100, momentum + floor(seven_day_habit_rate * 5))
```

## Worked example

Nick, 2026-09-06, areas Health / Learning / Productivity / Finance.

| Area | Tasks | Habits | Goals | Finance | Active weights | Area score |
|---|---|---|---|---|---|---|
| Health | — | 1/2 = 50 | on-track 80 | off | H0.43 G0.29 C0.14 (renorm from 0.3/0.2/0.1) | ~61 |
| Learning | 1/1 = 100 | 1/1 = 100 | 90 | off | T0.33 H0.33 G0.22 C0.11 | ~97 |
| Productivity | 2/3 = 67 | — | 70 | off | T0.50 G0.33 C0.17 | ~69 |
| Finance | — | — | 40 | 72/100 remaining → 100 | G0.50 F0.25 C0.25 | ~70 |

Overall mean of 61, 97, 69, 70 ≈ **74**. Plus consistency bonus if 7-day rate is 0.8 → +4 → **78**.

(Exact numbers in tests use fixtures; this table is illustrative of renormalization, not a golden fixture.)

## Config

Defaults live in `app/scoring/weights.py` and are copied onto `user_preferences.scoring_weights` at registration. Users may PATCH weights; each must be ≥ 0 and not all zero.
