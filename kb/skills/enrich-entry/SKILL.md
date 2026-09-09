---
name: enrich-entry
description: Deep-read a source into a full summary — read the whole paper, tag it, verify every figure. Use when asked to enrich, summarize, deep-read, or work through the capture backlog.
---

# Enrich an entry

Turn one source into a full summary, read from the whole text and verified against it.

Read `$KB_PATH` first. If it is unset, stop and say so — never guess the corpus location.
Every path below is relative to it.

Works on a stub left by `capture-entry`, or straight from a link. To work the backlog, find
the stubs — entries with no `enriched:` field — and take them oldest first:

```bash
grep -L '^enriched:' "$KB_PATH"/entries/*.md
```

If the entry already has `enriched:`, stop and say so. Do not silently overwrite a summary
someone may have edited. A stub carries provisional tags and a verbatim abstract; replace
both, since you are about to know much more than whoever captured it.

## 0. Fetch the source

Read the **full text**, not the abstract. A summary written from an abstract is the single
most common failure here and it is not acceptable.

- **arXiv:** archive it first, then read it:

  ```
  fetch_arxiv_paper(arxiv_id="<id>", save_to="$KB_PATH/fulltext/arxiv-<id>.md")
  ```

  That writes depth 3 byte-for-byte and returns only a receipt, so the text never passes
  through your context on the way to disk — retyping it back out is how summaries silently
  lose content. Then read what you need with `Read`, or page with `chunk=N`.

  References are dropped by default; they are half a typical paper and nothing in a summary
  needs them. Pass `include_references=True` only for citation work. Math comes back as
  LaTeX (`$R^{2}=0.96$`), so quote figures from it exactly.
- GitHub repo: read the README, then the entry-point source files. Claims in a README are
  marketing until the code agrees.
- Web article or PDF: WebFetch, or Read for a local PDF.

If you cannot get the full text, say so and stop. Do not write a summary from metadata and
do not mark it `enriched`.

## 1. Tag from the registry

Read `tags.md` at the corpus root **first, every time**. It is the vocabulary.

- Reuse an existing tag whenever one fits. Be reluctant to coin.
- Coining means appending to `tags.md` with a one-line description, in the right facet,
  in the same commit. Never write a tag that is not in the file.
- `topic:`, `use:` and `artifact:` are required. `method:` applies only when the source has
  a technique; `seat:` only when something adversarial is happening. Omit a facet that does
  not apply — there is no "none" value, and reaching for one is how tags stop meaning things.
- `use:` is the facet that gets skipped and the one that earns its keep. It is what links a
  security benchmark to an ML paper, which is the whole point of tagging a general corpus.
- Do not tag by title keyword. Tag by what the work actually does. A paper with "agent" in
  the title that never runs one is not `topic:tool-use`.
- **There is no target number of tags.** Assign what is true. If the count feels high,
  check whether two of them are near-duplicates and report that — never drop a tag that
  applies in order to hit a number.
- The registry is organized by area and areas are incomplete by design. A source from a
  field not listed is a gap in `tags.md`, not a source that does not belong. Report it.

## 2. Write the summary

Format, in this order. This template is eval-derived: each rule below cost an iteration.

```
Setup:        <the problem or question, one sentence>
Methodology:  <what they DID — technique, data, models. Include the decisive specifics:
               which layers or token positions, the experimental controls, how key
               quantities were computed>
Findings:     (1) ... (2) ... (3) ...  numbered, with EXACT figures
Scope:        <what was NOT tested; what the result does and does not cover>
Connections:  <OPTIONAL — only when the contribution IS a theoretical link. Omit for
               empirical papers>
Useful?:      <one line: concrete relevance to the reader, profile below>
```

Rules, in priority order:

1. **Exact numbers, never rounded.** Write `91% vs 39%`, not "more than doubled". Rounding
   is what lost the findings dimension to the human gold summary in the original eval.
2. **Length is an output, not a target.** There is no word count to hit. Every sentence
   must carry an exact figure, a decisive method specific, or a scope limit. If a sentence
   carries none of those, cut it — and keep cutting until every remaining one does. A thin
   paper yields a short entry; a figure-dense one yields a longer entry honestly.
   Never pad toward a number, and never drop a verified figure to reach one. Before you
   write the file, re-read the body and delete every sentence that survives only because it
   sounds like something a summary should say.
3. **Do not assert precision you cannot verify.** If the appendix is truncated, write
   "several", not a guessed count. An invented number is worse than a missing one.
4. **Scope is not optional.** What the paper did not test is what tells you whether it
   transfers to your range.
5. **`Connections` stays omitted** unless the contribution genuinely is a link between
   ideas. Forcing it is how bloat returns.

Reader profile for the `Useful?` line — security evaluation gyms and ranges, RL
(Reinforcement Learning) for upskilling agents, red and blue seat design, SOC (Security
Operations Center) agents, scoring surfaces and vantage points, and how realistic an
environment has to be. Write the line against *that*, or it comes out generic. Treat it as
a draft for the reader to edit; genuine relevance is their call, not yours.

## 2b. Verify the summary before you write it

Mandatory. Re-read your draft against the full text and check, one at a time:

- **Every number.** Find it in the source. A figure you cannot locate comes out.
- **Every attribution.** Which model, which system, which team. Naming the wrong one is the
  easiest error to make and the hardest to catch later.
- **Every experimental condition.** Results from different conditions must not end up in one
  sentence. Ask of each claim: was this measured with the mitigation on or off, the filter
  enabled or disabled, at which time limit? A sentence that merges two conditions reads as
  fluent and is simply false.
- **Every superlative and every aggregate.** "All models dropped to zero" is wrong if one
  retained two. Totals that span multiple runs must say so.

Then hand the draft and the full text to a **second reader** — a subagent, with the paper
and the draft, asked to find what is wrong. Do not tell it what you think is right.

The two passes catch different things, and this is measured, not assumed. Across the first
fifteen entries the self-check reliably caught arithmetic and attribution: wrong figure,
wrong model, merged conditions. It reliably missed *framing* and *omission* — a test-time
procedure described as a training arm, a superlative the source contradicts, an author-stated
limitation left out, a claim whose scope quietly widened. Every agent whose self-check came
back clean still had errors of the second kind found by an independent reader.

Ask the second reader for three things specifically: claims the source does not support,
author-stated limitations the draft omits, and any sentence whose framing implies more than
the source shows.

## 3. Write the file

One file, `entries/<id>.md`. The id is type-prefixed: `arxiv-2502.16681`, `gh-owner-repo`,
`web-<slug>`.

```md
---
title: Attention Is All You Need
url: https://arxiv.org/abs/1706.03762
id: arxiv-1706.03762
published: 2017-06-12
added: <today, ISO>
tags: [topic:tool-use, use:baseline-method, method:prompting, artifact:paper]
venue: NeurIPS 2017
citations: 173000
citations_as_of: <ISO date you looked it up, or omit both>
verification: unverified
fulltext: fulltext/arxiv-1706.03762.md
enriched: <today, ISO>
---

Setup: ...
```

On the two trust fields, which are deliberately separate:

- `venue` / `citations` / `citations_as_of` are **source trust** — external, fetchable, and
  they drift, so a citation count without its as-of date is worthless. Omit rather than guess.
- `verification` is **your** state, and only ever moves by hand: `unverified` on capture,
  `spot-checked` when someone confirmed the headline numbers against the paper,
  `reproduced` when someone ran it. Never set this above `unverified` yourself.

For a non-arXiv source, write what you retrieved to `fulltext/<id>.md` yourself. Depth 3 is
what makes a claim checkable later, and `search` greps it for verbatim quotes. That file is depth 3;
nothing reads it until a question needs the source verbatim.

## The depth ladder

Three depths, and the file layout *is* the mechanism:

| Depth | Where | Read it when |
|---|---|---|
| 1 | frontmatter — title, tags, dates | scanning or filtering the whole corpus |
| 2 | the summary body | deciding whether this is the right source |
| 3 | `fulltext/<id>.md` | quoting, or checking a claim |

Never read depth 3 to answer a depth-1 question. At a thousand entries the frontmatter of
the entire corpus still fits in context and the summaries do not, which is the whole reason
the ladder exists.

## Rebuild the index

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/build_index.py" --kb "$KB_PATH"
```

Always, as the last step. The index carries the Setup line and the stub marker, both of
which you just changed.
