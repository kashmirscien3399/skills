#!/usr/bin/env python3
"""Convert LaTeX math to human-readable plain text.

Usage: python3 scripts/latex_simplify.py <latex-string>
   Or: echo "<latex>" | python3 scripts/latex_simplify.py
Output: simplified plain text representation.

Auto-caching: results are cached in ~/.cache/arxiv-reading/latex_simplify_cache.json
keyed by MD5 hash of the input LaTeX string. Subsequent runs with the same input
return cached results.
"""
import sys, os, re, json, hashlib

CACHE_DIR = os.path.expanduser("~/.cache/arxiv-reading")
CACHE_FILE = os.path.join(CACHE_DIR, "latex_simplify_cache.json")

GREEK = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\varepsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η',
    r'\theta': 'θ', r'\vartheta': 'θ', r'\iota': 'ι', r'\kappa': 'κ',
    r'\lambda': 'λ', r'\mu': 'μ', r'\nu': 'ν', r'\xi': 'ξ',
    r'\omicron': 'ο', r'\pi': 'π', r'\rho': 'ρ', r'\sigma': 'σ',
    r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ', r'\varphi': 'φ',
    r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ',
    r'\Psi': 'Ψ', r'\Omega': 'Ω',
}

def simplify(tex: str) -> str:
    # Remove \displaystyle, \textstyle, etc.
    tex = re.sub(r'\\(displaystyle|textstyle|scriptstyle)', '', tex)
    # Remove \left, \right, \big, \Big, \bigg, \Bigg
    tex = re.sub(r'\\(left|right|big[lr]?|Big[lr]?|bigg[lr]?|Bigg[lr]?)\b', '', tex)
    # \tag{...} -> [eq ...]
    tex = re.sub(r'\\tag\s*\{([^}]*)\}', r'[eq \1]', tex)
    # \label{...} -> remove
    tex = re.sub(r'\\label\s*\{[^}]*\}', '', tex)
    # \frac{a}{b} -> (a/b)
    tex = re.sub(r'\\frac\s*\{([^}]*)\}\s*\{([^}]*)\}', r'(\1/\2)', tex)
    # \sum -> sum, \int -> integral, \prod -> prod
    tex = re.sub(r'\\sum', 'sum', tex)
    tex = re.sub(r'\\int', 'integral', tex)
    tex = re.sub(r'\\prod', 'prod', tex)
    tex = re.sub(r'\\partial', 'd', tex)
    tex = re.sub(r'\\infty', '∞', tex)
    tex = re.sub(r'\\to', '→', tex)
    tex = re.sub(r'\\mapsto', '↦', tex)
    tex = re.sub(r'\\subset', '⊂', tex)
    tex = re.sub(r'\\subseteq', '⊆', tex)
    tex = re.sub(r'\\supset', '⊃', tex)
    tex = re.sub(r'\\supseteq', '⊇', tex)
    tex = re.sub(r'\\in', '∈', tex)
    tex = re.sub(r'\\notin', '∉', tex)
    tex = re.sub(r'\\nabla', '∇', tex)
    tex = re.sub(r'\\times', '×', tex)
    tex = re.sub(r'\\cdot', '·', tex)
    tex = re.sub(r'\\dots', '…', tex)

    # \mathbb{R} -> R, \mathcal{X} -> script-X, \mathrm{text} -> text
    tex = re.sub(r'\\mathbb\{([^}]*)\}', r'\1', tex)
    tex = re.sub(r'\\mathcal\{([^}]*)\}', r'script-\1', tex)
    tex = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', tex)
    tex = re.sub(r'\\mathbf\{([^}]*)\}', r'\1', tex)
    tex = re.sub(r'\\mathit\{([^}]*)\}', r'\1', tex)

    # Greek letters
    for cmd, char in GREEK.items():
        tex = tex.replace(cmd, char)

    # Superscripts and subscripts: keep as-is (they're readable)
    # Remove redundant braces
    tex = re.sub(r'\{\}', '', tex)

    # Collapse spaces
    tex = re.sub(r'\s+', ' ', tex).strip()

    return tex

def _load_cache() -> dict[str, str]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def _save_cache(cache: dict[str, str]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def _hash_key(tex: str) -> str:
    return hashlib.md5(tex.encode("utf-8")).hexdigest()

def main():
    if len(sys.argv) >= 2:
        tex = " ".join(sys.argv[1:])
    else:
        tex = sys.stdin.read().strip()

    if not tex:
        print("Usage: python3 scripts/latex_simplify.py <latex-string>", file=sys.stderr)
        sys.exit(1)

    # Check cache
    cache = _load_cache()
    key = _hash_key(tex)
    if key in cache:
        print(cache[key])
        return

    # Compute and cache
    result = simplify(tex)
    cache[key] = result
    _save_cache(cache)
    print(result)

if __name__ == "__main__":
    main()
