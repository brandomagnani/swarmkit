#!/usr/bin/env npx tsx
/**
 * Swarm CLI Agent + Composio Integrations
 *
 * AI agent with access to 500+ external services via Composio Tool Router.
 * Can send emails, post to Slack, create GitHub issues, update Notion, and more.
 *
 * Run: npx tsx swarm.ts
 */
import { SwarmKit, readLocalDir, saveLocalDir } from "@swarmkit/sdk";
import { mkdirSync } from "fs";
import "dotenv/config";

import { makeRenderer, readPrompt, console_, printPanel } from "./ui";
import { ComposioIntegration } from "./composio-integration";
import chalk from "chalk";

// ─────────────────────────────────────────────────────────────
// Composio Setup
// ─────────────────────────────────────────────────────────────

const composio = new ComposioIntegration({
  userId: "swarm-user-001",
  toolkits: ["gmail"],
});

// ─────────────────────────────────────────────────────────────
// SwarmKit Agent
// ─────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `Your name is Swarm, a powerful autonomous AI agent.
You can execute code, manage files, and take actions across external services via Composio MCP.
`;

let agent: SwarmKit;

// ─────────────────────────────────────────────────────────────

async function main() {
  // Pre-authenticate Composio services
  const composioMcp = await composio.setupWithPreauth();

  // Create agent with Composio MCP
  agent = new SwarmKit()
    .withAgent({
      type: "claude",
      model: "sonnet",
    })
    .withSystemPrompt(SYSTEM_PROMPT)
    .withMcpServers({ composio: composioMcp })
    .withSessionTagPrefix("swarm-composio-ts");

  const renderer = makeRenderer();
  agent.on("content", (event) => renderer.handleEvent(event));

  console_.print();
  printPanel(
    `${chalk.bold.cyan("Swarm")} + ${chalk.bold.magenta("Composio")}\n${chalk.dim("AI Agent with external integrations")}`,
    { borderColor: "cyan" }
  );
  console_.print();

  while (true) {
    const prompt = await readPrompt();
    if (!prompt) continue;
    if (["/quit", "/exit", "/q"].includes(prompt)) {
      await agent.kill();
      console_.print();
      console_.printMuted("Goodbye");
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
  if (agent) {
    await agent.kill();
  }
  console_.print();
  console_.print();
  console_.printMuted("Goodbye");
}

// ─────────────────────────────────────────────────────────────

mkdirSync("input", { recursive: true });
mkdirSync("output", { recursive: true });

main().catch(console.error);

process.on("SIGINT", async () => {
  await shutdown();
  process.exit(0);
});
