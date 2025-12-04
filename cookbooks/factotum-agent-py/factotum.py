#!/usr/bin/env python3
"""
Factotum Agent - An interactive chat with a sandboxed AI agent that can think, execute code,
browse the web, read / edit files, and solve complex tasks.
Ask for anything—any files the agent creates are automatically downloaded to your local `output/` folder.

Run: python factotum.py
"""
import asyncio
import os
from dotenv import load_dotenv
from swarmkit import SwarmKit, AgentConfig, E2BProvider
from rich_ui import RichRenderer, console
from rich.panel import Panel

load_dotenv()  # Load .env file

# ─────────────────────────────────────────────────────────────
# SwarmKit Instance Configuration
# ─────────────────────────────────────────────────────────────

AGENT = AgentConfig(
    type="gemini",                              # claude, codex, gemini,
    api_key=os.getenv("SWARMKIT_API_KEY"),
    model="gemini-3-pro-preview",             # optional: override default model
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

SYSTEM_PROMPT = """SYSTEM PROMPT: Your name is Factotum, a powerful autonomous AI agent.
You can execute code, browse the web, manage files, and solve complex tasks."""

agent = SwarmKit(
    config=AGENT,
    sandbox=SANDBOX,
    system_prompt=SYSTEM_PROMPT,
    mcp_servers=MCP_SERVERS,
    session_tag_prefix="factotum-agent-py",
)

# ─────────────────────────────────────────────────────────────

async def main():
    renderer = RichRenderer()
    agent.on("content", renderer.handle_event)

    console.print()
    console.print(Panel.fit(
        "[bold cyan]🤖 Factotum[/bold cyan]\n"
        "[dim]Autonomous AI Agent - Code, Browse, Files & More[/dim]",
        border_style="cyan",
    ))
    console.print()

    while True:
        prompt = console.input("[bold green]you:[/bold green] ").strip()
        if not prompt:
            continue
        if prompt in ("/quit", "/exit", "/q"):
            await agent.kill()
            console.print("\n[muted]👋 Goodbye[/muted]")
            break

        renderer.reset()
        renderer.start_live()
        await agent.run(prompt=prompt)
        renderer.stop_live()

        for f in await agent.get_output_files():
            path = f"output/{f.name}"
            content = f.content if isinstance(f.content, bytes) else f.content.encode("utf-8")
            with open(path, "wb") as out:
                out.write(content)
            console.print(f"[success]📄 Saved: {path}[/success]")

        console.print()

async def shutdown():
    await agent.kill()
    console.print("\n\n[muted]👋 Goodbye[/muted]")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown())
