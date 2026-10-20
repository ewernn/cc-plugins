#!/usr/bin/env python3
"""UserPromptSubmit hook: inject the current datetime, the standing principles, and this
directory's recent human prompts.

stdout is the injection — UserPromptSubmit, UserPromptExpansion and SessionStart are the only
events that read bare stdout. Compose every piece in PIECES; drop one by naming it in EXCLUDE
with its reason, or by turning its `inject_*` option off.

Fail open. This hook runs in every session where the plugin is enabled; a crash would degrade
all of them. Any failure prints whatever composed, reports the rest on stderr, and exits 0.
That deliberately inverts the standing "fail fast and loud" principle: loud goes to stderr,
which the harness records on the hook_success attachment line without blocking a turn.

Settings come from this plugin's userConfig, delivered as CLAUDE_PLUGIN_OPTION_<KEY> env vars.
DEFAULTS mirrors the `default` values in .claude-plugin/plugin.json — keep the two in step; the
manifest's copy drives `claude plugin configure`, this one covers an unset or absent env var.
Principles content is read from ~/.claude/principles.json, which stays local and unversioned.
"""

import json
import os
import sys
import time
from pathlib import Path

PRINCIPLES_PATH = Path.home() / ".claude" / "principles.json"
TAG = "session-context"
DEFAULTS = {
    "recent_messages": 10,
    "clip_threshold": 4000,
    "inject_now": "on",
    "inject_principles": "on",
}
_HUMAN_BLOCK_TYPES = ("text", "image")


def option(name):
    """Return one userConfig value, falling back to its mirrored default."""
    raw = os.environ.get(f"CLAUDE_PLUGIN_OPTION_{name.upper()}")
    default = DEFAULTS[name]
    if raw is None or raw == "":
        return default
    return type(default)(raw) if isinstance(default, int) else raw


def stream_lines(path):
    """Yield each well-formed JSON object in a transcript, skipping blank and malformed lines.

    Port of cc_manager read/parse.py stream_lines. Stream rather than bulk-load: a single
    transcript runs to megabytes and this hook is on every turn.
    """
    try:
        handle = open(path, errors="ignore")
    except OSError:
        return
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except ValueError:
                continue
            if isinstance(parsed, dict):
                yield parsed


def is_human_typed(line):
    """Return whether a transcript line is a prompt the human typed into the prompt box.

    Port of cc_manager read/parse.py is_human_typed (v1.2-no-compact-summary): a user-role line
    that is not a sidechain, is not a /compact recap, is external, carries no tool result, and
    whose content is a string or an array of only text/image blocks. The array case matters — a
    pasted image or a multi-block paste is still a message the human typed.
    """
    if line.get("type") != "user" or line.get("isSidechain"):
        return False
    if line.get("isCompactSummary"):
        return False
    if line.get("userType") != "external" or "toolUseResult" in line:
        return False
    content = (line.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list) and content:
        return all(isinstance(block, dict) and block.get("type") in _HUMAN_BLOCK_TYPES
                   for block in content)
    return False


def human_text(line):
    """Return the text of a human-typed line, concatenating the text blocks of an array."""
    content = (line.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content
                         if isinstance(block, dict) and block.get("type") == "text")
    return ""


def looks_injected(text):
    """Return whether a user line's text looks machine-written rather than typed.

    Port of cc_manager read/injection_filter.py (v1.1). Hooks, resume banners and loop drivers
    all write user lines that are format-identical to typed input; only the text betrays them.
    High-precision and known-recall: it misfires on a human who genuinely opens with '<'.
    """
    stripped = (text or "").strip()
    if not stripped or stripped.startswith("<"):
        return True
    lowered = stripped.lower()
    if lowered in ("continue", "continue."):  # the canon anchors this one: Continue\.?$
        return True
    return any(lowered.startswith(prefix) for prefix in (
        "stop hook feedback", "caveat:", "this session is being continued",
        "[request interrupted", "your task is to", "please continue",
        "--num-iterations", "api error", "execute the "))


def clip(text, threshold):
    """Keep the head and tail of an over-long prompt, eliding the middle.

    A large paste usually carries the human's own words at one end or the other, so both ends
    are worth more than the bulk between them.
    """
    if len(text) <= threshold:
        return text
    half = threshold // 2
    return f"{text[:half]}\n…[{len(text) - 2 * half} chars elided]…\n{text[-half:]}"


def now(payload):
    """Return the current local datetime, which the model has no other live source for."""
    if option("inject_now") != "on":
        return ""
    return "# now\n" + time.strftime("%Y-%m-%d %H:%M:%S %Z")


def principles(payload):
    """Return every standing principle from the local principles file, grouped by section."""
    if option("inject_principles") != "on":
        return ""
    document = json.loads(PRINCIPLES_PATH.read_text())
    lines = [f"# principles ({PRINCIPLES_PATH} — standing, apply to every turn)"]
    for section, items in document["principles"].items():
        lines.append(f"## {section}")
        lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def recent_prompts(payload):
    """Return the last N human-typed prompts from every session in this working directory.

    Scope the history by directory, not by session: the transcript store keeps one directory per
    working directory, and it is the parent of the path the payload names — so a git worktree,
    having its own cwd, keeps its own history with no path-munging to reproduce. Read main
    transcripts newest-first by modification time until N prompts are in hand, then order them
    by timestamp.

    Hook injections are written to separate `attachment` lines, never onto the user line, so
    re-reading user lines cannot compound this hook's own output; the injection filter still
    screens resume banners and loop drivers.
    """
    keep = option("recent_messages")
    if keep <= 0:
        return ""
    transcript = payload.get("transcript_path")
    if not transcript:
        return ""
    project_dir = Path(transcript).parent
    if not project_dir.is_dir():
        return ""

    dated = []
    for path in sorted(project_dir.glob("*.jsonl"),
                       key=lambda p: p.stat().st_mtime, reverse=True):
        for line in stream_lines(str(path)):
            if not is_human_typed(line):
                continue
            text = human_text(line)
            if looks_injected(text):
                continue
            dated.append((line.get("timestamp") or "", text.strip()))
        if len(dated) >= keep:
            break  # newest files first, so the remaining ones are all older

    texts = [text for _, text in sorted(dated, key=lambda pair: pair[0])]
    # The turn being submitted is not on disk yet; drop it if a replay put it there.
    current = (payload.get("prompt") or "").strip()
    if texts and current and texts[-1] == current:
        texts.pop()

    selected = texts[-keep:]
    if not selected:
        return ""
    threshold = option("clip_threshold")
    lines = [f"# recent prompts in this directory (last {len(selected)}, oldest first, "
             f"verbatim; [-1] is the most recent) — {project_dir.name}"]
    for index, text in enumerate(selected):
        lines.append(f"[-{len(selected) - index}] {clip(text, threshold)}")
    return "\n".join(lines)


PIECES = {"now": now, "principles": principles, "recent_prompts": recent_prompts}
EXCLUDE = {
    "main": [],
    "subagent": [
        "recent_prompts",  # a subagent gets its own task, not the human's prompt history
    ],
}


def compose(audience, payload):
    """Join every piece not excluded for this audience, skipping ones that produced nothing."""
    produced = []
    for name, piece in PIECES.items():
        if name in EXCLUDE[audience]:
            continue
        try:
            text = piece(payload)
        except Exception as error:  # one broken piece must not cost the others
            print(f"mechanization: piece {name!r} failed: {error!r}", file=sys.stderr)
            continue
        if text:
            produced.append(text)
    return "\n\n".join(produced)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        text = compose("subagent" if payload.get("agent_id") else "main", payload)
        if text:
            print(f"<{TAG}>\n{text}\n</{TAG}>")
    except Exception as error:
        print(f"mechanization: {error!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
