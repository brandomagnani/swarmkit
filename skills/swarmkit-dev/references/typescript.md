# TypeScript SDK Reference

## Table of Contents
- [Installation](#installation)
- [SwarmKit](#swarmkit)
- [Skills](#skills)
- [Composio](#composio)
- [Swarm](#swarm)
- [Pipeline](#pipeline)
- [Types](#types)

---

## Installation

```bash
npm install @swarmkit/sdk
```

## SwarmKit

### Basic Setup

```ts
import { SwarmKit } from "@swarmkit/sdk";

const swarmkit = new SwarmKit()
    .withAgent({ type: "claude" })
    .withSkills(["pdf", "dev-browser"])
    .withComposio("user_123", { toolkits: ["github", "gmail"] });

await swarmkit.run({ prompt: "Analyze this document" });
const output = await swarmkit.getOutputFiles();
await swarmkit.kill();
```

### Full Configuration

```ts
import { SwarmKit, E2BProvider } from "@swarmkit/sdk";
import { z } from "zod";

const sandbox = new E2BProvider({
    apiKey: process.env.E2B_API_KEY,
    defaultTimeoutMs: 3600000,
});

const swarmkit = new SwarmKit()
    .withAgent({
        type: "codex",
        model: "gpt-5.2-codex",
        reasoningEffort: "high",
        apiKey: process.env.SWARMKIT_API_KEY,
    })
    .withSandbox(sandbox)
    .withContext({ "docs/readme.txt": "Context content..." })
    .withFiles({ "scripts/setup.sh": "#!/bin/bash\necho hello" })
    .withSystemPrompt("You are a careful pair programmer.")
    .withSchema(z.object({ summary: z.string(), score: z.number() }))
    .withSkills(["pdf", "docx"])
    .withComposio("user_123", {
        toolkits: ["github", "gmail"],
        tools: { github: ["github_create_issue"] },
        keys: { stripe: "sk_live_..." },
    })
    .withMcpServers({
        exa: {
            command: "npx",
            args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
            env: { EXA_API_KEY: process.env.EXA_API_KEY! },
        },
    })
    .withSecrets({ GITHUB_TOKEN: process.env.GITHUB_TOKEN! })
    .withSessionTagPrefix("my-app");
```

### Runtime Methods

```ts
// Run agent
const result = await swarmkit.run({
    prompt: "Analyze the data",
    timeoutMs: 15 * 60 * 1000,
    background: false,
});

// Execute shell command
const cmdResult = await swarmkit.executeCommand("pytest", {
    timeoutMs: 10 * 60 * 1000,
});

// Get output files
const output = await swarmkit.getOutputFiles(true); // recursive
console.log(output.files);  // FileMap
console.log(output.data);   // Parsed schema or null
console.log(output.error);  // Validation error or undefined

// Upload files
await swarmkit.uploadContext({ "spec.json": JSON.stringify(data) });
await swarmkit.uploadFiles({ "scripts/run.sh": "#!/bin/bash\necho hi" });

// Session management
const sessionId = swarmkit.getSession();
await swarmkit.pause();
await swarmkit.resume();
await swarmkit.setSession("existing-sandbox-id");
await swarmkit.kill();

// Builder method for reconnection
const swarmkit2 = new SwarmKit()
    .withAgent({ type: "claude" })
    .withSession("existing-sandbox-id");  // Reconnect on next run()

// Port forwarding
const url = await swarmkit.getHost(8000);
```

### Streaming

```ts
swarmkit.on("stdout", (chunk) => process.stdout.write(chunk));
swarmkit.on("stderr", (chunk) => process.stderr.write(chunk));
swarmkit.on("content", (event) => {
    const update = event.update;
    if (update.sessionUpdate === "agent_message_chunk") {
        console.log(update.content.text);
    }
});
```

**Events:**

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
| `tool_call` | Tool started | `toolCallId`, `title`, `kind`, `status`, `rawInput?` |
| `tool_call_update` | Tool finished | `toolCallId`, `status?`, `title?`, `content?` |
| `plan` | TodoWrite updates | `entries[]` with `content`, `status`, `priority` |

### Composio Static Methods

```ts
// Get OAuth URL for "Connect GitHub" button
const { url } = await SwarmKit.composio.auth("user_123", "github");

// Check connection status (all toolkits)
const status = await SwarmKit.composio.status("user_123");
// { github: true, gmail: false, slack: true }

// Check single toolkit
const isConnected = await SwarmKit.composio.status("user_123", "github");
// true | false

// Get detailed connection info
const connections = await SwarmKit.composio.connections("user_123");
// [{ toolkit: "github", connected: true, accountId: "ca_..." }, ...]
```

### Helper Functions

```ts
import { readLocalDir, saveLocalDir } from "@swarmkit/sdk";

// Read local directory → FileMap (for upload)
const files = readLocalDir("./input", true);  // recursive
await swarmkit.uploadContext(files);

// Save FileMap → local directory (for download)
const output = await swarmkit.getOutputFiles(true);
saveLocalDir("./output", output.files);
```

### Observability

```ts
const swarmkit = new SwarmKit()
    .withSessionTagPrefix("my-project");

await swarmkit.run({ prompt: "..." });

console.log(swarmkit.getSessionTag());        // "my-project-ab12cd34"
console.log(swarmkit.getSessionTimestamp());  // ISO timestamp for log file
```

Log files: `~/.swarmkit/observability/sessions/{tag}_{provider}_{sandboxId}_{agent}_{timestamp}.jsonl`

---

## Skills

Skills extend agent capabilities with specialized tools and workflows.

```ts
const swarmkit = new SwarmKit()
    .withSkills(["pdf", "dev-browser"]);
```

[Browse all available skills](https://github.com/brandomagnani/swarmkit/tree/main/skills)

---

## Composio

Access 1000+ integrations (GitHub, Gmail, Slack, etc.) via [Composio](https://composio.dev).

- [Tool Router Overview](https://docs.composio.dev/tool-router/overview)
- [Available Toolkits](https://docs.composio.dev/toolkits/introduction)

```ts
const swarmkit = new SwarmKit()
    .withComposio("user_123", { toolkits: ["github", "gmail"] });
```

---

## Swarm

### Basic Setup

```ts
import { Swarm } from "@swarmkit/sdk";

const swarm = new Swarm({
    agent: { type: "claude" },
    skills: ["pdf"],
    composio: { userId: "user_123", config: { toolkits: ["github"] } },
    concurrency: 4,
    timeoutMs: 3_600_000,
    tag: "my-pipeline",
    retry: { maxAttempts: 3, backoffMs: 1000, backoffMultiplier: 2 },
});
```

### map

```ts
import { z } from "zod";

const SummarySchema = z.object({
    title: z.string(),
    keyPoints: z.array(z.string()),
});

const results = await swarm.map({
    items: [
        { "report.txt": "Q1 revenue..." },
        { "report.txt": "Q2 revenue..." },
    ],
    prompt: "Summarize this document",
    schema: SummarySchema,
    agent: { type: "claude", model: "opus" },
    skills: ["pdf"],
    retry: { maxAttempts: 2 },
});

for (const r of results) {
    if (r.status === "success") {
        console.log(r.data);   // { title: "...", keyPoints: [...] }
        console.log(r.files);  // Output files
    }
}
```

### map with bestOf

```ts
const results = await swarm.map({
    items: documents,
    prompt: "Analyze thoroughly",
    schema: AnalysisSchema,
    bestOf: {
        n: 3,
        judgeCriteria: "Most comprehensive analysis",
        taskAgents: [
            { type: "claude", model: "opus" },
            { type: "codex", model: "gpt-5.2-codex" },
            { type: "gemini" },
        ],
        judgeAgent: { type: "claude" },
    },
});
```

### map with verify

```ts
const results = await swarm.map({
    items: documents,
    prompt: "Extract data",
    schema: DataSchema,
    verify: {
        criteria: "All required fields must be present and accurate",
        maxAttempts: 3,
        verifierAgent: { type: "claude", model: "opus" },
    },
});
```

### filter

```ts
const EvalSchema = z.object({
    severity: z.enum(["critical", "warning", "info"]),
    score: z.number(),
});

const results = await swarm.filter({
    items: documents,
    prompt: "Assess the severity of issues",
    schema: EvalSchema,
    condition: (data) => data.severity === "critical",
});

console.log(results.success);   // Passed condition
console.log(results.filtered);  // Didn't pass
console.log(results.error);     // Errors
```

### reduce

```ts
const ReportSchema = z.object({
    summary: z.string(),
    recommendations: z.array(z.string()),
});

const report = await swarm.reduce({
    items: results.success,
    prompt: "Create a unified report from all analyses",
    schema: ReportSchema,
});

if (report.status === "success") {
    console.log(report.data);
}
```

### best_of

```ts
const result = await swarm.bestOf({
    item: { "task.txt": "Complex problem..." },
    prompt: "Solve this problem",
    config: {
        n: 3,
        judgeCriteria: "Most accurate solution",
        onCandidateComplete: (idx, candIdx, status) =>
            console.log(`Candidate ${candIdx}: ${status}`),
        onJudgeComplete: (idx, winnerIdx, reasoning) =>
            console.log(`Winner: ${winnerIdx}`),
    },
});

console.log(result.winner);
console.log(result.winnerIndex);
console.log(result.judgeReasoning);
```

---

## Pipeline

```ts
import { Swarm, Pipeline } from "@swarmkit/sdk";

const swarm = new Swarm();

const pipeline = new Pipeline(swarm)
    .map({
        name: "analyze",
        prompt: (files, idx) => `Analyze document ${idx + 1}`,
        schema: AnalysisSchema,
        bestOf: { n: 3, judgeCriteria: "Most thorough" },
    })
    .filter({
        name: "quality-gate",
        prompt: "Rate the analysis quality",
        schema: z.object({ score: z.number() }),
        condition: (d) => d.score >= 8,
        emit: "success",
    })
    .reduce({
        name: "synthesize",
        prompt: "Create executive summary",
        schema: ReportSchema,
    })
    .on("stepStart", (e) => console.log(`Step ${e.index} started`))
    .on("stepComplete", (e) => console.log(`Step ${e.index} done`));

const result = await pipeline.run(documents);
console.log(result.output);
```

### Pipeline Events

```ts
pipeline
    .on("stepStart", (e) => console.log(`Step ${e.index}: ${e.itemCount} items`))
    .on("stepComplete", (e) => console.log(`Step ${e.index}: ${e.successCount} success in ${e.durationMs}ms`))
    .on("stepError", (e) => console.error(`Step ${e.index} failed:`, e.error))
    .on("itemRetry", (e) => console.log(`Retry: step ${e.stepIndex}, item ${e.itemIndex}`))
    .on("candidateComplete", (e) => console.log(`Candidate ${e.candidateIndex}: ${e.status}`))
    .on("judgeComplete", (e) => console.log(`Winner: ${e.winnerIndex}`))
    .on("verifierComplete", (e) => console.log(`Verify: ${e.passed ? "PASS" : e.feedback}`));
```

| Event | Fields |
|-------|--------|
| `stepStart` | `index`, `name?`, `itemCount` |
| `stepComplete` | `index`, `name?`, `durationMs`, `successCount`, `errorCount`, `filteredCount` |
| `stepError` | `index`, `name?`, `error` |
| `itemRetry` | `stepIndex`, `stepName?`, `itemIndex`, `attempt`, `error` |
| `candidateComplete` | `stepIndex`, `stepName?`, `itemIndex`, `candidateIndex`, `status` |
| `judgeComplete` | `stepIndex`, `stepName?`, `itemIndex`, `winnerIndex`, `reasoning` |
| `verifierComplete` | `stepIndex`, `stepName?`, `itemIndex`, `attempt`, `passed`, `feedback?` |

---

## Types

### AgentConfig

```ts
interface AgentConfig {
    type?: "claude" | "codex" | "gemini" | "qwen";
    apiKey?: string;
    providerApiKey?: string;
    oauthToken?: string;
    model?: string;
    reasoningEffort?: "low" | "medium" | "high" | "xhigh";  // Codex only
    betas?: string[];  // Claude only
}
```

### ComposioSetup

```ts
interface ComposioSetup {
    userId: string;
    config?: {
        toolkits?: string[];
        tools?: Record<string, ToolsFilter>;
        keys?: Record<string, string>;
        authConfigs?: Record<string, string>;
    };
}

type ToolsFilter =
    | string[]
    | { enable: string[] }
    | { disable: string[] }
    | { tags: string[] };
```

### RetryConfig

```ts
interface RetryConfig {
    maxAttempts?: number;
    backoffMs?: number;
    backoffMultiplier?: number;
    retryOn?: (result: SwarmResult) => boolean;
    onItemRetry?: (idx: number, attempt: number, error: string) => void;
}
```

### BestOfConfig

```ts
interface BestOfConfig {
    n?: number;
    judgeCriteria: string;
    taskAgents?: AgentConfig[];
    judgeAgent?: AgentConfig;
    skills?: string[];
    judgeSkills?: string[];
    composio?: ComposioSetup;
    judgeComposio?: ComposioSetup;
    mcpServers?: Record<string, McpServerConfig>;
    judgeMcpServers?: Record<string, McpServerConfig>;
    onCandidateComplete?: (idx: number, candIdx: number, status: string) => void;
    onJudgeComplete?: (idx: number, winnerIdx: number, reasoning: string) => void;
}
```

### VerifyConfig

```ts
interface VerifyConfig {
    criteria: string;
    maxAttempts?: number;
    verifierAgent?: AgentConfig;
    verifierSkills?: string[];
    verifierComposio?: ComposioSetup;
    verifierMcpServers?: Record<string, McpServerConfig>;
    onWorkerComplete?: (idx: number, attempt: number, status: string) => void;
    onVerifierComplete?: (idx: number, attempt: number, passed: boolean, feedback?: string) => void;
}
```

### SwarmResult

```ts
interface SwarmResult<T> {
    status: "success" | "filtered" | "error";
    data: T | null;
    files: FileMap;
    meta: IndexedMeta;
    error?: string;
    rawData?: string;
    bestOf?: BestOfInfo;
    verify?: VerifyInfo;
}
```

### AgentResponse

```ts
interface AgentResponse {
    sandboxId: string;
    exitCode: number;
    stdout: string;
    stderr: string;
}
```

### OutputResult

```ts
interface OutputResult<T> {
    files: FileMap;
    data: T | null;
    error?: string;
    rawData?: string;
}
```

### ReduceResult

```ts
interface ReduceResult<T> {
    status: "success" | "error";
    data: T | null;
    files: FileMap;
    meta: ReduceMeta;
    error?: string;
    rawData?: string;
    verify?: VerifyInfo;
}
```

### BestOfResult

```ts
interface BestOfResult<T> {
    winner: SwarmResult<T>;
    winnerIndex: number;
    judgeReasoning: string;
    judgeMeta: JudgeMeta;
    candidates: SwarmResult<T>[];
}
```

### SwarmConfig

```ts
interface SwarmConfig {
    agent?: AgentConfig;
    skills?: string[];
    composio?: ComposioSetup;
    mcpServers?: Record<string, McpServerConfig>;
    concurrency?: number;      // Default: 4
    timeoutMs?: number;        // Default: 3_600_000
    tag?: string;              // Default: "swarm"
    retry?: RetryConfig;
}
```

### PipelineResult

```ts
interface PipelineResult<T> {
    pipelineRunId: string;
    steps: StepResult[];         // { type, index, durationMs, results }
    output: SwarmResult<T>[] | ReduceResult<T>;
    totalDurationMs: number;
}
```

### Meta Types

```ts
interface IndexedMeta {
    operationId: string;
    operation: string;
    tag: string;
    sandboxId: string;
    itemIndex: number;
}

interface ReduceMeta {
    operationId: string;
    operation: string;
    tag: string;
    sandboxId: string;
    inputCount: number;
    inputIndices: number[];
}

interface JudgeMeta {
    operationId: string;
    operation: string;
    tag: string;
    sandboxId: string;
    candidateCount: number;
}

interface VerifyMeta {
    operationId: string;
    operation: string;
    tag: string;
    sandboxId: string;
    attempts: number;
}

interface BestOfInfo {
    winnerIndex: number;
    judgeReasoning: string;
    judgeMeta: JudgeMeta;
    candidates: SwarmResult[];
}

interface VerifyInfo {
    passed: boolean;
    reasoning: string;
    verifyMeta: VerifyMeta;
    attempts: number;
}
```
