#!/usr/bin/env python3
"""Check whether a source is already in the corpus, before capturing it.

Matches a URL, arXiv ID, or title against every entry's url/paper/id/title. Prints one line
per query: EXISTS for a definitive key match, SIMILAR for a fuzzy title match that needs a
human call, NEW otherwise. Exits 1 if any query matched, 2 on a usage or corpus error.

    python3 bin/find_source.py https://arxiv.org/pdf/2511.04898v1 [more...] [--kb PATH]
"""
import argparse
import difflib
import glob
import os
import re
import sys

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
ARXIV_ID = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")
TRACKING_PARAM = re.compile(r"^(utm_[a-z]+|fbclid|gclid|ref|ref_src|source)=")
TITLE_NOISE = re.compile(r"[^a-z0-9]+")
DIGITS = re.compile(r"\d+")
FUZZY_TITLE_THRESHOLD = 0.85
MIN_FUZZY_QUERY_LEN = 12


def normalize_url(raw):
    """Reduce a URL to a comparable key: no scheme, host prefix, tracking params, or arXiv variant."""
    url = raw.strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    url = url.split("#")[0]
    if "?" in url:
        base, _, query = url.partition("?")
        kept = sorted(p for p in query.split("&") if p and not TRACKING_PARAM.match(p))
        url = base + ("?" + "&".join(kept) if kept else "")
    url = url.rstrip("/")
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^(github\.com/[^/]+/[^/]+)/(tree|blob|commit)/.*$", r"\1", url)
    url = re.sub(r"^arxiv\.org/(abs|pdf)/", "arxiv.org/", url)
    url = re.sub(r"\.pdf$", "", url)
    if url.startswith("arxiv.org/"):
        url = re.sub(r"v\d+$", "", url)
    return url


def normalize_title(raw):
    """Reduce a title to lowercase alphanumerics for fuzzy comparison."""
    return TITLE_NOISE.sub(" ", raw.strip().lower().strip('"')).strip()


def field(front, name):
    m = re.search(rf"^{name}:\s*(.+?)$", front, re.M)
    return m.group(1).strip().strip('"') if m else ""


def load_corpus(kb):
    """Return one record per entry: its id, title, capture date, and every key it matches on."""
    corpus = []
    for path in sorted(glob.glob(os.path.join(kb, "entries", "*.md"))):
        m = FRONTMATTER.match(open(path).read())
        if not m:
            sys.exit(f"FATAL: {path}: no YAML frontmatter")
        front = m.group(1)
        urls = [field(front, "url"), field(front, "paper")]
        keys = {normalize_url(u) for u in urls if u}
        keys |= {i for u in urls for i in ARXIV_ID.findall(u)}
        entry_id = field(front, "id") or os.path.basename(path)[:-3]
        keys.add(entry_id.lower())
        keys |= set(ARXIV_ID.findall(entry_id))
        title = field(front, "title")
        keys.add(normalize_title(title))
        corpus.append({"id": entry_id, "title": title, "keys": keys,
                       "captured": field(front, "capture") or "no capture date",
                       "norm_title": normalize_title(title)})
    return corpus


def match(query, corpus):
    """Return (entry, how, detail) for a query that already exists, or None.

    Exact key matches are definitive. Fuzzy title matches are reported with their ratio, and
    flagged when the two titles differ in their digits — a version bump is a new source.
    """
    keys = {normalize_url(query), query.strip().lower(),
            normalize_title(query)} | set(ARXIV_ID.findall(query))
    for entry in corpus:
        if keys & entry["keys"]:
            return entry, "EXISTS", "exact key match"
    probe = normalize_title(query)
    if len(probe) < MIN_FUZZY_QUERY_LEN:
        return None
    best, best_ratio = None, 0.0
    for entry in corpus:
        ratio = difflib.SequenceMatcher(None, probe, entry["norm_title"]).ratio()
        if ratio > best_ratio:
            best, best_ratio = entry, ratio
    if best_ratio < FUZZY_TITLE_THRESHOLD:
        return None
    detail = f"title {best_ratio:.3f}"
    if DIGITS.findall(probe) != DIGITS.findall(best["norm_title"]):
        detail += " — DIGITS DIFFER, likely a different version, check before skipping"
    return best, "SIMILAR", detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+", help="URLs, arXiv IDs, or titles to check")
    ap.add_argument("--kb", default=os.environ.get("KB_PATH"),
                    help="corpus root (default: $KB_PATH)")
    args = ap.parse_args()
    if not args.kb:
        sys.exit("FATAL: pass --kb or set KB_PATH; refusing to guess the corpus location")
    if not os.path.isdir(os.path.join(args.kb, "entries")):
        sys.exit(f"FATAL: {args.kb} has no entries/ directory")

    corpus = load_corpus(args.kb)
    hits = 0
    for query in args.queries:
        found = match(query, corpus)
        if not found:
            print(f"NEW      {query}")
            continue
        hits += 1
        entry, verdict, detail = found
        print(f"{verdict:<8} {query}\n         -> {entry['id']} ({detail})"
              f"\n            captured {entry['captured']}: {entry['title']}")
    return 1 if hits else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str):      # sys.exit("FATAL: ...") — report it, then exit 2
            print(e.code, file=sys.stderr)
            raise SystemExit(2)
        raise
