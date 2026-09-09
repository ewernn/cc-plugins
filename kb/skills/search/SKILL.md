---
name: search
description: Find things in the knowledge base — entries by loose description, or verbatim passages with a citable location. Use when asked to find, recall, look up, or cite something from the KB.
---

# Search the knowledge base

Two different questions, two different depths. Work out which one is being asked before you
start, because answering the wrong one wastes a lot of reading.

| Question | Depth | Method |
|---|---|---|
| "that paper about the thing where…" | 1 | read `INDEX.md`, match on meaning |
| "what did it actually find?" | 2 | read the matching entries |
| "quote me the exact line" | 3 | ripgrep `fulltext/` |

Read `$KB_PATH` first. If it is unset, stop and say so.

## Depth 1 — find the entry

`INDEX.md` carries one line per entry: title, id, date, tags, and the Setup sentence.

**Read it and match on meaning.** You are the semantic search — there is no embedding index
and there does not need to be. A vague description matches a title and a Setup sentence
because you can reason about what the person meant, which is more than a distance metric
does. Do not grep for the user's literal words and report nothing found; that is the failure
mode this design exists to avoid.

Scale, so you know when to change tactics:

- Under ~350 entries: read the whole index. It fits.
- Above that: narrow first with `rg` on `INDEX.md` for a plausible tag or two, then read the
  matching lines. Tags are in the index precisely to make this filter cheap.

Prefer a tag filter over a keyword filter when narrowing. Keywords miss synonyms; tags were
assigned by someone who read the paper.

## Depth 2 — read the entry

Read `entries/<id>.md`. The body is the summary, and it carries exact figures, so quote from
it rather than paraphrasing numbers.

If the entry is a stub — no `enriched:` field — say so. Its tags are provisional and its
claims are the source's own abstract, not a verified summary. Offer to run `enrich-entry`.

## Depth 3 — the verbatim quote

Only when the answer must be exact, or a claim needs checking against the source.

```bash
rg -n --heading "<phrase>" "$KB_PATH/fulltext/"
```

Full text is plain markdown, so this is fast — milliseconds over the whole corpus — and it
gives you a file and line number, which is what makes a quote citable. Report the location
alongside the quote.

Search terms with punctuation need care: `rg -F` for a literal string, and remember that
identifiers like `CVE-2024-1234` or `C++` break under naive tokenizing. `rg` handles them
literally, which is exactly why this is a grep and not a keyword index.

## When nothing matches

Say so plainly, and say what you searched. Then check the obvious failure: is the thing
captured but missing from `INDEX.md`? Compare `ls entries/*.md | wc -l` against the index's
own count. A stale index is the one bug that makes a present entry invisible, and the fix is
to rebuild it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/build_index.py" --kb "$KB_PATH"
```

Never invent an entry that is not there, and never answer from your own knowledge of a paper
while implying it came from the corpus. If it is not in the KB, the answer is that it is not
in the KB.
