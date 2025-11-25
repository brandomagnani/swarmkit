# SwarmKit TypeScript SDK

SwarmKit lets you run and orchestrate terminal-based AI agents in secure sandboxes with built-in observability.

This guide walks through every surface of the SDK in the order you normally wire things up. Every example below is real code.

## Get Started

Install the SDK:

```bash
npm install @swarmkit/sdk @swarmkit/e2b
```

Get your API keys:
- **SwarmKit API key** - Sign up at https://dashboard.swarmlink.ai/request-access
- **E2B API key** - Sign up at https://e2b.dev

## Reporting Bugs

We welcome your feedback. File a [GitHub issue](https://github.com/brandomagnani/swarmkit/issues) to report bugs or request features.

## Connect on Discord

Join the [SwarmKit Developers Discord](https://discord.gg/Q36D8dGyNF) to connect with other developers using SwarmKit. Get help, share feedback, and discuss your projects with the community.

---

## 1. Build a SwarmKit instance

```ts
import { SwarmKit } from "@swarmkit/sdk";
import { createE2BProvider } from "@swarmkit/e2b";

const sandbox = createE2BProvider({
  apiKey: process.env.E2B_API_KEY!,
  // Optional: templateId, timeoutMs (default 3_600_000 ms)
});

const swarmkit = new SwarmKit()  // No constructor config needed
  .withAgent({
    type: "codex",
    apiKey: process.env.SWARMKIT_API_KEY!,  // Single key for all providers
    model: "gpt-5.1-codex",  // optional - CLI uses its default if omitted
    reasoningEffort: "medium",  // optional - only Codex uses it (other agents ignore)
  })
  .withSandbox(sandbox)
  .withWorkingDirectory("/home/user/workspace")   // optional (default: /home/user/workspace)
  .withWorkspaceMode("knowledge")                 // "knowledge" (default) or "swe"
  .withSystemPrompt("You are a careful pair programmer.") // optional
  .withSecrets({ GITHUB_TOKEN: process.env.GITHUB_TOKEN! }) // optional
  .withSessionTagPrefix("my-project")             // optional - adds semantic label to observability logs (see section 5)
  .withContextFiles([
    { path: "docs/readme.txt", data: "User provided context…" },
  ]) // optional, see section 4
  .withMcpServers({
    // STDIO transport (most common)
    "search_bravesearch": {
      command: "npx",
      args: [
        "-y",
        "@modelcontextprotocol/server-brave-search"
      ],
      env: {
        BRAVE_API_KEY: process.env.BRAVE_API_KEY!
      }
    },
    // SSE transport (remote servers - not supported by Codex)
    "remote-api": {
      type: "sse",
      url: "https://api.example.com/mcp/sse",
      headers: {
        Authorization: "Bearer YOUR_TOKEN"
      }
    },
    // HTTP transport (remote servers - not supported by Codex)
    "http-service": {
      type: "http",
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: "Bearer YOUR_TOKEN"
      }
    }
  }); // optional, agent-specific MCP support (Codex only supports STDIO)
```

Everything above is a fluent setter.  The instance does not reach the sandbox until you call one of the runtime methods (`run`, `executeCommand`, …).

**Initialization:** Context files, MCP servers, and system prompt are set up once on first `run()` or `executeCommand()` call. Using `withSession()` to reconnect skips all setup.

### Agent selection cheat sheet

**All agents use a single SwarmKit API key** (get yours from the [SwarmKit dashboard](https://dashboard.swarmlink.ai/request-access)).

| Agent type       | Notes |
|------------------|-------|
| `"codex"`        | • Supports `reasoningEffort`<br>• `run()` auto-resumes past turns |
| `"claude"`       | • `run()` auto-resumes past turns |
| `"gemini"`       | • `run()` auto-resumes past turns |
| `"acp-gemini"`   | • Agent Client Protocol<br>• Persistent session across `run()` calls<br>• Auto-resumes past turns |
| `"acp-qwen"`     | • Agent Client Protocol<br>• Persistent session across `run()` calls<br>• Auto-resumes past turns |
| `"acp-claude"`   | • Agent Client Protocol<br>• Persistent session across `run()` calls<br>• Auto-resumes past turns |
| `"acp-codex"`    | • Agent Client Protocol<br>• Persistent session across `run()` calls<br>• Auto-resumes past turns<br>• Supports `reasoningEffort` |

> **Gateway routing**: All requests are automatically routed through the SwarmKit gateway, which handles provider authentication and cost tracking. You no longer need individual provider API keys (OpenAI, Anthropic, Google, etc.).

---

## 2. Runtime methods (hands-on)

All runtime calls are `async` and return a shared `AgentResponse`:

```ts
type AgentResponse = {
  sandboxId: string;
  exitCode: number;
  stdout: string;
  stderr: string;
};
```

### 2.1 `run`

Generates work by delegating to the agent CLI.

**All agents auto-resume past conversation turns** 

```ts
// Agent maintains conversation state automatically
const result = await swarmkit.run({
  prompt: "Now add unit tests for the foo module.",
  timeoutMs: 15 * 60 * 1000, // optional (default 1 hour)
});

console.log(result.exitCode, result.stdout);
```

If `timeoutMs` is omitted the agent uses the TypeScript default of 3_600_000 ms.

### 2.2 `executeCommand`

Runs a direct shell command in the sandbox working directory.

The command automatically executes in the directory set by `withWorkingDirectory()` (default: `/home/user/workspace`).

```ts
// Runs "pytest" inside /home/user/workspace (or your custom working directory)
await swarmkit.executeCommand("pytest", {
  timeoutMs: 10 * 60 * 1000,  // optional (default 1 hour)
  background: false,           // optional (default false)
});
```

### 2.3 Streaming events

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

### 2.4 `uploadFile`

Write files to the sandbox.  Accepts `string`, `Buffer`, or `ArrayBuffer`.  You can send a single path+content pair or an array.

```ts
await swarmkit.uploadFile("/home/user/workspace/scripts/setup.sh", "#!/bin/bash\necho hi\n");

await swarmkit.uploadFile([
  { path: "/home/user/workspace/context/spec.json", data: JSON.stringify(spec) },
  { path: "/home/user/workspace/context/logo.png", data: logoBuffer },
]);
```

**Note:** Unlike `withContextFiles()` which auto-prefixes relative paths to `context/`, `uploadFile()` uses paths exactly as given.

### 2.5 `getOutputFiles`

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

### 2.6 Session controls

```ts
const sessionId = await swarmkit.getSession();  // Returns sandbox ID (string) or null

await swarmkit.pause();  // Suspends sandbox (stops billing, preserves state)
await swarmkit.resume(); // Reactivates same sandbox

await swarmkit.kill();   // Destroys sandbox; next run() creates a new sandbox

await swarmkit.setSession("existing-sandbox-id"); // Sets sandbox ID; reconnection happens on next run()
```

`withSession("sandbox-id")` is a builder method equivalent to `setSession()` - use it during initialization to reconnect to an existing sandbox.

### 2.7 `getHost`

Expose a forwarded port:

```ts
const url = await swarmkit.getHost(8000);
console.log(`Workspace service available at ${url}`);
```

---

## 3. Workspace setup

### Knowledge mode (default)

```ts
swarmkit.withWorkspaceMode("knowledge"); // implicit default
```

Calling `run` or `executeCommand` for the first time provisions the workspace:

```
/home/user/workspace/
  ├── output/    # return artifacts to caller
  ├── scripts/   # generated code to run
  ├── context/   # uploaded input data
  └── temp/      # scratch space
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

### SWE mode

```ts
swarmkit.withWorkspaceMode("swe");
```

SWE mode skips directory scaffolding and does **not** prepend the workspace instructions above—useful when targeting an existing repository layout.  All other features (`withSystemPrompt`, `withContextFiles`, etc.) continue to work normally.

---

## 4. Cleaning up and session management

**Multi-turn conversations** (most common):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSandbox(sandbox);

await swarmkit.run({ prompt: 'Analyze data.csv' });
const files = await swarmkit.getOutputFiles();

await swarmkit.run({ prompt: 'Now create visualization' });  // Automatically continues conversation
const files2 = await swarmkit.getOutputFiles();

await swarmkit.run({ prompt: 'Export to PDF' });  // Still same session
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

await swarmkit.kill();  // When done
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

## 6. Sandbox provider API (E2B)

`createE2BProvider(config)` returns a `SandboxProvider` that covers every method SwarmKit uses:

- `create(envs, agentType, workingDirectory)` provisions a new sandbox, creates the workspace directories, and honours the `timeoutMs` you pass (default 1 hour).
- `resume(sandboxId)` re-attaches to a paused/previous sandbox.
- `commands.run` executes shell commands; `commands.runWithHandle` fuels the ACP bridge; `files.read` / `files.write` implement file I/O.
- `getHost(port)` handles port forwarding via the underlying provider.

If you need a different sandbox backend you can implement the `SandboxProvider` interface and plug it into `.withSandbox()`.

---

## 7. Error handling

Errors from `run()` and `executeCommand()` are handled in two ways:

1. **Error event**: Triggers the `"error"` event on the SwarmKit instance
2. **Exception thrown**: Rejects the promise with an error message

Always attach an error listener if you want real-time error notifications:

```ts
swarmkit.on("error", message => console.error("[error]", message));

try {
  await swarmkit.executeCommand("exit 1");
} catch (error) {
  console.error("Command failed:", error);
}
```

---

## 8. Secrets, MCP servers, and system prompts

- `withSecrets({ MY_TOKEN: "..." })` injects environment variables into the sandbox create call.
- `withSystemPrompt` writes an agent-specific prompt file (e.g., `AGENTS.md`, `CLAUDE.md`) inside the workspace.
- `withMcpServers` lets agents that support the Model Context Protocol (Claude, Codex, Gemini, ACP variants) write their configuration automatically.

All three are optional and can be mixed as needed.

---

## 9. Recap checklist

1. `createE2BProvider({ apiKey, timeoutMs? })`
2. Build a `SwarmKit` instance with `.withAgent()` and `.withSandbox()`
3. Attach event listeners (`stdout`, `stderr`, `update`, `error`)
4. `await run` or `await executeCommand`
5. Fetch artifacts via `getOutputFiles`
6. Manage sandbox lifecycle with `getSession`, `setSession`, `pause`, `resume`, `kill`
7. Use `uploadFile`, `withContextFiles`, and `withSecrets` to seed the environment

Happy shipping!

---

## License

Proprietary and Confidential

Copyright (c) 2025 Swarmlink, Inc. All rights reserved.

This software is licensed under proprietary terms. See the [LICENSE](../../LICENSE) file for full terms and conditions.

Unauthorized copying, modification, distribution, or use is strictly prohibited.

For licensing inquiries: brandomagnani@swarmlink.ai
