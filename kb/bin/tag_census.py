#!/usr/bin/env python3
"""Report tag usage, co-occurrence, and registry drift across entries/.

Mechanical signals only — no judgment. The kb-reconcile skill reads this and decides.

    python3 bin/tag_census.py [--min-uses N]
"""
import argparse
import collections
import glob
import itertools
import os
import re
import sys

def _root(explicit):
    root = explicit or os.environ.get("KB_PATH")
    if not root:
        sys.exit("FATAL: pass --kb or set KB_PATH; refusing to guess the corpus location")
    return root
TAG_LINE = re.compile(r"^- `([a-z]+:[a-z0-9-]+)`\s+—\s+(.+)$", re.M)
FRONT_TAGS = re.compile(r"^tags:\s*\[(.*?)\]\s*$", re.M | re.S)


def load_registry():
    path = os.path.join(ROOT, "tags.md")
    if not os.path.exists(path):
        sys.exit(f"FATAL: no registry at {path}")
    described = dict(TAG_LINE.findall(open(path).read()))
    if not described:
        sys.exit(f"FATAL: registry at {path} defines no tags — check its format")
    return described


def load_entries():
    entries = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "entries", "*.md"))):
        m = FRONT_TAGS.search(open(path).read())
        name = os.path.basename(path)
        if not m:
            entries[name] = []
            continue
        entries[name] = [t.strip() for t in m.group(1).split(",") if t.strip()]
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=None, help="corpus root (default: $KB_PATH)")
    ap.add_argument("--min-uses", type=int, default=2,
                    help="tags used fewer times than this are merge candidates")
    args = ap.parse_args()
    global ROOT
    ROOT = _root(args.kb)

    registry = load_registry()
    entries = load_entries()
    if not entries:
        sys.exit("FATAL: no entries found under entries/")

    uses = collections.Counter(t for tags in entries.values() for t in tags)
    pairs = collections.Counter()
    for tags in entries.values():
        for a, b in itertools.combinations(sorted(set(tags)), 2):
            pairs[(a, b)] += 1

    print(f"entries: {len(entries)}   registry: {len(registry)} tags   "
          f"assignments: {sum(uses.values())}")

    unregistered = {t: n for t, n in uses.items() if t not in registry}
    if unregistered:
        print("\nUNREGISTERED tags in use (registry violation):")
        for t, n in sorted(unregistered.items()):
            print(f"  {t}  x{n}")

    unused = [t for t in registry if t not in uses]
    print(f"\nnever used ({len(unused)}) — fine while the corpus is small, "
          f"merge candidates once it is not:")
    print("  " + ", ".join(sorted(unused)) if unused else "  (none)")

    thin = sorted((n, t) for t, n in uses.items() if n < args.min_uses)
    print(f"\nused fewer than {args.min_uses} times ({len(thin)}) — "
          f"the registry says a tag must span many entries:")
    for n, t in thin:
        print(f"  {t}  x{n}")

    print("\nredundancy suspects — pairs that almost always travel together:")
    found = False
    for (a, b), n in pairs.most_common():
        if n < 2:
            break
        # flag only when co-occurrence explains most of BOTH tags' usage
        if n >= 0.8 * uses[a] and n >= 0.8 * uses[b]:
            print(f"  {a} + {b}  together x{n}  (of {uses[a]} / {uses[b]})")
            found = True
    if not found:
        print("  (none)")

    print("\nper-entry tag counts:")
    for name, tags in sorted(entries.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(tags):>2}  {name}")

    facets = collections.Counter(t.split(":")[0] for t in uses.elements())
    print("\nassignments per facet: " +
          "  ".join(f"{f}={n}" for f, n in sorted(facets.items())))


if __name__ == "__main__":
    main()
