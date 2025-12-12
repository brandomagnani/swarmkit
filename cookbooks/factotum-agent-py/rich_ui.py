"""Rich UI renderer for SwarmKit content events - Claude Code style incremental output."""

import sys
from rich.console import Console
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
        self.spinner_live = None
        self._last_was_tool = False
        self._last_plan_str = ""
        self._has_content = False
        self._needs_spacing = False
        self._can_update_tools = True  # False if plan/message printed after tools

    def _one_line(self, value: str, max_len: int = 120) -> str:
        if not isinstance(value, str):
            value = str(value)
        compact = " ".join(value.split())
        if len(compact) > max_len:
            return compact[: max_len - 3] + "..."
        return compact

    def reset(self):
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}
        self.tool_order = []
        self._last_was_tool = False
        self._last_plan_str = ""
        self._has_content = False
        self._needs_spacing = False
        self._can_update_tools = True

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

        # Flush message first
        self._flush_message()

        # Skip if already printed
        if tool_id in self.tools:
            return

        self.tools[tool_id] = {
            'title': title,
            'kind': kind,
            'status': 'pending',
            'raw_input': raw_input
        }
        self.tool_order.append(tool_id)

        # Skip todo tools
        if title in ("write_todos", "TodoWrite") or "todo" in title.lower():
            return

        self._stop_spinner()
        self._print_tool(tool_id)
        self._last_was_tool = True
        self._can_update_tools = True  # tools can be updated now
        self._start_spinner()

    def _handle_tool_update(self, update: dict):
        tool_id = update.get("toolCallId", "")
        status = update.get("status", "")

        if tool_id not in self.tools:
            return

        old_status = self.tools[tool_id]['status']
        if old_status == status:
            return

        self.tools[tool_id]['status'] = status

        # Update dot color in place
        title = self.tools[tool_id]['title']
        if title in ("write_todos", "TodoWrite") or "todo" in title.lower():
            return

        self._update_tool_in_place(tool_id)

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

        self._stop_spinner()

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
        self._needs_spacing = False  # already has blank line
        self._can_update_tools = False  # can't update tools above plan
        self._start_spinner()

    def _print_tool(self, tool_id: str):
        tool = self.tools[tool_id]
        title = tool['title']
        kind = tool['kind']
        status = tool['status']
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

        console.print(result)
        self._has_content = True
        self._needs_spacing = True

    def _update_tool_in_place(self, tool_id: str):
        """Update a tool's dot color using ANSI cursor movement."""
        if tool_id not in self.tool_order:
            return

        # Skip if plan/message was printed after tools (line count would be wrong)
        if not self._can_update_tools:
            return

        # Find position: count visible tools after this one
        tool_index = self.tool_order.index(tool_id)
        visible_after = 0
        for tid in self.tool_order[tool_index + 1:]:
            t = self.tools.get(tid, {})
            title = t.get('title', '')
            if title not in ("write_todos", "TodoWrite") and "todo" not in title.lower():
                visible_after += 1

        lines_back = visible_after + 1  # +1 for spinner

        self._stop_spinner()

        # Build the tool line string
        tool = self.tools[tool_id]
        title = tool['title']
        kind = tool['kind']
        status = tool['status']
        raw_input = tool.get('raw_input', {}) or {}

        kind_labels = {
            "read": "Read", "edit": "Write", "execute": "Bash",
            "fetch": "Fetch", "search": "Search", "think": "Task", "switch_mode": "Mode",
        }
        content = self._get_tool_content(kind, raw_input, title)
        content = self._one_line(content)

        # Color codes
        dot_color = "\033[32m" if status == 'completed' else "\033[31m" if status == 'failed' else "\033[36m"
        reset = "\033[0m"
        dim = "\033[2m"

        label = kind_labels.get(kind, title)
        line = f"{dot_color}● {reset}{label}({dim}{content}{reset})"

        # Move up, clear line, print, move back down
        sys.stdout.write(f"\033[{lines_back}A")  # Move up
        sys.stdout.write("\033[2K")  # Clear line
        sys.stdout.write(f"\r{line}\n")  # Print with newline
        if lines_back > 1:
            sys.stdout.write(f"\033[{lines_back - 1}B")  # Move down
        sys.stdout.flush()

        self._start_spinner()

    def _flush_message(self):
        if self.current_message.strip():
            self._stop_spinner()

            if self._last_was_tool:
                console.print()

            console.print(Markdown(self.current_message))
            console.print()
            self.current_message = ""
            self._last_was_tool = False
            self._has_content = True
            self._needs_spacing = False  # already has blank line
            self._can_update_tools = False  # can't update tools above message
            self._start_spinner()

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

    def _start_spinner(self):
        if self.spinner_live is None:
            if self._needs_spacing:
                console.print()  # blank line before spinner
                self._needs_spacing = False
            spinner_table = Table.grid(padding=(0, 1))
            spinner_table.add_row(Spinner("dots", style="cyan"), Text("Working...", style="dim cyan"))
            self.spinner_live = Live(spinner_table, console=console, refresh_per_second=10, transient=True)
            self.spinner_live.start()

    def _stop_spinner(self):
        if self.spinner_live:
            self.spinner_live.stop()
            self.spinner_live = None

    def start_live(self):
        console.print()
        console.print("[bold cyan]Factotum[/bold cyan]")
        console.print()
        self._start_spinner()

    def stop_live(self):
        self._stop_spinner()

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
