---
name: capture-entry
description: Add a source to the knowledge base fast — metadata and provisional tags only, no deep read. Use when given a link to save, capture, add, or file away.
---

# Capture an entry

Take a link, write a depth-1 stub, regenerate the index. Seconds, not minutes.

This is deliberately shallow. The deep read is `enrich-entry`, and it runs later, in batches,
on the things you actually decide to read. Capture should never make you wait long enough
that you hesitate to save something.

## 1. Locate the corpus

Read `$KB_PATH`. If it is unset, stop and say so — do not guess a location and do not write
into the current directory. Every path below is relative to it.

## 2. Resolve the source

Fetch **metadata only**. Do not read the full text; that is enrich's job.

| Source | Get | Id |
|---|---|---|
| arXiv | the abstract page or API: title, authors, date, abstract, DOI | `arxiv-<id>` |
| GitHub repo | the API record and README head: description, topics, dates | `gh-<owner>-<repo>` |
| Web article | `<title>`, `<meta>` description, published date | `web-<slug>` |

**When a direct fetch fails, use the reader service.** A 403, or a page yielding under ~500
characters, means bot protection or client-side rendering — not an unavailable source.
Refetch through `https://r.jina.ai/<the full url>`, which needs no key. Corporate research
and lab blog pages block direct fetches routinely.

**Record the paper link if there is one.** Lab posts and project pages are usually front
doors: a short body, a "read the paper" link, a PDF or arXiv URL. Capture the page itself,
but put that target in a `paper:` field so `enrich-entry` reads the source rather than the
announcement. If the body is short *and* a paper link exists, say so in your report — that
entry needs the deep read pointed somewhere else.

If `entries/<id>.md` already exists, stop. Report whether it is a stub or enriched, and
change nothing — a capture must never clobber a summary someone wrote or edited.

## 3. Tag provisionally

Read `tags.md` at the corpus root first, every time. Assign from it and only from it.

You are tagging from a title and an abstract, so you know less than enrich will. That is
fine, and the rule is: **tag what the abstract actually supports, and no more.** An abstract
names the topic reliably; it rarely supports a `method:` claim and almost never supports
`use:harness` or `artifact:benchmark`, which turn on a release you have not verified.

Under-tagging here is cheap because enrich retags from the full text. Over-tagging is not,
because a wrong tag that nobody revisits is worse than a missing one.

If you want a tag that does not exist, use the closest one that does and say so in your
report. Never edit `tags.md` during a capture.

## 4. Write the stub

`entries/<id>.md`, frontmatter only, no body:

```md
---
title: Attention Is All You Need
url: https://arxiv.org/abs/1706.03762
id: arxiv-1706.03762
published: 2017-06-12
added: <today, ISO>
tags: [topic:tool-use, artifact:paper]
paper: <url of the linked paper/PDF, if this page is a front door; omit otherwise>
abstract: <the source's own abstract or description, verbatim, one paragraph>
verification: unverified
---
```

No `enriched:` field. Its absence is what marks this a stub and puts it in enrich's queue.

Keep `abstract` verbatim from the source — it is what makes the stub findable before anyone
deep-reads it, and it must not be your paraphrase.

## 5. Rebuild the index

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/build_index.py" --kb "$KB_PATH"
```

Always. An entry missing from `INDEX.md` is invisible to search.

## Report

The id, the tags you assigned, anything you wanted and could not find in the registry, and
the current stub count. Keep it to a few lines — this is a fast path.
