"""
CRE Portfolio Analysis - SwarmKit Edition

Rent roll PDFs → Extract → Analyze → Portfolio Dashboard
"""

from pathlib import Path
from dotenv import load_dotenv
from swarmkit import (
    Swarm, SwarmConfig, Pipeline,
    MapConfig, ReduceConfig,
    RetryConfig, AgentConfig
)
from utils import load_rent_rolls, save_intermediate
from prompts import (
    EXTRACT_SYSTEM, EXTRACT,
    ANALYZE_SYSTEM, ANALYZE,
    REDUCE_SYSTEM, REDUCE,
)
from schema import RentRollExtract, PropertyAnalysis

load_dotenv()


swarm = Swarm(SwarmConfig(
    concurrency=4,                      # max parallel sandboxes
    retry=RetryConfig(max_attempts=2),  # 1 retry
))

pipeline = (
    Pipeline(swarm)
    .map(MapConfig(
        name='extract',
        system_prompt=EXTRACT_SYSTEM,
        prompt=EXTRACT,
        schema=RentRollExtract,
        agent=AgentConfig(type='claude', model='sonnet'),
    ))
    .map(MapConfig(
        name='analyze',
        system_prompt=ANALYZE_SYSTEM,
        prompt=ANALYZE,
        schema=PropertyAnalysis,
        agent=AgentConfig(type='claude', model='haiku'),
    ))
    .reduce(ReduceConfig(
        name='portfolio',
        system_prompt=REDUCE_SYSTEM,
        prompt=REDUCE,
    ))
)


async def main(pdf_dir: str):
    print("Loading rent rolls...")
    items = load_rent_rolls(pdf_dir)
    print(f"Processing {len(items)} properties...\n")

    result = await pipeline.run(items)

    # Save intermediate outputs
    save_intermediate(result.steps[0].results, "extract")
    save_intermediate(result.steps[1].results, "analyze")

    # Save final output
    Path("output").mkdir(exist_ok=True)
    for name, content in result.output.files.items():
        Path(f"output/{name}").write_text(content)

    print(f"\nDone! Output saved to ./output/")


if __name__ == "__main__":
    import sys
    import asyncio

    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else "./input"
    asyncio.run(main(pdf_dir))
