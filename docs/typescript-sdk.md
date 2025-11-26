# SwarmKit TypeScript SDK

Run terminal-based AI agents in secure sandboxes with built-in observability.

> See the [main README](../README.md) for installation and API keys.

---

## 1. Quick Start

```ts
import { SwarmKit } from "@swarmkit/sdk";
import { createE2BProvider } from "@swarmkit/e2b";

// Create sandbox provider
const sandbox = createE2BProvider({
    apiKey: process.env.E2B_API_KEY!
});

// Build SwarmKit instance
const swarmkit = new SwarmKit()
    .withAgent({
        type: "codex",
        apiKey: process.env.SWARMKIT_API_KEY!
    })
    .withSandbox(sandbox)
    .withSessionTagPrefix("my-app") // optional tag for the agent session
    .withSystemPrompt("You are a helpful coding assistant.")
    .withMcpServers({
        "exa": {
            command: "npx",
            args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
            env: { EXA_API_KEY: process.env.EXA_API_KEY! }
        }
    });

// Run agent
const result = await swarmkit.run({
    prompt: "Create a hello world script"
});

console.log(result.stdout);

// Clean up
await swarmkit.kill();
```

**Tracing:** Every run is automatically logged to [dashboard.swarmlink.ai/traces](https://dashboard.swarmlink.ai/traces)—no extra setup needed. Optionally use `withSessionTagPrefix()` to label your traces for easy filtering.

---

## 2. Full Configuration

```ts
const swarmkit = new SwarmKit()

    // (required) Agent type and API key
    .withAgent({
        type: "codex",
        apiKey: process.env.SWARMKIT_API_KEY!,
        model: "gpt-5.1-codex",               // (optional) Uses default if omitted
        reasoningEffort: "medium",            // (optional) Only Codex agents use this
    })

    // (required) Sandbox provider for execution
    .withSandbox(sandbox)

    // (optional) Custom working directory, default: /home/user/workspace
    .withWorkingDirectory("/home/user/workspace")

    // (optional) Workspace mode: "knowledge" (default) for knowledge work use cases or "swe" for coding use cases
    .withWorkspaceMode("knowledge")

    // (optional) System prompt appended to default instructions
    .withSystemPrompt("You are a careful pair programmer.")

    // (optional) Environment variables injected into sandbox
    .withSecrets({
        GITHUB_TOKEN: process.env.GITHUB_TOKEN!
    })

    // (optional) Prefix for observability logs
    .withSessionTagPrefix("my-agent")

    // (optional) Files uploaded to workspace/context/ on first run
    .withContextFiles([
        { path: "docs/readme.txt", data: "User provided context..." },
    ])

    // (optional) MCP servers for agent tools
    .withMcpServers({
        "exa": {
            command: "npx",
            args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
            env: { EXA_API_KEY: process.env.EXA_API_KEY! }
        }
    });
```

**Note:**
- Configuration methods can be chained in any order.
- The sandbox is created on the first `run()` or `executeCommand()` call (see below).
- Context files, MCP servers, and system prompt are set up once on the first call.
- Using `.withSession()` to reconnect skips setup since the sandbox already exists.

---

## 3. Agents

All agents use a single SwarmKit API key from [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai/).

| Type         | Recommended Models                                        | Notes                                                                         |
|--------------|-----------------------------------------------------------|-------------------------------------------------------------------------------|
| `codex`      | `gpt-5.1`, `gpt-5.1-codex`, `gpt-5.1-codex-max`           | • Codex Agent<br>• persistent memory<br>• supports `reasoningEffort`          |
| `claude`     | `claude-opus-4-5`, `claude-sonnet-4-5`                    | • Claude agent<br>• persistent memory                                         |
| `gemini`     | `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash` | • Gemini agent<br>• persistent memory                                      |
| `acp-codex`  | `gpt-5.1`, `gpt-5.1-codex`, `gpt-5.1-codex-max`           | • Codex via ACP<br>• persistent ACP session + memory<br>• supports `reasoningEffort` |
| `acp-claude` | `claude-opus-4-5`, `claude-sonnet-4-5`                    | • Claude via ACP<br>• persistent ACP session + memory                         |
| `acp-gemini` | `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash` | • Gemini via ACP<br>• persistent ACP session + memory                      |
| `acp-qwen`   | `qwen3-coder-plus`, `qwen3-vl-plus`, `qwen3-max-preview`  | • Qwen via ACP<br>• persistent ACP session + memory                           |

---

## 4. Runtime Methods

All runtime calls are `async` and return a shared `AgentResponse`:

```ts
type AgentResponse = {
  sandboxId: string;
  exitCode: number;
  stdout: string;
  stderr: string;
};
```

### 4.1 `run`

Runs the agent with a given prompt. 

```ts
const result = await swarmkit.run({
    prompt: "Analyze the data and create a report",
    timeoutMs: 15 * 60 * 1000,                // (optional) Default 1 hour
});

console.log(result.exitCode);
console.log(result.stdout);
```

- If `timeoutMs` is omitted the agent uses the TypeScript default of 3_600_000 ms (1 hour).

- Calling `run()` multiple times maintains the agent context / history. 

### 4.2 `executeCommand`

Runs a direct shell command in the sandbox working directory.

```ts
// Run shell command directly in sandbox
const result = await swarmkit.executeCommand("pytest", {
    timeoutMs: 10 * 60 * 1000,                // (optional) Default 1 hour
    background: false,                         // (optional) Run in background
});
```
- The command automatically executes in the directory set by `withWorkingDirectory()` (default: `/home/user/workspace`).

### 4.3 Streaming events

`SwarmKit` extends Node's `EventEmitter`. Both `run()` and `executeCommand()` stream output in real-time during execution:

```ts
swarmkit.on("stdout", chunk => process.stdout.write(chunk));
swarmkit.on("stderr", chunk => process.stderr.write(chunk));
swarmkit.on("update", message => {
  try {
    console.log("[update]", JSON.parse(message));
  } catch {
    console.log("[update]", message);
  }
});
swarmkit.on("error", message => console.error("[error]", message));
```

**Event behavior**:

- `"update"` – Always receives start message (`{"type": "start", "sandbox_id": "..."}`) and end message (`{"type": "end", "sandbox_id": "...", "output": {...}}`). Also receives agent output if no `stdout` listener is registered (fallback).
- `"stdout"` – Receives agent output only (JSON streams), if a listener is registered.
- `"stderr"` – Receives stderr chunks (string).
- `"error"` – Terminal error message (string).

**No duplication:** When both `stdout` and `update` listeners are registered, `stdout` receives agent output and `update` receives only start/end messages.

All listeners are optional; if omitted the agent still runs and you can inspect the return value after completion.

### 4.4 `uploadFile`

Write files to the sandbox.  Accepts `string`, `Buffer`, or `ArrayBuffer`.  You can send a single path+content pair or an array.

```ts
await swarmkit.uploadFile("/home/user/workspace/scripts/setup.sh", "#!/bin/bash\necho hi\n");

await swarmkit.uploadFile([
  { path: "/home/user/workspace/context/spec.json", data: JSON.stringify(spec) },
  { path: "/home/user/workspace/context/logo.png", data: logoBuffer },
]);
```

**Note:** Unlike `withContextFiles()` which auto-prefixes relative paths to `context/`, `uploadFile()` uses paths exactly as given.

### 4.5 `getOutputFiles`

Fetch new files from `/output` after a run/command.  Files created before the last operation are filtered out.

```ts
const files = await swarmkit.getOutputFiles();
for (const file of files) {
  if (typeof file.content === "string") {
    console.log("text file:", file.path);
  } else {
    // Buffer | ArrayBuffer
    await fs.promises.writeFile(localPath(file.name), Buffer.from(file.content));
  }
}
```

Each entry includes `name`, `path`, `content`, `size`, `modifiedTime`.

### 4.6 Session controls

```ts
const sessionId = await swarmkit.getSession();  // Returns sandbox ID (string) or null

await swarmkit.pause();  // Suspends sandbox (stops billing, preserves state)
await swarmkit.resume(); // Reactivates same sandbox

await swarmkit.kill();   // Destroys sandbox; next run() creates a new sandbox

await swarmkit.setSession("existing-sandbox-id"); // Sets sandbox ID; reconnection happens on next run()
```

`withSession("sandbox-id")` is a builder method equivalent to `setSession()` - use it during initialization to reconnect to an existing sandbox.

### 4.7 `getHost`

Expose a forwarded port:

```ts
const url = await swarmkit.getHost(8000);
console.log(`Workspace service available at ${url}`);
```
---

## 5. Workspace setup and Modes

### 5.1 Knowledge Mode (default)

Ideal for knowledge work applications.
```ts
swarmkit.withWorkspaceMode("knowledge"); // implicit default
```

Calling `run` or `executeCommand` for the first time provisions the workspace:

```
/home/user/workspace/
    ├── output/    # Final artifacts (returned to caller)
    ├── scripts/   # Generated code
    ├── context/   # Input files from withContextFiles()
    └── temp/      # Scratch space
```
Relative context file paths are automatically prefixed with `${workingDirectory}/context/`.  Provide absolute paths if you need to write elsewhere.

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

Any string passed to `withSystemPrompt()` is appended after this default.


### 5.2 SWE Mode

Ideal for coding applications (when working with repositories).
```ts
swarmkit.withWorkspaceMode("swe");
```

SWE mode skips directory scaffolding and does **not** prepend the workspace instructions above—useful when targeting an existing repository layout.  All other features (`withSystemPrompt`, `withContextFiles`, etc.) continue to work normally.


---

## 6. Cleaning up and session management

**Multi-turn conversations** (most common):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox);

await swarmkit.run({ prompt: 'Analyze data.csv' });
const files = await swarmkit.getOutputFiles();

// Still same session, automatically maintains context / history
await swarmkit.run({ prompt: 'Now create visualization' });  
const files2 = await swarmkit.getOutputFiles();

// Still same session, automatically maintains context / history
await swarmkit.run({ prompt: 'Export to PDF' });  
const files3 = await swarmkit.getOutputFiles();

await swarmkit.kill();  // When done
```

**Pause and resume** (same instance):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox);

await swarmkit.run({ prompt: 'Start analysis' });
await swarmkit.pause();  // Suspend billing, keep state
// Do other work...
await swarmkit.resume();  // Reactivate same sandbox
await swarmkit.run({ prompt: 'Continue analysis' });  // Session intact

await swarmkit.kill();  // Kill the Sandbox when done
```

**Save and reconnect** (different script/session):

```ts
// Script 1: Save session for later
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox);

await swarmkit.run({ prompt: 'Start analysis' });

const sessionId = await swarmkit.getSession();
// Save to file, database, environment variable, etc.
fs.writeFileSync('session.txt', sessionId);

// Script 2: Reconnect to saved session
const savedId = fs.readFileSync('session.txt', 'utf-8');

const swarmkit2 = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox)
  .withSession(savedId);  // Reconnect

await swarmkit2.run({ prompt: 'Continue analysis' });  // Session continues from Script 1
```

**Switch between sandboxes** (same instance):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox);

// Work with first sandbox
await swarmkit.run({ prompt: 'Analyze dataset A' });
const sessionA = await swarmkit.getSession();

// Switch to different sandbox
await swarmkit.setSession('existing-sandbox-b-id');
await swarmkit.run({ prompt: 'Analyze dataset B' });  // Now working with sandbox B

// Switch back to first sandbox
await swarmkit.setSession(sessionA);
await swarmkit.run({ prompt: 'Compare results' });  // Back to sandbox A
```

---

## 7. Observability

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

```ts
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox)
  .withSessionTagPrefix("my-project");

await swarmkit.run({ prompt: "Kick off analysis" });

console.log(await swarmkit.getSessionTag());        // "my-project-ab12cd34"
console.log(await swarmkit.getSessionTimestamp()); // Timestamp for first log file

await swarmkit.kill();                              // Flushes log file for sandbox A

await swarmkit.run({ prompt: "Start fresh" });      // New sandbox → new log file

console.log(await swarmkit.getSessionTag());        // "my-project-f56789cd"
console.log(await swarmkit.getSessionTimestamp()); // Timestamp for second log file
```

- `kill()` or `setSession()` flushes the current log; the next `run()` starts a
  fresh file with the new sandbox id.
- Long-running sessions (pause/resume or ACP auto-resume) keep appending to the
  current file, so you always have the full timeline.
- Logging is buffered inside the SDK, so it never blocks streaming output.

Use the tag together with the sandbox id to correlate logs with files saved in
`/output/`.

---