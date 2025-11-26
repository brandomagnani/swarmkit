# SwarmKit Python SDK

SwarmKit lets you run and orchestrate terminal-based AI agents in secure sandboxes with built-in observability.

This guide walks through every surface of the SDK in the order you normally wire things up. Every example below is real code.

**[REQUEST ACCESS](https://dashboard.swarmlink.ai/request-access)**

## Get Started

Install the SDK:

```bash
pip install swarmkit
```

Get your API keys:
- **SwarmKit API key** - Sign up at https://dashboard.swarmlink.ai/request-access
- **E2B API key** - Sign up at https://e2b.dev/sign-up

**Note:** Requires [Node.js 18+](https://nodejs.org/) (the SDK uses a lightweight Node.js bridge).

## Reporting Bugs

We welcome your feedback. File a [GitHub issue](https://github.com/brandomagnani/swarmkit/issues) to report bugs or request features.

## Connect on Discord

Join the [SwarmKit Developers Discord](https://discord.gg/Q36D8dGyNF) to connect with other developers using SwarmKit. Get help, share feedback, and discuss your projects with the community.

---

## 1. Build a SwarmKit instance

```python
import os
from swarmkit import SwarmKit, AgentConfig, E2BProvider

swarmkit = SwarmKit(
    config=AgentConfig(
        type='codex',
        api_key=os.getenv('SWARMKIT_API_KEY'),
        model='gpt-5-codex',  # optional - CLI uses its default if omitted
        reasoning_effort='medium',  # optional - only Codex uses it (other agents ignore)
    ),
    sandbox=E2BProvider(
        api_key=os.getenv('E2B_API_KEY'),
        # Optional: template_id, timeout_ms (default 3_600_000 ms)
    ),
    working_directory='/home/user/workspace',  # optional (default: /home/user/workspace)
    workspace_mode='knowledge',  # 'knowledge' (default) or 'swe'
    system_prompt='You are a careful pair programmer.',  # optional
    secrets={'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN')},  # optional
    session_tag_prefix='my-project',  # optional - adds semantic label to observability logs (see section 5)
    context_files=[
        {'path': 'docs/readme.txt', 'data': 'User provided context…'},
    ],  # optional, see section 3
    mcp_servers={
        # STDIO transport (most common)
        'search_bravesearch': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-brave-search'],
            'env': {'BRAVE_API_KEY': os.getenv('BRAVE_API_KEY')},
        },
        # SSE transport (remote servers - not supported by Codex)
        'remote-api': {
            'type': 'sse',
            'url': 'https://api.example.com/mcp/sse',
            'headers': {
                'Authorization': 'Bearer YOUR_TOKEN'
            }
        },
        # HTTP transport (remote servers - not supported by Codex)
        'http-service': {
            'type': 'http',
            'url': 'https://api.example.com/mcp',
            'headers': {
                'Authorization': 'Bearer YOUR_TOKEN'
            }
        },
    },  # optional, agent-specific MCP support (Codex only supports STDIO)
)
```

Only `config` and `sandbox` are required.  The instance does not reach the sandbox until you call one of the runtime methods (`run`, `execute_command`, …).

**Initialization:** Context files, MCP servers, and system prompt are set up once on first `run()` or `execute_command()` call. Reconnecting with `sandbox_id` parameter skips all setup.

### Agent selection cheat sheet

All agents share the same `SWARMKIT_API_KEY` (get it from the [SwarmKit dashboard](https://dashboard.swarmlink.ai/request-access)).

| Agent type       | Notes |
|------------------|-------|
| `'codex'`        | • Supports `reasoning_effort`<br>• Auto-resumes past turns |
| `'claude'`       | • Auto-resumes past turns |
| `'gemini'`       | • Auto-resumes past turns |
| `'acp-gemini'`   | • Agent Client Protocol (ACP) session management<br>• Auto-resumes past turns |
| `'acp-qwen'`     | • ACP session<br>• Auto-resumes past turns |
| `'acp-claude'`   | • ACP session<br>• Auto-resumes past turns |
| `'acp-codex'`    | • ACP session<br>• Supports `reasoning_effort`<br>• Auto-resumes past turns |

> All of these map to the Python config types and delegate to the TypeScript bridge implementation.

---

## 2. Runtime methods (hands-on)

All runtime calls are `async` and return an `ExecuteResult`:

```python
@dataclass
class ExecuteResult:
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
```

### 2.1 `run`

Generates work by delegating to the agent CLI.

**All agents auto-resume past conversation turns**

```python
# Agent maintains conversation state automatically
result = await swarmkit.run(
    prompt='Now add unit tests for the foo module.',
    timeout_ms=15 * 60 * 1000,  # optional (default 1 hour)
)

print(result.exit_code, result.stdout)
```

If `timeout_ms` is omitted the agent uses the default of 3_600_000 ms.

### 2.2 `execute_command`

Runs a direct shell command in the sandbox working directory.

The command automatically executes in the directory set by `working_directory` parameter (default: `/home/user/workspace`).

```python
# Runs "pytest" inside /home/user/workspace (or your custom working directory)
await swarmkit.execute_command(
    command='pytest',
    timeout_ms=10 * 60 * 1000,  # optional (default 1 hour)
    background=False,            # optional (default False)
)
```

### 2.3 Streaming events

Both `run()` and `execute_command()` stream output in real-time during execution. The SDK provides **two patterns** for consuming events:

**Pattern 1: Callback-based**:

```python
swarmkit.on('stdout', lambda data: print(data, end=''))
swarmkit.on('stderr', lambda data: print(f'[ERR] {data}', end=''))
swarmkit.on('update', lambda data: print(f'[UPDATE] {data}'))
swarmkit.on('error', lambda error: print(f'[ERROR] {error}'))
swarmkit.on('complete', lambda info: print(f"[COMPLETE] exit={info['exit_code']}, sandbox={info['sandbox_id']}"))
```

**Pattern 2: Async generator**:

```python
import asyncio

task = asyncio.create_task(swarmkit.run(prompt='Analyze data.csv'))

async for event in swarmkit.stream():
    match event.type:
        case 'stdout':
            print(event.data, end='')
        case 'stderr':
            print(f'[ERR] {event.data}', end='')
        case 'update':
            print(f'[UPDATE] {event.data}')
        case 'error':
            print(f'[ERROR] {event.error}')
        case 'complete':
            print(f'[COMPLETE] exit={event.exit_code}')
            break

result = await task
```

**Event behavior** (delegated to TypeScript SDK):

- `'update'` – Always receives start message (`{"type": "start", "sandbox_id": "..."}`) and end message (`{"type": "end", "sandbox_id": "...", "output": {...}}`). Also receives agent output if no `stdout` listener is registered (fallback).
- `'stdout'` – Receives agent output only (JSON streams), if a listener is registered.
- `'stderr'` – Receives stderr chunks (string).
- `'error'` – Terminal error message (string).
- `'complete'` – Final completion signal with exit code and sandbox id. Emitted exactly once per `run()`/`execute_command()` call. Note: For background commands, this indicates the command started successfully (not completed).

**No duplication:** When both `stdout` and `update` listeners are registered, `stdout` receives agent output and `update` receives only start/end messages.

All listeners are optional; if omitted the agent still runs and you can inspect the return value after completion.

### 2.4 `upload_file`

Write files to the sandbox.  Accepts `str` or `bytes`.  You can send a single path+content pair or a list of files.

```python
await swarmkit.upload_file('/home/user/workspace/scripts/setup.sh', '#!/bin/bash\necho hi\n')

await swarmkit.upload_file([
    {'path': '/home/user/workspace/context/spec.json', 'data': json.dumps(spec)},
    {'path': '/home/user/workspace/context/logo.png', 'data': logo_bytes},
])
```

**Note:** Unlike `context_files` which auto-prefixes relative paths to `context/`, `upload_file()` uses paths exactly as given.

### 2.5 `get_output_files`

Fetch new files from `/output` after a run/command.  Files created before the last operation are filtered out.

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

Each `OutputFile` includes `name`, `path`, `content`, `size`, `modified_time`.

### 2.6 Session controls

```python
session_id = await swarmkit.get_session()  # Returns sandbox ID (str) or None

await swarmkit.pause()  # Suspends sandbox (stops billing, preserves state)
await swarmkit.resume()  # Reactivates same sandbox

await swarmkit.kill()  # Destroys sandbox; next run() creates a new sandbox

await swarmkit.set_session('existing-sandbox-id')  # Sets sandbox ID; reconnection happens on next run()
```

Passing `sandbox_id` to the `SwarmKit` constructor is equivalent to `set_session()` - use it during initialization to reconnect to an existing sandbox.

### 2.7 `get_host`

Expose a forwarded port:

```python
url = await swarmkit.get_host(8000)
print(f'Workspace service available at {url}')
```

---

## 3. Workspace setup

### Knowledge mode (default)

```python
SwarmKit(..., workspace_mode='knowledge')  # implicit default
```

Calling `run` or `execute_command` for the first time provisions the workspace (delegated to TypeScript SDK):

```
/home/user/workspace/
  ├── output/    # return artifacts to caller
  ├── scripts/   # generated code to run
  ├── context/   # uploaded input data
  └── temp/      # scratch space
```

Relative context file paths are automatically prefixed with `{working_directory}/context/`.  Provide absolute paths if you need to write elsewhere.

SwarmKit also writes a default system prompt:

```
You are running in a sandbox environment.
Current directory: /home/user/workspace/

Directory structure:
/home/user/workspace/
  ├── output/      # Save all final results, reports, and artifacts here
  ├── scripts/     # Write and run any code you generate here
  ├── context/     # User-provided input files and data (read from here)
  └── temp/        # Temporary files and intermediate processing

* Always save your final work to output/. The content of output/ will be sent back to the user.
* Use scripts/ for any code you need to write and execute.
* context/ contains all user-provided input files and data, read when necessary.
* Use temp/ to save any temporary and intermediate processing files.
```

Any string passed to `system_prompt` is appended after this default.

### SWE mode

```python
SwarmKit(..., workspace_mode='swe')
```

SWE mode skips directory scaffolding and does **not** prepend the workspace instructions above—useful when targeting an existing repository layout.  All other features (`system_prompt`, `context_files`, etc.) continue to work normally.

---

## 4. Cleaning up and session management

**Multi-turn conversations** (most common):

```python
swarmkit = SwarmKit(...)  # Don't use 'async with'

await swarmkit.run(prompt='Analyze data.csv')
files = await swarmkit.get_output_files()

await swarmkit.run(prompt='Now create visualization')  # Automatically continues conversation
files = await swarmkit.get_output_files()

await swarmkit.run(prompt='Export to PDF')  # Still same session
files = await swarmkit.get_output_files()

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
swarmkit = SwarmKit(...)

await swarmkit.run(prompt='Start analysis')
await swarmkit.pause()  # Suspend billing, keep state
# Do other work, close laptop, etc.
await swarmkit.resume()  # Reactivate same sandbox
await swarmkit.run(prompt='Continue analysis')  # Session intact

await swarmkit.kill()  # When done
```

**Save and reconnect** (different process/script):

```python
# Script 1: Save session for later
swarmkit = SwarmKit(...)
await swarmkit.run(prompt='Start analysis')

session_id = await swarmkit.get_session()
# Save to file, database, environment variable, etc.
with open('session.txt', 'w') as f:
    f.write(session_id)

# Script 2: Reconnect to saved session
with open('session.txt') as f:
    saved_id = f.read()

swarmkit = SwarmKit(..., sandbox_id=saved_id)  # Reconnect
await swarmkit.run(prompt='Continue analysis')  # Session continues from Script 1
```

**Switch between sandboxes** (same instance):

```python
swarmkit = SwarmKit(...)

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

## 5. Observability

Full execution traces—including tool calls, file operations (read/write/edit), text responses, and reasoning chunks—are logged to your SwarmKit dashboard at **https://dashboard.swarmlink.ai/traces** for debugging and replay.

Additionally, every run and command is logged locally to structured JSON lines under `~/.swarmkit/observability/sessions`. File name format:

```
{tag}_{provider}_{sandboxId}_{agent}_{timestamp}.jsonl
```

- `{tag}` – `my-prefix-` + 8 random hex characters (e.g. `my-prefix-a1b2c3d4`)
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
    session_tag_prefix='my-project',
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

## 6. Sandbox provider API (E2B)

`E2BProvider(api_key, template_id=None, timeout_ms=3600000)` returns a `SandboxProvider` that the SDK uses via the TypeScript bridge:

- `create(envs, agentType, workingDirectory)` provisions a new sandbox, creates the workspace directories, and honours the `timeout_ms` you pass (default 1 hour).
- `resume(sandboxId)` re-attaches to a paused/previous sandbox.
- Commands and file operations are handled via the bridge to the TypeScript implementation.

If you need a different sandbox backend you can implement a custom provider matching the `SandboxProvider` protocol and pass it to the `sandbox` parameter.

---

## 7. Error handling

Errors from `run()` and `execute_command()` are handled in two ways:

1. **Error event**: Triggers the `'error'` event callback
2. **Exception raised**: The async method raises an exception

Always attach an error listener if you want real-time error notifications:

```python
swarmkit.on('error', lambda error: print(f'[ERROR] {error}'))

try:
    await swarmkit.execute_command('exit 1')
except Exception as e:
    print(f'Command failed: {e}')
```

Python SDK also exports custom exceptions:
- `SandboxNotFoundError` – Sandbox ID not found
- `BridgeConnectionError` – Bridge communication failed
- `BridgeBuildError` – Bridge build/start failed

---

## 8. Secrets, MCP servers, and system prompts

- `secrets={'MY_TOKEN': '...'}` injects environment variables into the sandbox create call.
- `system_prompt` writes an agent-specific prompt file (e.g., `AGENTS.md`, `CLAUDE.md`) inside the workspace.
- `mcp_servers` lets agents that support the Model Context Protocol (Claude, Codex, Gemini, ACP variants) write their configuration automatically.

All three are optional and can be mixed as needed.

---

## 9. Recap checklist

1. Create `E2BProvider(api_key, timeout_ms=...)`
2. Create `SwarmKit` instance with `AgentConfig` and `E2BProvider`
3. Attach event listeners (`on()` or `stream()`)
4. `await run()` or `await execute_command()`
5. Fetch artifacts via `get_output_files()`
6. Manage sandbox lifecycle with `get_session`, `set_session`, `pause`, `resume`, `kill`
7. Use `upload_file`, `context_files`, and `secrets` to seed the environment
8. Use `async with` context manager for automatic cleanup
9. Use `session_tag_prefix` for semantic log labeling; retrieve with `get_session_tag()` and `get_session_timestamp()`

Everything above delegates to the TypeScript SDK implementation via a JSON-RPC bridge.  The Python SDK provides a Pythonic wrapper with type hints, dataclasses, and async patterns.

Happy shipping!
