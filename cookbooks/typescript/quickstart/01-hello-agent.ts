/**
 * 01 - Hello Agent
 * Minimal sandboxed AI agent.
 */
import "dotenv/config";
import { SwarmKit } from "@swarmkit/sdk";

// Auto-resolves SWARMKIT_API_KEY and E2B_API_KEY from environment
const agent = new SwarmKit();

await agent.run({
    prompt: "Create a Python fibonacci script and save it to output/",
});

// Retrieve files from sandbox output/ folder
const output = await agent.getOutputFiles();
console.log(Object.keys(output.files));

await agent.kill();
