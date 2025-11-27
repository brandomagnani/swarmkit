# Manus Clone

Build your own Manus in a few lines of code. 
A sandboxed AI agent in your terminal that can think, 
execute code, browse the web, read / edit files, and solve complex tasks.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys
```

## Run

```bash
source .venv/bin/activate
python manus.py
```

Ask Manus anything and check the traces at https://dashboard.swarmlink.ai/traces.

## What it does

- Multi-turn conversation with a sandboxed AI agent
- Agent can write code, create files, browse the web (with EXA)
- Output files are saved to `output/`
