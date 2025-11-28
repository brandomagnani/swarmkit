# Factotum Chat (TypeScript)

A sandboxed AI agent in your terminal that can think, execute code, browse the web, read / edit files, and solve complex tasks. Ask for anything—any files created are automatically saved to `output/`.

## Setup

```bash
npm install

cp .env.example .env
# Edit .env with your API keys
```

## Run

```bash
npx tsx factotum.ts
```

Ask anything and check the traces at https://dashboard.swarmlink.ai/traces. Type `/quit` to exit.

## What it does

- Multi-turn conversation with a sandboxed AI agent
- Agent can write code, create files, browse the web (with EXA)
- Output files are saved to `output/`
