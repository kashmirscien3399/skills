#!/usr/bin/env python3
"""Fetch all papers that cite a given arXiv paper via INSPIRE-HEP API.

Usage:
    python3 fetch_citations.py --out-dir <cache_dir> <arxiv_id>
    python3 fetch_citations.py --out-dir <cache_dir> --topic <keyword> <arxiv_id>

Output:
    Markdown file: <cache_dir>/arXiv_<arxiv_id>_citations.md
    Compact format: N. Title | Authors | cited N | arXiv:ID
    Authors truncated to first 6 + "et al." for large collaborations.
"""

import argparse
import os
import sys
import time
from urllib.parse import quote

import requests

INSPIRE_API = "https://inspirehep.net/api/literature"
MAX_AUTHORS = 6


def search_paper(arxiv_id):
    url = f"{INSPIRE_API}?q=arXiv:{arxiv_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        print(f"No INSPIRE record found for arXiv:{arxiv_id}", file=sys.stderr)
        sys.exit(1)
    rec = hits[0]
    recid = rec["id"]
    citation_count = rec["metadata"].get("citation_count", 0)
    return recid, citation_count


def authors_string(meta):
    """Build comma-separated author string, truncated to MAX_AUTHORS + 'et al.'"""
    authors = meta.get("authors", [])
    names = [a.get("full_name", "Unknown") for a in authors]
    if len(names) > MAX_AUTHORS:
        return ", ".join(names[:MAX_AUTHORS]) + " et al."
    return ", ".join(names)


def fetch_citing_papers(recid):
    all_papers = []
    page = 1
    size = 250
    while True:
        url = f"{INSPIRE_API}?q=refersto:recid:{recid}&sort=mostrecent&size={size}&page={page}"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break
        for hit in hits:
            meta = hit.get("metadata", {})
            titles = meta.get("titles", [{}])
            title = titles[0].get("title", "Unknown") if titles else "Unknown"
            arxiv_eprints = meta.get("arxiv_eprints", [])
            arxiv_id = arxiv_eprints[0].get("value", "") if arxiv_eprints else ""
            paper = (
                title,
                authors_string(meta),
                meta.get("citation_count", 0),
                arxiv_id,
            )
            all_papers.append(paper)
        page += 1
        total = data.get("hits", {}).get("total", 0)
        if len(all_papers) >= total:
            break
        time.sleep(0.2)
    return all_papers


def main():
    parser = argparse.ArgumentParser(
        description="Fetch all papers citing a given arXiv paper via INSPIRE-HEP"
    )
    parser.add_argument("arxiv_id", help="arXiv ID (e.g., 0911.3380)")
    parser.add_argument("--out-dir", required=True, help="Cache directory")
    parser.add_argument("--topic", default="", help="Topic filter (stored in output header)")
    args = parser.parse_args()

    arxiv_id = args.arxiv_id.strip()
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    output_file = os.path.join(out_dir, f"arXiv_{arxiv_id}_citations.md")

    print(f"Searching INSPIRE for arXiv:{arxiv_id}...")
    recid, total_citations = search_paper(arxiv_id)
    print(f"Found INSPIRE record {recid} with {total_citations} citations")

    print(f"Fetching all {total_citations} citing papers...")
    papers = fetch_citing_papers(recid)
    print(f"Retrieved {len(papers)} papers")

    lines = []
    lines.append(f"# Citing Papers for arXiv:{arxiv_id}")
    header = f"**Total:** {len(papers)} papers"
    if args.topic:
        header += f" | **Topic:** {args.topic}"
    lines.append(header)
    lines.append("")
    for i, (title, authors, cited, aid) in enumerate(papers, 1):
        aid_str = f"arXiv:{aid}" if aid else "(no arXiv ID)"
        lines.append(f"{i}. {title} | {authors} | cited {cited} | {aid_str}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Cached to {output_file}")
    print(f"File size: {os.path.getsize(output_file)} bytes")


if __name__ == "__main__":
    main()
