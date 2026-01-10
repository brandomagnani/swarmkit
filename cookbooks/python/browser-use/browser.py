"""
09 - MCP Browser-Use
Browser automation with browser-use cloud API.

Setup:
1. Get an API key from https://browser-use.com
2. Set BROWSER_USE_API_KEY in your .env file
"""
import asyncio
import os

from dotenv import load_dotenv
from swarmkit import AgentConfig, MapConfig, Pipeline, RetryConfig, Swarm, SwarmConfig, VerifyConfig

from items import build_items, save_results, setup_run_dir
from prompt import visit_post_prompt
from schema import HNPostResult

load_dotenv()

# Load API key
api_key = os.getenv("BROWSER_USE_API_KEY", "")
if not api_key:
    raise RuntimeError(
        "Missing BROWSER_USE_API_KEY. Add it to your .env file (see header comment)."
    )

# MCP servers extend agent capabilities with external tools.
# browser-use cloud API - no local browser required.
mcp_servers = {
    "browser-use": {
        "command": "npx",
        "args": [
            "-y",
            "mcp-remote",
            "https://api.browser-use.com/mcp",
            "--header",
            f"X-Browser-Use-API-Key: {api_key}",
        ],
    }
}

# Pipeline configuration
swarm = Swarm(
    SwarmConfig(
        tag="quickstart-hn-browser-use",
        concurrency=4,
        retry=RetryConfig(max_attempts=2),
        mcp_servers=mcp_servers,
    )
)

pipeline = Pipeline(swarm).map(
    MapConfig(
        name="visit-post",
        prompt=visit_post_prompt,
        schema=HNPostResult,
        agent=AgentConfig(type="claude", model="haiku"),
        timeout_ms=15 * 60 * 1000,  # 15 minutes per post
        verify=VerifyConfig(
            criteria="""
                The result must meet ALL these requirements:
                1. Summary field must contain a meaningful markdown summary (not an error message)
                2. Summary must be at least 500 characters long with proper formatting
                3. At least 2-3 relevant screenshots must be captured and listed
                4. Title, outbound_url, and final_url must be extracted
                5. Summary must include embedded screenshot references using markdown image syntax
                6. No error field or error field must be null
            """,
            max_attempts=2,
        ),
    )
)


async def main():
    # Scrape top 3 Hacker News posts with browser-use
    items = build_items(count=3)
    run_dir, posts_dir, started_at = setup_run_dir(items)

    print(f"Visiting top {len(items)} Hacker News posts (ranks 1-{len(items)})...")
    result = await pipeline.run(items)

    save_results(result, items, posts_dir, run_dir, started_at)
    print(f"Done. All artifacts saved to: {run_dir}")

if __name__ == "__main__":
    asyncio.run(main())