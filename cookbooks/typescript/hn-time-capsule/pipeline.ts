/**
 * HN Time Capsule - SwarmKit Edition
 *
 * Karpathy's 1,486 lines -> ~50 lines
 */

import "dotenv/config";
import { writeFileSync, mkdirSync } from "fs";
import { Swarm, Pipeline } from "@swarmkit/sdk";
import { fetchHnDay, saveIntermediate } from "./fetch";
import { ANALYZE, RENDER } from "./prompts";
import { AnalysisSchema } from "./schema";

const swarm = new Swarm({
    concurrency: 10,            // max parallel sandboxes
    retry: { maxAttempts: 3 },  // 2 retries
});

const pipeline = new Pipeline(swarm)
    .map({
        name: "analyze",
        prompt: ANALYZE,
        schema: AnalysisSchema,
        agent: { type: "claude", model: "haiku" },
    })  // analyze each article
    .reduce({
        name: "render",
        prompt: RENDER,
    });  // aggregate into HTML

async function main() {
    console.log("Fetching HN data...");
    const items = fetchHnDay("2015-12-01", 10);  // top 10 HN articles from 10 years ago
    console.log(`Processing ${items.length} articles...`);

    const result = await pipeline.run(items);

    saveIntermediate(result.steps[0].results as any[]);  // map output

    mkdirSync("output", { recursive: true });  // reduce output
    for (const [name, content] of Object.entries(result.output.files)) {
        writeFileSync(`output/${name}`, content);
    }
    console.log("Done! Output saved to ./output/");
}

main().catch(console.error);
