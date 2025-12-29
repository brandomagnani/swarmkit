"""
01 - Hello Agent
Sandboxed AI agent with optional web search.
"""
import asyncio
import os
from dotenv import load_dotenv
from swarmkit import SwarmKit

load_dotenv()

async def main():
    # Auto-resolves SWARMKIT_API_KEY and E2B_API_KEY from environment
    agent = SwarmKit()

    # Optional: Exa web search (set EXA_API_KEY to enable)
    if os.getenv("EXA_API_KEY"):
        agent = SwarmKit(
            mcp_servers={
                "exa": {
                    "command": "npx",
                    "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp"],
                    "env": {"EXA_API_KEY": os.getenv("EXA_API_KEY")},
                },
            }
        )

    # With Exa: searches web and generates report
    # Without Exa: generates report from agent's knowledge
    await agent.run(
        prompt="""
            Research the latest developments in AI agents.
            Write a brief report summarizing the top 3 findings.
            Save the report to output/
        """
    )

    # Retrieve files from sandbox output/ folder
    output = await agent.get_output_files()
    print(list(output.files.keys()))

    await agent.kill()

if __name__ == "__main__":
    asyncio.run(main())
