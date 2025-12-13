# Swarm Agent (Python)

- A sandboxed terminal agent that can think, execute code, browse the web, read / edit files, and solve complex tasks.
- Put any files to the `input/` folder that is automatically created upon running `python Swarm.py`: these files will be part of the agent context.
- Ask for anything—any files the agent creates are automatically downloaded to your local `output/` folder.
- Check traces at https://dashboard.swarmlink.ai/traces. Type `/quit` to exit.

## Setup

```bash
cd cookbooks/agent-python
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

- Edit `.env` with your API keys: `SWARMKIT_API_KEY` ([dashboard.swarmlink.ai](https://dashboard.swarmlink.ai)), `E2B_API_KEY` ([e2b.dev](https://e2b.dev/sign-in)), `EXA_API_KEY` ([exa.ai](https://exa.ai), optional)

## Run

```bash
python Swarm.py
```

## What it does

- Multi-turn conversation with a sandboxed AI agent
- Agent can write code, create files, browse the web (with EXA)
- Output files are saved to `output/`
