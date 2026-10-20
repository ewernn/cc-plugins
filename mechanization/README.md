# mechanization

Injects three things into every turn through a `UserPromptSubmit` hook: the current local
datetime, your standing principles, and the most recent human prompts from the directory the
session was started in.

## Why a hook instead of CLAUDE.md

`CLAUDE.md` is delivered once at session start and drifts out of attention over a long session.
A `UserPromptSubmit` hook re-injects on every turn, so the content stays in recent context.

## Setup

Principles content is **not** shipped with the plugin — it is personal and stays local and
unversioned. Copy the template and fill it in:

```sh
cp "$CLAUDE_PLUGIN_ROOT/principles.example.json" ~/.claude/principles.json
```

Only the `principles` key is read: a map of section name to a list of strings. Any other key is
ignored. With the file absent the hook still injects the other pieces and notes the miss on
stderr.

## Options

`claude plugin configure mechanization@ewernn-plugins`

| option | default | effect |
|---|---|---|
| `recent_messages` | 10 | how many recent prompts to inject; 0 disables the piece |
| `clip_threshold` | 4000 | a longer prompt keeps its first and last 2000 chars and elides the middle |
| `inject_now` | on | the current local datetime |
| `inject_principles` | on | the contents of `~/.claude/principles.json` |

Whole-plugin on/off is `enabledPlugins` in settings, not an option here — one switch per
question. A project disables it with `"enabledPlugins": {"mechanization@ewernn-plugins": false}`
in its `.claude/settings.json`, which applies at session start.

## How recent prompts are scoped

By directory, not by session. The transcript store keeps one directory per working directory,
and it is the parent of the `transcript_path` the hook payload names — so a git worktree, having
its own cwd, keeps its own history with no path-munging to reproduce. Transcripts are read
newest-first by mtime until enough prompts are in hand, then ordered by timestamp.

Nothing is stored. There is no capture log, index or state file; every turn is derived from the
transcripts the harness already writes.

## Notes

- **Fails open.** A user-level hook runs in every session, so a crash would degrade all of them.
  Any failure prints what composed, reports the rest on stderr (recorded on the `hook_success`
  attachment line) and exits 0. This deliberately inverts the usual fail-fast rule.
- **No feedback loop.** Hook output is written to a separate `attachment` line, never onto the
  user line, so re-reading user lines cannot compound the hook's own injections.
- Transcript-reading logic is a port of `cc_manager`'s `read/` core — the canonical
  implementation lives there and fixes should land there first. The port is verified equivalent
  across 212k transcript lines (0 predicate, text-extraction or injection-filter disagreements).
