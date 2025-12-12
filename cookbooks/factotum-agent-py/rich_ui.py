"""Rich UI renderer for SwarmKit content events."""

import time
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from rich.theme import Theme

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

    def __init__(self, show_reasoning: bool = False):
        self.events = []  # Ordered list: {'type': 'tool'|'message', ...}
        self.current_message = ""  # Accumulating message chunk
        self.thought_buffer = ""
        self.plan_entries = []
        self.tools = {}  # id -> {title, status} for updates
        self.live = None
        self.working = False
        self.show_reasoning = show_reasoning
        # Throttle explicit refreshes; Live also auto-refreshes.
        self._last_refresh_s = 0.0
        self._min_refresh_interval_s = 0.1  # ~10Hz

    def _one_line(self, value: str, max_len: int = 160) -> str:
        """Collapse whitespace/newlines and truncate for single-line tool display."""
        if not isinstance(value, str):
            value = str(value)
        compact = " ".join(value.split())
        if len(compact) > max_len:
            return compact[: max_len - 3] + "..."
        return compact

    def reset(self):
        self.events = []
        self.current_message = ""
        self.thought_buffer = ""
        self.plan_entries = []
        self.tools = {}
        self.working = False

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
            self.current_message += text
            self._refresh()

    def _handle_thought(self, update: dict):
        content = update.get("content", {})
        if content.get("type") == "text":
            text = content.get("text", "")
            self.thought_buffer += text

    def _handle_tool_call(self, update: dict):
        tool_id = update.get("toolCallId", "")
        title = update.get("title", "Tool")
        kind = update.get("kind", "other")
        status = update.get("status", "pending")
        raw_input = update.get("rawInput", {})

        # Flush current message if any (to maintain order)
        if self.current_message.strip():
            self.events.append({'type': 'message', 'text': self.current_message})
            self.current_message = ""

        # Track tool
        self.tools[tool_id] = {'title': title, 'kind': kind, 'status': status, 'raw_input': raw_input}
        self.events.append({'type': 'tool', 'id': tool_id})
        self._refresh()

    def _handle_tool_update(self, update: dict):
        tool_id = update.get("toolCallId", "")
        status = update.get("status", "")

        if tool_id in self.tools:
            self.tools[tool_id]['status'] = status
            self._refresh()

    def _handle_plan(self, update: dict):
        self.plan_entries = update.get("entries", [])
        self._refresh()

    def _refresh(self):
        # Avoid re-rendering on every event (quadratic cost with many tool calls).
        if not self.live:
            return
        now = time.monotonic()
        if now - self._last_refresh_s >= self._min_refresh_interval_s:
            self._last_refresh_s = now
            # Update renderable without forcing per-event renders.
            self.live.update(self, refresh=True)

    def _render_tool(self, tool_id: str) -> Text:
        """Render a single tool status with kind-based label."""
        tool = self.tools.get(tool_id, {})
        title = tool.get('title', 'Tool')
        kind = tool.get('kind', 'other')
        status = tool.get('status', 'pending')
        raw_input = tool.get('raw_input', {}) or {}

        # Skip displaying todo/plan tools (plan is shown separately)
        if title in ("write_todos", "TodoWrite") or "todo" in title.lower():
            return None

        # Map kind to display label (like Claude Code)
        kind_labels = {
            "read": "Read",
            "edit": "Write",
            "execute": "Bash",
            "fetch": "Fetch",
            "search": "Search",
            "think": "Task",
            "switch_mode": "Mode",
        }

        # Extract meaningful content from rawInput based on kind
        def get_content():
            # Try to get the most relevant parameter
            if kind == "fetch":
                return raw_input.get("url") or raw_input.get("query") or title
            elif kind == "search":
                # Web search (query) or file search (pattern/path)
                return raw_input.get("query") or raw_input.get("pattern") or raw_input.get("path") or raw_input.get("command") or title
            elif kind == "edit":
                return raw_input.get("file_path") or raw_input.get("path") or title
            elif kind == "read":
                return raw_input.get("file_path") or raw_input.get("absolute_path") or raw_input.get("path") or title
            elif kind == "execute":
                return raw_input.get("command") or title
            else:
                # For unknown kinds, try common parameter names
                return (raw_input.get("command") or raw_input.get("query") or
                        raw_input.get("file_path") or raw_input.get("path") or
                        raw_input.get("instruction") or title)

        # Determine dot color based on status
        if status in ('pending', 'in_progress'):
            dot_style = "tool"
        elif status == 'completed':
            dot_style = "success"
        elif status == 'failed':
            dot_style = "error"
        else:
            dot_style = "muted"

        # Build styled text: colored dot, white label and content
        result = Text()
        result.append("● ", style=dot_style)

        label = kind_labels.get(kind)
        content = get_content()

        # Strip backticks - not needed with Type() format
        if isinstance(content, str):
            content = content.strip("`")

        if isinstance(content, str):
            content = self._one_line(content)
        else:
            content = self._one_line(str(content))

        if label:
            # Strip redundant prefix (e.g., "Read /path" → "/path")
            if isinstance(content, str) and content.lower().startswith(label.lower() + " "):
                content = content[len(label) + 1:]
            result.append(f"{label}(", style="white")
            result.append(str(content), style="dim white")
            result.append(")", style="white")
        else:
            # Use tool name as label for unknown kinds (MCP tools etc.)
            result.append(f"{title}(", style="white")
            result.append(str(content), style="dim white")
            result.append(")", style="white")

        return result

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

        # Working spinner at top
        if self.working:
            from rich.table import Table
            spinner_row = Table.grid(padding=(0, 1))
            spinner_row.add_row(Spinner("dots", style="cyan"), Text("Working...", style="bold cyan"))
            elements.append(spinner_row)
            elements.append(Text())

        # Plan at top if exists
        plan = self._render_plan()
        if plan:
            elements.append(plan)
            elements.append(Text())

        # Render events in order (interleaved tools and messages)
        # Each tool on its own line, with spacing between sections
        prev_type = None
        for event in self.events:
            # Add spacing when switching between tools and messages
            if prev_type and prev_type != event['type']:
                elements.append(Text())

            if event['type'] == 'message':
                elements.append(Markdown(event['text']))
            elif event['type'] == 'tool':
                tool_element = self._render_tool(event['id'])
                if tool_element:  # Skip None (e.g., todo tools)
                    elements.append(tool_element)

            prev_type = event['type']

        # Current streaming message
        if self.current_message.strip():
            # Add spacing if previous was a tool
            if prev_type == 'tool':
                elements.append(Text())
            elements.append(Markdown(self.current_message))

        # If nothing yet, show working spinner only
        if not elements:
            elements.append(Text(" ", style="muted"))

        # Wrap everything in panel
        content = Group(*elements) if len(elements) > 1 else elements[0]
        return Panel(content, title="[bold cyan]Factotum[/bold cyan]", border_style="cyan", padding=(1, 2))

    def __rich__(self):
        """Make renderer itself a renderable for Live auto-refresh."""
        return self._render()

    def start_live(self):
        self.working = True
        self.live = Live(self, console=console, refresh_per_second=10, transient=False)
        self.live.start()

    def stop_live(self):
        self.working = False
        if self.live:
            # Final render with "Factotum" title (not working)
            self.live.update(self._render())
            self.live.stop()
            self.live = None

        # Show reasoning if any (after main panel)
        if self.show_reasoning and self.thought_buffer.strip():
            console.print()
            console.print(Panel(
                Text(self.thought_buffer, style="thought"),
                title="[dim]Reasoning[/dim]",
                border_style="dim",
                padding=(0, 1),
            ))
