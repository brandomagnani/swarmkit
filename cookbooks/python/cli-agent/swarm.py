#!/usr/bin/env python3
"""
Swarm CLI Agent - A sandboxed CLI agent that can think, execute code,
browse the web, read / edit files, and solve complex tasks.

- Put files in `input/` folder - they're uploaded to the agent's context before each run
- Files the agent creates are automatically downloaded to your `output/` folder

Run: python swarm.py
"""
import asyncio
import os
from dotenv import load_dotenv
from swarmkit import SwarmKit, AgentConfig, read_local_dir, save_local_dir
from ui import make_renderer, read_prompt, console
from rich.panel import Panel

load_dotenv()  # Load .env file

# ─────────────────────────────────────────────────────────────
# SwarmKit Instance Configuration
# ─────────────────────────────────────────────────────────────

MCP_SERVERS = {}

if os.getenv("BROWSER_USE_API_KEY"):            # optional: browser automation
    MCP_SERVERS["browser-use"] = {
        "command": "npx",
        "args": [
            "-y",
            "mcp-remote",
            "https://api.browser-use.com/mcp",
            "--header",
            f"X-Browser-Use-API-Key: {os.getenv('BROWSER_USE_API_KEY')}",
        ],
    }

SYSTEM_PROMPT = """Your name is Swarm, a powerful autonomous AI agent.
You can execute code, browse the web, manage files, and solve complex tasks such as extracting
data from complex documents, analyzing data, producing evidence based reports, and more.
"""

agent = SwarmKit(
    config=AgentConfig(
        type="claude", 
        model="haiku"
    ), 
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
        input_files = read_local_dir("input")
        if input_files:
            await agent.upload_context(input_files)

        await agent.run(prompt=prompt)
        renderer.stop_live()

        # Download output files
        output = await agent.get_output_files(recursive=True)
        if output.files:
            save_local_dir("output", output.files)
            console.print()
            for name in output.files:
                console.print(f"[success]📄 Saved: output/{name}[/success]")

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
