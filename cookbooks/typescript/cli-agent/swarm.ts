#!/usr/bin/env npx tsx
/**
 * Swarm CLI Agent - A sandboxed CLI agent that can think, execute code,
 * browse the web, read / edit files, and solve complex tasks.
 *
 * - Put files in `input/` folder - they're uploaded to the agent's context before each run
 * - Files the agent creates are automatically downloaded to your `output/` folder
 *
 * Run: npx tsx swarm.ts
 */
import { SwarmKit, readLocalDir, saveLocalDir } from "@swarmkit/sdk";
import { createE2BProvider } from "@swarmkit/e2b";
import { mkdirSync } from "fs";
import "dotenv/config";

import { makeRenderer, readPrompt, console_, printPanel } from "./ui";
import chalk from "chalk";

// ─────────────────────────────────────────────────────────────
// SwarmKit Instance Configuration
// ─────────────────────────────────────────────────────────────

const SANDBOX = createE2BProvider({
  apiKey: process.env.E2B_API_KEY!,
  defaultTimeoutMs: 3_600_000, // optional: 1 hour default
});

const MCP_SERVERS: Record<string, { command: string; args: string[]; env: Record<string, string> }> = {};

// Chrome DevTools MCP - browser automation and debugging
MCP_SERVERS["chrome-devtools"] = {
  command: "npx",
  args: [
    "chrome-devtools-mcp@latest",
    "--headless=true",
    "--isolated=true",
    "--chromeArg=--no-sandbox",
    "--chromeArg=--disable-setuid-sandbox",
    "--chromeArg=--disable-dev-shm-usage",
  ],
  env: {},
};

if (process.env.EXA_API_KEY) {
  // optional: web search
  MCP_SERVERS["exa"] = {
    command: "npx",
    args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
    env: { EXA_API_KEY: process.env.EXA_API_KEY },
  };
}

const SYSTEM_PROMPT = `Your name is Swarm, a powerful autonomous AI agent.
You can execute code, browse the web, manage files, and solve complex tasks such as extracting
data from complex documents, analyzing data, producing evidence based reports, and more.
`;

const agent = new SwarmKit()
  .withAgent({
    type: "gemini", // claude, codex, gemini
    apiKey: process.env.SWARMKIT_API_KEY!,
  })
  .withSandbox(SANDBOX)
  .withSystemPrompt(SYSTEM_PROMPT)
  .withMcpServers(MCP_SERVERS)
  .withSessionTagPrefix("Swarm-agent-ts");

// ─────────────────────────────────────────────────────────────

async function main() {
  const renderer = makeRenderer();
  agent.on("content", (event) => renderer.handleEvent(event));

  console_.print();
  printPanel(
    `${chalk.bold.cyan("🤖 Swarm")}\n${chalk.dim("Autonomous AI Agent - Code, Browse, Files & More")}`,
    { borderColor: "cyan" }
  );
  console_.print();

  while (true) {
    const prompt = await readPrompt();
    if (!prompt) continue;
    if (["/quit", "/exit", "/q"].includes(prompt)) {
      await agent.kill();
      console_.print();
      console_.printMuted("👋 Goodbye");
      break;
    }

    renderer.reset();
    renderer.startLive();

    // Upload input files to agent's context
    const inputFiles = readLocalDir("input");
    if (Object.keys(inputFiles).length > 0) {
      await agent.uploadContext(inputFiles);
    }

    await agent.run({ prompt });
    renderer.stopLive();

    // Download output files
    const output = await agent.getOutputFiles(true);
    if (Object.keys(output.files).length > 0) {
      saveLocalDir("output", output.files);
      console_.print();
      for (const name of Object.keys(output.files)) {
        console_.printSuccess(`📄 Saved: output/${name}`);
      }
    }

    console_.print();
  }
}

async function shutdown() {
  await agent.kill();
  console_.print();
  console_.print();
  console_.printMuted("👋 Goodbye");
}

// ─────────────────────────────────────────────────────────────

mkdirSync("input", { recursive: true });
mkdirSync("output", { recursive: true });

main().catch(console.error);

process.on("SIGINT", async () => {
  await shutdown();
  process.exit(0);
});
