---
name: enrich-entry
description: Deep-read a source into a full summary — inventory the source, write from that inventory, verify against it. Use when asked to enrich, summarize, deep-read, or work through the capture backlog.
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
- **Web article:** WebFetch first. If it returns 403, or yields under ~500 characters of
  prose, the site is bot-protected or client-rendered — refetch through the reader service:

  ```bash
  curl -sL --max-time 40 "https://r.jina.ai/<the full url>"
  ```

  It needs no key and returns markdown. Corporate research pages commonly block a direct
  fetch and pass cleanly this way; treat a 403 as "use the reader", not as "unavailable".
- Local PDF: `Read` with the `pages` parameter.

**Follow the link to the actual source.** A lab blog post, a project page, or a press
release is usually a *front door*, not the source. If the page links a PDF, an arXiv ID, or
a "read the paper" target, and its own body is short or trails off in "read more", then the
page you fetched is an index and summarizing it produces a shallow entry wearing the badge
of a deep one.

In that case, fetch the linked paper and summarize **that**. Keep the blog post as `url`
because it is the address you will look for again, and record what you actually read in
`fulltext:` and in the Methodology line. If both exist and differ in substance — the post
reports a result the paper does not, or vice versa — say so rather than silently choosing.

If you cannot get the full text by any of these routes, say so and stop. Do not write a
summary from metadata and do not mark it `enriched`.

### Edge cases

Each of these has actually occurred in this corpus. The rule underneath all of them is the
same: **record what you read, from where, and when.** A summary whose source you cannot
re-identify is not checkable, and depth 3 exists to make claims checkable.

- **The source is still moving.** An actively developed repo, a leaderboard, a living spec.
  Pin it: record the commit SHA (or the retrieval date, if that is all there is) in the
  fulltext header and in `scale`. Without a pin, the summary silently rots as the source
  changes and nobody can tell which version it described.
- **The source states one thing and its registry says another.** A repo whose description
  claims a license its `LICENSE` file does not carry; a page whose visible date differs from
  its metadata. Record both and say they disagree. Never silently pick the one that reads
  better.
- **Versioned sources.** arXiv papers get revised, and `published` is the v1 date while the
  text you read may be v3. Record the version you actually read; the corpus already contains
  an entry where these silently disagree.
- **No text at all.** A video, a podcast, a dataset release with a bare README. Capture it,
  say what it is, and do not mark it `enriched` — an entry claiming a deep read of something
  with nothing to read is worse than a stub.
- **Behind a login or paywall.** Stop. Do not summarize from an abstract or a preview and do
  not mark it enriched. Record the address so a human can decide.
- **The link is dead.** If it 404s at capture time, do not write an entry. If an existing
  entry's URL has died, that is a `Defects` line and a job for `reconcile-tags`, not a
  silent deletion.

**Check for truncation before you trust the text.** If a section header is followed by
almost nothing, or an appendix the body references is absent, the extraction dropped it.
Say so, and treat every claim that depended on it as unverifiable rather than absent.

## 1. Inventory the source — before you write anything

This step exists because of a measured failure. A summary pass that reads the draft and asks
"is each claim supported?" can only find things that are *there*; it is structurally unable
to find what is missing. Across the first fifteen entries, limitation coverage was **39%** —
75% for caveats under a `Limitations` heading and **22%** for caveats stated anywhere else.
Building the checklist first is what fixes that, and it only works if you do it before the
summary exists to anchor on.

Write these down before drafting. They are the ground truth section 4 scores against.

**Every headline number**, with the condition attached and where you found it. A figure
without its condition is the most dangerous thing in this corpus, because the number is
right and the sentence is false. Record: value, what it measures, which model or system,
under what setting (budget, seed count, mitigation on or off, time limit), and the table or
section it came from. Keep the anchors while you work even though they do not appear in the
final prose.

**Every limitation the authors state — and sweep the whole paper for them.** A `Limitations`
section is where the easy ones live. The ones that get lost sit in footnotes, in a Methods
hedge, in a Discussion aside, in an appendix caption. Search for hedging language, not just
the heading: *only, cannot, we did not, future work, leave to, restricted to, assume, may
not generalize, caveat, in practice*.

**Every experimental condition that varies.** Which arms exist, what differs between them,
which results belong to which. Papers describe a grid and report a subset; the subset is
what you must attribute correctly.

**What the paper does not have.** No baseline or comparator. No control condition. No
statistical test where one is implied. No release. If a claim has no supporting artifact,
that absence is itself a finding — record it, because the authors will not state it.

## 2. Tag from the registry

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
- **Release-gated tags need evidence in the body.** `artifact:benchmark`, `artifact:dataset`
  and `use:harness` all assert a real release. If you assign one, the Scope line must say
  where the release is. If you cannot find a release claim, do not assign the tag.
- **There is no target number of tags.** Assign what is true. If the count feels high,
  check whether two of them are near-duplicates and report that — never drop a tag that
  applies in order to hit a number.
- The registry is organized by area and areas are incomplete by design. A source from a
  field not listed is a gap in `tags.md`, not a source that does not belong. Report it.

## 3. Write the summary

Format, in this order:

```
Setup:        <the problem or question, one sentence>
Methodology:  <what they DID — technique, data, models, scale. Include the decisive
               specifics: which layers or token positions, the experimental controls,
               how key quantities were computed>
Findings:     (1) ... (2) ... (3) ...  numbered, each with its exact figures AND the
               condition those figures were measured under
Scope:        <what was NOT tested; what the result does and does not cover; release
               status; anything the paper claims without support>
Defects:      <OPTIONAL — contradictions or errors in the source itself. Omit if none>
Useful?:      <one or two lines: concrete relevance to the reader, profile below>
```

Rules, in priority order:

1. **Exact numbers, never rounded.** Write `91% vs 39%`, not "more than doubled". Write
   `5.2×`, not "4-5×". Copy the value as the source states it — if it says 42K, write 42K.
2. **Every result-bearing claim carries its condition.** This is the second-weakest
   dimension measured on this corpus, at 76%, and the most dangerous, because the number is
   correct so review slides past it. "157 successes" is incomplete; "157 successes with
   mitigations disabled, two-hour limit" is a claim. If a finding spans arms with different
   sample sizes or budgets, say so in the finding rather than leaving it implied.
3. **Mark what the source does not report.** Write `[paper does not report X]` inline. This
   rule exists because it was previously stated and never fired once across fifteen entries
   — an absent number silently became an absent sentence. If you are working from a
   truncated extraction, say which part and stop guessing at what it held.
4. **Length is an output, never a target.** Do not aim at a word count; the last version of
   this file suggested one and twelve of fifteen entries landed within ten words of it,
   which is the instrument steering the writing. Every sentence must carry an exact figure,
   a decisive method specific, a scope limit, or a condition. Cut every sentence that
   carries none. A thin paper yields a short entry and that is a correct outcome.
5. **Scope is not optional**, and it is where the inventory from section 1 lands. What the
   paper did not test is what tells you whether it transfers.
6. **Report the paper's own result, not just its instrument.** If the authors ran an
   experiment and stated its answer, the answer belongs in Findings. Describing the
   apparatus and dropping what it measured is the most common omission in this corpus.

**Banned constructions.** Each of these is a sentence that survives only because it sounds
like something a summary should say. Cut on sight:

- "significant results", "substantially outperforms" — which results, what margin?
- "various factors", "several approaches" used to avoid naming them
- "the methodology is robust", "a thorough evaluation" — say what makes it so
- "has important implications", "contributes to the literature" — for whom, how?
- "further research is needed" — what research, and why this one?

**Acronyms.** Spell out every acronym in parentheses on first use, including in the
`Useful?` line — FPR (False Positive Rate), SFT (Supervised Fine-Tuning), TPR, RLHF, PPO.
This is a house convention and it does not reach you from the corpus repo, so it is stated
here.

**Reader profile for `Useful?`** — security evaluation gyms and ranges, RL (Reinforcement
Learning) for upskilling agents, red and blue seat design, SOC (Security Operations Center)
agents, scoring surfaces and vantage points, and how realistic an environment has to be.
Write the line against *that* or it comes out generic. It is a draft for the reader to edit;
genuine relevance is their call, not yours.

## 4. Verify — two passes that catch different things

Mandatory, and the two passes are not interchangeable. Measured across the first fifteen
entries: the self-check reliably caught arithmetic and attribution and reliably missed
framing and omission. Every writer whose self-check came back clean still had errors of the
second kind, found only by an independent reader.

**Pass one — you, against your inventory.** Walk section 1's list, not your draft:

- Every number in the inventory: is it in the summary, or deliberately left out? Every
  number in the summary: is it in the inventory, with the same condition attached?
- Every limitation in the inventory: does Scope cover it? Report the fraction.
- Every attribution: which model, which system, which team. Wrong attribution is the
  easiest error to make and the hardest to catch later.
- Every superlative and aggregate. "All models dropped to zero" is false if one retained
  two. A total spanning multiple runs must say so.
- Cross-table consistency: when the same quantity appears in two places in the source, do
  they agree? If not, that is a `Defects` line, not something to silently pick a side on.

**Pass two — an independent reader, given the source before the draft.** Spawn a subagent
and hand it the paper first, asking it to list the paper's headline results, its stated
limitations, and its experimental conditions. *Then* give it the draft and ask what is
missing or misframed. This ordering matters: a reader shown the draft first anchors on it
and rationalizes rather than checks — the effect is large enough that showing prior context
blocks roughly half of the corrections a reader would otherwise make, and telling it to
ignore the anchor does not fix it.

Ask it for four things: claims the source does not support, limitations the draft omits,
sentences whose framing implies more than the source shows, and results the paper reported
that the draft describes only as an instrument.

Do not ask for a fixed number of findings. "Nothing further" is a legitimate answer and
forcing a quota manufactures nits.

## 5. Write the file

One file, `entries/<id>.md`. The id is type-prefixed: `arxiv-2502.16681`, `gh-owner-repo`,
`web-<slug>`.

```md
---
title: Attention Is All You Need
url: https://arxiv.org/abs/1706.03762
id: arxiv-1706.03762
authors: Vaswani et al., Google Brain
published: 2017-06-12
added: <today, ISO>
tags: [topic:tool-use, use:baseline-method, method:prompting, artifact:paper]
scale: 8 models, 2 translation tasks
release: https://github.com/tensorflow/tensor2tensor
venue: NeurIPS 2017
verification: unverified
fulltext: fulltext/arxiv-1706.03762.md
enriched: <today, ISO>
---

Setup: ...
```

On the fields that are easy to get wrong:

- `authors` — first author plus affiliation is enough. Whether a result comes from a
  government lab or the vendor whose model it evaluates is a first-order trust filter, and
  it is unrecoverable from a summary that omits it.
- `scale` — the size of the thing: task count, model count, instance count. This is the
  first filter anyone applies to a benchmark and it should not require reading the body.
- `release` — a URL, or the literal `none`. Never omit it: a missing field is
  indistinguishable from an unreleased artifact, and the release-gated tags depend on this.
- `venue` — omit rather than guess. For a preprint with no journal reference, omit.
- `verification` — the reader's field, never yours. `unverified` on write; a human moves it
  to `spot-checked` or `reproduced`. Nothing in this pipeline may raise it.
- For a repo, `published` is meaningless — record the commit SHA in `scale` or the fulltext
  header instead, and omit `published`.

For a non-arXiv source, write what you retrieved to `fulltext/<id>.md` yourself. Depth 3 is
what makes a claim checkable later, and `search` greps it for verbatim quotes.

## The depth ladder

Three depths, and the file layout *is* the mechanism:

| Depth | Where | Read it when |
|---|---|---|
| 1 | frontmatter — title, tags, scale, dates | scanning or filtering the whole corpus |
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
