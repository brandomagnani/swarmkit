#!/usr/bin/env python3
"""
Factotum Agent - An interactive chat with a sandboxed AI agent that can think, execute code,
browse the web, read / edit files, and solve complex tasks.

- Put files in `input/` folder - they're uploaded to the agent's context before each run
- Files the agent creates are automatically downloaded to your `output/` folder

Run: python factotum.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from swarmkit import SwarmKit, AgentConfig, E2BProvider
from rich_ui import RichRenderer, console
from rich.panel import Panel

load_dotenv()  # Load .env file

# ─────────────────────────────────────────────────────────────
# SwarmKit Instance Configuration
# ─────────────────────────────────────────────────────────────

AGENT = AgentConfig(
    type="codex",                              # claude, codex, gemini,
    api_key=os.getenv("SWARMKIT_API_KEY"),
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
You can execute code, browse the web, manage files, and solve complex tasks such as 
extracting data from complex documents, analyzing data, and producing reports, and more. 
When you are asked to extract data, do not use external toos, rely on your excellent multimodal
reasoning capabilities to extract the data from the documents. You can read most file formats such 
as text, csv, json, pdf, images, and more.
"""

agent = SwarmKit(
    config=AGENT,
    sandbox=SANDBOX,
    system_prompt=SYSTEM_PROMPT,
    mcp_servers=MCP_SERVERS,
    session_tag_prefix="factotum-agent-py",
)

# ─────────────────────────────────────────────────────────────

async def prompt_input() -> str:
    """Read user input with a styled, full-width input bar.

    Uses prompt_toolkit when available (recommended) for a Codex-like multiline input
    experience. Falls back to Rich's console.input() if prompt_toolkit isn't installed.
    """
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import HSplit, Window
        from prompt_toolkit.output import create_output
        from prompt_toolkit.styles import Style
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.widgets import TextArea
    except Exception:
        # Keep prompt responsive even inside async main.
        return (await asyncio.to_thread(console.input, "[bold green]>[/bold green] ")).rstrip("\n")

    bg = "#303030"
    style = Style.from_dict({
        "inputbar": f"bg:{bg}",
        "prompt": f"bold fg:#00d75f bg:{bg}",
        "input": f"fg:#ffffff bg:{bg}",
    })

    text_area = TextArea(
        prompt=HTML("<prompt>&gt;</prompt> "),
        multiline=True,
        wrap_lines=True,
        style="class:input",
    )

    kb = KeyBindings()

    @kb.add("enter")
    def _submit(event) -> None:
        event.app.exit(result=text_area.text)

    # prompt_toolkit doesn't support Shift+Enter in a portable way.
    # Use Esc then Enter to insert a newline.
    @kb.add("escape", "enter")
    def _newline(event) -> None:
        text_area.buffer.insert_text("\n")

    def _max_input_lines() -> int:
        try:
            rows = create_output().get_size().rows
        except Exception:
            rows = 24
        # 2 pad lines + keep ~3 lines for context above.
        return max(1, rows - 5)

    def _input_height() -> int:
        return max(1, min(text_area.document.line_count, _max_input_lines()))

    input_window = Window(
        content=text_area.control,
        style="class:inputbar",
        height=_input_height,
        dont_extend_height=True,
    )

    pad = Window(
        content=FormattedTextControl(""),
        style="class:inputbar",
        height=1,
        dont_extend_height=True,
    )

    input_bar = HSplit([pad, input_window, pad])

    app = Application(
        layout=Layout(input_bar),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    # Run prompt-toolkit without nesting event loops.
    return ((await app.run_async()) or "").rstrip("\n")

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
        prompt = await prompt_input()
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

        output_files = await agent.get_output_files()
        if output_files:
            console.print()  # blank line before saved files
            for f in output_files:
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
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown())
