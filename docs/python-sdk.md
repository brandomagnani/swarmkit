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
sandbox = E2BProvider(
    api_key=os.getenv('E2B_API_KEY'),
    timeout_ms=3_600_000,  # 1 hour (default), max sandbox lifetime
)

# Build SwarmKit instance
swarmkit = SwarmKit(
    config=AgentConfig(
        type='codex',
        api_key=os.getenv('SWARMKIT_API_KEY'),
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
output = await swarmkit.get_output_files()
for name, content in output.files.items():
    print(name)

# Clean up
await swarmkit.kill()
```

- **Tracing:** Every run is automatically logged to [dashboard.swarmlink.ai/traces](https://dashboard.swarmlink.ai/traces)—no extra setup needed. Optionally use `session_tag_prefix` to label your agent session for easy filtering.

### 1.1 Environment Variables

With `SWARMKIT_API_KEY` and `E2B_API_KEY` set, you can skip explicit configuration:

```python
from dotenv import load_dotenv
load_dotenv()  # If using .env file (pip install python-dotenv)

from swarmkit import SwarmKit

# Minimal — auto-resolves from environment
swarmkit = SwarmKit()  # type defaults to "claude"

await swarmkit.run(prompt="Hello")
```

| Variable | Description |
|----------|-------------|
| `SWARMKIT_API_KEY` | API key from [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai) |
| `E2B_API_KEY` | Sandbox key from [e2b.dev](https://e2b.dev) |

Agent type defaults to `claude`. Override with `config=AgentConfig(type="codex")`.

---

## 2. Full Configuration

```python
swarmkit = SwarmKit(

    # Agent configuration (optional if SWARMKIT_API_KEY set, defaults to claude)
    config=AgentConfig(
        type='codex',                        # 'claude' | 'codex' | 'gemini' | 'qwen' - defaults to 'claude'
        model='gpt-5.2-codex',               # (optional) Uses default if omitted
        reasoning_effort='medium',           # (optional) 'low' | 'medium' | 'high' | 'xhigh' - Codex only
        # betas=['context-1m-2025-08-07'],   # (optional) Claude Sonnet only
        api_key=os.getenv('SWARMKIT_API_KEY'), # (optional) Auto-resolves from env
    ),

    # Sandbox provider (optional if E2B_API_KEY set)
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

    # (optional) Schema for structured output (agent writes result.json, validated on get_output_files())
    # Accepts Pydantic models or JSON Schema dicts
    schema=MyPydanticModel,

    # Or with JSON Schema:
    # schema={
    #     'type': 'object',
    #     'properties': {
    #         'summary': {'type': 'string'},
    #         'score': {'type': 'number'},
    #     },
    #     'required': ['summary', 'score'],
    # },
)
```

**Note:**
- Configuration parameters can be combined in any order.
- The sandbox is created on the first `run()` or `execute_command()` call (see below).
- Context files, workspace files, MCP servers, and system prompt are set up once on the first call.
- Using `sandbox_id` parameter to reconnect skips setup since the sandbox already exists.
- `schema` accepts both Pydantic model classes and JSON Schema dicts.

**McpServerConfig** — MCP server connection (STDIO or HTTP/SSE):
```python
{'command': str, 'args': list[str], 'env': dict[str, str], 'url': str}  # STDIO: command+args, HTTP: url
```

---

## 3. Agents

All agents use a single SwarmKit API key from [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai/).

| type       | model                                                                                                                                       | model default             | reasoning_effort                                           | betas                                           |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|------------------------------------------------------------|-------------------------------------------------|
| `'claude'` | `'opus'`<br>`'sonnet'`<br>`'haiku'`                                                                                                         | `'opus'`                  | —                                                          | `['context-1m-2025-08-07']` (Sonnet only)   |
| `'codex'`  | `'gpt-5.2'`<br>`'gpt-5.2-codex'`<br>`'gpt-5.1-codex-max'`<br>`'gpt-5.1-mini'`                                                               | `'gpt-5.2'`               | `'low'`<br>`'medium'`<br>`'high'`<br>`'xhigh'`             | —                                               |
| `'gemini'` | `'gemini-3-pro-preview'`<br>`'gemini-3-flash-preview'`<br>`'gemini-2.5-pro'`<br>`'gemini-2.5-flash'`<br>`'gemini-2.5-flash-lite'`           | `'gemini-3-flash-preview'` | —                                                          | —                                               |
| `'qwen'`   | `'qwen3-coder-plus'`<br>`'qwen3-vl-plus'`                                                                                                   | `'qwen3-coder-plus'`      | —                                                          | —                                               |

<br>

```python
# claude
AgentConfig(type='claude')
AgentConfig(type='claude', model='opus')
AgentConfig(type='claude', model='sonnet', betas=['context-1m-2025-08-07'])

# codex
AgentConfig(type='codex')
AgentConfig(type='codex', model='gpt-5.2-codex')
AgentConfig(type='codex', reasoning_effort='high')

# gemini
AgentConfig(type='gemini')
AgentConfig(type='gemini', model='gemini-3-pro-preview')

# qwen
AgentConfig(type='qwen')
AgentConfig(type='qwen', model='qwen3-coder-plus')
```

## 4. Runtime Methods

All runtime calls are `async` and return an `AgentResponse`:

```python
@dataclass
class AgentResponse:
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
| `tool_call` | Tool started | `toolCallId`, `title`, `kind`, `status`, `rawInput?`, `content?`, `locations?` |
| `tool_call_update` | Tool finished | `toolCallId`, `status?`, `title?`, `content?`, `locations?` |
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
                'kind': update.get("kind", "other"),  # read, edit, search, execute, think, fetch, switch_mode, other
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
5. **Use `kind` for tool categorization** - `read`, `edit`, `search`, `execute`, `think`, `fetch`, `switch_mode`, `other`

> **Full production example:** See [`cookbooks/agent-python/ui.py`](../cookbooks/agent-python/ui.py) for styled formatting, tool content display, and advanced Live block management.

### 4.4 Upload: Local → Sandbox

**Format:** `{"destination": content}` — directories created automatically

| Method | Destination |
|--------|-------------|
| `upload_context()` | `context/{path}` |
| `upload_files()` | `{workingDir}/{path}` |

```python
# Single file
await swarmkit.upload_context({'spec.json': json.dumps(data)})

# Multiple files
await swarmkit.upload_files({
    'scripts/setup.sh': '#!/bin/bash\necho hello',
    'data/input.csv': csv_bytes,
})

# From local directory (helper)
from swarmkit import read_local_dir
await swarmkit.upload_context(read_local_dir('./input', recursive=True))
```

> **Setup alternative:** Constructor parameters `context` and `files` use the same format but upload on first `run()` instead of immediately.

### 4.5 Download: Sandbox → Local

**Flow:** `get_output_files()` → `save_local_dir()`

```python
# Return type
@dataclass
class OutputResult:
    files: dict          # All files from output/ folder
    data: Any | None     # Parsed result.json (if schema was set via schema=)
    error: str | None    # Validation error message (if schema validation failed)
    raw_data: str | None # Raw result.json content when parse/validation failed (for debugging)
```

```python
from pydantic import BaseModel
from swarmkit import SwarmKit, save_local_dir

class ResultSchema(BaseModel):
    summary: str
    score: float

swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...),
    schema=ResultSchema,  # Agent will be prompted to write result.json
)

await swarmkit.run(prompt='Analyze and score the document')

output = await swarmkit.get_output_files(recursive=True)  # recursive=True for nested dirs

# Access all fields
save_local_dir('./output', output.files)  # Save files locally
print(output.data)                         # ResultSchema(summary='...', score=85.0)
print(output.error)                        # None (or validation error message)
```

- **`files`** — dict of all files from `output/` folder
- **`data`** — Parsed `result.json` validated against schema (None if no schema or validation failed). For Pydantic schemas, returns a model instance.
- **`error`** — Validation error message if schema validation failed (None otherwise)
- **`raw_data`** — Raw result.json content when parse/validation failed (for debugging)

Files created before the last `run()` or `execute_command()` are filtered out.

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
## FILESYSTEM INSTRUCTIONS

You are running in a sandbox environment.

Present working directory: /home/user/workspace/

IMPORTANT - Directory structure:
/home/user/workspace/
├── context/   # Input files (read-only) provided by the user
├── scripts/   # Your code goes here
├── temp/      # Scratch space
└── output/    # Final deliverables

## OUTPUT RESULTS (DELIVERABLES) MUST BE SAVED to `output/` as files.
```

Any string passed to `system_prompt` is appended after this default.


### 5.2 SWE Mode

Ideal for coding applications (when working with repositories).
```python
SwarmKit(..., workspace_mode='swe')
```

SWE mode is the same as knowledge mode but includes an additional `repo/` folder for code repositories:

```
/home/user/workspace/
├── repo/      # Code repository
├── context/   # Input files (read-only) provided by the user
├── scripts/   # Your code goes here
├── temp/      # Scratch space
└── output/    # Final deliverables
```

The workspace prompt is automatically written with the `repo/` folder included. All other features (`system_prompt`, `context`, `files`, etc.) work the same as knowledge mode.


---

## 6. Cleaning up and session management

**Multi-turn conversations** (most common):

```python
swarmkit = SwarmKit(
    config=AgentConfig(...),
    sandbox=E2BProvider(...)
)

await swarmkit.run(prompt='Analyze data.csv')
output = await swarmkit.get_output_files()

# Still same session, automatically maintains context / history
await swarmkit.run(prompt='Now create visualization')
output2 = await swarmkit.get_output_files()

# Still same session, automatically maintains context / history
await swarmkit.run(prompt='Export to PDF')
output3 = await swarmkit.get_output_files()

await swarmkit.kill()  # When done
```

**One-shot tasks** (automatic cleanup):

```python
async with swarmkit:
    result = await swarmkit.run(prompt='...')
    output = await swarmkit.get_output_files()
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

# Swarm Abstractions

Functional programming for AI agents: `map`, `filter`, `reduce`, `best_of`.

```python
from swarmkit import Swarm, SwarmConfig, AgentConfig, E2BProvider
from pydantic import BaseModel  # Or use plain JSON Schema dicts instead

sandbox = E2BProvider(api_key=os.getenv('E2B_API_KEY'))

agent = AgentConfig(type='claude')

swarm = Swarm(SwarmConfig(
    agent=agent,                     # Default agent for all operations
    sandbox=sandbox,                 # Sandbox provider
    concurrency=4,                   # Max parallel sandboxes (default: 4)
    timeout_ms=3_600_000,            # Default timeout per worker (default: 1 hour)
    tag='my-pipeline',               # Tag prefix for observability
    workspace_mode='knowledge',      # 'knowledge' (default) or 'swe'
    mcp_servers={...},               # Default MCP servers for all workers
    retry=RetryConfig(               # Default retry config for all operations
        max_attempts=3,
        backoff_ms=1000,
        backoff_multiplier=2,
    ),
))
```

> **Defaults**: `agent`, `timeout_ms`, `mcp_servers`, and `retry` set here are inherited by all operations (`map`, `filter`, `reduce`, `best_of`). Pass these options to individual operations to override.

**Minimal setup** — with `SWARMKIT_API_KEY` and `E2B_API_KEY` set (see [1.1 Environment Variables](#11-environment-variables)):

```python
from dotenv import load_dotenv
load_dotenv()  # If using .env file

from swarmkit import Swarm

swarm = Swarm()  # Auto-resolves agent (claude) and sandbox from env
```

**RetryConfig** — auto-retry on error with exponential backoff:
```python
RetryConfig(
    max_attempts=3,
    backoff_ms=1000,
    backoff_multiplier=2,
    retry_on=lambda r: r.status == 'error',        # Custom condition
    on_item_retry=lambda idx, attempt, error: ..., # Callback
)
```

**VerifyConfig** — LLM-as-judge verifies output, retries with feedback if failed:
```python
VerifyConfig(
    criteria='...',                                         # Required
    max_attempts=3,
    verifier_agent=AgentConfig(...),                        # Optional override
    on_worker_complete=lambda idx, attempt, status: ...,    # Callback
    on_verifier_complete=lambda idx, attempt, passed, feedback: ...,
)
```

## 1. Input Types

Swarm runs in **knowledge mode** by default—files are uploaded to `context/` in the sandbox.

**FileMap structure:**

```python
# FileMap: dict[path, content]
#   - path: str              → file path in context/ folder
#   - content: str | bytes   → file content

FileMap = dict[str, str | bytes]
```

---

**Case 1: One file per worker**

```python
# 3 workers, each gets 1 file
items: list[FileMap] = [
    {'report.txt': 'Q1 revenue...'},      # → Worker 0: context/report.txt
    {'report.txt': 'Q2 revenue...'},      # → Worker 1: context/report.txt
    {'report.txt': 'Q3 revenue...'},      # → Worker 2: context/report.txt
]

results = await swarm.map(
    items=items,
    prompt='Summarize this report',
)
```

---

**Case 2: Multiple files per worker**

```python
# 3 workers, each gets 2 files
items: list[FileMap] = [
    {                                       # → Worker 0:
        'doc1.pdf': open('./doc1.pdf', 'rb').read(),  #   context/doc1.pdf
        'doc2.pdf': open('./doc2.pdf', 'rb').read(),  #   context/doc2.pdf
    },
    {                                       # → Worker 1:
        'doc3.pdf': open('./doc3.pdf', 'rb').read(),  #   context/doc3.pdf
        'doc4.pdf': open('./doc4.pdf', 'rb').read(),  #   context/doc4.pdf
    },
    {                                       # → Worker 2:
        'doc5.pdf': open('./doc5.pdf', 'rb').read(),  #   context/doc5.pdf
        'doc6.pdf': open('./doc6.pdf', 'rb').read(),  #   context/doc6.pdf
    },
]

results = await swarm.map(
    items=items,
    prompt='Compare these two documents',
)
```

---

**Case 3: Entire folder per worker**

```python
from swarmkit import read_local_dir

# read_local_dir(path, recursive) → returns FileMap with all files
items: list[FileMap] = [
    read_local_dir('./project-a', recursive=True),   # → Worker 0: all files from project-a
    read_local_dir('./project-b', recursive=True),   # → Worker 1: all files from project-b
    read_local_dir('./project-c', recursive=True),   # → Worker 2: all files from project-c
]

results = await swarm.map(
    items=items,
    prompt='Review this codebase',
)
```

## 2. Abstractions

Two types of operations:

| Operation | Type | Description | Passes On |
|-----------|------|-------------|-----------|
| `best_of` | transform + select | `input` → `output` (best of N candidates) | winner output |
| `map` | transform | `input` → `output` (agent produces new data) | agent output |
| `filter` | gate | `input` → `input` (agent evaluates, condition decides) | original input + status (`success` \| `filtered`) |
| `reduce` | transform | `inputs` → `output` (agent synthesizes) | agent output |

**Transforms** produce new output files. **Filter** passes through original input files unchanged.

### 2.1 best_of

Run N agents on the same `item` in parallel, then a judge picks the best. `Agent[i]` outputs `candidates[i]`, judge selects `winner`.

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Sandbox 0    │ │    Sandbox 1    │ │    Sandbox 2    │
│    Agent 0      │ │    Agent 1      │ │    Agent 2      │
│                 │ │                 │ │                 │
│  context/       │ │  context/       │ │  context/       │
│    item         │ │    item         │ │    item         │
│  output/        │ │  output/        │ │  output/        │
│    candidates[0]│ │    candidates[1]│ │    candidates[2]│
└───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌───────────────┐
                    │     Judge     │
                    └───────┬───────┘
                            │
                            ▼
                         winner
```

```python
# Signature
await swarm.best_of(
    item=FileMap | SwarmResult,
    prompt=str,
    config=BestOfConfig(                    # n?, judge_criteria, task_agents?, judge_agent?, callbacks
        judge_criteria='...',
        n=3,
        on_candidate_complete=lambda idx, cand_idx, status: ...,
        on_judge_complete=lambda idx, winner_idx, reasoning: ...,
    ),
    schema=PydanticModel | dict,            # Optional
    system_prompt=str,                      # Optional
    retry=RetryConfig(...),                 # Per-candidate retry (judge uses default)
    timeout_ms=int,                         # Optional
) -> BestOfResult
```

```python
input_item = {'task.txt': 'Complex problem...'}

result = await swarm.best_of(
    item=input_item,
    prompt='Solve this problem',
    config=BestOfConfig(
        n=3,
        judge_criteria='Most accurate and well-explained solution',
        on_candidate_complete=lambda idx, cand_idx, status: print(f'Candidate {cand_idx}: {status}'),
        on_judge_complete=lambda idx, winner_idx, reasoning: print(f'Winner: {winner_idx}'),
    ),
)

print(result.winner)          # Best SwarmResult
print(result.winner_index)    # 0, 1, or 2
print(result.judge_reasoning) # Why this was chosen
print(result.candidates)      # All candidate results
```

Use different agents per candidate:

```python
claude_agent = AgentConfig(type='claude', model='opus')
codex_agent = AgentConfig(type='codex', model='gpt-5.2-codex')
gemini_agent = AgentConfig(type='gemini', model='gemini-3-flash')

result = await swarm.best_of(
    item=input_item,
    prompt='Solve this',
    config=BestOfConfig(
        task_agents=[claude_agent, codex_agent, gemini_agent],
        judge_criteria='Best solution quality',
        judge_agent=claude_agent,
        mcp_servers={...},        # (optional) MCP servers for candidates
        judge_mcp_servers={...},  # (optional) MCP servers for judge
    ),
)
```

### 2.2 map

Process items in parallel. `Agent[i]` sees `items[i]` and outputs `results[i]` (which includes `result.json` if `schema` provided).

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Sandbox 0    │ │    Sandbox 1    │ │    Sandbox 2    │
│    Agent 0      │ │    Agent 1      │ │    Agent 2      │
│                 │ │                 │ │                 │
│  context/       │ │  context/       │ │  context/       │
│    items[0]     │ │    items[1]     │ │    items[2]     │
│  output/        │ │  output/        │ │  output/        │
│    results[0]   │ │    results[1]   │ │    results[2]   │
└───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              [results[0], results[1], results[2]]
```

```python
# Signature (schema accepts Pydantic model or JSON Schema dict)
await swarm.map(
    items=list[FileMap] | list[SwarmResult],
    prompt=str | Callable[[FileMap, int], str],
    schema=PydanticModel | dict,            # Optional
    system_prompt=str,                      # Optional
    agent=AgentConfig,                      # Optional override
    best_of=BestOfConfig,                   # N candidates + judge (mutually exclusive with verify)
    verify=VerifyConfig,                    # LLM-as-judge quality check with retry loop
    retry=RetryConfig,                      # Auto-retry on error with backoff
    mcp_servers=dict[str, McpServerConfig], # Optional
    timeout_ms=int,                         # Optional
) -> SwarmResultList
```

```python
# Basic
results = await swarm.map(
    items=documents,
    prompt='Summarize this document',
)
```

When `schema` is provided, a structured output prompt is automatically embedded—instructing the agent to write `output/result.json` matching the schema.

```python
# With Pydantic schema
class SummarySchema(BaseModel):
    title: str
    key_points: list[str]

results = await swarm.map(
    items=documents,
    prompt='Extract summary',
    schema=SummarySchema,
)

# Or with JSON Schema
summary_json_schema = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'key_points': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['title', 'key_points'],
}

results = await swarm.map(
    items=documents,
    prompt='Extract summary',
    schema=summary_json_schema,
)

# With dynamic prompt
results = await swarm.map(
    items=documents,
    prompt=lambda files, index: f'Analyze document {index + 1}: focus on revenue',
)

# Access results
for r in results:
    if r.status == 'success':
        print(r.data)   # Parsed schema instance or FileMap
        print(r.files)  # Output files from agent
```

### 2.3 map with best_of

Combine map parallelism with best_of quality:

```python
class AnalysisSchema(BaseModel):
    findings: list[str]
    confidence: float

# Each item gets N candidates, judge picks best per item
results = await swarm.map(
    items=documents,
    prompt='Analyze thoroughly',
    schema=AnalysisSchema,
    best_of=BestOfConfig(
        n=3,
        judge_criteria='Most comprehensive analysis',
        # task_agents=[...],       # Different agent per candidate
        # judge_agent=...,         # Override judge agent
        # mcp_servers={...},       # MCP servers for candidates
        # judge_mcp_servers={...}, # MCP servers for judge
    ),
)

# Results contain only winners (one per input item)
```

### 2.4 filter

Two-step evaluation (`schema` and `condition` are required):
1. `Agent[i]` sees `items[i]`, assesses it, outputs `result.json` matching `schema`
2. SDK parses `result.json` → `data`, your `condition(data)` applies the threshold
3. Passing items forward their original input files, not agent output

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Sandbox 0    │ │    Sandbox 1    │ │    Sandbox 2    │
│    Agent 0      │ │    Agent 1      │ │    Agent 2      │
│                 │ │                 │ │                 │
│  context/       │ │  context/       │ │  context/       │
│    items[0]     │ │    items[1]     │ │    items[2]     │
│  output/        │ │  output/        │ │  output/        │
│    result.json  │ │    result.json  │ │    result.json  │
└───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                   condition(data)
                      ✓    ✗    ✓
                      │         │
                      ▼         ▼
                [items[0], items[2]]
```

```python
# Signature (schema accepts Pydantic model or JSON Schema dict)
await swarm.filter(
    items=list[FileMap] | list[SwarmResult],
    prompt=str,                             # Describe what to assess (agent outputs result.json)
    schema=PydanticModel | dict,            # Required - defines evaluation output structure
    condition=Callable[[Any], bool],        # Local function applies threshold
    system_prompt=str,                      # Optional
    agent=AgentConfig,                      # Optional override
    verify=VerifyConfig,                    # LLM-as-judge quality check with retry loop
    retry=RetryConfig,                      # Auto-retry on error with backoff
    mcp_servers=dict[str, McpServerConfig], # Optional
    timeout_ms=int,                         # Optional
) -> SwarmResultList
```

```python
class EvalSchema(BaseModel):
    severity: Literal['critical', 'warning', 'info']
    score: float

results = await swarm.filter(
    items=documents,
    prompt='Assess the severity of issues in this document',  # Agent evaluates
    schema=EvalSchema,
    condition=lambda data: data.severity == 'critical',       # Code applies threshold
)

# Three possible statuses:
results.success    # Passed condition
results.filtered   # Evaluated but didn't pass
results.error      # Agent error

# Chain to next step
await swarm.reduce(
    items=results.success,
    prompt='Summarize critical issues',
)
```

### 2.5 reduce

Synthesize many items into one. A single agent sees all `items` as `item_0/`, `item_1/`, etc. and outputs a unified `result` (which includes `result.json` if `schema` provided).

```
        ┌─────────────────────────┐
        │         Sandbox         │
        │         Agent           │
        │                         │
        │  context/               │
        │    item_0/items[0]      │
        │    item_1/items[1]      │
        │    item_2/items[2]      │
        │  output/                │
        │    result               │
        └────────────┬────────────┘
                     │
                     ▼
                  result
```

```python
# Signature (schema accepts Pydantic model or JSON Schema dict)
await swarm.reduce(
    items=list[FileMap] | list[SwarmResult],
    prompt=str,
    schema=PydanticModel | dict,            # Optional
    system_prompt=str,                      # Optional
    agent=AgentConfig,                      # Optional override
    verify=VerifyConfig,                    # LLM-as-judge quality check with retry loop
    retry=RetryConfig,                      # Auto-retry on error with backoff
    mcp_servers=dict[str, McpServerConfig], # Optional
    timeout_ms=int,                         # Optional
) -> ReduceResult
```

```python
# Agent sees: item_0/, item_1/, item_2/, etc.
report = await swarm.reduce(
    items=results.success,
    prompt='Create a unified report from all analyses',
)

if report.status == 'success':
    print(report.files)  # Final output files
    print(report.data)   # Parsed schema if provided

# With schema
class ReportSchema(BaseModel):
    summary: str
    recommendations: list[str]

report = await swarm.reduce(
    items=items,
    prompt='Create report',
    schema=ReportSchema,
)
```

## 3. Result Types

```python
@dataclass
class SwarmResult:
    """Result from map, filter, best_of candidates."""
    status: Literal['success', 'filtered', 'error']
    data: Any | None        # Parsed schema, or None on error
    files: FileMap          # Output files (map/best_of) or input files (filter)
    meta: IndexedMeta       # run_id, operation, tag, sandbox_id, index
    error: str | None       # Error message if status == 'error'
    raw_data: str | None    # Raw result.json when parse/validation failed
    best_of: BestOfInfo | None  # Present when map used best_of option
    verify: VerifyInfo | None   # Present when verify option was used

# SwarmResultList - from map, filter (extends list)
results.success    # list[SwarmResult] with status 'success'
results.filtered   # list[SwarmResult] with status 'filtered'
results.error      # list[SwarmResult] with status 'error'

@dataclass
class ReduceResult:
    """Result from reduce."""
    status: Literal['success', 'error']
    data: Any | None
    files: FileMap
    meta: ReduceMeta        # run_id, operation, tag, sandbox_id, input_count, input_indices
    error: str | None
    raw_data: str | None
    verify: VerifyInfo | None

@dataclass
class VerifyInfo:
    """Verification outcome."""
    passed: bool            # Final verification status
    reasoning: str          # Verifier's reasoning
    verify_meta: VerifyMeta # run_id, operation, tag, sandbox_id, attempts
    attempts: int           # Total attempts made

@dataclass
class BestOfInfo:
    """Present when map used best_of option."""
    winner_index: int
    judge_reasoning: str
    judge_meta: JudgeMeta   # run_id, operation, tag, sandbox_id, candidate_count
    candidates: list[SwarmResult]

@dataclass
class BestOfResult:
    """Result from best_of."""
    winner: SwarmResult
    winner_index: int
    judge_reasoning: str
    judge_meta: JudgeMeta
    candidates: list[SwarmResult]
```

## 4. Chaining Operations

```python
class AnalysisSchema(BaseModel):
    summary: str

class SeveritySchema(BaseModel):
    severity: Literal['critical', 'warning', 'info']

# Full pipeline: map → filter → reduce
analyzed = await swarm.map(
    items=documents,
    prompt='Analyze',
    schema=AnalysisSchema,
)

critical = await swarm.filter(
    items=analyzed.success,
    prompt='Evaluate severity',
    schema=SeveritySchema,
    condition=lambda d: d.severity == 'critical',
)

report = await swarm.reduce(
    items=critical.success,
    prompt='Create summary report',
)

# Combine success and filtered
all_evaluated = [*critical.success, *critical.filtered]
await swarm.reduce(
    items=all_evaluated,
    prompt='Summarize all evaluated items',
)
```

## 5. AgentOverride

Override the default agent for any operation (api_key inherited from Swarm config):

```python
@dataclass
class AgentConfig:
    type: Literal['claude', 'codex', 'gemini', 'qwen']
    api_key: str | None = None
    model: str | None = None
    reasoning_effort: Literal['low', 'medium', 'high', 'xhigh'] | None = None  # Codex only
    betas: list[str] | None = None  # Claude only
```

```python
codex_agent = AgentConfig(
    type='codex',
    reasoning_effort='high',
)

results = await swarm.map(
    items=items,
    prompt='Analyze',
    agent=codex_agent,
)
```

## 6. Concurrency

Global semaphore limits parallel sandboxes across all operations.

```python
swarm = Swarm(SwarmConfig(
    agent=agent,
    sandbox=sandbox,
    concurrency=4,  # Max 4 sandboxes at once (default: 4)
))

# map(10) with best_of(5) = 60 agent calls, but only 4 run at any time
```

**Ordering guarantees:**
- `best_of`: Judge runs only after all candidates complete
- `map` → `filter` → `reduce`: Each phase completes before next starts
- Within a phase: Items run in parallel (up to concurrency limit)

---

## 7. Pipeline

Fluent wrapper over Swarm for chaining operations. **All Swarm features work in Pipeline steps** — schema, best_of, verify, retry, agent, mcp_servers, dynamic prompts.

```python
from dotenv import load_dotenv
load_dotenv()

from swarmkit import Swarm, Pipeline

swarm = Swarm()  # See Swarm Abstractions for full config

pipeline = (
    Pipeline(swarm)
    .map(MapConfig(
        name='analyze',
        prompt='Analyze...',
        schema=AnalysisSchema,
    ))
    .filter(FilterConfig(
        name='critical',
        prompt='Rate...',
        schema=SeveritySchema,
        condition=lambda d: d.severity == 'critical',
    ))
    .reduce(ReduceConfig(
        name='report',
        prompt='Summarize...',
    ))
)

# Reusable — run with different data
result1 = await pipeline.run(batch1)
result2 = await pipeline.run(batch2)
```

### Step Configurations

Each step accepts the same options as the corresponding Swarm method, plus `name` for observability:

```python
# Map step — same as swarm.map() + name
MapConfig(
    name=str,                               # Step name (appears in events)
    prompt=str | Callable[[FileMap, int], str],
    schema=PydanticModel | dict,            # Optional
    best_of=BestOfConfig,                   # N candidates + judge
    verify=VerifyConfig,                    # LLM-as-judge quality check
    retry=RetryConfig,                      # Auto-retry on error
    agent=AgentConfig,
    mcp_servers=dict[str, McpServerConfig],
    system_prompt=str,
    timeout_ms=int,
)

# Filter step — same as swarm.filter() + name + emit
FilterConfig(
    name=str,
    prompt=str,
    schema=PydanticModel | dict,            # Required
    condition=Callable[[Any], bool],        # Required
    emit='success' | 'filtered' | 'all',    # What passes to next step (default: 'success')
    verify=VerifyConfig,
    retry=RetryConfig,
    agent=AgentConfig,
    mcp_servers=dict[str, McpServerConfig],
    system_prompt=str,
    timeout_ms=int,
)

# Reduce step — same as swarm.reduce() + name (terminal: no steps after)
ReduceConfig(
    name=str,
    prompt=str,
    schema=PydanticModel | dict,            # Optional
    verify=VerifyConfig,
    retry=RetryConfig,
    agent=AgentConfig,
    mcp_servers=dict[str, McpServerConfig],
    system_prompt=str,
    timeout_ms=int,
)
```

### Full Example

```python
pipeline = (
    Pipeline(swarm)

    .map(MapConfig(
        name='analyze',
        prompt=lambda files, idx: f'Analyze document {idx + 1}',
        schema=AnalysisSchema,
        best_of=BestOfConfig(
            n=3,
            judge_criteria='Most thorough analysis',
        ),
        retry=RetryConfig(max_attempts=2),
        agent=AgentConfig(type='claude', model='opus'),
    ))

    .filter(FilterConfig(
        name='quality-gate',
        prompt='Rate the analysis quality',
        schema=QualitySchema,  # Has score: float, reasoning: str
        condition=lambda d: d.score >= 8,
        emit='success',                     # Only high-quality pass through
        verify=VerifyConfig(
            criteria='Rating must be justified with specific examples',
        ),
    ))

    .reduce(ReduceConfig(
        name='synthesize',
        prompt='Create executive summary from all analyses',
        schema=ReportSchema,
        verify=VerifyConfig(
            criteria='Summary must cover all key findings',
        ),
    ))

    .on('step_complete', lambda e: print(f'{e.name}: {e.success_count}/{e.success_count + e.error_count}'))
)

result = await pipeline.run(documents)
```

### Events

Pipeline unifies all Swarm callbacks at the pipeline level, adding `step_index` and `step_name`:

```python
(
    pipeline
    .on('step_start', lambda e: print(f'Step {e.index} started with {e.item_count} items'))
    .on('step_complete', lambda e: print(f'Step {e.index} done in {e.duration_ms}ms'))
    .on('step_error', lambda e: print(f'Step {e.index} failed: {e.error}'))
)

# Or object style
pipeline.on(PipelineEvents(
    on_step_complete=lambda e: print(f'{e.name}: {e.success_count} success'),
    on_item_retry=lambda e: print(f'Retry: step {e.step_index}, item {e.item_index}'),
    on_verifier_complete=lambda e: print(f"Verify: {'PASS' if e.passed else e.feedback}"),
))
```

| Event | Fields |
|-------|--------|
| `step_start` | `type`, `index`, `name?`, `item_count` |
| `step_complete` | `type`, `index`, `name?`, `duration_ms`, `success_count`, `error_count`, `filtered_count` |
| `step_error` | `type`, `index`, `name?`, `error` |
| `item_retry` | `step_index`, `step_name?`, `item_index`, `attempt`, `error` |
| `worker_complete` | `step_index`, `step_name?`, `item_index`, `attempt`, `status` |
| `verifier_complete` | `step_index`, `step_name?`, `item_index`, `attempt`, `passed`, `feedback?` |
| `candidate_complete` | `step_index`, `step_name?`, `item_index`, `candidate_index`, `status` |
| `judge_complete` | `step_index`, `step_name?`, `item_index`, `winner_index`, `reasoning` |

### Result

```python
@dataclass
class PipelineResult:
    run_id: str
    steps: list[StepResult]   # type, index, duration_ms, results
    output: list[SwarmResult] | ReduceResult
    total_duration_ms: int

# Access step results
for step in result.steps:
    print(f'{step.type} took {step.duration_ms}ms')
```

### Terminal Pipeline

After `.reduce()`, no more steps can be added (returns `TerminalPipeline`):

```python
terminal = pipeline.reduce(ReduceConfig(prompt='...'))
terminal.map(MapConfig(prompt='...'))  # Raises: "Cannot add steps after reduce"
```

---
