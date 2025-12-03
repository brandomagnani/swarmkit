/**
 * Factotum Agent - An interactive chat with a sandboxed AI agent that can think, execute code,
 * browse the web, read / edit files, and solve complex tasks.
 * Ask for anything—any files the agent creates are automatically downloaded to your local `output/` folder.
 *
 * Run: npx tsx factotum.ts
 */
import { SwarmKit } from "@swarmkit/sdk";
import { createE2BProvider } from "@swarmkit/e2b";
import { mkdirSync, writeFileSync } from "fs";
import { createInterface } from "readline";
import "dotenv/config";

// ─────────────────────────────────────────────────────────────
// SwarmKit Instance Configuration
// ─────────────────────────────────────────────────────────────

const sandbox = createE2BProvider({
  apiKey: process.env.E2B_API_KEY!,
  timeoutMs: 3_600_000,
});

const mcpServers: Record<string, any> = {};

// Chrome DevTools MCP - browser automation and debugging
mcpServers["chrome-devtools"] = {
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
  mcpServers["exa"] = {
    command: "npx",
    args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
    env: { EXA_API_KEY: process.env.EXA_API_KEY },
  };
}

const agent = new SwarmKit()
  .withAgent({
    type: "gemini",
    apiKey: process.env.SWARMKIT_API_KEY!,
    model: "gemini-3-pro-preview",
  })
  .withSandbox(sandbox)
  .withSystemPrompt(`You are Factotum, a powerful autonomous AI agent.
You can execute code, browse the web, manage files, and solve complex tasks.`)
  .withMcpServers(mcpServers)
  .withSessionTagPrefix("factotum-agent-ts");

// ─────────────────────────────────────────────────────────────

const rl = createInterface({ input: process.stdin, output: process.stdout });
const ask = (q: string) => new Promise<string>((r) => rl.question(q, r));

async function main() {
  agent.on("content", (event) => console.log(event.update));
  console.log("\n🤖 Agent ready. Ask anything.\n");

  while (true) {
    const prompt = (await ask("\nyou: ")).trim();
    if (!prompt) continue;
    if (["/quit", "/exit", "/q"].includes(prompt)) {
      await agent.kill();
      console.log("\n👋 Goodbye");
      process.exit(0);
    }

    console.log();
    await agent.run({ prompt });

    for (const f of await agent.getOutputFiles()) {
      const path = `output/${f.name}`;
      writeFileSync(path, Buffer.from(f.content as ArrayBuffer));
      console.log(`\n📄 Saved: ${path}`);
    }
  }
}

mkdirSync("output", { recursive: true });
main().catch(console.error);
process.on("SIGINT", async () => {
  await agent.kill();
  console.log("\n\n👋 Goodbye");
  process.exit(0);
});
