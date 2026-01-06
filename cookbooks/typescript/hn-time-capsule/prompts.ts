/**
 * Prompts for HN Time Capsule analysis.
 */

export const ANALYZE = `Analyze this HN article from 10 years ago.

Files in context/:
- meta.json: article metadata
- article.txt: article content
- comments.json: discussion thread

With 10 years of hindsight:
1. Summarize the article and discussion
2. Research what actually happened
3. Find the most prescient and most wrong comments
4. Note any fun or notable aspects
5. Grade commenters
6. Rate how interesting this retrospective is

Save only result.json to output/ (no other files).`;

export const RENDER = `Create a beautiful HTML dashboard from all analyses.

Files: context/item_*/data.json (schema provided)

Write a script to:
1. Load all data.json files
2. Aggregate grades per user (keep users with 3+ grades)
3. Calculate GPA (A=4, B=3, C=2, D=1, F=0, ±0.3)
4. Generate a single-page HTML app:
   - Sidebar: articles ranked by score
   - Main panel: full analysis on click
   - Hall of Fame: top commenters by GPA
   - Style: light theme, warm grays, generous whitespace

Design: minimalist, Apple-like, intuitive. Simplicity as ultimate sophistication.
Do not make it look LLM-generated or vibe-coded. Make it look done by a professional
human designer with superior taste for beauty.

Run script and save to output/index.html`;
