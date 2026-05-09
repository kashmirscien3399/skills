#!/usr/bin/env python3
"""Extract LaTeX equations from ar5iv HTML.

Usage: python3 scripts/extract_eqs.py <html-file>
Output: JSON array of {index, tex, context_before, context_after, eq_number} objects to stdout.

Auto-caching: results are cached as <html-file>.eqs.json. Subsequent runs read from cache
even if the HTML file no longer exists.
"""
import sys, os, re, json
from html.parser import HTMLParser

class AnnotationExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_annotation = False
        self.in_math = 0
        self.current_tex = []
        self.equations = []
        self.text_buf = []
        self.tag_stack = []
        self._context_before = ""
        # Equation number tracking for ar5iv HTML structure
        self._in_tag_span = False
        self._current_tag = []
        self._pending_tag: str | None = None

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        attrs_dict = dict(attrs)
        if tag == "annotation" and attrs_dict.get("encoding") == "application/x-tex":
            self.in_annotation = True
            self.current_tex = []
        elif tag == "math":
            self.in_math += 1
            self._context_before = "".join(self.text_buf[-200:])  # keep recent text
        elif tag == "span" and "ltx_tag_equation" in attrs_dict.get("class", ""):
            # ar5iv renders equation numbers as <span class="ltx_tag ltx_tag_equation">(N)</span>
            # in the equation-number cell, which appears BEFORE the math cell in HTML.
            self._in_tag_span = True
            self._current_tag = []

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        if tag == "span" and self._in_tag_span:
            # End of equation-number span: save the captured text
            self._in_tag_span = False
            tag_text = "".join(self._current_tag).strip()
            if tag_text:
                self._pending_tag = tag_text
            self._current_tag = []
        if tag == "annotation" and self.in_annotation:
            self.in_annotation = False
            tex = "".join(self.current_tex).strip()
            if tex:
                # Use pending tag (from ar5iv HTML), fall back to \tag/\label in LaTeX source
                eq_num = self._pending_tag if self._pending_tag else self._extract_eq_number(tex)
                self._pending_tag = None  # consumed
                self.equations.append({
                    "index": len(self.equations),
                    "tex": tex,
                    "context_before": self._context_before.strip()[-300:],
                    "context_after": "",
                    "eq_number": eq_num,
                })
        elif tag == "math":
            self.in_math = max(0, self.in_math - 1)

    def handle_data(self, data):
        if self.in_annotation:
            self.current_tex.append(data)
        elif self._in_tag_span:
            self._current_tag.append(data)
        else:
            self.text_buf.append(data)

    def _extract_eq_number(self, tex: str) -> str | None:
        m = re.search(r'\\tag\s*\{([^}]+)\}', tex)
        if m:
            return m.group(1)
        m = re.search(r'\\label\s*\{([^}]+)\}', tex)
        if m:
            return m.group(1)
        return None

def _cache_path(html_path: str) -> str:
    """Derive cache path from HTML path: replace .html with .eqs.json."""
    base, _ = os.path.splitext(html_path)
    return base + ".eqs.json"

def _read_cache(cache_path: str) -> str | None:
    """Read cached equations JSON. Returns None if cache doesn't exist."""
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def _write_cache(cache_path: str, equations: list) -> None:
    """Write equations to cache file."""
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(equations, f, indent=2, ensure_ascii=False)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/extract_eqs.py <html-file>", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    cache = _cache_path(html_path)

    # Try cache first (works even if HTML is gone)
    cached = _read_cache(cache)
    if cached is not None:
        print(cached)
        return

    # Cache miss: need HTML to extract
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found and no cache at {cache}", file=sys.stderr)
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    extractor = AnnotationExtractor()
    extractor.feed(html)

    _write_cache(cache, extractor.equations)
    print(json.dumps(extractor.equations, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
