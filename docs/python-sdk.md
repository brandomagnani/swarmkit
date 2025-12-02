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
        reasoning_effort='medium',           # (optional) 'medium' | 'high' - Only Codex agents
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

| Type         | Recommended Models                                        | Notes                                                                         |
|--------------|-----------------------------------------------------------|-------------------------------------------------------------------------------|
| `codex`      | `gpt-5.1`, `gpt-5.1-codex`, `gpt-5.1-codex-mini`          | • Codex Agent<br>• persistent memory<br>• `reasoning_effort`: `medium`, `high` |
| `claude`     | `claude-opus-4-5-20251101` (`opus`), `claude-sonnet-4-5-20250929` (`sonnet`)                   | • Claude agent<br>• persistent memory                                         |
| `gemini`     | `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash` | • Gemini agent<br>• persistent memory                                      |
| `acp-codex` [experimental]  | `gpt-5.1`, `gpt-5.1-codex`, `gpt-5.1-codex-mini`          | • Codex via ACP<br>• persistent ACP session + memory<br>• `reasoning_effort`: `medium`, `high` |
| `acp-claude` [experimental] | `claude-opus-4-5-20251101`(`opus`), `claude-sonnet-4-5-20250929`(`sonnet`)                    | • Claude via ACP<br>• persistent ACP session + memory                         |
| `acp-gemini` [experimental] | `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash` | • Gemini via ACP<br>• persistent ACP session + memory                      |
| `acp-qwen` [experimental]   | `qwen3-coder-plus`, `qwen3-vl-plus`, `qwen3-max-preview`  | • Qwen via ACP<br>• persistent ACP session + memory                           |

---
- **Note**: ACP agents are experimental.

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
)

print(result.exit_code)
print(result.stdout)
```

- If `timeout_ms` is omitted the agent uses the default of 3_600_000 ms (1 hour).

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

Both `run()` and `execute_command()` stream output in real-time.

**Pattern 1: Callback-based**:

```python
# Raw output
swarmkit.on('stdout', lambda data: print(data, end=''))
swarmkit.on('stderr', lambda data: print(f'[ERR] {data}', end=''))
swarmkit.on('update', lambda data: print(f'[UPDATE] {data}'))
swarmkit.on('error', lambda error: print(f'[ERROR] {error}'))

# Parsed output (recommended)
swarmkit.on('content', lambda event: print(event['update']))
```

**Pattern 2: Async generator**:

```python
task = asyncio.create_task(swarmkit.run(prompt='Analyze data.csv'))

async for event in swarmkit.stream():
    match event.type:
        case 'content':
            print(event.update)  # Parsed ACP-style event
        case 'stdout':
            print(event.data, end='')
        case 'complete':
            break

result = await task
```

**Events**:

| Event | Description |
|-------|-------------|
| `content` | Parsed ACP-style events (recommended). Takes priority over `stdout`. |
| `stdout` | Raw JSONL output |
| `stderr` | Stderr chunks |
| `update` | Start/end messages. Fallback for output if no `stdout`/`content` listener. |
| `error` | Terminal errors |
| `complete` | Run finished with `exit_code`, `sandbox_id` |

**Content event types** (`event.update['sessionUpdate']`):

| Type | Description |
|------|-------------|
| `agent_message_chunk` | Text/image from agent |
| `agent_thought_chunk` | Reasoning/thinking |
| `tool_call` | Tool started (status: `pending`) |
| `tool_call_update` | Tool finished (status: `completed`/`failed`) |
| `plan` | TodoWrite updates |

All listeners are optional.

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
- `{agent}` – the agent type (`codex`, `acp-qwen`, …)
- `{timestamp}` – ISO timestamp with `:` and `.` replaced by `-`

Each file contains three entry types:

```json
{"_meta":{"tag":"my-prefix-a1b2c3d4","provider":"e2b","sandbox_id":"sbx_123","agent":"acp-qwen","timestamp":"2025-10-26T20:15:17.984Z"}}
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
