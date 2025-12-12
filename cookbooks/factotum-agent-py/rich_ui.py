"""Rich UI renderer for SwarmKit content events - Claude Code style incremental output."""

from __future__ import annotations

from rich.console import Console
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
from rich.spinner import Spinner
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
    """Renders ACP content events with incremental output (Claude Code style)."""

    def __init__(self, show_reasoning: bool = False):
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}  # tool_id -> {info}
        self.tool_order = []  # ordered list of tool_ids
        self.show_reasoning = show_reasoning
        self.status_live: Live | None = None
        self._last_was_tool = False
        self._last_plan_str = ""
        self._has_content = False

    def _one_line(self, value: str, max_len: int = 120) -> str:
        if not isinstance(value, str):
            value = str(value)
        compact = " ".join(value.split())
        if len(compact) > max_len:
            return compact[: max_len - 3] + "..."
        return compact

    def reset(self):
        self._stop_status_live(final=False)
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}
        self.tool_order = []
        self._last_was_tool = False
        self._last_plan_str = ""
        self._has_content = False

    def handle_event(self, event: dict):
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

    def _handle_message(self, update: dict):
        content = update.get("content", {})
        if content.get("type") == "text":
            self.current_message += content.get("text", "")

    def _handle_thought(self, update: dict):
        content = update.get("content", {})
        if content.get("type") == "text":
            self.thought_buffer += content.get("text", "")

    def _handle_tool_call(self, update: dict):
        tool_id = update.get("toolCallId", "")
        title = update.get("title", "Tool")
        kind = update.get("kind", "other")
        raw_input = update.get("rawInput", {})
        status = update.get("status") or "pending"

        # Flush message first
        self._flush_message()

        # Upsert tool (some backends may emit tool_call multiple times per id)
        if tool_id not in self.tools:
            self.tool_order.append(tool_id)
            self.tools[tool_id] = {}
        self.tools[tool_id].update({
            'title': title,
            'kind': kind,
            'status': status,
            'raw_input': raw_input,
        })

        # Skip todo tools
        if title in ("write_todos", "TodoWrite") or "todo" in title.lower():
            return

        self._last_was_tool = True
        self._refresh_status_live()

    def _handle_tool_update(self, update: dict):
        tool_id = update.get("toolCallId", "")
        status = update.get("status")
        title = update.get("title")

        # Create placeholder if updates arrive out of order
        if tool_id not in self.tools:
            self.tool_order.append(tool_id)
            self.tools[tool_id] = {
                'title': title or "Tool",
                'kind': "other",
                'status': status or "pending",
                'raw_input': {},
            }

        old_status = self.tools[tool_id].get('status')
        if status is not None and old_status != status:
            self.tools[tool_id]['status'] = status
        if title:
            self.tools[tool_id]['title'] = title

        # Skip todo tools
        effective_title = self.tools[tool_id].get('title', '')
        if effective_title in ("write_todos", "TodoWrite") or "todo" in effective_title.lower():
            return

        self._refresh_status_live()

    def _handle_plan(self, update: dict):
        entries = update.get("entries", [])
        if not entries:
            return

        # Build plan string to check if it changed
        lines = []
        for entry in entries:
            status = entry.get("status", "pending")
            content = entry.get("content", "")
            icon = {"completed": "✓", "in_progress": "→", "pending": "○"}.get(status, "○")
            lines.append(f"{icon} {content}")

        plan_str = "\n".join(lines)

        # Only print if plan content changed
        if plan_str == self._last_plan_str:
            return
        self._last_plan_str = plan_str

        # Blank line before plan if there's prior content
        if self._has_content:
            console.print()

        styled_lines = []
        for entry in entries:
            status = entry.get("status", "pending")
            content = entry.get("content", "")
            icon = {"completed": "✓", "in_progress": "→", "pending": "○"}.get(status, "○")
            style = {"completed": "success", "in_progress": "info", "pending": "muted"}.get(status, "muted")
            styled_lines.append(f"[{style}]{icon} {content}[/{style}]")

        console.print(Panel("\n".join(styled_lines), title="[bold]Plan[/bold]", border_style="cyan", padding=(0, 1)))
        console.print()  # blank line after plan
        self._last_was_tool = False
        self._has_content = True
        self._refresh_status_live()

    def _should_display_tool(self, title: str) -> bool:
        if title in ("write_todos", "TodoWrite") or "todo" in title.lower():
            return False
        return True

    def _format_tool_line(self, tool_id: str) -> Text:
        tool = self.tools[tool_id]
        title = tool.get('title', 'Tool')
        kind = tool.get('kind', 'other')
        status = tool.get('status', 'pending')
        raw_input = tool.get('raw_input', {}) or {}

        kind_labels = {
            "read": "Read", "edit": "Write", "execute": "Bash",
            "fetch": "Fetch", "search": "Search", "think": "Task", "switch_mode": "Mode",
        }

        content = self._get_tool_content(kind, raw_input, title)

        result = Text()
        dot_style = "success" if status == 'completed' else "error" if status == 'failed' else "tool"
        result.append("● ", style=dot_style)

        label = kind_labels.get(kind)
        if label:
            result.append(f"{label}(", style="white")
            result.append(self._one_line(content), style="dim white")
            result.append(")", style="white")
        else:
            result.append(f"{title}(", style="white")
            result.append(self._one_line(content), style="dim white")
            result.append(")", style="white")

        return result

    def _flush_message(self):
        if self.current_message.strip():
            if self._last_was_tool:
                console.print()

            console.print(Markdown(self.current_message))
            console.print()
            self.current_message = ""
            self._last_was_tool = False
            self._has_content = True
            self._refresh_status_live()

    def _get_tool_content(self, kind: str, raw_input: dict, title: str) -> str:
        raw_input = raw_input or {}
        if kind == "fetch":
            return raw_input.get("url") or raw_input.get("query") or title
        elif kind == "search":
            return raw_input.get("query") or raw_input.get("pattern") or raw_input.get("path") or title
        elif kind == "edit":
            return raw_input.get("file_path") or raw_input.get("path") or title
        elif kind == "read":
            return raw_input.get("file_path") or raw_input.get("absolute_path") or raw_input.get("path") or title
        elif kind == "execute":
            return raw_input.get("command") or title
        else:
            return (raw_input.get("command") or raw_input.get("query") or
                    raw_input.get("file_path") or raw_input.get("path") or
                    raw_input.get("instruction") or title)

    def _render_status(self, show_spinner: bool = True):
        lines = []
        for tool_id in self.tool_order:
            tool = self.tools.get(tool_id, {}) or {}
            title = tool.get('title', '') or ''
            if not self._should_display_tool(title):
                continue
            lines.append(self._format_tool_line(tool_id))

        if not show_spinner:
            return Group(*lines) if lines else Text("")

        spinner_table = Table.grid(padding=(0, 1))
        spinner_table.add_row(Spinner("dots", style="cyan"), Text("Working...", style="dim cyan"))

        if lines:
            lines.append(Text(""))
            lines.append(spinner_table)
            return Group(*lines)

        return spinner_table

    def _start_status_live(self):
        if self.status_live is not None:
            return
        self.status_live = Live(
            self._render_status(show_spinner=True),
            console=console,
            refresh_per_second=12,
            transient=False,
        )
        self.status_live.start()

    def _refresh_status_live(self):
        if self.status_live is None:
            return
        self.status_live.update(self._render_status(show_spinner=True), refresh=True)

    def _stop_status_live(self, *, final: bool):
        if self.status_live is None:
            return
        if final:
            self.status_live.update(self._render_status(show_spinner=False), refresh=True)
        self.status_live.stop()
        self.status_live = None

    def start_live(self):
        console.print()
        console.print("[bold cyan]Factotum[/bold cyan]")
        console.print()
        self._start_status_live()

    def stop_live(self):
        self._stop_status_live(final=True)

        if self.current_message.strip():
            if self._last_was_tool:
                console.print()
            console.print(Markdown(self.current_message))

        if self.show_reasoning and self.thought_buffer.strip():
            console.print()
            console.print(Panel(
                Text(self.thought_buffer, style="thought"),
                title="[dim]Reasoning[/dim]",
                border_style="dim",
                padding=(0, 1),
            ))
