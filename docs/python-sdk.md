# SwarmKit Python SDK

Run terminal-based AI agents in secure sandboxes with built-in observability.

> See the [main README](../README.md) for installation and API keys.
>
> **Note:** Requires [Node.js 18+](https://nodejs.org/) (the SDK uses a lightweight Node.js bridge).

---

## 1. Quick Start

```python
import os
from swarmkit import SwarmKit, AgentConfig, E2BProvider

# Create sandbox provider
sandbox = E2BProvider(api_key=os.getenv('E2B_API_KEY'))

# Build SwarmKit instance
swarmkit = SwarmKit(
    config=AgentConfig(
        type='codex',
        api_key=os.getenv('SWARMKIT_API_KEY')
    ),
    sandbox=sandbox,
    session_tag_prefix='my-agent',  # optional tag for the agent session
    system_prompt='You are a helpful coding assistant.',
    mcp_servers={
        'exa': {
            'command': 'npx',
            'args': ['-y', 'mcp-remote', 'https://mcp.exa.ai/mcp'],
            'env': {'EXA_API_KEY': os.getenv('EXA_API_KEY')}
        }
    }
)

# Run agent
result = await swarmkit.run(prompt='Create a hello world script')

print(result.stdout)

# Get output files
files = await swarmkit.get_output_files()
for file in files:
    print(f"{file.name} ({file.size} bytes)")

# Clean up
await swarmkit.kill()
```

- **Tracing:** Every run is automatically logged to [dashboard.swarmlink.ai/traces](https://dashboard.swarmlink.ai/traces)—no extra setup needed. Optionally use `session_tag_prefix` to label your agent session for easy filtering.

---

## 2. Full Configuration

```python
swarmkit = SwarmKit(

    # (required) Agent type and API key
    config=AgentConfig(
        type='codex',
        api_key=os.getenv('SWARMKIT_API_KEY'),
        model='gpt-5.1-codex',               # (optional) Uses default if omitted
        reasoning_effort='medium',           # (optional) 'low' | 'medium' | 'high' | 'xhigh' - Only Codex agents
    ),

    # (required) Sandbox provider for execution
    sandbox=E2BProvider(api_key=os.getenv('E2B_API_KEY')),

    # (optional) Custom working directory, default: /home/user/workspace
    working_directory='/home/user/workspace',

    # (optional) Workspace mode: 'knowledge' (default) for knowledge work use cases or 'swe' for coding use cases
    workspace_mode='knowledge',

    # (optional) System prompt appended to default instructions
    system_prompt='You are a careful pair programmer.',

    # (optional) Environment variables injected into sandbox
    secrets={'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN')},

    # (optional) Prefix for observability logs
    session_tag_prefix='my-agent',

    # (optional) Uploads to {workingDir}/context/ on first run
    context={
        'docs/readme.txt': 'User provided context...',
        'data.json': '{"key": "value"}',
    },

    # (optional) Uploads to {workingDir}/ on first run
    files={
        'scripts/setup.sh': '#!/bin/bash\necho hello',
    },

    # (optional) MCP servers for agent tools
    mcp_servers={
        'exa': {
            'command': 'npx',
            'args': ['-y', 'mcp-remote', 'https://mcp.exa.ai/mcp'],
            'env': {'EXA_API_KEY': os.getenv('EXA_API_KEY')}
        }
    },
)
```

**Note:**
- The sandbox is created on the first `run()` or `execute_command()` call (see below).
- Context files, workspace files, MCP servers, and system prompt are set up once on the first call.
- Using `sandbox_id` parameter to reconnect skips setup since the sandbox already exists.

---

## 3. Agents

All agents use a single SwarmKit API key from [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai/).

| Type     | Recommended Models                                                          | Notes                                                                                  |
|----------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `codex`  | `gpt-5.2`, `gpt-5.1-codex`, `gpt-5.1-codex-mini`                            | • Codex Agent<br>• persistent memory<br>• `reasoning_effort`: `low`, `medium`, `high`, `xhigh` |
| `claude` | `claude-opus-4-5-20251101` (`opus`), `claude-sonnet-4-5-20250929` (`sonnet`) | • Claude agent<br>• persistent memory<br>• `betas` (Sonnet 4.5 only): `["context-1m-2025-08-07"]` |
| `gemini` | `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`                 | • Gemini agent<br>• persistent memory                                                  |
| `qwen`   | `qwen3-coder-plus`, `qwen3-vl-plus`, `qwen3-max-preview`                     | • Qwen agent<br>• persistent memory                                                    |

### 3.1 Claude betas (Sonnet 4.5 only)

The `betas` field is only used by the Claude agent, and `context-1m-2025-08-07` only applies to **Claude Sonnet 4.5** (not Opus/Haiku).

```python
swarmkit = SwarmKit(
    config=AgentConfig(
        type='claude',
        api_key=os.getenv('SWARMKIT_API_KEY'),
        model='sonnet',
        betas=['context-1m-2025-08-07'],
    ),
    sandbox=E2BProvider(api_key=os.getenv('E2B_API_KEY')),
)
```

## 4. Runtime Methods

All runtime calls are `async` and return an `ExecuteResult`:

```python
@dataclass
class ExecuteResult:
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
```

### 4.1 run

Runs the agent with a given prompt.

```python
result = await swarmkit.run(
    prompt='Analyze the data and create a report',
    timeout_ms=15 * 60 * 1000,                # (optional) Default 1 hour
    background=False,                          # (optional) Run in background
)

print(result.exit_code)
print(result.stdout)
```

- If `timeout_ms` is omitted the agent uses the default of 3_600_000 ms (1 hour).
- If `background` is `True`, the call returns immediately while the agent continues running.

- Calling `run()` multiple times maintains the agent context / history.

### 4.2 execute_command

Runs a direct shell command in the sandbox working directory.

```python
# Run shell command directly in sandbox
result = await swarmkit.execute_command(
    command='pytest',
    timeout_ms=10 * 60 * 1000,                # (optional) Default 1 hour
    background=False,                          # (optional) Run in background
)
```
- The command automatically executes in the directory set by `working_directory` (default: `/home/user/workspace`).

### 4.3 Streaming events

Both `run()` and `execute_command()` stream output in real-time:

```python
# Raw output
swarmkit.on('stdout', lambda data: print(data, end=''))
swarmkit.on('stderr', lambda data: print(f'[ERR] {data}', end=''))

# Parsed output (recommended)
swarmkit.on('content', lambda event: print(event['update']))
```

**Events**:

| Event | Description |
|-------|-------------|
| `content` | Parsed ACP-style events (recommended) |
| `stdout` | Raw JSONL output |
| `stderr` | Stderr chunks |

**Content event structure** (`event['update']`):

| `sessionUpdate` | Description | Key Fields |
|-----------------|-------------|------------|
| `agent_message_chunk` | Text/image from agent | `content.type`, `content.text` |
| `agent_thought_chunk` | Reasoning/thinking (Codex/Claude) | `content.type`, `content.text` |
| `user_message_chunk` | User message echo (Gemini) | `content.type`, `content.text` |
| `tool_call` | Tool started | `toolCallId`, `title`, `kind`, `status`, `rawInput` |
| `tool_call_update` | Tool finished | `toolCallId`, `status` |
| `plan` | TodoWrite updates | `entries[]` with `content`, `status`, `priority` |

All listeners are optional.

#### Building a Real-Time UI with Callbacks

When building interactive CLI applications with streaming, use a **stateful renderer class** with callbacks. The recommended pattern uses Rich's `Live` for tool status updates while printing messages directly:

```python
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

console = Console()

class StreamRenderer:
    def __init__(self):
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}           # tool_id -> {title, status, kind, raw_input}
        self.tool_order = []      # preserve tool ordering
        self.plan_entries = []    # [{content, status, priority}, ...]
        self.status_live = None

    def reset(self):
        self._stop_status_live()
        self.current_message = ""
        self.thought_buffer = ""
        self.tools = {}
        self.tool_order = []
        self.plan_entries = []

    def handle_event(self, event: dict):
        """Main callback - register with swarmkit.on('content', ...)"""
        update = event.get("update", {})
        event_type = update.get("sessionUpdate")

        if event_type == "agent_message_chunk":
            content = update.get("content", {})
            if content.get("type") == "text":
                self.current_message += content.get("text", "")

        elif event_type == "agent_thought_chunk":
            # Reasoning/thinking from Codex or Claude
            content = update.get("content", {})
            if content.get("type") == "text":
                self.thought_buffer += content.get("text", "")

        elif event_type == "tool_call":
            self._flush_message()  # Print message before tool
            tool_id = update.get("toolCallId", "")
            if tool_id not in self.tools:
                self.tool_order.append(tool_id)
            self.tools[tool_id] = {
                'title': update.get("title", "Tool"),
                'kind': update.get("kind", "other"),  # read, edit, execute, fetch, search
                'status': update.get("status", "pending"),
                'raw_input': update.get("rawInput", {}),
            }
            self._refresh_status()

        elif event_type == "tool_call_update":
            tool_id = update.get("toolCallId", "")
            # Handle out-of-order: update may arrive before tool_call
            if tool_id not in self.tools:
                self.tool_order.append(tool_id)
                self.tools[tool_id] = {
                    'title': update.get("title", "Tool"),
                    'kind': "other",
                    'status': "pending",
                    'raw_input': {},
                }
            self.tools[tool_id]['status'] = update.get("status", "completed")
            self._refresh_status()

        elif event_type == "plan":
            # TodoWrite updates - list of {content, status, priority}
            self._flush_message()
            self.plan_entries = update.get("entries", [])
            self._render_plan()

    def _flush_message(self):
        if self.current_message.strip():
            console.print(Markdown(self.current_message))
            console.print()
            self.current_message = ""

    def _render_plan(self):
        """Render plan/todo entries"""
        if not self.plan_entries:
            return
        for entry in self.plan_entries:
            status = entry.get("status", "pending")
            content = entry.get("content", "")
            icon = {"completed": "✓", "in_progress": "→", "pending": "○"}.get(status, "○")
            style = {"completed": "green", "in_progress": "cyan", "pending": "dim"}.get(status, "dim")
            console.print(f"[{style}]{icon} {content}[/{style}]")
        console.print()

    def _render_status(self):
        """Render all tools as a Group - updates in place"""
        lines = []
        for tool_id in self.tool_order:
            tool = self.tools[tool_id]
            status = tool.get('status', 'pending')
            dot_style = "green" if status == 'completed' else "red" if status == 'failed' else "cyan"
            line = Text()
            line.append("● ", style=dot_style)
            line.append(f"{tool['title']}", style="white")
            lines.append(line)
        lines.append(Spinner("dots", style="cyan"))
        return Group(*lines) if lines else Text("")

    def _refresh_status(self):
        if self.status_live:
            self.status_live.update(self._render_status(), refresh=True)

    def _stop_status_live(self):
        if self.status_live:
            self.status_live.stop()
            self.status_live = None

    def start_live(self):
        self.status_live = Live(self._render_status(), console=console, refresh_per_second=12)
        self.status_live.start()

    def stop_live(self):
        self._stop_status_live()
        self._flush_message()
        # Optionally display collected thoughts
        if self.thought_buffer.strip():
            console.print("[dim]Reasoning:[/dim]")
            console.print(f"[dim italic]{self.thought_buffer}[/dim italic]")

# Usage:
renderer = StreamRenderer()
swarmkit.on("content", renderer.handle_event)

renderer.reset()
renderer.start_live()
await swarmkit.run(prompt="Your task here")
renderer.stop_live()
```

**Key patterns:**

1. **Handle all 5 event types** - `agent_message_chunk`, `agent_thought_chunk`, `tool_call`, `tool_call_update`, `plan`
2. **Flush messages before tools/plan** - Preserves correct interleaving order
3. **Track tools by ID** - `tool_call` (start) and `tool_call_update` (end) share `toolCallId`
4. **Handle out-of-order updates** - `tool_call_update` may arrive before `tool_call`
5. **Use `kind` for tool categorization** - `read`, `edit`, `execute`, `fetch`, `search`, `other`

> **Full production example:** See [`cookbooks/factotum-agent-py/ui.py`](../cookbooks/factotum-agent-py/ui.py) for styled formatting, tool content display, and advanced Live block management.

### 4.4 upload_context / upload_files

Upload files to the sandbox at runtime (immediate upload).

```python
await swarmkit.upload_context({
    'spec.json': json.dumps(spec),
    'logo.png': logo_bytes,
})

await swarmkit.upload_files({
    'scripts/setup.sh': '#!/bin/bash\necho hi\n',
    'data/input.csv': csv_data,
})
```

| Method | Destination | Default Path |
|--------|-------------|--------------|
| `upload_context()` | `{workingDir}/context/{path}` | `/home/user/workspace/context/` |
| `upload_files()` | `{workingDir}/{path}` | `/home/user/workspace/` |

**Format:** `{"path": content}` — key is relative path, value is `str` or `bytes`.

> **Note:** The constructor parameters `context` and `files` use the same format, but upload on first `run()` instead of immediately.

### 4.5 get_output_files

Fetch new files from `/output` after a run/command. Files created before the last operation are filtered out.

```python
files = await swarmkit.get_output_files()
for file in files:
    if isinstance(file.content, str):
        print('text file:', file.path)
    else:
        # bytes
        with open(f'./downloads/{file.name}', 'wb') as f:
            f.write(file.content)
```

Each entry includes `name`, `path`, `content`, `size`, `modified_time`.

### 4.6 Session controls

```python
session_id = await swarmkit.get_session()  # Returns sandbox ID (str) or None

await swarmkit.pause()   # Suspends sandbox (stops billing, preserves state)
await swarmkit.resume()  # Reactivates same sandbox

await swarmkit.kill()    # Destroys sandbox; next run() creates a new sandbox

await swarmkit.set_session('existing-sandbox-id')  # Sets sandbox ID; reconnection happens on next run()
```

`sandbox_id` constructor parameter is equivalent to `set_session()` - use it during initialization to reconnect to an existing sandbox.

### 4.7 get_host

Expose a forwarded port:

```python
url = await swarmkit.get_host(8000)
print(f'Workspace service available at {url}')
```
---

## 5. Workspace setup and Modes

### 5.1 Knowledge Mode (default)

Ideal for knowledge work applications.
```python
SwarmKit(..., workspace_mode='knowledge')  # implicit default
```

Calling `run` or `execute_command` for the first time provisions the workspace:

```
/home/user/workspace/
├── context/   # Input files (read-only) provided by the user
├── scripts/   # Your code goes here
├── temp/      # Scratch space
└── output/    # Final deliverables
```
Files passed to `context` are uploaded to `context/`. Files passed to `files` are uploaded relative to the working directory.

SwarmKit also writes a default system prompt:

```
You are running in a sandbox environment.
Present working directory: /home/user/workspace/

IMPORTANT - Directory structure:
/home/user/workspace/
├── context/   # Input files (read-only) provided by the user
├── scripts/   # Your code goes here
├── temp/      # Scratch space
└── output/    # Final deliverables

IMPORTANT - Always save deliverables to output/. The user only receives this folder.
```

Any string passed to `system_prompt` is appended after this default.


### 5.2 SWE Mode

Ideal for coding applications (when working with repositories).
```python
SwarmKit(..., workspace_mode='swe')
```

SWE mode skips directory scaffolding and does **not** prepend the workspace instructions above—useful when targeting an existing repository layout. All other features (`system_prompt`, `context`, `files`, etc.) continue to work normally.


---

## 6. Cleaning up and session management

**Multi-turn conversations** (most common):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...)
)

await swarmkit.run(prompt='Analyze data.csv')
files = await swarmkit.get_output_files()

# Still same session, automatically maintains context / history
await swarmkit.run(prompt='Now create visualization')
files2 = await swarmkit.get_output_files()

# Still same session, automatically maintains context / history
await swarmkit.run(prompt='Export to PDF')
files3 = await swarmkit.get_output_files()

await swarmkit.kill()  # When done
```

**One-shot tasks** (automatic cleanup):

```python
async with swarmkit:
    result = await swarmkit.run(prompt='...')
    files = await swarmkit.get_output_files()
# Calls kill() automatically via __aexit__()
```

**Pause and resume** (same instance):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...)
)

await swarmkit.run(prompt='Start analysis')
await swarmkit.pause()  # Suspend billing, keep state
# Do other work...
await swarmkit.resume()  # Reactivate same sandbox
await swarmkit.run(prompt='Continue analysis')  # Session intact

await swarmkit.kill()  # Kill the Sandbox when done
```

**Save and reconnect** (different script/session):

```python
# Script 1: Save session for later
swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...)
)

await swarmkit.run(prompt='Start analysis')

session_id = await swarmkit.get_session()
# Save to file, database, environment variable, etc.
with open('session.txt', 'w') as f:
    f.write(session_id)

# Script 2: Reconnect to saved session
with open('session.txt') as f:
    saved_id = f.read()

swarmkit2 = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...),
    sandbox_id=saved_id  # Reconnect
)

await swarmkit2.run(prompt='Continue analysis')  # Session continues from Script 1
```

**Switch between sandboxes** (same instance):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...)
)

# Work with first sandbox
await swarmkit.run(prompt='Analyze dataset A')
session_a = await swarmkit.get_session()

# Switch to different sandbox
await swarmkit.set_session('existing-sandbox-b-id')
await swarmkit.run(prompt='Analyze dataset B')  # Now working with sandbox B

# Switch back to first sandbox
await swarmkit.set_session(session_a)
await swarmkit.run(prompt='Compare results')  # Back to sandbox A
```

---

## 7. Observability

Full execution traces—including tool calls, file operations (read/write/edit), text responses, and reasoning chunks—are logged to your SwarmKit dashboard at **https://dashboard.swarmlink.ai/traces** for debugging and replay.

Additionally, every run and command is logged locally to structured JSON lines under `~/.swarmkit/observability/sessions`. File name format:

```
{tag}_{provider}_{sandboxId}_{agent}_{timestamp}.jsonl
```

- `{tag}` – `my-prefix-` + 16 random hex characters (e.g. `my-prefix-a1b2c3d4e5f6g7h8`)
- `{provider}` – the sandbox provider (e.g. `e2b`)
- `{sandboxId}` – the active sandbox ID
- `{agent}` – the agent type (`codex`, `claude`, `gemini`, `qwen`)
- `{timestamp}` – ISO timestamp with `:` and `.` replaced by `-`

Each file contains three entry types:

```json
{"_meta":{"tag":"my-prefix-a1b2c3d4","provider":"e2b","sandbox_id":"sbx_123","agent":"qwen","timestamp":"2025-10-26T20:15:17.984Z"}}
{"_prompt":{"text":"hello how are you?"}}
{"jsonrpc":"2.0","method":"session/update", ...}
```

- `_meta` – exactly one line per file (sandbox, agent, timestamp)
- `_prompt` – one line per `run()` call with the prompt text
- Raw JSON – every streamed payload (ACP notifications, stdout, etc.)

Attach your own prefix to make logs easy to search:

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...),
    session_tag_prefix='my-project'
)

await swarmkit.run(prompt='Kick off analysis')

print(await swarmkit.get_session_tag())        # "my-project-ab12cd34"
print(await swarmkit.get_session_timestamp())  # Timestamp for first log file

await swarmkit.kill()                          # Flushes log file for sandbox A

await swarmkit.run(prompt='Start fresh')       # New sandbox → new log file

print(await swarmkit.get_session_tag())        # "my-project-f56789cd"
print(await swarmkit.get_session_timestamp())  # Timestamp for second log file
```

- `kill()` or `set_session()` flushes the current log; the next `run()` starts a
  fresh file with the new sandbox id.
- Long-running sessions (pause/resume or ACP auto-resume) keep appending to the
  current file, so you always have the full timeline.
- Logging is buffered inside the SDK, so it never blocks streaming output.

Use the tag together with the sandbox id to correlate logs with files saved in
`/output/`.

---
