# SwarmKit TypeScript SDK

Run terminal-based AI agents in secure sandboxes with built-in observability.

> See the [main README](../README.md) for installation and API keys.

---

## 1. Quick Start

```ts
import { SwarmKit } from "@swarmkit/sdk";

// Build SwarmKit instance
const swarmkit = new SwarmKit()
    .withAgent({
        type: "codex",
        apiKey: process.env.SWARMKIT_API_KEY!,
    })
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

// Get output files
const output = await swarmkit.getOutputFiles();
for (const [name, content] of Object.entries(output.files)) {
    console.log(name);
}

// Clean up
await swarmkit.kill();
```

- **Tracing:** Every run is automatically logged to [dashboard.swarmlink.ai/traces](https://dashboard.swarmlink.ai/traces)—no extra setup needed. Optionally use `withSessionTagPrefix()` to label your agent session for easy filtering.

## 1.1 Authentication

| | Gateway | Direct (BYOK) |
|---|---------|---------------|
| Setup | `SWARMKIT_API_KEY` | Model provider keys + E2B sandbox keys |
| Observability | [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai) | `~/.swarmkit/observability/` |
| Billing | Swarmlink | Your provider accounts |

---

### Gateway Mode

Get API key from [dashboard.swarmlink.ai](https://dashboard.swarmlink.ai).

```bash
# .env
SWARMKIT_API_KEY=sk-...
E2B_API_KEY=e2b_...
```

```ts
import { SwarmKit, E2BProvider } from "@swarmkit/sdk";

const sandbox = new E2BProvider({
    apiKey: process.env.E2B_API_KEY,
});

const swarmkit = new SwarmKit()
    .withAgent({
        type: "claude",
        apiKey: process.env.SWARMKIT_API_KEY,
    })
    .withSandbox(sandbox);

await swarmkit.run({ prompt: "Hello" });
```

---

### Direct Mode (BYOK)

Use your own provider keys. Requires E2B for sandbox.

```bash
# .env
ANTHROPIC_API_KEY=sk-...
E2B_API_KEY=e2b_...
```

```ts
import { SwarmKit, E2BProvider } from "@swarmkit/sdk";

const sandbox = new E2BProvider({
    apiKey: process.env.E2B_API_KEY,
});

const swarmkit = new SwarmKit()
    .withAgent({
        type: "claude",
        providerApiKey: process.env.ANTHROPIC_API_KEY,
    })
    .withSandbox(sandbox);
```

---

### Use SwarmKit with your Claude Max subscription

```bash
# Run in terminal, follow login steps → receive token:
claude --setup-token

# ✓ Long-lived authentication token created successfully!
# Your OAuth token (valid for 1 year): sk-ant-...
```

```bash
# .env
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-...
E2B_API_KEY=e2b_...
```

```ts
import { SwarmKit, E2BProvider } from "@swarmkit/sdk";

const sandbox = new E2BProvider({
    apiKey: process.env.E2B_API_KEY,
});

const swarmkit = new SwarmKit()
    .withAgent({
        type: "claude",
        oauthToken: process.env.CLAUDE_CODE_OAUTH_TOKEN,
    })
    .withSandbox(sandbox);
```

---

### Auto-resolve from Environment

Set env vars and the SDK picks them up automatically—no need to pass explicitly. See Agent Reference below for env var names.

### Agent Reference

| type | models | default | env var (BYOK) |
|------|--------|---------|----------------|
| `"claude"` | `"opus"` `"sonnet"` `"haiku"` | `"opus"` | `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` |
| `"codex"` | `"gpt-5.2"` `"gpt-5.2-codex"` `"gpt-5.1-codex-max"` `"gpt-5.1-mini"` | `"gpt-5.2"` | `OPENAI_API_KEY` |
| `"gemini"` | `"gemini-3-pro-preview"` `"gemini-3-flash-preview"` `"gemini-2.5-pro"` `"gemini-2.5-flash"` `"gemini-2.5-flash-lite"` | `"gemini-3-flash-preview"` | `GEMINI_API_KEY` |
| `"qwen"` | `"qwen3-coder-plus"` `"qwen3-vl-plus"` | `"qwen3-coder-plus"` | `OPENAI_API_KEY` |

Agent-specific options: `reasoningEffort` (Codex: `"low"` `"medium"` `"high"` `"xhigh"`), `betas` (Claude Sonnet: `["context-1m-2025-08-07"]`)

### Agent Examples

```bash
# .env - set env vars for auto-pickup
ANTHROPIC_API_KEY=sk-...   # claude
OPENAI_API_KEY=sk-...      # codex, qwen
GEMINI_API_KEY=...         # gemini
E2B_API_KEY=e2b_...        # sandbox
```

```ts
// claude (auto-picks ANTHROPIC_API_KEY + E2B_API_KEY)
const swarmkit = new SwarmKit()
    .withAgent({ type: "claude" });

const swarmkit = new SwarmKit()
    .withAgent({ type: "claude", model: "opus" });

const swarmkit = new SwarmKit()
    .withAgent({
        type: "claude",
        model: "sonnet",
        betas: ["context-1m-2025-08-07"],
    });
```

```ts
// codex (auto-picks OPENAI_API_KEY + E2B_API_KEY)
const swarmkit = new SwarmKit()
    .withAgent({ type: "codex" });

const swarmkit = new SwarmKit()
    .withAgent({ type: "codex", model: "gpt-5.2-codex" });

const swarmkit = new SwarmKit()
    .withAgent({ type: "codex", reasoningEffort: "high" });
```

```ts
// gemini (auto-picks GEMINI_API_KEY + E2B_API_KEY)
const swarmkit = new SwarmKit()
    .withAgent({ type: "gemini" });

const swarmkit = new SwarmKit()
    .withAgent({ type: "gemini", model: "gemini-3-pro-preview" });
```

```ts
// qwen (auto-picks OPENAI_API_KEY + E2B_API_KEY)
const swarmkit = new SwarmKit()
    .withAgent({ type: "qwen" });

const swarmkit = new SwarmKit()
    .withAgent({ type: "qwen", model: "qwen3-coder-plus" });
```

---

## 2. Full Configuration

```ts
import { SwarmKit, E2BProvider } from "@swarmkit/sdk";

// Sandbox provider (auto-resolved from E2B_API_KEY, or explicit)
const sandbox = new E2BProvider({
    apiKey: process.env.E2B_API_KEY,   // (optional) Auto-resolves from E2B_API_KEY env var
    defaultTimeoutMs: 3600000,          // (optional) Default sandbox timeout (default: 1 hour)
});
```

```ts
const swarmkit = new SwarmKit()

    // Agent configuration (optional if SWARMKIT_API_KEY set, defaults to claude)
    .withAgent({
        type: "codex",                        // "claude" | "codex" | "gemini" | "qwen" - defaults to "claude"
        model: "gpt-5.2-codex",               // (optional) Uses default if omitted
        reasoningEffort: "medium",            // (optional) "low" | "medium" | "high" | "xhigh" - Codex only
        // betas: ["context-1m-2025-08-07"],  // (optional) Claude Sonnet only
        apiKey: process.env.SWARMKIT_API_KEY!, // (optional) Gateway mode - auto-resolves from env
        // providerApiKey: process.env.ANTHROPIC_API_KEY!, // (optional) Direct mode (BYOK)
        // oauthToken: process.env.CLAUDE_CODE_OAUTH_TOKEN!, // (optional) Claude Max subscription
    })

    // Sandbox provider (auto-resolved from E2B_API_KEY, or use sandbox from above)
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

    // (optional) Uploads to {workingDir}/context/ on first run
    .withContext({
        "docs/readme.txt": "User provided context...",
        "data.json": JSON.stringify({ key: "value" }),
    })

    // (optional) Uploads to {workingDir}/ on first run
    .withFiles({
        "scripts/setup.sh": "#!/bin/bash\necho hello",
    })

    // (optional) MCP servers for agent tools
    .withMcpServers({
        "exa": {
            command: "npx",
            args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
            env: { EXA_API_KEY: process.env.EXA_API_KEY! }
        }
    })

    // (optional) Schema for structured output (agent writes result.json, validated on getOutputFiles())
    // Accepts Zod schemas or JSON Schema objects
    .withSchema(z.object({
        summary: z.string(),
        score: z.number(),
    }));

    // Or with JSON Schema:
    // .withSchema({
    //     type: "object",
    //     properties: {
    //         summary: { type: "string" },
    //         score: { type: "number" },
    //     },
    //     required: ["summary", "score"],
    // });
```

**Note:**
- Configuration methods can be chained in any order.
- The sandbox is created on the first `run()` or `executeCommand()` call (see below).
- Context files, workspace files, MCP servers, and system prompt are set up once on the first call.
- Using `.withSession()` to reconnect skips setup since the sandbox already exists.
- `withSchema()` accepts both Zod schemas and JSON Schema objects.

**McpServerConfig** — MCP server connection (STDIO or HTTP/SSE):
```ts
{ command?: string, args?: string[], env?: Record<string, string>, url?: string }  // STDIO: command+args, HTTP: url
```

---

## 3. Runtime Methods

All runtime calls are `async` and return a shared `AgentResponse`:

```ts
type AgentResponse = {
  sandboxId: string;
  exitCode: number;
  stdout: string;
  stderr: string;
};
```

### 3.1 run

Runs the agent with a given prompt. 

```ts
const result = await swarmkit.run({
    prompt: "Analyze the data and create a report",
    timeoutMs: 15 * 60 * 1000,                // (optional) Default 1 hour
    background: false,                         // (optional) Run in background
});

console.log(result.exitCode);
console.log(result.stdout);
```

- If `timeoutMs` is omitted the agent uses the TypeScript default of 3_600_000 ms (1 hour).
- If `background` is `true`, the call returns immediately while the agent continues running.

- Calling `run()` multiple times maintains the agent context / history. 

### 3.2 executeCommand

Runs a direct shell command in the sandbox working directory.

```ts
// Run shell command directly in sandbox
const result = await swarmkit.executeCommand("pytest", {
    timeoutMs: 10 * 60 * 1000,                // (optional) Default 1 hour
    background: false,                         // (optional) Run in background
});
```
- The command automatically executes in the directory set by `withWorkingDirectory()` (default: `/home/user/workspace`).

### 3.3 Streaming events

`SwarmKit` extends Node's `EventEmitter`. Both `run()` and `executeCommand()` stream output in real-time:

```ts
// Raw output
swarmkit.on("stdout", chunk => process.stdout.write(chunk));
swarmkit.on("stderr", chunk => process.stderr.write(chunk));

// Parsed output (recommended)
swarmkit.on("content", event => console.log(event.update));
```

**Events**:

| Event | Description |
|-------|-------------|
| `content` | Parsed ACP-style events (recommended) |
| `stdout` | Raw JSONL output |
| `stderr` | Stderr chunks |

**Content event structure** (`event.update`):

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

When building interactive CLI applications with streaming, use a **stateful renderer class** with callbacks. The recommended pattern uses a live-updating status area for tool calls while printing messages directly:

```ts
import logUpdate from "log-update";

interface ToolInfo {
  title: string;
  kind: string;
  status: string;
  rawInput: Record<string, unknown>;
}

interface PlanEntry {
  status: string;
  content: string;
  priority?: string;  // "high" | "medium" | "low"
}

class StreamRenderer {
  private currentMessage = "";
  private thoughtBuffer = "";
  private tools: Map<string, ToolInfo> = new Map();
  private toolOrder: string[] = [];
  private planEntries: PlanEntry[] = [];
  private isLive = false;

  reset(): void {
    this.stopLive();
    this.currentMessage = "";
    this.thoughtBuffer = "";
    this.tools.clear();
    this.toolOrder = [];
    this.planEntries = [];
  }

  handleEvent(event: { update?: Record<string, unknown> }): void {
    const update = event.update ?? {};
    const eventType = update.sessionUpdate as string | undefined;

    if (eventType === "agent_message_chunk") {
      const content = update.content as Record<string, unknown> | undefined;
      if (content?.type === "text") {
        this.currentMessage += (content.text as string) ?? "";
      }

    } else if (eventType === "agent_thought_chunk") {
      // Reasoning/thinking from Codex or Claude
      const content = update.content as Record<string, unknown> | undefined;
      if (content?.type === "text") {
        this.thoughtBuffer += (content.text as string) ?? "";
      }

    } else if (eventType === "tool_call") {
      this.flushMessage(); // Print message before tool
      const toolId = (update.toolCallId as string) ?? "";
      if (!this.tools.has(toolId)) {
        this.toolOrder.push(toolId);
      }
      this.tools.set(toolId, {
        title: (update.title as string) ?? "Tool",
        kind: (update.kind as string) ?? "other", // read, edit, search, execute, think, fetch, switch_mode, other
        status: (update.status as string) ?? "pending",
        rawInput: (update.rawInput as Record<string, unknown>) ?? {},
      });
      this.refreshStatus();

    } else if (eventType === "tool_call_update") {
      const toolId = (update.toolCallId as string) ?? "";
      // Handle out-of-order: update may arrive before tool_call
      if (!this.tools.has(toolId)) {
        this.toolOrder.push(toolId);
        this.tools.set(toolId, {
          title: (update.title as string) ?? "Tool",
          kind: "other",
          status: "pending",
          rawInput: {},
        });
      }
      const tool = this.tools.get(toolId)!;
      tool.status = (update.status as string) ?? "completed";
      this.refreshStatus();

    } else if (eventType === "plan") {
      // TodoWrite updates - list of {content, status, priority}
      this.flushMessage();
      this.planEntries = (update.entries as PlanEntry[]) ?? [];
      this.renderPlan();
    }
  }

  private flushMessage(): void {
    if (this.currentMessage.trim()) {
      this.clearLive();
      console.log(this.currentMessage.trim());
      console.log();
      this.currentMessage = "";
      this.startLive();
    }
  }

  private renderPlan(): void {
    if (this.planEntries.length === 0) return;
    this.clearLive();
    for (const entry of this.planEntries) {
      const status = entry.status ?? "pending";
      const content = entry.content ?? "";
      const icon = { completed: "✓", in_progress: "→", pending: "○" }[status] ?? "○";
      console.log(`${icon} ${content}`);
    }
    console.log();
    this.startLive();
  }

  private renderStatus(): string {
    const lines: string[] = [];
    for (const toolId of this.toolOrder) {
      const tool = this.tools.get(toolId)!;
      const dot = tool.status === "completed" ? "●" : tool.status === "failed" ? "●" : "●";
      lines.push(`${dot} ${tool.title}`);
    }
    lines.push("⠋ Working...");
    return lines.join("\n");
  }

  private refreshStatus(): void {
    if (this.isLive) {
      logUpdate(this.renderStatus());
    }
  }

  private clearLive(): void {
    if (this.isLive) {
      logUpdate("");
      logUpdate.done();
      this.isLive = false;
    }
  }

  startLive(): void {
    this.isLive = true;
    this.refreshStatus();
  }

  stopLive(): void {
    this.clearLive();
    this.flushMessage();
    // Optionally display collected thoughts
    if (this.thoughtBuffer.trim()) {
      console.log("Reasoning:");
      console.log(this.thoughtBuffer);
    }
  }
}

// Usage:
const renderer = new StreamRenderer();
swarmkit.on("content", (event) => renderer.handleEvent(event));

renderer.reset();
renderer.startLive();
await swarmkit.run({ prompt: "Your task here" });
renderer.stopLive();
```

**Key patterns:**

1. **Handle all 5 event types** - `agent_message_chunk`, `agent_thought_chunk`, `tool_call`, `tool_call_update`, `plan`
2. **Flush messages before tools/plan** - Preserves correct interleaving order
3. **Track tools by ID** - `tool_call` (start) and `tool_call_update` (end) share `toolCallId`
4. **Handle out-of-order updates** - `tool_call_update` may arrive before `tool_call`
5. **Use `kind` for tool categorization** - `read`, `edit`, `search`, `execute`, `think`, `fetch`, `switch_mode`, `other`

> **Full production example:** See [`cookbooks/agent-typescript/ui.ts`](../cookbooks/agent-typescript/ui.ts) for styled formatting with chalk, markdown rendering, spinner animations, and advanced live output management.

### 3.4 Upload: Local → Sandbox

**Format:** `{ "destination": content }` — directories created automatically

| Method | Destination |
|--------|-------------|
| `uploadContext()` | `context/{path}` |
| `uploadFiles()` | `{workingDir}/{path}` |

```ts
// Single file
await swarmkit.uploadContext({ "spec.json": JSON.stringify(data) });

// Multiple files
await swarmkit.uploadFiles({
  "scripts/setup.sh": "#!/bin/bash\necho hello",
  "data/input.csv": csvBuffer,
});

// From local directory (helper)
import { readLocalDir } from "@swarmkit/sdk";
await swarmkit.uploadContext(readLocalDir("./input", true));
```

> **Setup alternative:** `withContext()` and `withFiles()` use the same format but upload on first `run()` instead of immediately.

### 3.5 Download: Sandbox → Local

**Flow:** `getOutputFiles()` → `saveLocalDir()`

```ts
// Return type
interface OutputResult<T = unknown> {
    files: FileMap;      // All files from output/ folder
    data: T | null;      // Parsed result.json (if schema was set via withSchema())
    error?: string;      // Validation error message (if schema validation failed)
    rawData?: string;    // Raw result.json content when parse/validation failed (for debugging)
}
```

```ts
import { z } from "zod";
import { saveLocalDir } from "@swarmkit/sdk";

const ResultSchema = z.object({
    summary: z.string(),
    score: z.number(),
});

const swarmkit = new SwarmKit()
    .withAgent({...})
    .withSchema(ResultSchema);  // Agent will be prompted to write result.json

await swarmkit.run({ prompt: "Analyze and score the document" });

const output = await swarmkit.getOutputFiles(true);  // recursive=true for nested dirs

// Access all three fields
saveLocalDir("./output", output.files);  // Save files locally
console.log(output.data);                 // { summary: "...", score: 85 }
console.log(output.error);                // undefined (or validation error message)
```

- **`files`** — `FileMap` of all files from `output/` folder
- **`data`** — Parsed `result.json` validated against schema (null if no schema or validation failed)
- **`error`** — Validation error message if schema validation failed (undefined otherwise)

Files created before the last `run()` or `executeCommand()` are filtered out.

### 3.6 Session controls

```ts
const sessionId = swarmkit.getSession();  // Returns sandbox ID (string) or null (sync)

await swarmkit.pause();  // Suspends sandbox (stops billing, preserves state)
await swarmkit.resume(); // Reactivates same sandbox

await swarmkit.kill();   // Destroys sandbox; next run() creates a new sandbox

await swarmkit.setSession("existing-sandbox-id"); // Sets sandbox ID; reconnection happens on next run()
```

`withSession("sandbox-id")` is a builder method equivalent to `setSession()` - use it during initialization to reconnect to an existing sandbox.

### 3.7 getHost

Expose a forwarded port:

```ts
const url = await swarmkit.getHost(8000);
console.log(`Workspace service available at ${url}`);
```
---

## 4. Workspace setup and Modes

### 4.1 Knowledge Mode (default)

Ideal for knowledge work applications.
```ts
swarmkit.withWorkspaceMode("knowledge"); // implicit default
```

Calling `run` or `executeCommand` for the first time provisions the workspace:

```
/home/user/workspace/
├── context/   # Input files (read-only) provided by the user
├── scripts/   # Your code goes here
├── temp/      # Scratch space
└── output/    # Final deliverables
```
Files passed to `withContext()` are uploaded to `context/`. Files passed to `withFiles()` are uploaded relative to the working directory.

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

Any string passed to `withSystemPrompt()` is appended after this default.


### 4.2 SWE Mode

Ideal for coding applications (when working with repositories).
```ts
swarmkit.withWorkspaceMode("swe");
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

The workspace prompt is automatically written with the `repo/` folder included. All other features (`withSystemPrompt`, `withContext`, `withFiles`, etc.) work the same as knowledge mode.


---

## 5. Cleaning up and session management

**Multi-turn conversations** (most common):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...});

await swarmkit.run({ prompt: 'Analyze data.csv' });
const output1 = await swarmkit.getOutputFiles();

// Still same session, automatically maintains context / history
await swarmkit.run({ prompt: 'Now create visualization' });
const output2 = await swarmkit.getOutputFiles();

// Still same session, automatically maintains context / history
await swarmkit.run({ prompt: 'Export to PDF' });
const output3 = await swarmkit.getOutputFiles();

await swarmkit.kill();  // When done
```

**Pause and resume** (same instance):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...});

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
  .withAgent({...});

await swarmkit.run({ prompt: 'Start analysis' });

const sessionId = swarmkit.getSession();
// Save to file, database, environment variable, etc.
fs.writeFileSync('session.txt', sessionId);

// Script 2: Reconnect to saved session
const savedId = fs.readFileSync('session.txt', 'utf-8');

const swarmkit2 = new SwarmKit()
  .withAgent({...})
  .withSession(savedId);  // Reconnect

await swarmkit2.run({ prompt: 'Continue analysis' });  // Session continues from Script 1
```

**Switch between sandboxes** (same instance):

```ts
const swarmkit = new SwarmKit()
  .withAgent({...});

// Work with first sandbox
await swarmkit.run({ prompt: 'Analyze dataset A' });
const sessionA = swarmkit.getSession();

// Switch to different sandbox
await swarmkit.setSession('existing-sandbox-b-id');
await swarmkit.run({ prompt: 'Analyze dataset B' });  // Now working with sandbox B

// Switch back to first sandbox
await swarmkit.setSession(sessionA);
await swarmkit.run({ prompt: 'Compare results' });  // Back to sandbox A
```

---

## 6. Observability

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

```ts
const swarmkit = new SwarmKit()
  .withAgent({...})
  .withSessionTagPrefix("my-project");

await swarmkit.run({ prompt: "Kick off analysis" });

console.log(swarmkit.getSessionTag());        // "my-project-ab12cd34"
console.log(swarmkit.getSessionTimestamp()); // Timestamp for first log file

await swarmkit.kill();                              // Flushes log file for sandbox A

await swarmkit.run({ prompt: "Start fresh" });      // New sandbox → new log file

console.log(swarmkit.getSessionTag());        // "my-project-f56789cd"
console.log(swarmkit.getSessionTimestamp()); // Timestamp for second log file
```

- `kill()` or `setSession()` flushes the current log; the next `run()` starts a
  fresh file with the new sandbox id.
- Long-running sessions (pause/resume or ACP auto-resume) keep appending to the
  current file, so you always have the full timeline.
- Logging is buffered inside the SDK, so it never blocks streaming output.

Use the tag together with the sandbox id to correlate logs with files saved in
`/output/`.

---

# Swarm Abstractions

Functional programming for AI agents: `map`, `filter`, `reduce`, `bestOf`.

```ts
import { Swarm } from "@swarmkit/sdk";
import { z } from "zod";  // Or use plain JSON Schema objects instead

const agent = { type: "claude" };

const swarm = new Swarm({
    agent,                       // Default agent for all operations
    concurrency: 4,              // Max parallel sandboxes (default: 4)
    timeoutMs: 3_600_000,        // Default timeout per worker (default: 1 hour)
    tag: "my-pipeline",          // Tag prefix for observability
    workspaceMode: "knowledge",  // "knowledge" (default) or "swe"
    mcpServers: {...},           // Default MCP servers for all workers
    retry: {                     // Default retry config for all operations
        maxAttempts: 3,
        backoffMs: 1000,
        backoffMultiplier: 2,
    },
});
```

> **Defaults**: `agent`, `timeoutMs`, `mcpServers`, and `retry` set here are inherited by all operations (`map`, `filter`, `reduce`, `bestOf`). Pass these options to individual operations to override.

| Option | Default | Notes |
|--------|---------|-------|
| `agent.type` | `'claude'` | Auto-resolved from env |
| `agent.model` | per type | `'opus'` (claude), `'gpt-5.2'` (codex), etc. |
| `concurrency` | `4` | Max parallel sandboxes |
| `timeoutMs` | `3_600_000` | 1 hour per worker |
| `workspaceMode` | `'knowledge'` | or `'swe'` |
| `tag` | `'swarm'` | Observability prefix |
| `retry` | `undefined` | Set here or per-operation |
| `verify` | `undefined` | Per-operation only |
| `mcpServers` | `undefined` | Set here or per-operation |

**Minimal setup** — with `SWARMKIT_API_KEY` set (see [1.1 Authentication](#11-authentication)):

```ts
import "dotenv/config";  // If using .env file
import { Swarm } from "@swarmkit/sdk";

const swarm = new Swarm();  // Auto-resolves agent (claude) and sandbox from env
```

**RetryConfig** — auto-retry on error with exponential backoff:
```ts
{ maxAttempts?: number, backoffMs?: number, backoffMultiplier?: number, retryOn?: (r) => boolean, onItemRetry?: (idx, attempt, error) => void }
```

**VerifyConfig** — LLM-as-judge verifies output, retries with feedback if failed:
```ts
{ criteria: string, maxAttempts?: number, verifierAgent?: AgentOverride, onWorkerComplete?: (idx, attempt, status) => void, onVerifierComplete?: (idx, attempt, passed, feedback?) => void }
```

## 1. Input Types

Swarm runs in **knowledge mode** by default—files are uploaded to `context/` in the sandbox.

**FileMap structure:**

```ts
// FileMap: Record<path, content>
//   - path: string              → file path in context/ folder
//   - content: string | Uint8Array  → file content

type FileMap = Record<string, string | Uint8Array>;
```

---

**Case 1: One file per worker**

```ts
// 3 workers, each gets 1 file
const items: FileMap[] = [
    { "report.txt": "Q1 revenue..." },      // → Worker 0: context/report.txt
    { "report.txt": "Q2 revenue..." },      // → Worker 1: context/report.txt
    { "report.txt": "Q3 revenue..." },      // → Worker 2: context/report.txt
];

const results = await swarm.map({
    items,
    prompt: "Summarize this report",
});
```

---

**Case 2: Multiple files per worker**

```ts
// 3 workers, each gets 2 files
const items: FileMap[] = [
    {                                       // → Worker 0:
        "doc1.pdf": fs.readFileSync("./doc1.pdf"),  //   context/doc1.pdf
        "doc2.pdf": fs.readFileSync("./doc2.pdf"),  //   context/doc2.pdf
    },
    {                                       // → Worker 1:
        "doc3.pdf": fs.readFileSync("./doc3.pdf"),  //   context/doc3.pdf
        "doc4.pdf": fs.readFileSync("./doc4.pdf"),  //   context/doc4.pdf
    },
    {                                       // → Worker 2:
        "doc5.pdf": fs.readFileSync("./doc5.pdf"),  //   context/doc5.pdf
        "doc6.pdf": fs.readFileSync("./doc6.pdf"),  //   context/doc6.pdf
    },
];

const results = await swarm.map({
    items,
    prompt: "Compare these two documents",
});
```

---

**Case 3: Entire folder per worker**

```ts
import { readLocalDir } from "@swarmkit/sdk";

// readLocalDir(path, recursive) → returns FileMap with all files
const items: FileMap[] = [
    readLocalDir("./project-a", true),      // → Worker 0: all files from project-a (recursive)
    readLocalDir("./project-b", true),      // → Worker 1: all files from project-b (recursive)
    readLocalDir("./project-c", true),      // → Worker 2: all files from project-c (recursive)
];

const results = await swarm.map({
    items,
    prompt: "Review this codebase",
});
```

## 2. Abstractions

Two types of operations:

| Operation | Type | Description | Passes On |
|-----------|------|-------------|-----------|
| `bestOf` | transform + select | `input` → `output` (best of N candidates) | winner output |
| `map` | transform | `input` → `output` (agent produces new data) | agent output |
| `filter` | gate | `input` → `input` (agent evaluates, condition decides) | original input + status (`success` \| `filtered`) |
| `reduce` | transform | `inputs` → `output` (agent synthesizes) | agent output |

**Transforms** produce new output files. **Filter** passes through original input files unchanged.

### 2.1 bestOf

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

```ts
// Signature
swarm.bestOf<T>({
    item: FileMap | SwarmResult,
    prompt: string,
    config: BestOfConfig,               // { n?, judgeCriteria, taskAgents?, judgeAgent?, onCandidateComplete?, onJudgeComplete? }
    name?: string,                      // Operation name for observability (appears in meta.operationName)
    schema?: z.ZodType<T> | JsonSchema,
    systemPrompt?: string,
    retry?: RetryConfig,                // Per-candidate retry (judge uses default)
    timeoutMs?: number,
}): Promise<BestOfResult<T>>
```

```ts
const input = { "task.txt": "Complex problem..." };

const result = await swarm.bestOf({
    item: input,
    prompt: "Solve this problem",
    config: {
        n: 3,
        judgeCriteria: "Most accurate and well-explained solution",
        onCandidateComplete: (idx, candIdx, status) => console.log(`Candidate ${candIdx}: ${status}`),
        onJudgeComplete: (idx, winnerIdx, reasoning) => console.log(`Winner: ${winnerIdx}`),
    },
});

console.log(result.winner);         // Best SwarmResult
console.log(result.winnerIndex);    // 0, 1, or 2
console.log(result.judgeReasoning); // Why this was chosen
console.log(result.candidates);     // All candidate results
```

Use different agents per candidate:

```ts
const claudeAgent = { type: "claude", model: "opus" };
const codexAgent = { type: "codex", model: "gpt-5.2-codex" };
const geminiAgent = { type: "gemini", model: "gemini-3-flash" };

const result = await swarm.bestOf({
    item: input,
    prompt: "Solve this",
    config: {
        taskAgents: [claudeAgent, codexAgent, geminiAgent],
        judgeCriteria: "Best solution quality",
        judgeAgent: claudeAgent,
        mcpServers: {...},        // (optional) MCP servers for candidates
        judgeMcpServers: {...},   // (optional) MCP servers for judge
    },
});
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

```ts
// Signature (schema accepts Zod or JSON Schema object)
swarm.map<T>({
    items: FileMap[] | SwarmResult[],
    prompt: string | ((files: FileMap, index: number) => string),
    name?: string,                      // Operation name for observability (appears in meta.operationName)
    schema?: z.ZodType<T> | JsonSchema,
    systemPrompt?: string,
    agent?: AgentOverride,
    bestOf?: BestOfConfig,              // N candidates + judge (mutually exclusive with verify)
    verify?: VerifyConfig,              // LLM-as-judge quality check with retry loop
    retry?: RetryConfig,                // Auto-retry on error with backoff
    mcpServers?: Record<string, McpServerConfig>,
    timeoutMs?: number,
}): Promise<SwarmResultList<T>>
```

```ts
// Basic
const results = await swarm.map({
    items: documents,
    prompt: "Summarize this document",
});
```

When `schema` is provided, a structured output prompt is automatically embedded—instructing the agent to write `output/result.json` matching the schema.

```ts
// With Zod schema
const SummarySchema = z.object({
    title: z.string(),
    keyPoints: z.array(z.string()),
});

const results = await swarm.map({
    items: documents,
    prompt: "Extract summary",
    schema: SummarySchema,
});

// Or with JSON Schema
const SummaryJsonSchema = {
    type: "object",
    properties: {
        title: { type: "string" },
        keyPoints: { type: "array", items: { type: "string" } },
    },
    required: ["title", "keyPoints"],
};

const results = await swarm.map({
    items: documents,
    prompt: "Extract summary",
    schema: SummaryJsonSchema,
});

// With dynamic prompt
const results = await swarm.map({
    items: documents,
    prompt: (files, index) => `Analyze document ${index + 1}: focus on revenue`,
});

// Access results
for (const r of results) {
    if (r.status === "success") {
        console.log(r.data);   // Parsed schema or FileMap
        console.log(r.files);  // Output files from agent
    }
}
```

### 2.3 map with bestOf

Combine map parallelism with bestOf quality:

```ts
const AnalysisSchema = z.object({
    findings: z.array(z.string()),
    confidence: z.number(),
});

// Each item gets N candidates, judge picks best per item
const results = await swarm.map({
    items: documents,
    prompt: "Analyze thoroughly",
    schema: AnalysisSchema,
    bestOf: {
        n: 3,
        judgeCriteria: "Most comprehensive analysis",
        // taskAgents?: AgentOverride[],     // Different agent per candidate
        // judgeAgent?: AgentOverride,       // Override judge agent
        // mcpServers?: {...},               // MCP servers for candidates
        // judgeMcpServers?: {...},          // MCP servers for judge
    },
});

// Results contain only winners (one per input item)
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

```ts
// Signature (schema accepts Zod or JSON Schema object)
swarm.filter<T>({
    items: FileMap[] | SwarmResult[],
    prompt: string,           // Describe what to assess (agent outputs result.json)
    name?: string,                      // Operation name for observability (appears in meta.operationName)
    schema: z.ZodType<T> | JsonSchema,  // Required - defines evaluation output structure
    condition: (data: T) => boolean,    // Local function applies threshold
    systemPrompt?: string,
    agent?: AgentOverride,
    verify?: VerifyConfig,              // LLM-as-judge quality check with retry loop
    retry?: RetryConfig,                // Auto-retry on error with backoff
    mcpServers?: Record<string, McpServerConfig>,
    timeoutMs?: number,
}): Promise<SwarmResultList<T>>
```

```ts
const EvalSchema = z.object({
    severity: z.enum(["critical", "warning", "info"]),
    score: z.number(),
});

const results = await swarm.filter({
    items: documents,
    prompt: "Assess the severity of issues in this document",  // Agent evaluates
    schema: EvalSchema,
    condition: (data) => data.severity === "critical",  // Code applies threshold
});

// Three possible statuses:
results.success;   // Passed condition
results.filtered;  // Evaluated but didn't pass
results.error;     // Agent error

// Chain to next step
await swarm.reduce({
    items: results.success,
    prompt: "Summarize critical issues",
});
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

```ts
// Signature (schema accepts Zod or JSON Schema object)
swarm.reduce<T>({
    items: FileMap[] | SwarmResult[],
    prompt: string,
    name?: string,                      // Operation name for observability (appears in meta.operationName)
    schema?: z.ZodType<T> | JsonSchema,
    systemPrompt?: string,
    agent?: AgentOverride,
    verify?: VerifyConfig,              // LLM-as-judge quality check with retry loop
    retry?: RetryConfig,                // Auto-retry on error with backoff
    mcpServers?: Record<string, McpServerConfig>,
    timeoutMs?: number,
}): Promise<ReduceResult<T>>
```

```ts
// Agent sees: item_0/, item_1/, item_2/, etc.
const report = await swarm.reduce({
    items: results.success,
    prompt: "Create a unified report from all analyses",
});

if (report.status === "success") {
    console.log(report.files);  // Final output files
    console.log(report.data);   // Parsed schema if provided
}

// With schema
const ReportSchema = z.object({
    summary: z.string(),
    recommendations: z.array(z.string()),
});

const report = await swarm.reduce({
    items,
    prompt: "Create report",
    schema: ReportSchema,
});
```

## 3. Result Types

```ts
// SwarmResult<T> - from map, filter, bestOf candidates
interface SwarmResult<T> {
    status: "success" | "filtered" | "error";
    data: T | null;      // Parsed schema, or null on error
    files: FileMap;      // Output files (map/bestOf) or input files (filter)
    meta: IndexedMeta;   // { operationId, operation, tag, sandboxId, itemIndex }
    error?: string;      // Error message if status === "error"
    rawData?: string;    // Raw result.json when parse/validation failed (for debugging)
    bestOf?: {           // Present when map used bestOf option
        winnerIndex: number;
        judgeReasoning: string;
        judgeMeta: JudgeMeta;   // { operationId, operation, tag, sandboxId, candidateCount }
        candidates: SwarmResult<T>[];
    };
    verify?: VerifyInfo; // Present when verify option was used
}

// SwarmResultList<T> - from map, filter (extends Array)
results.success;   // SwarmResult[] with status "success"
results.filtered;  // SwarmResult[] with status "filtered"
results.error;     // SwarmResult[] with status "error"

// ReduceResult<T> - from reduce
interface ReduceResult<T> {
    status: "success" | "error";
    data: T | null;
    files: FileMap;
    meta: ReduceMeta;   // { operationId, operation, tag, sandboxId, inputCount, inputIndices }
    error?: string;
    rawData?: string;   // Raw result.json when parse/validation failed (for debugging)
    verify?: VerifyInfo; // Present when verify option was used
}

// VerifyInfo - verification outcome
interface VerifyInfo {
    passed: boolean;        // Final verification status
    reasoning: string;      // Verifier's reasoning
    verifyMeta: VerifyMeta; // { operationId, operation, tag, sandboxId, attempts }
    attempts: number;       // Total attempts made
}

// BestOfResult<T> - from bestOf
interface BestOfResult<T> {
    winner: SwarmResult<T>;
    winnerIndex: number;
    judgeReasoning: string;
    judgeMeta: JudgeMeta;   // { operationId, operation, tag, sandboxId, candidateCount }
    candidates: SwarmResult<T>[];
}
```

## 4. Chaining Operations

When chaining Swarm operations, `result.json` from a previous step is automatically renamed to `data.json`. This avoids confusion when the downstream agent writes its own `result.json`. This also applies to [Pipeline](#7-pipeline).

**Example: map → reduce chain**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MAP (parallel)                                                             │
│                                                                             │
│  item_0 agent writes:          item_1 agent writes:                         │
│  output/                       output/                                      │
│    result.json ← schema        result.json ← schema                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  REDUCE (single agent)                                                      │
│                                                                             │
│  context/                                                                   │
│    item_0/                                                                  │
│      data.json      ← renamed from result.json                              │
│    item_1/                                                                  │
│      data.json      ← renamed from result.json                              │
│  output/                                                                    │
│    result.json      ← reduce agent writes its own                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```ts
const AnalysisSchema = z.object({ summary: z.string() });
const SeveritySchema = z.object({ severity: z.enum(["critical", "warning", "info"]) });

// Full pipeline: map → filter → reduce
const analyzed = await swarm.map({
    items: documents,
    prompt: "Analyze",
    schema: AnalysisSchema,
});

const critical = await swarm.filter({
    items: analyzed.success,
    prompt: "Evaluate severity",
    schema: SeveritySchema,
    condition: (d) => d.severity === "critical",
});

const report = await swarm.reduce({
    items: critical.success,
    prompt: "Create summary report",
});

// Combine success and filtered
const allEvaluated = [...critical.success, ...critical.filtered];
await swarm.reduce({
    items: allEvaluated,
    prompt: "Summarize all evaluated items",
});
```

## 5. AgentOverride

Override the default agent for any operation (apiKey inherited from Swarm config):

```ts
interface AgentOverride {
    type: "claude" | "codex" | "gemini" | "qwen";
    model?: string;
    reasoningEffort?: "low" | "medium" | "high" | "xhigh";  // Codex only
    betas?: string[];  // Claude only
}
```

```ts
const codexAgent: AgentOverride = {
    type: "codex",
    reasoningEffort: "high",
};

const results = await swarm.map({
    items,
    prompt: "Analyze",
    agent: codexAgent,
});
```

## 6. Concurrency

Global semaphore limits parallel sandboxes across all operations.

```ts
const swarm = new Swarm({
    agent,
    sandbox,
    concurrency: 4,  // Max 4 sandboxes at once (default: 4)
});

// map(10) with bestOf(5) = 60 agent calls, but only 4 run at any time
```

**Ordering guarantees:**
- `bestOf`: Judge runs only after all candidates complete
- `map` → `filter` → `reduce`: Each phase completes before next starts
- Within a phase: Items run in parallel (up to concurrency limit)

---

## 7. Pipeline

Fluent wrapper over Swarm for chaining operations. **All Swarm features work in Pipeline steps** — `schema`, `bestOf`, `verify`, `retry`, `agent`, `mcpServers`, dynamic prompts.

```ts
import "dotenv/config";
import { Swarm, Pipeline } from "@swarmkit/sdk";

const swarm = new Swarm();  // See Swarm Abstractions for full config

const pipeline = new Pipeline(swarm)
    .map({
        name: "analyze",
        prompt: "Analyze...",
        schema: AnalysisSchema,
    })
    .filter({
        name: "critical",
        prompt: "Rate...",
        schema: SeveritySchema,
        condition: d => d.severity === "critical",
    })
    .reduce({
        name: "report",
        prompt: "Summarize...",
    });

// Reusable — run with different data
const result1 = await pipeline.run(batch1);
const result2 = await pipeline.run(batch2);
```

### Step Configurations

Each step accepts the same options as the corresponding Swarm method, plus `name` for observability:

```ts
// Map step — same as swarm.map() + name
.map<T>({
    name?: string,                        // Step name (appears in events)
    prompt: string | ((files, idx) => string),
    schema?: z.ZodType<T> | JsonSchema,
    bestOf?: BestOfConfig,                // N candidates + judge
    verify?: VerifyConfig,                // LLM-as-judge quality check
    retry?: RetryConfig,                  // Auto-retry on error
    agent?: AgentOverride,
    mcpServers?: Record<string, McpServerConfig>,
    systemPrompt?: string,
    timeoutMs?: number,
})

// Filter step — same as swarm.filter() + name + emit
.filter<T>({
    name?: string,
    prompt: string,
    schema: z.ZodType<T> | JsonSchema,    // Required
    condition: (data: T) => boolean,      // Required
    emit?: "success" | "filtered" | "all",  // What passes to next step (default: "success")
    verify?: VerifyConfig,
    retry?: RetryConfig,
    agent?: AgentOverride,
    mcpServers?: Record<string, McpServerConfig>,
    systemPrompt?: string,
    timeoutMs?: number,
})

// Reduce step — same as swarm.reduce() + name (terminal: no steps after)
.reduce<T>({
    name?: string,
    prompt: string,
    schema?: z.ZodType<T> | JsonSchema,
    verify?: VerifyConfig,
    retry?: RetryConfig,
    agent?: AgentOverride,
    mcpServers?: Record<string, McpServerConfig>,
    systemPrompt?: string,
    timeoutMs?: number,
})
```

### Full Example

```ts
const pipeline = new Pipeline(swarm)

    .map({
        name: "analyze",
        prompt: (files, idx) => `Analyze document ${idx + 1}`,
        schema: AnalysisSchema,
        bestOf: {
            n: 3,
            judgeCriteria: "Most thorough analysis",
        },
        retry: { maxAttempts: 2 },
        agent: { type: "claude", model: "opus" },
    })

    .filter({
        name: "quality-gate",
        prompt: "Rate the analysis quality",
        schema: z.object({
            score: z.number(),
            reasoning: z.string(),
        }),
        condition: d => d.score >= 8,
        emit: "success",                  // Only high-quality pass through
        verify: {
            criteria: "Rating must be justified with specific examples",
        },
    })

    .reduce({
        name: "synthesize",
        prompt: "Create executive summary from all analyses",
        schema: ReportSchema,
        verify: {
            criteria: "Summary must cover all key findings",
        },
    })

    .on("stepComplete", e => {
        console.log(`${e.name}: ${e.successCount}/${e.successCount + e.errorCount}`);
    });

const result = await pipeline.run(documents);
```

### Events

Pipeline unifies all Swarm callbacks at the pipeline level, adding `stepIndex` and `stepName`:

```ts
pipeline
    .on("stepStart", e => {
        console.log(`Step ${e.index} started with ${e.itemCount} items`);
    })
    .on("stepComplete", e => {
        console.log(`Step ${e.index} done in ${e.durationMs}ms`);
    })
    .on("stepError", e => {
        console.error(`Step ${e.index} failed:`, e.error);
    });

// Or object style
pipeline.on({
    onStepComplete: e => console.log(`${e.name}: ${e.successCount} success`),
    onItemRetry: e => console.log(`Retry: step ${e.stepIndex}, item ${e.itemIndex}`),
    onVerifierComplete: e => console.log(`Verify: ${e.passed ? "PASS" : e.feedback}`),
});
```

| Event | Fields |
|-------|--------|
| `stepStart` | `type`, `index`, `name?`, `itemCount` |
| `stepComplete` | `type`, `index`, `name?`, `durationMs`, `successCount`, `errorCount`, `filteredCount` |
| `stepError` | `type`, `index`, `name?`, `error` |
| `itemRetry` | `stepIndex`, `stepName?`, `itemIndex`, `attempt`, `error` |
| `workerComplete` | `stepIndex`, `stepName?`, `itemIndex`, `attempt`, `status` |
| `verifierComplete` | `stepIndex`, `stepName?`, `itemIndex`, `attempt`, `passed`, `feedback?` |
| `candidateComplete` | `stepIndex`, `stepName?`, `itemIndex`, `candidateIndex`, `status` |
| `judgeComplete` | `stepIndex`, `stepName?`, `itemIndex`, `winnerIndex`, `reasoning` |

### Result

```ts
interface PipelineResult<T> {
  pipelineRunId: string;
  steps: StepResult[];        // { type, index, durationMs, results }
  output: SwarmResult<T>[] | ReduceResult<T>;
  totalDurationMs: number;
}

// Access step results
for (const step of result.steps) {
  console.log(`${step.type} took ${step.durationMs}ms`);
}
```

### Terminal Pipeline

After `.reduce()`, no more steps can be added (returns `TerminalPipeline`):

```ts
const terminal = pipeline.reduce({ prompt: "..." });
terminal.map({ prompt: "..." });  // Throws: "Cannot add steps after reduce"
```

---
