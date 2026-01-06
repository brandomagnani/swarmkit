# HN Time Capsule

Recreating [Karpathy's HN Time Capsule](https://github.com/karpathy/hn-time-capsule) (1,486 lines) in ~50 lines with SwarmKit.

Analyzes HN frontpage articles from 10 years ago with hindsight, grades commenters on prediction accuracy, and generates an interactive HTML dashboard.

## Setup

```bash
cd cookbooks/typescript/hn-time-capsule
npm install
cp .env.example .env
# Edit .env with your API key
```

## Run

```bash
npm start
```

Output saved to `./output/index.html`

## How it works

1. **Fetch** — Scrapes HN frontpage, article content, and comments for a given date
2. **Map** — Each article analyzed by Claude Haiku agent (structured output)
3. **Reduce** — All analyses aggregated into interactive HTML dashboard
