/**
 * Prompts for HN Time Capsule analysis.
 */

export const ANALYZE = `Analyze this HN article from 10 years ago.

Files in context/:
- meta.json: title, url, points, author
- article.txt: article content
- comments.json: discussion thread

With 10 years of hindsight:
1. Summarize the article and discussion
2. Research what actually happened to this topic/company/technology
3. Find the most prescient comment (who got it right?)
4. Find the most wrong comment (who got it wrong?)
5. Grade commenters A-F based on prediction accuracy
6. Rate how interesting this retrospective is (0-10)

Write result.json matching the schema.`;

export const RENDER = `Create a beautiful, interactive HTML dashboard from all analyses.

Files: context/item_*/data.json
Each data.json follows the same schema:
\`\`\`
{title, summary, what_happened, most_prescient, most_wrong, grades, score}
\`\`\`

Write a Python script to:
1. Load all data.json files
2. Aggregate grades per user, keep only users with 3+ grades
3. Calculate GPA (A=4, B=3, C=2, D=1, F=0, +/-: ±0.3)
4. Generate a stunning single-page HTML app:
   - Sidebar: articles ranked by interestingness score
   - Main panel: click article to reveal full analysis with smooth transitions
   - Hall of Fame: leaderboard of most prescient HN commenters by GPA
   - Polish: dark theme, orange accents (#ff6600), modern typography, subtle animations

Make it look impressive. This is a showcase.

Run the script and save to output/index.html`;
