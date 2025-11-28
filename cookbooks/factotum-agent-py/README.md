# Factotum Agent (Python)

- An interactive chat with a sandboxed AI agent that can think, execute code, browse the web, read / edit files, and solve complex tasks.
- Ask for anything—any files the agent creates are automatically downloaded to your local `output/` folder.
- Check traces at https://dashboard.swarmlink.ai/traces. Type `/quit` to exit.

## Setup

```bash
cd cookbooks/factotum-agent-py
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

- Edit `.env` with your API keys: `SWARMKIT_API_KEY` ([swarmlink.ai](https://swarmlink.ai)), `E2B_API_KEY` ([e2b.dev](https://e2b.dev)), `EXA_API_KEY` ([exa.ai](https://exa.ai), optional)

## Run

```bash
python factotum.py
```

## What it does

- Multi-turn conversation with a sandboxed AI agent
- Agent can write code, create files, browse the web (with EXA)
- Output files are saved to `output/`
