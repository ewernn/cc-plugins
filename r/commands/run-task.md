---
description: Execute a task plan autonomously. Runs steps, verifies outputs, adapts approach when needed. For code tasks (bugs, features, refactors) — not experiments.
allowed-tools: ["Task", "Read", "Write", "Bash", "Glob", "Grep", "TaskCreate", "TaskUpdate", "TaskList"]
---

# Run Task

Target: $ARGUMENTS

If no argument provided, look for a plan file (`*_plan.md` or `PLAN.md`) in the current directory.

## Startup

### 1. Load System Spec

Read `${CLAUDE_PLUGIN_ROOT}/docs/system.md`. Focus on:
- Failure modes F1-F12 (especially F1: fake verification, F3: skipping hard parts, F5: one error and stop)
- Evidence-based verification
- Anti-patterns table

### 2. Load Plan

Read the plan file. Parse:
- **Goal** — what "done" looks like
- **Stages** and steps (if staged plan)
- **Success criteria** (tests pass, build succeeds, specific behavior)
- **Dependencies**, verification criteria, "If wrong" fields
- **"If Stuck"** section

Also read:
- **Notepad** (`*_notepad.md`) — resume if exists
- **Decision tree** (`*_decision_tree.md`) — pruned approaches

### 3. Initialize Notepad (if new)

```markdown
# {Task Name} — Notepad

## Status: IN_PROGRESS
## Started: {YYYY-MM-DD HH:MM PST}
## Last updated: {YYYY-MM-DD HH:MM PST}

---
```

### 4. Create Task List

One task per step, grouped by stage if applicable.

---

## Execution Loop

For each step in the plan:

### 1. Check Dependencies

Confirm prior steps are PASSED. If not → STOP.

### 2. Check Decision Tree

Don't re-attempt pruned approaches.

### 3. Re-Anchor

Re-read plan (current step) and last ~10 notepad entries. [Addresses F6]

### 4. Execute

If step involves a script, read its argparse first. Then run the step.

For code changes: make the edits, run relevant tests immediately.

### 5. Verify

**Evidence, not claims.**

```
IF tests exist:     RUN them → record pass/fail
IF build step:      RUN it → record output
IF behavior change: DEMONSTRATE it works (show before/after)
ELSE:               SPAWN critic to review
```

Re-verify after fixes (max 3 iterations). [Addresses F5]

Record in notepad:
```
### [YYYY-MM-DD HH:MM PST] Step N: {name} — VERIFIED
- Method: {how verified}
- Evidence: {test output, build log, behavior demo}
- Clean: {yes | no}
```

### 6. Decision Point

**Pass** → continue.

**Fail** → check "If wrong" → "If Stuck" → fix (3x) → STOP.

**Unexpected side effect** → note in notepad, check if it affects downstream steps. If it does, adjust approach and document why.

---

## Stage Judgment (Staged Plans)

After each stage checkpoint:

### 1. Verify Checkpoint Items

All stage outputs exist, tests pass, no regressions.

### 2. Assess Approach

- **Does the approach still make sense?** Sometimes Stage 1 reveals the plan's approach won't work. Say so.
- **Any callers or consumers affected?** Code changes ripple. Check what depends on what you changed.
- **Is there a simpler path?** If Stage 1 showed the problem is different than expected, the remaining stages might be overcomplicated.

If adjustments needed → note in notepad, adapt. Don't follow a broken plan out of obligation.

### 3. Correction Propagation

If a fix in this stage changes behavior that prior stages assumed:
- List affected code paths
- Re-run relevant tests
- Update notepad with what changed and what was re-verified

---

## Completion

### 1. Check Success Criteria

For each criterion: find specific evidence. No evidence → go back and do the work.

### 2. Remaining Concerns

"What could still be wrong? What haven't I tested?"

Check:
- Edge cases the plan didn't mention
- Callers/consumers of changed code
- Error paths and failure modes
- Performance implications (if relevant)

### 3. Post-Execution Verification (MANDATORY)

Spawn a **verifier** agent on all code changes:
1. Enumerate what could be wrong (data flow, state, API contracts, integration, semantics)
2. Read actual code to check each
3. Report: SHIP / FIX FIRST / RETHINK

Fix bugs found. Don't mark complete until verifier passes.

### 4. Final Report

```
### [YYYY-MM-DD HH:MM PST] COMPLETE

## Success Criteria
- [x] Criteria 1: {evidence}

## Summary
{What was changed, 3-5 bullets}

## Testing
{What was tested, how, results}

## Remaining Concerns
{Anything worth noting for the reviewer}
```

Update task index if it exists.

---

## Error Handling

**Step fails:** "If wrong" → "If Stuck" → fix (3x) → STOP.

**Test regressions:** Don't ignore them. Fix the regression before proceeding, or document why it's acceptable.

**Overnight / autonomous runs:** Same as run-experiment — decide autonomously, document reasoning. Don't block on user for judgment calls. Stop only for cascading failures or ambiguous requirements where any choice could be wrong.

---

## Guidelines

- **Run tests early and often.** Don't save testing for the end.
- **Check callers.** When you change an interface, verify everything that uses it.
- **Assess at stage boundaries.** Don't follow a broken plan. If the approach isn't working, adapt.
- **Trace corrections.** When a fix changes behavior, check what depends on it.
- **Evidence, not claims.** Test output > "I verified it works."
- **Verifier is mandatory.** It catches logic bugs that type checking misses. Don't skip it.
