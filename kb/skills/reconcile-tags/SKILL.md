---
name: reconcile-tags
description: Periodic maintenance pass over the tag registry and tagged entries — merge near-duplicate tags, find mistagged entries, and report drift. Use when asked to reconcile, refresh, audit, merge, or clean up tags.
---

# Reconcile the registry

A tag vocabulary does not stay correct on its own. Entries are tagged one at a time against
a registry that keeps changing, so the corpus drifts out of agreement with itself. Run this
every 25-50 new entries, or when tagging starts feeling ambiguous.

The question early on is *which tags exist*. After a hundred entries the question is
*which entries are mistagged*, and that one is invisible without deliberately looking.

## 1. Census

Read `$KB_PATH` first; if it is unset, stop and say so.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/tag_census.py" --kb "$KB_PATH"
```

Mechanical signals only. Read them, don't trust them — every one is a lead, not a verdict:

- **Unregistered tags in use.** A hard violation. Fix immediately: either add the tag to
  `tags.md` with a description, or retag the entry.
- **Used fewer than twice.** The registry says a tag must span many entries. A thin tag is
  either too narrow, or a near-duplicate of one that's absorbing its entries.
- **Never used.** Harmless while the corpus is small. Past ~100 entries, an unused tag is
  either dead vocabulary or a gap nobody noticed they could fill.
- **Redundancy suspects.** Pairs that almost always co-occur. Two tags that travel together
  through 80% of their uses may be one tag wearing two names — or a genuine pattern, like a
  method that only appears in one topic. Read the entries before deciding.
- **Per-entry tag counts.** An outlier is usually over-tagging, occasionally a genuinely
  broad source.

## 2. Blind re-tag, on a sample

The only way to find mistagged entries. Take 5-10 entries at random. For each:

1. Read **only** the summary body. Do not look at the stored tags.
2. Tag it fresh from the current `tags.md`.
3. Now diff against what's stored.

Every disagreement is one of three things, and they need different fixes:

| Disagreement | Means | Fix |
|---|---|---|
| The stored tag is wrong | tagger error, or the entry predates a registry change | retag the entry |
| Both are defensible | two tags are too close to choose between | merge them in `tags.md` |
| You wanted a tag that doesn't exist | genuine vocabulary gap | add it, with a description |

Report the disagreement rate. It is the health metric. Rising means the registry is getting
harder to apply, not that the tagger is getting worse.

## 3. Merge

Merging is the main maintenance action. The registry has a ceiling of ~200 tags and the
rule is merge before you add.

To merge `a` into `b`:

1. Confirm from actual entries that `b`'s description honestly covers `a`'s uses. If it
   doesn't, sharpen `b`'s description as part of the merge.
2. Rewrite `a` to `b` in every entry that carries it.
3. Delete `a` from `tags.md`.
4. If the pair was confusable, add a line to the "When several tags all seem to fit"
   section saying how to choose. That section is where merges leave their lesson — without
   it the same collision comes back under new names.

Splitting is rarer and needs stronger evidence: a tag is doing two jobs *and* both jobs
have enough entries to stand alone.

## 4. Report

Say what changed and what you left alone:

- entries scanned, disagreement rate on the sample
- tags merged, added, deleted, with the reason for each
- entries retagged
- anything you saw and deliberately did not act on, and why

## Rules

- **Never merge tags you have not read the entries for.** Co-occurrence is a lead. Two tags
  can be statistically inseparable in a small corpus and genuinely distinct.
- **Never retag from the title.** Read the summary. Title-based tagging is what produced the
  drift you're cleaning up.
- **Never silently drop a tag from an entry.** Retagging is an edit with a reason.
- **Do not touch `verification:`.** It is the reader's field and only moves by hand.
- **A shrinking registry is a healthy outcome.** So is an unchanged one. Manufacturing
  churn to look productive is the failure mode here.

## Rebuild the index

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/build_index.py" --kb "$KB_PATH"
```

Any retag changes the index. Skipping this leaves search filtering on stale tags.
