/**
 * 01 - Hello Agent
 * Sandboxed AI agent with optional web search.
 */
import "dotenv/config";
import { SwarmKit } from "@swarmkit/sdk";

// Auto-resolves SWARMKIT_API_KEY and E2B_API_KEY from environment
const agent = new SwarmKit();

// Optional: Exa web search (set EXA_API_KEY to enable)
if (process.env.EXA_API_KEY) {
    agent.withMcpServers({
        "exa": {
            command: "npx",
            args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
            env: { EXA_API_KEY: process.env.EXA_API_KEY },
        },
    });
}

// With Exa: searches web and generates report
// Without Exa: generates report from agent's knowledge
await agent.run({
    prompt: `
        Research the latest developments in AI agents.
        Generate a brief report summarizing the top 3 findings.
    `,
});

// Retrieve report files from sandbox output/ folder
const output = await agent.getOutputFiles();
console.log(Object.keys(output.files));

await agent.kill();
