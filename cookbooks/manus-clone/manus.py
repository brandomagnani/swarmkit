#!/usr/bin/env python3
"""
Manus Clone
-----------
Build your own Manus in a few lines of code. An autonomous AI agent in your terminal.

Run: python manus.py
"""
import asyncio
import os
from dotenv import load_dotenv
from swarmkit import SwarmKit, AgentConfig, E2BProvider

load_dotenv()  # Load .env file

# ─────────────────────────────────────────────────────────────
# SwarmKit Instance Configuration
# ─────────────────────────────────────────────────────────────

AGENT = AgentConfig(
    type="codex",                              # claude, codex, gemini,
    api_key=os.getenv("SWARMKIT_API_KEY"),
    # model="gpt-5.1-codex-max",                # optional: override default model
)

SANDBOX = E2BProvider(
    api_key=os.getenv("E2B_API_KEY"),
    timeout_ms=3_600_000,                       # optional: 1 hour default
)

MCP_SERVERS = {}
if os.getenv("EXA_API_KEY"):                    # optional: web search
    MCP_SERVERS["exa"] = {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
        "env": {"EXA_API_KEY": os.getenv("EXA_API_KEY")}
    }

agent = SwarmKit(config=AGENT, sandbox=SANDBOX, mcp_servers=MCP_SERVERS)

# ─────────────────────────────────────────────────────────────

async def main():
    agent.on("stdout", lambda x: print(x + ("\n" if x.rstrip().endswith("}") else ""), end=""))

    print("\n🤖 Agent ready. Ask anything.\n")

    while True:
        prompt = input("\nyou: ").strip()
        if not prompt:
            continue

        print()
        await agent.run(prompt=prompt)

        for f in await agent.get_output_files():
            path = f"output/{f.name}"
            content = f.content if isinstance(f.content, bytes) else f.content.encode("utf-8")
            with open(path, "wb") as out:
                out.write(content)
            print(f"\n📄 Saved: {path}")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye")
