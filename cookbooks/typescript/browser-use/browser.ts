/**
 * Browser-Use Cookbook
 * Browser automation with browser-use cloud API.
 *
 * Setup:
 * 1. Get an API key from https://browser-use.com
 * 2. Set BROWSER_USE_API_KEY in your .env file
 */

import "dotenv/config";
import { Swarm, Pipeline } from "@swarmkit/sdk";

import { buildItems, setupRunDir, saveResults } from "./items";
import { visitPostPrompt } from "./prompt";
import { HNPostResultSchema } from "./schema";

// Load API key
const apiKey = process.env.BROWSER_USE_API_KEY ?? "";
if (!apiKey) {
    throw new Error(
        "Missing BROWSER_USE_API_KEY. Add it to your .env file (see header comment)."
    );
}

// MCP servers extend agent capabilities with external tools.
// browser-use cloud API - no local browser required.
const mcpServers = {
    "browser-use": {
        command: "npx",
        args: [
            "-y",
            "mcp-remote",
            "https://api.browser-use.com/mcp",
            "--header",
            `X-Browser-Use-API-Key: ${apiKey}`,
        ],
    },
};

// Pipeline configuration
const swarm = new Swarm({
    tag: "quickstart-hn-browser-use",
    concurrency: 4,
    retry: { maxAttempts: 2 },
    mcpServers,
});

const pipeline = new Pipeline(swarm).map({
    name: "visit-post",
    prompt: visitPostPrompt,
    schema: HNPostResultSchema,
    agent: { type: "claude", model: "haiku" },
    timeoutMs: 15 * 60 * 1000, // 15 minutes per post
    verify: {
        criteria: `
            The result must meet ALL these requirements:
            1. Summary field must contain a meaningful markdown summary (not an error message)
            2. Summary must be at least 500 characters long with proper formatting
            3. At least 2-3 relevant screenshots must be captured and listed
            4. Title, outbound_url, and final_url must be extracted
            5. Summary must include embedded screenshot references using markdown image syntax
            6. No error field or error field must be null
        `,
        maxAttempts: 2,
    },
});

async function main(): Promise<void> {
    // Scrape top 3 Hacker News posts with browser-use
    const items = buildItems(3);
    const { runDir, postsDir, startedAt } = setupRunDir(items);

    console.log(`Visiting top ${items.length} Hacker News posts (ranks 1-${items.length})...`);
    const result = await pipeline.run(items);

    saveResults(result, items, postsDir, runDir, startedAt);
    console.log(`Done. All artifacts saved to: ${runDir}`);
}

main().catch(console.error);
