"""Rich UI renderer for SwarmKit content events."""

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from rich.theme import Theme
from rich.table import Table

theme = Theme({
    "info": "cyan",
    "warning": "magenta",
    "error": "bold red",
    "success": "bold green",
    "muted": "dim white",
    "thought": "dim italic",
    "tool": "dim cyan",
})

console = Console(theme=theme)


class RichRenderer:
    """Renders ACP content events with Rich formatting."""

    def __init__(self):
        self.message_buffer = ""
        self.thought_buffer = ""
        self.live = None
        self.tools = []  # List of {id, title, status}
        self.plan_entries = []

    def reset(self):
        self.message_buffer = ""
        self.thought_buffer = ""
        self.tools = []
        self.plan_entries = []

    def handle_event(self, event: dict):
        """Handle a content event and render it."""
        update = event.get("update", {})
        event_type = update.get("sessionUpdate")

        if event_type == "agent_message_chunk":
            self._handle_message(update)
        elif event_type == "agent_thought_chunk":
            self._handle_thought(update)
        elif event_type == "tool_call":
            self._handle_tool_call(update)
        elif event_type == "tool_call_update":
            self._handle_tool_update(update)
        elif event_type == "plan":
            self._handle_plan(update)
        # Skip user_message_chunk - inconsistent across agents

    def _handle_message(self, update: dict):
        content = update.get("content", {})
        if content.get("type") == "text":
            text = content.get("text", "")
            self.message_buffer += text
            self._refresh()

    def _handle_thought(self, update: dict):
        content = update.get("content", {})
        if content.get("type") == "text":
            text = content.get("text", "")
            self.thought_buffer += text

    def _handle_tool_call(self, update: dict):
        tool_id = update.get("toolCallId", "")
        title = update.get("title", "Tool")
        status = update.get("status", "pending")

        # Add or update tool in list
        for tool in self.tools:
            if tool["id"] == tool_id:
                tool["status"] = status
                self._refresh()
                return

        self.tools.append({"id": tool_id, "title": title, "status": status})
        self._refresh()

    def _handle_tool_update(self, update: dict):
        tool_id = update.get("toolCallId", "")
        status = update.get("status", "")

        for tool in self.tools:
            if tool["id"] == tool_id:
                tool["status"] = status
                self._refresh()
                return

    def _handle_plan(self, update: dict):
        self.plan_entries = update.get("entries", [])
        self._refresh()

    def _refresh(self):
        if self.live:
            self.live.update(self._render())

    def _render_tools(self) -> Text:
        """Render tool status as compact text."""
        if not self.tools:
            return Text()

        parts = []
        for tool in self.tools:
            status = tool["status"]
            title = tool["title"]
            if status in ("pending", "in_progress"):
                parts.append(f"[tool]⚙ {title}...[/tool]")
            elif status == "completed":
                parts.append(f"[success]✓ {title}[/success]")
            elif status == "failed":
                parts.append(f"[error]✗ {title}[/error]")

        return Text.from_markup("  ".join(parts))

    def _render_plan(self) -> Panel:
        """Render plan as a panel."""
        if not self.plan_entries:
            return None

        lines = []
        for entry in self.plan_entries:
            status = entry.get("status", "pending")
            content = entry.get("content", "")
            icon = {"completed": "✓", "in_progress": "→", "pending": "○"}.get(status, "○")
            style = {"completed": "success", "in_progress": "info", "pending": "muted"}.get(status, "muted")
            lines.append(f"[{style}]{icon} {content}[/{style}]")

        return Panel("\n".join(lines), title="[bold]Plan[/bold]", border_style="cyan", padding=(0, 1))

    def _render(self):
        """Render current state for live display."""
        elements = []

        # Plan at top if exists
        plan = self._render_plan()
        if plan:
            elements.append(plan)
            elements.append(Text())

        # Tools status
        tools = self._render_tools()
        if tools.plain:
            elements.append(tools)
            elements.append(Text())

        # Message or spinner
        if self.message_buffer.strip():
            elements.append(Markdown(self.message_buffer))
        else:
            elements.append(Spinner("dots", text="Working...", style="cyan"))

        return Group(*elements) if len(elements) > 1 else elements[0]

    def start_live(self):
        self.live = Live(self._render(), console=console, refresh_per_second=10, transient=True)
        self.live.start()

    def stop_live(self):
        if self.live:
            self.live.stop()
            self.live = None

        # Show reasoning if any (before message)
        if self.thought_buffer.strip():
            console.print(Panel(
                Text(self.thought_buffer, style="thought"),
                title="[dim]Reasoning[/dim]",
                border_style="dim",
                padding=(0, 1),
            ))
            console.print()

        # Show final message in panel
        if self.message_buffer.strip():
            console.print(Panel(
                Markdown(self.message_buffer),
                title="[bold cyan]Factotum[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            ))

        # Show final plan if any
        if self.plan_entries:
            console.print()
            console.print(self._render_plan())
