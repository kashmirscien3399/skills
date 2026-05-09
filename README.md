# Literature Skills

This directory contains research-oriented skills for agent workflows:

- `arxiv-reading`: read an arXiv paper, extract sections and equations, and build a reusable memory file.
- `cited-by`: fetch papers that cite a target arXiv paper, filter them by topic, and optionally hand selected papers off to `arxiv-reading`.

These skills are designed for agent-assisted literature review. The agent should choose the skill based on the user's request, run the provided scripts, and keep all generated cache files in the user's working directory rather than inside this repository.

## Skill Summary

### `arxiv-reading`

Use this skill when the user gives an arXiv ID and wants to:

- read or summarize the paper
- extract equations
- inspect specific sections
- understand derivations or references

Main workflow:

1. Check whether cached files already exist under `<user-working-dir>/arxiv-reading/`.
2. If needed, download the paper's ar5iv HTML with `scripts/fetch.py`.
3. Extract equations with `scripts/extract_eqs.py`.
4. Extract sections with `scripts/extract_sections.py`.
5. Simplify LaTeX snippets with `scripts/latex_simplify.py` when needed.
6. Write a paper memory file at `<user-working-dir>/arxiv-reading/<arxiv-id>.memory.md`.

Key outputs:

- `<arxiv-id>.html`
- `<arxiv-id>.eqs.json`
- `<arxiv-id>.sections.json`
- `<arxiv-id>.sections_content.json`
- `<arxiv-id>.memory.md`

### `cited-by`

Use this skill when the user wants to find papers that cite a given arXiv paper, especially with a topical filter.

Main workflow:

1. Check for a cached citation list under `<user-working-dir>/arxiv-reading/`.
2. If needed, fetch citing papers from INSPIRE-HEP with `scripts/fetch_citations.py`.
3. Filter the cached results by topic.
4. Present candidate papers to the user.
5. If the user approves papers for deeper reading, delegate those papers to `arxiv-reading`.
6. Write a final report at `<user-working-dir>/arxiv-reading/<arxiv-id>_citing_report_<topic>.md`.

Key outputs:

- `arXiv_<arxiv-id>_citations.md`
- `<arxiv-id>_citing_report_<topic>.md`

## How To Use With Agents

## 1. Let the agent infer the skill from the request

The simplest approach is to ask in natural language. If the prompt clearly matches one of the skill descriptions, the agent should apply that skill.

Example prompts:

```text
Read arXiv:2508.12856 and summarize the introduction, main equations, and references.
```

```text
Extract the equations from arXiv:2508.12856 and explain equation (12).
```

```text
Find papers citing arXiv:0911.3380 about cosmology.
```

```text
In papers citing arXiv:0911.3380, look for work related to primordial black holes.
```

## 2. Use the skills together

The intended multi-step agent flow is:

1. Use `cited-by` to collect and rank citing papers.
2. Ask the user which papers should be read in detail.
3. Use `arxiv-reading` on the approved papers.
4. Produce a combined report.

This keeps the expensive reading step limited to papers the user actually wants.

## 3. Pass the correct working directory

Both skills assume cache and report files are written under the user's working directory:

```text
<user-working-dir>/arxiv-reading/
```

The agent should use the absolute session working directory from its runtime context. Do not rely on `$PWD` or `os.getcwd()`, because the skill may execute from its installation directory instead of the user's project directory.

## Script Reference

### `arxiv-reading/scripts`

| Script | Purpose |
| --- | --- |
| `fetch.py` | Download ar5iv HTML for an arXiv paper |
| `extract_eqs.py` | Extract numbered equations and context |
| `extract_sections.py` | List sections or extract section text |
| `latex_simplify.py` | Convert LaTeX math into readable plain text |

### `cited-by/scripts`

| Script | Purpose |
| --- | --- |
| `fetch_citations.py` | Fetch and cache citing papers from INSPIRE-HEP |

## Agent Notes

- Prefer cached files before downloading or re-fetching data.
- Use `arxiv-reading` for direct paper analysis.
- Use `cited-by` for citation discovery and paper selection.
- Ask for confirmation before reading many citing papers in depth.
- Store generated artifacts in the user's working directory, not in this repository.