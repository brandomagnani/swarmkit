"""
HN Time Capsule - SwarmKit Edition

Karpathy's 1,486 lines → 50 lines
"""

from pathlib import Path
from dotenv import load_dotenv
from swarmkit import Swarm, SwarmConfig, Pipeline, MapConfig, ReduceConfig, RetryConfig, AgentConfig
from fetch import fetch_hn_day, save_intermediate
from prompts import ANALYZE, RENDER
from schema import Analysis

load_dotenv()


swarm = Swarm(SwarmConfig(
    concurrency=10,                     # max parallel sandboxes
    retry=RetryConfig(max_attempts=3),  # 2 retries
))

pipeline = (
    Pipeline(swarm)
    .map(MapConfig(
        name='analyze',
        prompt=ANALYZE,
        schema=Analysis,
        agent=AgentConfig(type='claude', model='haiku'),
    ))  # analyze each article
    .reduce(ReduceConfig(
        name='render', 
        prompt=RENDER,
    ))  # aggregate into HTML
)


async def main():
    print("Fetching HN data...")
    items = fetch_hn_day("2015-12-01", limit=10)  # top 30 HN articles from 10 years ago
    print(f"Processing {len(items)} articles...")
    result = await pipeline.run(items)

    save_intermediate(result.steps[0].results)  # map output

    Path("output").mkdir(exist_ok=True)  # reduce output
    for name, content in result.output.files.items():
        Path(f"output/{name}").write_text(content)
    print(f"Done! Output saved to ./output/")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
