#!/usr/bin/env python3
"""
Manus Clone - Rich TUI Streaming Example with Browser-Use
---------------------------------------------------------
Beautiful terminal UI with markdown rendering using Rich.
Streams agent output with syntax highlighting and formatted text.
Includes browser-use MCP for web automation capabilities.

Run: python manus_callbacks_browser.py
"""
import asyncio
import json
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from rich.theme import Theme
from swarmkit import SwarmKit, AgentConfig, E2BProvider

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Rich Console Theme
# ─────────────────────────────────────────────────────────────

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "success": "bold green",
    "muted": "dim white",
})

console = Console(theme=custom_theme)

# ─────────────────────────────────────────────────────────────
# SwarmKit Instance Configuration
# ─────────────────────────────────────────────────────────────

AGENT = AgentConfig(
    type="gemini",
    api_key=os.getenv("SWARMKIT_API_KEY"),
    model="gemini-3-pro-preview",
)

SANDBOX = E2BProvider(
    api_key=os.getenv("E2B_API_KEY"),
    timeout_ms=3_600_000,
)

MCP_SERVERS = {}

# Exa search support
# if os.getenv("EXA_API_KEY"):
#     MCP_SERVERS["exa"] = {
#         "command": "npx",
#         "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
#         "env": {"EXA_API_KEY": os.getenv("EXA_API_KEY")}
#     }

# Browser-Use MCP support (hosted version)
# Option 1: Using the hosted API (recommended for cloud deployments)
if os.getenv("BROWSER_USE_API_KEY"):
    MCP_SERVERS["browser-use"] = {
        "command": "npx",
        "args": [
            "-y",
            "mcp-remote",
            "https://api.browser-use.com/mcp",
            "--header",
            f"X-Browser-Use-API-Key: {os.getenv('BROWSER_USE_API_KEY')}"
        ]
    }
else:
    # Option 2: Using local self-hosted version (requires OpenAI/Anthropic key)
    # Falls back to local version if no BROWSER_USE_API_KEY is set
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        MCP_SERVERS["browser-use"] = {
            "command": "uvx",
            "args": ["--from", "browser-use[cli]", "browser-use", "--mcp"],
            "env": {"OPENAI_API_KEY": openai_key}
        }

SYSTEM_PROMPT = """You are Manus, a powerful autonomous AI agent.
You can execute code, browse the web with browser automation, manage files, and solve complex tasks.
With browser-use, you can automate browser interactions, extract data from websites, 
fill forms, click buttons, and navigate complex web applications.

IMPORTANT TOOL RESTRICTIONS:
- DO NOT use any tool named "web_fetch", "fetch", or similar HTTP fetching tools
- You MAY use browser automation tools (browser_navigate, browser_click, browser_type, etc.)
- Browser automation is preferred over direct HTTP fetching for web interactions

When responding, use markdown formatting for better readability."""

agent = SwarmKit(
    config=AGENT,
    sandbox=SANDBOX,
    system_prompt=SYSTEM_PROMPT,
    mcp_servers=MCP_SERVERS,
    session_tag_prefix="manus-tui-browser",
)

# ─────────────────────────────────────────────────────────────
# Streaming State & Handlers
# ─────────────────────────────────────────────────────────────

class StreamState:
    def __init__(self):
        self.buffer = ""
        self.sandbox_id = None
        self.is_running = False
        self.live = None
        self.events = []
        self.current_message = ""

state = StreamState()


def format_json_event(event_str):
    """Pretty format a JSON event for display."""
    try:
        event = json.loads(event_str)
        event_type = event.get("type", "unknown")
        
        if event_type == "init":
            return f"🚀 **Session Started**\n- Model: `{event.get('model', 'unknown')}`\n"
        
        elif event_type == "message":
            role = event.get("role", "unknown")
            content = event.get("content", "")
            delta = event.get("delta", False)
            
            if delta and content:
                state.current_message += content
                return None  # Don't render deltas individually
            elif not delta and content:
                state.current_message = content
                icon = "👤" if role == "user" else "🤖"
                return f"\n{icon} **{role.title()}:**\n{content}\n"
        
        elif event_type == "tool_use":
            tool_name = event.get("tool_name", "unknown")
            params = event.get("parameters", {})
            # Special icon for browser-use tools
            icon = "🌐" if "browser" in tool_name.lower() else "🔧"
            return f"\n{icon} **Tool Call:** `{tool_name}`\n```json\n{json.dumps(params, indent=2)}\n```\n"
        
        elif event_type == "tool_result":
            status = event.get("status", "unknown")
            output = event.get("output", "")
            icon = "✅" if status == "success" else "❌"
            result = f"\n{icon} **Result:** {status}\n"
            if output:
                result += f"```\n{output[:500]}{'...' if len(output) > 500 else ''}\n```\n"
            return result
        
        elif event_type == "result":
            stats = event.get("stats", {})
            return (f"\n📊 **Stats:**\n"
                   f"- Tokens: {stats.get('total_tokens', 0)} "
                   f"(in: {stats.get('input_tokens', 0)}, out: {stats.get('output_tokens', 0)})\n"
                   f"- Duration: {stats.get('duration_ms', 0)}ms\n"
                   f"- Tool calls: {stats.get('tool_calls', 0)}\n")
        
        return None
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def render_output():
    """Render current buffer as formatted markdown."""
    if not state.buffer.strip():
        return Spinner("dots", text="Thinking...", style="cyan")
    
    # If we have accumulated message content, show it
    if state.current_message:
        return Markdown(state.current_message)
    
    return Markdown(state.buffer)


def on_stdout(data):
    """Accumulate agent output and update live display."""
    # Try to parse as JSON events first
    lines = data.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        formatted = format_json_event(line)
        if formatted:
            state.buffer += formatted
        else:
            # If not a JSON event, just append raw data
            if not line.startswith('{"type":'):
                state.buffer += line + '\n'
    
    if state.live:
        state.live.update(render_output())


def on_stderr(data):
    """Handle stderr from sandbox."""
    console.print(Text(data, style="error"), end="")


def on_update(data):
    """Handle status updates (start/end messages)."""
    try:
        parsed = json.loads(data) if isinstance(data, str) else data
        if parsed.get("type") == "start":
            state.sandbox_id = parsed.get("sandbox_id")
            state.is_running = True
            console.print(f"[info]⚡ Sandbox: {state.sandbox_id}[/info]")
        elif parsed.get("type") == "end":
            state.is_running = False
    except (json.JSONDecodeError, TypeError):
        console.print(f"[muted]{data}[/muted]")


def on_error(error):
    """Handle terminal errors."""
    console.print(Panel(str(error), title="Error", border_style="red"))


def on_complete(info):
    """Handle completion event."""
    if state.live:
        state.live.stop()
    
    # Final render with full markdown - prefer current_message if available
    final_content = state.current_message if state.current_message else state.buffer
    
    if final_content.strip():
        console.print()
        console.print(Panel(
            Markdown(final_content),
            title="[bold cyan]Manus + Browser[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
    
    console.print(f"[success]✓ Complete[/success] [muted]exit={info['exit_code']}[/muted]")
    
    # Reset state for next run
    state.buffer = ""
    state.current_message = ""
    state.events = []


# Register callbacks
agent.on('stdout', on_stdout)
agent.on('stderr', on_stderr)
agent.on('update', on_update)
agent.on('error', on_error)
agent.on('complete', on_complete)

# ─────────────────────────────────────────────────────────────


async def run_with_live(prompt: str):
    """Run agent with live updating display."""
    state.buffer = ""
    state.is_running = True
    
    with Live(render_output(), console=console, refresh_per_second=10, transient=True) as live:
        state.live = live
        result = await agent.run(prompt=prompt)
        state.live = None
    
    return result


async def main():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🤖 Manus + Browser[/bold cyan]\n"
        "[dim]Autonomous AI Agent with Rich TUI & Browser Automation[/dim]",
        border_style="cyan",
    ))
    console.print()

    while True:
        try:
            prompt = console.input("[bold green]you:[/bold green] ").strip()
        except EOFError:
            break
            
        if not prompt:
            continue

        console.print()
        result = await run_with_live(prompt)

        # Save any output files
        for f in await agent.get_output_files():
            path = f"output/{f.name}"
            content = f.content if isinstance(f.content, bytes) else f.content.encode("utf-8")
            with open(path, "wb") as out:
                out.write(content)
            console.print(f"[success]📄 Saved:[/success] {path}")
        
        console.print()


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[muted]👋 Goodbye[/muted]")

