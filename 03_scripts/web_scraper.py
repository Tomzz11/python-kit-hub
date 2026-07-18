#!/usr/bin/env python3
# ============================================================
# WEB SCRAPER — Utility Scripts
# ============================================================
"""
Web scraping utilities (stdlib only — ไม่ต้อง install ใดๆ):
  - fetch_html    : ดึง HTML พร้อม retry + headers
  - parse_table   : แปลง HTML table → list[dict]
  - extract_links : ดึง links จากหน้า
  - extract_meta  : ดึง meta tags
  - RateLimiter   : ควบคุมความเร็วการ request
  - SitemapParser : อ่าน sitemap.xml

หมายเหตุ: สำหรับ JS-rendered pages ใช้ playwright หรือ selenium
"""

import re
import time
import gzip
import json
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
from dataclasses import dataclass, field
from typing import Iterator
from io import BytesIO

# ── 1. RateLimiter ────────────────────────────────────────────
class RateLimiter:
    """ป้องกัน request เร็วเกินไป"""
    def __init__(self, calls_per_second: float = 1.0):
        self._interval  = 1.0 / calls_per_second
        self._last_call = 0.0

    def wait(self):
        elapsed = time.time() - self._last_call
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
        self._last_call = time.time()

# ── 2. fetch_html ─────────────────────────────────────────────
DEFAULT_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

def fetch_html(
    url: str,
    headers: dict | None = None,
    timeout: float = 15.0,
    max_retries: int = 3,
    backoff: float = 1.0,
    encoding: str | None = None,
) -> str:
    """
    ดึง HTML จาก URL พร้อม retry + gzip support

    Returns:
        HTML string

    Raises:
        urllib.error.HTTPError : HTTP error (4xx, 5xx)
        urllib.error.URLError  : network error
    """
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    req    = urllib.request.Request(url, headers=merged)

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                # decompress gzip
                if resp.info().get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                # detect encoding
                enc = encoding or _detect_encoding(resp, raw)
                return raw.decode(enc, errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                wait = backoff * (2 ** attempt)
                print(f"  Rate limited. Retrying in {wait:.1f}s...")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_retries - 1:
                wait = backoff * (2 ** attempt)
                print(f"  Network error ({e}). Retrying in {wait:.1f}s...")
                time.sleep(wait)
                continue
            raise

def _detect_encoding(resp, raw: bytes) -> str:
    content_type = resp.info().get("Content-Type", "")
    if "charset=" in content_type:
        return content_type.split("charset=")[-1].strip()
    match = re.search(rb'charset=["\']?([^"\'>\s]+)', raw[:2048])
    if match:
        return match.group(1).decode()
    return "utf-8"

# ── 3. SimpleHTMLParser ───────────────────────────────────────
class SimpleHTMLParser(HTMLParser):
    """
    Minimal HTML parser สำหรับ extract tags/text
    ไม่รองรับ JS-rendered content
    """

    def __init__(self):
        super().__init__()
        self._current_tag = ""
        self._current_attrs: dict = {}
        self._stack: list[tuple[str, dict]] = []
        self.elements: list[dict] = []

    def handle_starttag(self, tag: str, attrs):
        attr_dict = dict(attrs)
        self._stack.append((tag, attr_dict))
        self._current_tag   = tag
        self._current_attrs = attr_dict

    def handle_endtag(self, tag: str):
        if self._stack and self._stack[-1][0] == tag:
            self._stack.pop()

    def handle_data(self, data: str):
        text = data.strip()
        if text and self._stack:
            tag, attrs = self._stack[-1]
            self.elements.append({
                "tag":   tag,
                "attrs": attrs,
                "text":  text,
            })

# ── 4. extract_links ─────────────────────────────────────────
def extract_links(html: str, base_url: str = "") -> list[dict]:
    """
    ดึง links ทั้งหมดจาก HTML

    Returns:
        list ของ {"href": ..., "text": ..., "absolute": ...}
    """
    pattern = re.compile(
        r'<a\s+[^>]*?href=["\']([^"\']+)["\'][^>]*?>(.*?)</a>',
        re.IGNORECASE | re.DOTALL
    )
    links = []
    for m in pattern.finditer(html):
        href = m.group(1).strip()
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        absolute = urllib.parse.urljoin(base_url, href) if base_url else href
        links.append({"href": href, "text": text, "absolute": absolute})
    return links

# ── 5. extract_meta ───────────────────────────────────────────
def extract_meta(html: str) -> dict:
    """ดึง meta tags จาก HTML"""
    meta: dict = {}

    # title
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        meta["title"] = re.sub(r"\s+", " ", m.group(1)).strip()

    # meta name/property
    for m in re.finditer(
        r'<meta\s+(?:[^>]*?)'
        r'(?:name|property)=["\']([^"\']+)["\']'
        r'[^>]*?content=["\']([^"\']*)["\']',
        html, re.IGNORECASE
    ):
        meta[m.group(1).lower()] = m.group(2)

    # canonical URL
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
                  html, re.IGNORECASE)
    if m:
        meta["canonical"] = m.group(1)

    return meta

# ── 6. parse_table ────────────────────────────────────────────
def parse_table(html: str, table_index: int = 0) -> list[dict]:
    """
    แปลง HTML <table> → list[dict]

    Args:
        html:        HTML string
        table_index: ลำดับของ table (เริ่มจาก 0)

    Returns:
        list ของ dict (header → value)
    """
    # ดึง tables ทั้งหมด
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html,
                        re.IGNORECASE | re.DOTALL)
    if table_index >= len(tables):
        return []
    table_html = tables[table_index]

    def _extract_cells(row_html: str, tag: str = "td") -> list[str]:
        return [re.sub(r"<[^>]+>", "", c).strip()
                for c in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>",
                                    row_html, re.IGNORECASE | re.DOTALL)]

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html,
                      re.IGNORECASE | re.DOTALL)
    if not rows:
        return []

    # headers from <th>
    headers = _extract_cells(rows[0], "th")
    if not headers:
        headers = _extract_cells(rows[0], "td")
    if not headers:
        return []

    result = []
    for row in rows[1:]:
        cells = _extract_cells(row, "td")
        if cells:
            result.append(dict(zip(headers, cells)))
    return result

# ── 7. SitemapParser ─────────────────────────────────────────
def parse_sitemap(url: str) -> Iterator[dict]:
    """
    อ่าน sitemap.xml และ yield URL entries

    Yields:
        {"loc": ..., "lastmod": ..., "changefreq": ..., "priority": ...}
    """
    try:
        html = fetch_html(url, timeout=10)
    except Exception as e:
        print(f"  Cannot fetch sitemap: {e}")
        return

    # sitemap index (ลิสต์ sitemaps)
    sub_maps = re.findall(r"<loc>(https?://[^<]+\.xml)</loc>", html)
    if sub_maps:
        for sm_url in sub_maps:
            yield from parse_sitemap(sm_url)
        return

    # regular sitemap
    for m in re.finditer(r"<url>(.*?)</url>", html, re.DOTALL):
        entry = {}
        for tag in ("loc", "lastmod", "changefreq", "priority"):
            tm = re.search(rf"<{tag}>(.*?)</{tag}>", m.group(1))
            if tm:
                entry[tag] = tm.group(1).strip()
        if "loc" in entry:
            yield entry

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Demo ด้วย example.com (เบาที่สุด)
    limiter = RateLimiter(calls_per_second=0.5)

    print("=== Fetching example.com ===")
    limiter.wait()
    try:
        html  = fetch_html("https://example.com")
        meta  = extract_meta(html)
        links = extract_links(html, "https://example.com")

        print(f"Title: {meta.get('title')}")
        print(f"Links found: {len(links)}")
        for link in links[:5]:
            print(f"  {link['text']!r:20} → {link['absolute']}")
    except Exception as e:
        print(f"  Network unavailable: {e}")

    # Table parsing example (offline)
    sample_table = """
    <table>
      <tr><th>Name</th><th>Age</th><th>City</th></tr>
      <tr><td>Alice</td><td>30</td><td>Bangkok</td></tr>
      <tr><td>Bob</td><td>25</td><td>Chiang Mai</td></tr>
    </table>
    """
    print("\n=== Parsed Table ===")
    for row in parse_table(sample_table):
        print(" ", row)
