#!/usr/bin/env python3
"""
Swarm Agent - An interactive chat with a sandboxed AI agent that can think, execute code,
browse the web, read / edit files, and solve complex tasks.

- Put files in `input/` folder - they're uploaded to the agent's context before each run
- Files the agent creates are automatically downloaded to your `output/` folder

Run: python swarm.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from swarmkit import SwarmKit, AgentConfig, E2BProvider
from ui import make_renderer, read_prompt, console
from rich.panel import Panel

load_dotenv()  # Load .env file

# ─────────────────────────────────────────────────────────────
# SwarmKit Instance Configuration
# ─────────────────────────────────────────────────────────────

AGENT = AgentConfig(
    type="codex",                              # claude, codex, gemini,
    api_key=os.getenv("SWARMKIT_API_KEY"),
    model="gpt-5.2",
)

SANDBOX = E2BProvider(
    api_key=os.getenv("E2B_API_KEY"),
    timeout_ms=3_600_000,                       # optional: 1 hour default
)

MCP_SERVERS = {}

# Chrome DevTools MCP - browser automation and debugging
MCP_SERVERS["chrome-devtools"] = {
    "command": "npx",
    "args": [
        "chrome-devtools-mcp@latest",
        "--headless=true",
        "--isolated=true",
        "--chromeArg=--no-sandbox",
        "--chromeArg=--disable-setuid-sandbox",
        "--chromeArg=--disable-dev-shm-usage",
    ],
    "env": {}
}

if os.getenv("EXA_API_KEY"):                    # optional: web search
    MCP_SERVERS["exa"] = {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
        "env": {"EXA_API_KEY": os.getenv("EXA_API_KEY")}
    }

SYSTEM_PROMPT = """Your name is Swarm, a powerful autonomous AI agent.
You can execute code, browse the web, manage files, and solve complex tasks such as extracting
data from complex documents, analyzing data, producing evidence based reports, and more.
"""

agent = SwarmKit(
    config=AGENT,
    sandbox=SANDBOX,
    system_prompt=SYSTEM_PROMPT,
    mcp_servers=MCP_SERVERS,
    session_tag_prefix="Swarm-agent-py",
)

# ─────────────────────────────────────────────────────────────

async def main():
    renderer = make_renderer()
    agent.on("content", renderer.handle_event)

    console.print()
    console.print(Panel.fit(
        "[bold cyan]🤖 Swarm[/bold cyan]\n"
        "[dim]Autonomous AI Agent - Code, Browse, Files & More[/dim]",
        border_style="cyan",
    ))
    console.print()

    while True:
        prompt = await read_prompt()
        if not prompt:
            continue
        if prompt in ("/quit", "/exit", "/q"):
            await agent.kill()
            console.print("\n[muted]👋 Goodbye[/muted]")
            break

        console.print()
        renderer.reset()
        renderer.start_live()

        # Upload input files to agent's context
        input_files = {f.name: f.read_bytes() for f in Path("input").iterdir() if f.is_file()}
        if input_files:
            await agent.upload_context(input_files)

        await agent.run(prompt=prompt)
        renderer.stop_live()

        output_files = await agent.get_output_files(recursive=True)
        for name, content in output_files.items():
            path = f"output/{name}"
            with open(path, "wb") as out:
                out.write(content if isinstance(content, bytes) else content.encode("utf-8"))
            console.print(f"[success]📄 Saved: {path}[/success]")

        console.print()

async def shutdown():
    await agent.kill()
    console.print("\n\n[muted]👋 Goodbye[/muted]")

if __name__ == "__main__":
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown())
