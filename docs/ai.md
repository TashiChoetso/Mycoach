# AI coach

Phase 8. Specified now so later work does not dump the database into the prompt.

## Context briefing (always sent)

Compact JSON, numbers only from analytics DTOs:

- profile: name, timezone, selected area names
- today: momentum, task/habit counts, remaining priorities
- week: averages, best/worst area
- patterns: ids + one-line summaries from `detected_patterns` (phase 9)
- safety flags: finance_enabled, rest_day, consecutive_miss_days

Token budget: keep briefing under ~2k tokens. Tools pull detail.

## Tool JSON Schema (OpenAI-style)

```json
{
  "type": "function",
  "function": {
    "name": "get_today_summary",
    "description": "Deterministic today dashboard DTO in the user's timezone.",
    "parameters": { "type": "object", "properties": {} }
  }
}
```

Other tools take the arguments listed in ARCHITECTURE.md. Return shapes must include `"source": "analytics"` and `"as_of": "<iso>"`. If a tool has no rows:

```json
{ "source": "analytics", "as_of": "...", "empty": true, "reason": "no_expenses_in_range" }
```

The model is instructed to say so, not to guess.

## Safety contract (system prompt non-negotiables)

1. Never invent statistics. Only cite tool numbers.
2. Never claim an action happened unless a tool shows it.
3. No mutations in chat MVP.
4. No guaranteed financial outcomes; not professional financial advice.
5. No medical diagnosis.
6. No guilt, shame, or manipulative urgency.
7. Label observations vs recommendations.
8. Insufficient data → say so and suggest the smallest tracking step.
9. Falling behind → encouragement first, then one practical next action.

## Encouragement policy

| Signal | Mode |
|---|---|
| Completion ≥ 80% today | Brief praise + protect rest |
| One miss, day still open | Normalize; one next action |
| 2–4 consecutive quiet days | Welcome back; one small win |
| Finance overspend | Neutral fact + optional question; no moralizing |

## Pattern handoff (phase 9)

Analytics writes `detected_patterns`. Coach may call `get_behavior_patterns` and must quote evidence (e.g. “morning workouts 82% vs evening 41%, n=24 days”). No pattern → no causal claim.
