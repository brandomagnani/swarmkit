/**
 * Structured output schema for HN Time Capsule analysis.
 */

import { z } from "zod";

const AwardSchema = z.object({
    user: z.string().describe("HN username"),
    reason: z.string().describe("Why they were right/wrong in hindsight"),
});

export const AnalysisSchema = z.object({
    title: z.string().describe("Article title"),
    summary: z.string().describe("Brief summary of article and discussion"),
    what_happened: z.string().describe("What actually happened to this topic/company/technology"),
    most_prescient: AwardSchema.describe("Commenter who best predicted the future"),
    most_wrong: AwardSchema.describe("Commenter who was most wrong"),
    grades: z.record(z.string()).describe("HN username → letter grade (A+ to F)"),
    score: z.number().describe("0-10 how interesting this retrospective is"),
});
