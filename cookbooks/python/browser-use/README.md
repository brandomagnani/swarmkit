# Browser-Use Cookbook

Scrape Hacker News posts using browser-use cloud API with SwarmKit.

## What it does

1. Visits the top 3 Hacker News posts in parallel
2. Extracts metadata (title, points, comments, URLs)
3. Captures screenshots of each post
4. Generates a markdown summary with embedded images
5. Saves everything locally

## Setup

1. Get a browser-use API key from https://browser-use.com
2. Create a `.env` file:
   ```
   BROWSER_USE_API_KEY=your_key_here
   SWARMKIT_API_KEY=your_swarmkit_key
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
python browser.py
```

## Output

Results are saved to `output_browser_use/hn_top_3_multimodal_<timestamp>/`:

```
output_browser_use/
└── hn_top_3_multimodal_20250109_120000/
    ├── run_config.json
    ├── index.json
    └── posts/
        ├── 001/
        │   ├── data.json
        │   ├── summary.md
        │   └── screenshots/...
        ├── 002/
        └── 003/
```

## Files

| File | Purpose |
|------|---------|
| `browser.py` | Main script with pipeline configuration |
| `prompt.py` | Prompt template for the agent |
| `schema.py` | Pydantic schema for structured output |
| `items.py` | Helper functions for items and result saving |
