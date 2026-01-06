/**
 * Fetch HN frontpage data for a given date.
 */

import { execSync } from "child_process";

type FileMap = Record<string, string>;

interface Article {
    rank: number;
    title: string;
    url: string;
    hn_url: string;
    points: number;
    author: string;
    comment_count: number;
    item_id: string;
}

interface Comment {
    author: string;
    text: string;
    children: Comment[];
}

function curlGet(url: string): string {
    try {
        const result = execSync(`curl -sL -A "Mozilla/5.0" "${url}"`, {
            encoding: "utf-8",
            timeout: 30000,
        });
        return result;
    } catch {
        return "";
    }
}

function cleanHtmlToText(html: string): string {
    return html
        .replace(/<a href="([^"]+)"[^>]*>([^<]+)<\/a>/g, "[$2]($1)")
        .replace(/<i>([^<]+)<\/i>/g, "*$1*")
        .replace(/<b>([^<]+)<\/b>/g, "**$1**")
        .replace(/<code>([^<]+)<\/code>/g, "`$1`")
        .replace(/<p>/g, "\n\n")
        .replace(/<\/p>/g, "")
        .replace(/<[^>]+>/g, "")
        .replace(/\n{3,}/g, "\n\n")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&amp;/g, "&")
        .replace(/&quot;/g, '"')
        .replace(/&#x27;/g, "'")
        .trim();
}

function parseFrontpage(html: string): Article[] {
    const articles: Article[] = [];
    const rows = html.split("<tr");

    let currentArticle: Partial<Article> = {};
    let rank = 0;

    for (const row of rows) {
        // Extract rank
        const rankMatch = row.match(/<span class="rank">(\d+)\./);
        if (rankMatch) {
            rank = parseInt(rankMatch[1]);
            currentArticle.rank = rank;
        }

        // Extract title and URL
        const titleMatch = row.match(/<span class="titleline"><a href="([^"]+)"[^>]*>([^<]+)<\/a>/);
        if (titleMatch) {
            currentArticle.url = titleMatch[1];
            currentArticle.title = titleMatch[2];
        }

        // Extract points
        const pointsMatch = row.match(/<span class="score"[^>]*>(\d+) points?<\/span>/);
        if (pointsMatch) {
            currentArticle.points = parseInt(pointsMatch[1]);
        }

        // Extract author
        const authorMatch = row.match(/<a href="user\?id=([^"]+)" class="hnuser"/);
        if (authorMatch) {
            currentArticle.author = authorMatch[1];
        }

        // Extract item ID and comment count
        const itemMatch = row.match(/item\?id=(\d+)"[^>]*>(\d+)&nbsp;comment/);
        if (itemMatch) {
            currentArticle.item_id = itemMatch[1];
            currentArticle.comment_count = parseInt(itemMatch[2]);
            currentArticle.hn_url = `https://news.ycombinator.com/item?id=${itemMatch[1]}`;

            if (currentArticle.title && currentArticle.url) {
                articles.push(currentArticle as Article);
            }
            currentArticle = {};
        }

        // Handle "discuss" link (0 comments)
        const discussMatch = row.match(/item\?id=(\d+)"[^>]*>discuss<\/a>/);
        if (discussMatch && currentArticle.title) {
            currentArticle.item_id = discussMatch[1];
            currentArticle.comment_count = 0;
            currentArticle.hn_url = `https://news.ycombinator.com/item?id=${discussMatch[1]}`;

            if (currentArticle.url) {
                articles.push(currentArticle as Article);
            }
            currentArticle = {};
        }
    }

    return articles;
}

function fetchFrontpage(day: string): Article[] {
    const url = `https://news.ycombinator.com/front?day=${day}`;
    const html = curlGet(url);
    return parseFrontpage(html);
}

function parseComments(data: any): Comment[] {
    const comments: Comment[] = [];
    const children = data.children || [];

    for (const child of children) {
        if (child.type !== "comment" || !child.text) continue;

        comments.push({
            author: child.author || "[deleted]",
            text: cleanHtmlToText(child.text || ""),
            children: parseComments(child),
        });
    }

    return comments;
}

function fetchComments(itemId: string): Comment[] {
    const url = `https://hn.algolia.com/api/v1/items/${itemId}`;
    const json = curlGet(url);
    if (!json) return [];

    try {
        const data = JSON.parse(json);
        return parseComments(data);
    } catch {
        return [];
    }
}

function fetchArticleContent(url: string): string {
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        return "";
    }

    const skipPatterns = [".pdf", "youtube.com", "youtu.be", "twitter.com", "x.com"];
    if (skipPatterns.some((p) => url.includes(p))) {
        return "";
    }

    const html = curlGet(url);
    if (!html) return "";

    // Simple HTML to text extraction
    let text = html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
        .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, "")
        .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, "")
        .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, "")
        .replace(/<[^>]+>/g, " ")
        .replace(/&nbsp;/g, " ")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&amp;/g, "&")
        .replace(/&quot;/g, '"')
        .replace(/\s+/g, " ")
        .trim();

    // Truncate to 15000 chars
    if (text.length > 15000) {
        const truncateAt = text.lastIndexOf(". ", 14500);
        text = text.slice(0, truncateAt > 0 ? truncateAt + 1 : 15000) + "\n\n[TRUNCATED]";
    }

    return text.length > 100 ? text : "";
}

export function fetchHnDay(day: string, limit?: number): FileMap[] {
    const articles = fetchFrontpage(day);
    const items: FileMap[] = [];

    const toProcess = limit ? articles.slice(0, limit) : articles;

    for (const article of toProcess) {
        const meta = {
            rank: article.rank,
            title: article.title,
            url: article.url,
            hn_url: article.hn_url,
            points: article.points,
            author: article.author,
            comment_count: article.comment_count,
        };

        const articleText = fetchArticleContent(article.url);
        const comments = fetchComments(article.item_id);

        items.push({
            "meta.json": JSON.stringify(meta, null, 2),
            "article.txt": articleText,
            "comments.json": JSON.stringify(comments, null, 2),
        });
    }

    return items;
}
