/**
 * 01 - Hello Agent
 * Sandboxed AI agent with web search.
 */
import "dotenv/config";
import { SwarmKit } from "@swarmkit/sdk";

// Auto-resolves SWARMKIT_API_KEY and E2B_API_KEY from environment
const agent = new SwarmKit()
    .withMcpServers({
        "exa": {
            command: "npx",
            args: ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
            env: { EXA_API_KEY: process.env.EXA_API_KEY! },
        },
    });

await agent.run({
    prompt: `
        Search for the latest news about AI agents in 2024.
        Write a brief report summarizing the top 3 findings.
        Save the report to output/
    `,
});

// Retrieve files from sandbox output/ folder
const output = await agent.getOutputFiles();
console.log(Object.keys(output.files));

await agent.kill();
