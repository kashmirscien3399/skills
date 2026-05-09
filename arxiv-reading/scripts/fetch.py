#!/usr/bin/env python3
"""Download ar5iv HTML for a given arXiv ID.

Usage: python3 scripts/fetch.py --out-dir <directory> <arxiv-id>
   Or: python3 scripts/fetch.py --out-dir /abs/path/arxiv-reading 0911.3380

The --out-dir must be an absolute path. The script does NOT auto-detect
the working directory — the caller must provide it explicitly.
"""
import sys, os, requests, re, argparse

def sanitize_id(raw: str) -> str:
    m = re.search(r'(?:arxiv\s*[:.\s]*)?(\d{4}\.\d{4,5})(?:v\d+)?', raw, re.I)
    if not m:
        raise ValueError(f"Could not extract arXiv ID from: {raw}")
    return m.group(1)

def main():
    parser = argparse.ArgumentParser(description="Download ar5iv HTML")
    parser.add_argument("--out-dir", required=True,
                        help="Absolute path to cache directory (e.g. /home/user/project/arxiv-reading)")
    parser.add_argument("arxiv_id", help="arXiv ID (e.g. 0911.3380)")
    args = parser.parse_args()

    out_dir = args.out_dir
    arxiv_id = sanitize_id(args.arxiv_id)
    url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{arxiv_id}.html")

    try:
        resp = requests.get(url, timeout=60, headers={"User-Agent": "arxiv-reading-skill/1.0"})
        if resp.status_code == 404:
            print(f"Error: ar5iv page not found for {arxiv_id} (HTTP 404)", file=sys.stderr)
            sys.exit(1)
        resp.raise_for_status()
    except requests.ConnectionError:
        print(f"Error: Could not connect to ar5iv — network may be blocked.", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Error: HTTP request failed: {e}", file=sys.stderr)
        sys.exit(1)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)

    print(f"Downloaded {url} -> {out_path}")

if __name__ == "__main__":
    main()
