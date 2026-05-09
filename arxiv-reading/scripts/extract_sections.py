#!/usr/bin/env python3
"""Extract sections from ar5iv HTML.

Usage:
  python3 scripts/extract_sections.py <html-file>
      List all section headings with their character offsets.

  python3 scripts/extract_sections.py <html-file> "Section Name"
      Extract content of the matching section as clean plain text.

Auto-caching:
  - Section listing is cached as <html-file>.sections.json
  - Section content is cached as <html-file>.sections_content.json (all sections)
  Subsequent runs read from cache even if the HTML file no longer exists.
"""
import sys, os, re, json
from html import unescape

def strip_tags(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def find_sections(html: str) -> list[dict]:
    # Match <section> tags with data-title attribute, or heading tags
    sections = []
    # ar5iv uses <section data-title="...">
    pattern = re.compile(
        r'<section\s[^>]*data-title\s*=\s*"([^"]*)"[^>]*>',
        re.IGNORECASE
    )
    for m in pattern.finditer(html):
        title = unescape(m.group(1))
        sections.append({
            "title": title,
            "offset": m.end(),
        })

    # Also capture <h1>-<h3> tags as fallback
    if not sections:
        pattern2 = re.compile(r'<h([1-3])\b[^>]*>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)
        for m in pattern2.finditer(html):
            sections.append({
                "title": unescape(strip_tags(m.group(2))),
                "offset": m.end(),
            })

    return sections

def extract_section_content(html: str, section_title: str, sections: list[dict]) -> str | None:
    # Find the section
    idx = None
    for i, sec in enumerate(sections):
        if section_title.lower() in sec["title"].lower():
            idx = i
            break

    if idx is None:
        return None

    start = sections[idx]["offset"]
    end = sections[idx + 1]["offset"] if idx + 1 < len(sections) else len(html)
    content = html[start:end]

    # Clean to plain text
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<[^>]+>', '\n', content)
    content = re.sub(r'\n\s*\n', '\n\n', content)
    return content.strip()

def extract_all_sections_content(html: str, sections: list[dict]) -> dict[str, str]:
    """Extract clean text for every section. Returns {title: content}."""
    result = {}
    for i, sec in enumerate(sections):
        start = sec["offset"]
        end = sections[i + 1]["offset"] if i + 1 < len(sections) else len(html)
        content = html[start:end]
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'<[^>]+>', '\n', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = unescape(content.strip())
        result[sec["title"]] = content
    return result

def _unescape_titles(sections: list[dict]) -> list[dict]:
    """Unescape HTML entities in section titles (handles cached data)."""
    for sec in sections:
        sec["title"] = unescape(sec["title"])
    return sections

def _unescape_content_keys(content: dict[str, str]) -> dict[str, str]:
    """Unescape HTML entities in content dict keys (handles cached data)."""
    return {unescape(k): v for k, v in content.items()}

def _cache_path(html_path: str, suffix: str) -> str:
    """Derive cache path: replace .html with the given suffix."""
    base, _ = os.path.splitext(html_path)
    return base + suffix

def _read_cache(cache_path: str) -> str | None:
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def _write_cache(cache_path: str, data) -> None:
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/extract_sections.py <html-file> [section-name-pattern]", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]

    if len(sys.argv) >= 3:
        # Section content extraction mode
        pattern = sys.argv[2]
        content_cache = _cache_path(html_path, ".sections_content.json")

        # Try cache first
        cached = _read_cache(content_cache)
        if cached is not None:
            all_content = _unescape_content_keys(json.loads(cached))
        else:
            # Cache miss: need HTML to extract everything
            if not os.path.exists(html_path):
                print(f"Error: {html_path} not found and no cache at {content_cache}", file=sys.stderr)
                sys.exit(1)
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            sections = find_sections(html)
            all_content = extract_all_sections_content(html, sections)
            _write_cache(content_cache, all_content)

        # Find the matching section
        for title, content in all_content.items():
            if pattern.lower() in title.lower():
                print(content)
                return
        print(f"Section matching '{pattern}' not found.", file=sys.stderr)
        sys.exit(1)
    else:
        # Section listing mode
        listing_cache = _cache_path(html_path, ".sections.json")

        # Try cache first
        cached = _read_cache(listing_cache)
        if cached is not None:
            sections = _unescape_titles(json.loads(cached))
        else:
            # Cache miss: need HTML
            if not os.path.exists(html_path):
                print(f"Error: {html_path} not found and no cache at {listing_cache}", file=sys.stderr)
                sys.exit(1)
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            sections = find_sections(html)
            _write_cache(listing_cache, sections)

        print(f"Found {len(sections)} sections:")
        for i, sec in enumerate(sections):
            print(f"  [{i}] offset={sec['offset']}: {sec['title']}")

if __name__ == "__main__":
    main()
