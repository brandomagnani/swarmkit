#!/usr/bin/env python3
"""
Swarm CLI Agent + Composio Integrations

AI agent with access to 500+ external services via Composio Tool Router.
Can send emails, post to Slack, create GitHub issues, update Notion, and more.

Run: python swarm.py
"""
import asyncio
import os
from dotenv import load_dotenv
from swarmkit import SwarmKit, AgentConfig, read_local_dir, save_local_dir
from ui import make_renderer, read_prompt, console
from rich.panel import Panel
from composio_integration import ComposioIntegration

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Composio Setup
# ─────────────────────────────────────────────────────────────

composio = ComposioIntegration(
    user_id="swarm-user-001",
    toolkits=["gmail"],
)

# ─────────────────────────────────────────────────────────────
# SwarmKit Agent
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Your name is Swarm, a powerful autonomous AI agent.
You can execute code, manage files, and take actions across external services via Composio MCP.
"""

agent = SwarmKit(
    config=AgentConfig(type="claude", model="sonnet"),
    system_prompt=SYSTEM_PROMPT,
    mcp_servers={"composio": composio.get_mcp_config()},
    session_tag_prefix="swarm-composio-py",
)

# ─────────────────────────────────────────────────────────────

async def main():
    # Pre-authenticate Composio services
    await composio.setup_with_preauth()

    renderer = make_renderer()
    agent.on("content", renderer.handle_event)

    console.print()
    console.print(Panel.fit(
        "[bold cyan]Swarm[/bold cyan] + [bold magenta]Composio[/bold magenta]\n"
        "[dim]AI Agent with external integrations[/dim]",
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
