# CRE Portfolio Analysis

Analyzes commercial real estate rent roll PDFs and generates an investment committee portfolio dashboard.

Extracts tenant data from PDFs, computes property-level KPIs (occupancy, WALT, concentration, rollover risk), and classifies properties into Core Portfolio vs Watch List.

## Setup

```bash
cd cookbooks/python/cre-portfolio
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key
```

## Run

```bash
# Place rent roll PDFs in ./input/
python pipeline.py
```

Output saved to `./output/index.html`

## How it works

1. **Extract** — Claude Sonnet parses rent roll PDFs into structured tenant data
2. **Analyze** — Claude Haiku computes KPIs: occupancy, WALT, tenant concentration, rollover exposure
3. **Reduce** — Aggregates into HTML dashboard with Core Portfolio and Watch List classification
