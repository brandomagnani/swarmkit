/**
 * HN Time Capsule - SwarmKit Edition
 *
 * Karpathy's 1,486 lines -> ~50 lines
 */

import "dotenv/config";
import { writeFileSync, mkdirSync } from "fs";
import { z } from "zod";
import { Swarm, Pipeline } from "@swarmkit/sdk";
import { fetchHnDay } from "./fetch";
import { ANALYZE, RENDER } from "./prompts";

const AnalysisSchema = z.object({
    title: z.string(),
    summary: z.string(),
    what_happened: z.string(),
    most_prescient: z.object({ user: z.string(), reason: z.string() }),
    most_wrong: z.object({ user: z.string(), reason: z.string() }),
    grades: z.record(z.string()),  // {"tptacek": "A+", "pg": "B"}
    score: z.number(),             // 0-10
});

const swarm = new Swarm({
    concurrency: 10,                  // max parallel sandboxes
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
    const items = fetchHnDay("2015-12-01", 30);  // top 30 HN articles from 10 years ago
    console.log(`Processing ${items.length} articles...`);

    const result = await pipeline.run(items);

    // Save to ./output/
    mkdirSync("output", { recursive: true });
    for (const [name, content] of Object.entries(result.output.files)) {
        writeFileSync(`output/${name}`, content);
    }
    console.log("Done! Output saved to ./output/");
}

main().catch(console.error);
