# AIgram

A daily, swipeable feed of AI-engineering micro-lessons (LangChain, LangGraph, RAG, MLflow, evals), generated nightly from a learner profile. Installable on iPhone as a full-screen web app.

**Live:** https://parth1604.github.io/Practicals/

## Layout

```
docs/
  index.html, app.js, styles.css   # the app shell (never changes day to day)
  manifest.webmanifest, sw.js      # installability + offline cache
  icons/                           # home-screen icons
  profile.json                     # what the learner knows / struggled with / is ready for next
  feed/index.json                  # { latest, dates[] }
  feed/YYYY-MM-DD.json             # one day's cards
```

## Card schema

```json
{
  "id": "2026-11-21-07",
  "bucket": "reinforce | next | fresh",
  "type": "concept | code | diagram | quiz",
  "topic": "kebab-case-topic-id",
  "title": "One line. Markdown-lite: `code`, *em*, **strong**.",
  "body": "2–4 sentences, one idea.",
  "why": "Optional: why it matters / where it shows up in practice.",
  "code": { "lang": "python", "src": "..." },
  "diagram": {
    "direction": "row | col",
    "nodes": [{ "id": "a", "label": "planner", "kind": "terminal?" }],
    "edges": [["a", "b"]],
    "caption": "optional"
  },
  "quiz": { "question": "...", "options": ["..."], "answer": 1, "explain": "..." }
}
```

Buckets per day: ~40% reinforce (spaced repetition over `profile.known`), ~40% next (one hop past current level, from `profile.next`), ~20% fresh (recent releases / production patterns).

## Nightly generation

A scheduled Claude task runs at 05:00 Europe/London: reads `profile.json` and any feedback pasted into it, writes `feed/<tomorrow>.json`, updates `feed/index.json`, commits and pushes. The app picks the newest feed whose date ≤ today.

## Feedback loop (v1)

The app logs views, saves, "explain more", "already know it" and quiz results to `localStorage`. Tap **Export log**, paste it to Claude, and it is merged into `profile.json` for the next run. A proper backend (Supabase) replaces this once the habit sticks.

## Install on iPhone

Open the live URL in Safari → Share → **Add to Home Screen**. Opens full-screen, works offline with the last cached feed.
