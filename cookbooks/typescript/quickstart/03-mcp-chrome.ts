/**
 * 03 - MCP Chrome DevTools
 * Browser automation with Chrome DevTools MCP server.
 */
import "dotenv/config";
import { SwarmKit } from "@swarmkit/sdk";

// MCP servers extend agent capabilities with external tools
const agent = new SwarmKit()
    .withMcpServers({
        "chrome-devtools": {
            command: "npx",
            args: [
                "-y",
                "chrome-devtools-mcp@latest",
                "--chromeArg=--no-sandbox",
                "--chromeArg=--disable-setuid-sandbox",
                "--chromeArg=--disable-dev-shm-usage",
            ],
        },
    });

await agent.run({
    prompt: `
        Use Chrome DevTools to:
        1. Navigate to https://news.ycombinator.com
        2. Take a screenshot
        3. Save it to output/
    `,
});

const output = await agent.getOutputFiles();
console.log(Object.keys(output.files));

await agent.kill();
