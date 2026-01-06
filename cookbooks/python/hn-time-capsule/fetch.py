"""HN data fetching - all the boring scraping code lives here."""

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


def _curl_get(url: str) -> str:
    """Fetch URL using curl (avoids Python SSL issues)."""
    result = subprocess.run(
        ['curl', '-sL', '-A', 'Mozilla/5.0', url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise Exception(f"curl failed: {result.stderr}")
    return result.stdout


@dataclass
class Article:
    rank: int
    title: str
    url: str
    hn_url: str
    points: int
    author: str
    comment_count: int
    item_id: str


class HNFrontpageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.articles = []
        self.current_article = {}
        self.in_titleline = False
        self.in_title_link = False
        self.in_subline = False
        self.in_score = False
        self.in_user = False
        self.in_subline_links = False
        self.current_rank = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "span" and attrs_dict.get("class") == "rank":
            self.in_titleline = True
        if tag == "span" and attrs_dict.get("class") == "titleline":
            self.in_titleline = True
        if self.in_titleline and tag == "a" and "href" in attrs_dict:
            if not self.current_article.get("title"):
                self.current_article["url"] = attrs_dict["href"]
                self.in_title_link = True
        if tag == "span" and attrs_dict.get("class") == "subline":
            self.in_subline = True
        if self.in_subline:
            if tag == "span" and attrs_dict.get("class") == "score":
                self.in_score = True
            if tag == "a" and attrs_dict.get("class") == "hnuser":
                self.in_user = True
            if tag == "a" and "href" in attrs_dict and "item?id=" in attrs_dict["href"]:
                href = attrs_dict["href"]
                item_id = href.split("item?id=")[-1]
                self.current_article["item_id"] = item_id
                self.current_article["hn_url"] = f"https://news.ycombinator.com/{href}"
                self.in_subline_links = True

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self.in_title_link:
            self.current_article["title"] = data
        if self.in_score:
            try:
                self.current_article["points"] = int(data.split()[0])
            except (ValueError, IndexError):
                self.current_article["points"] = 0
        if self.in_user:
            self.current_article["author"] = data
        if self.in_subline_links:
            if "comment" in data.lower():
                try:
                    self.current_article["comment_count"] = int(data.split()[0])
                except (ValueError, IndexError):
                    self.current_article["comment_count"] = 0
            elif data.lower() == "discuss":
                self.current_article["comment_count"] = 0
        if data.endswith(".") and data[:-1].isdigit():
            self.current_rank = int(data[:-1])
            self.current_article["rank"] = self.current_rank

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_title_link = False
            self.in_user = False
            self.in_subline_links = False
        if tag == "span":
            self.in_score = False
            if self.in_titleline:
                self.in_titleline = False
        if tag == "tr" and self.in_subline:
            self.in_subline = False
            if self.current_article.get("title") and self.current_article.get("item_id"):
                self.articles.append(Article(
                    rank=self.current_article.get("rank", 0),
                    title=self.current_article.get("title", ""),
                    url=self.current_article.get("url", ""),
                    hn_url=self.current_article.get("hn_url", ""),
                    points=self.current_article.get("points", 0),
                    author=self.current_article.get("author", ""),
                    comment_count=self.current_article.get("comment_count", 0),
                    item_id=self.current_article.get("item_id", ""),
                ))
            self.current_article = {}


def fetch_frontpage(day: str) -> list[Article]:
    url = f"https://news.ycombinator.com/front?day={day}"
    html = _curl_get(url)
    parser = HNFrontpageParser()
    parser.feed(html)
    return parser.articles


def fetch_comments(item_id: str) -> list[dict]:
    url = f"https://hn.algolia.com/api/v1/items/{item_id}"
    data = json.loads(_curl_get(url))

    def parse_children(children) -> list[dict]:
        comments = []
        for child in children:
            if child.get("type") != "comment" or child.get("text") is None:
                continue
            text = unescape(re.sub(r'<[^>]+>', '', child.get("text", "")))
            comments.append({
                "author": child.get("author") or "[deleted]",
                "text": text,
                "children": parse_children(child.get("children", [])),
            })
        return comments

    return parse_children(data.get("children", []))


def fetch_article_content(url: str) -> str:
    unavailable = "[Article unavailable - analyze based on meta.json and comments.json]"
    if not url.startswith(('http://', 'https://')):
        return unavailable
    if any(x in url for x in ['.pdf', 'youtube.com', 'youtu.be', 'twitter.com', 'x.com']):
        return unavailable
    try:
        html = _curl_get(url)
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) < 100 or '404' in text or 'Not Found' in text:
            return unavailable
        return text[:15000] if len(text) > 15000 else text
    except:
        return unavailable


def fetch_hn_day(date: str, limit: int | None = None) -> list[dict]:
    """Fetch HN frontpage data as list of FileMap for SwarmKit."""
    # Clean previous run
    shutil.rmtree("input", ignore_errors=True)
    shutil.rmtree("intermediate", ignore_errors=True)
    shutil.rmtree("output", ignore_errors=True)

    articles = fetch_frontpage(date)
    if limit:
        articles = articles[:limit]

    items = []
    for i, article in enumerate(articles):
        item = {
            'meta.json': json.dumps({
                'rank': article.rank,
                'title': article.title,
                'url': article.url,
                'hn_url': article.hn_url,
                'points': article.points,
                'author': article.author,
                'comment_count': article.comment_count,
            }, indent=2),
            'article.txt': fetch_article_content(article.url),
            'comments.json': json.dumps(fetch_comments(article.item_id), indent=2),
        }
        items.append(item)

        # Save to input/ for inspection
        item_dir = Path(f"input/item_{i:02d}")
        item_dir.mkdir(parents=True, exist_ok=True)
        for name, content in item.items():
            (item_dir / name).write_text(content)

    return items


def save_intermediate(results) -> None:
    """Save intermediate map results to intermediate/."""
    Path("intermediate").mkdir(exist_ok=True)
    for r in results:
        item_dir = Path(f"intermediate/item_{r.meta.item_index:02d}")
        item_dir.mkdir(exist_ok=True)
        (item_dir / "status.txt").write_text(r.status)
        if r.data:
            (item_dir / "analysis.json").write_text(json.dumps(r.data.model_dump(), indent=2))
        if r.error:
            (item_dir / "error.txt").write_text(r.error)
