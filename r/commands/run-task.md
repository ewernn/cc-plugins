---
description: Execute a task plan autonomously. Runs steps, verifies outputs, adapts approach when needed. For code tasks (bugs, features, refactors) — not experiments.
allowed-tools: ["Task", "Read", "Write", "Bash", "Glob", "Grep", "TaskCreate", "TaskUpdate", "TaskList"]
---

# Run Task

Target: $ARGUMENTS

If no argument provided, look for a plan file (`*_plan.md` or `PLAN.md`) in the current directory.

---

## Core Rules

**P1: Externalize all state.** Context compacts and drifts. Files survive.
**P2: Verify structurally.** "Verified" means specific evidence, never a claim.
**P5: Never trust completion claims.** Loop until success criteria met with evidence.
**P6: Spawn subagents liberally.** Fresh context is cheap, stale parent context is expensive.

**Key failure modes:**
- **F1**: claiming "verified" without checking
- **F3**: skipping hard parts for easier ones
- **F5**: finding one error and stopping
- **F6**: losing direction on long tasks
- **F11**: re-attempting previously failed approaches

---

## Startup

### 1. Load Plan

Read the plan file. Identify:
- Task directory and task name
- Goal, stages, steps, success criteria
- Dependencies, verification criteria, "If wrong" fields
- "If Stuck" section

### 2. Initialize Task Files (DETERMINISTIC)

```bash
r-init-task-files {task_dir} {task_name}
```

Idempotent — creates notepad, findings, decision_tree, user_messages, results/ if missing.

### 3. Load State

Read notepad (resume progress), decision tree (check pruned approaches).

### 4. Create Task List

One task per step, grouped by stage if applicable.

---

## Execution Loop

For each step in the plan:

### 1. Check Dependencies

Confirm prior steps are VERIFIED in the notepad. If not → STOP.

### 2. Check Decision Tree

Don't re-attempt pruned approaches.

### 3. Re-Anchor

Re-read plan (current step) and last ~10 notepad entries. [Addresses F6]

### 4. Execute

If step involves a script, read its argparse first. For code changes, run relevant tests immediately.

### 5. Verify

**Evidence, not claims.**

```
IF tests exist:     RUN them → record pass/fail
IF build step:      RUN it → record output
IF behavior change: DEMONSTRATE it (show before/after)
ELSE:               SPAWN critic to review
```

Re-verify after fixes (max 3 iterations). [Addresses F5]

### 6. RECORD (MANDATORY GATE — via script)

**Cannot execute step N+1 until step N is recorded:**

```bash
r-append-notepad {notepad_path} {step_num} "{step_name}" VERIFIED \
  "{how verified}" "{specific evidence}" "{yes | no}"
```

If a decision was made between approaches, also write a D{N} entry to the decision tree.

Record failures:
```bash
r-append-notepad {notepad_path} {step_num} "{step_name}" FAILURE \
  "{what tried}" "{error details}" "no — {root cause}"
```

Then add to decision tree:
```
### D{N}-PRUNED: {approach name}
- Status: ATTEMPTED_AND_FAILED
- Reason: {specific evidence}
- DO NOT RETRY UNLESS: {what would need to change}
```

### 7. Decision Point

**Pass** → continue.

**Fail** → check "If wrong" → "If Stuck" → fix (3x) → record FAILURE + D-PRUNED → STOP.

**Unexpected side effect** → note in notepad, check downstream impact. Adjust if needed.

---

## Progress Checkpoint (Every 5 Steps)

Spawn a background **check-in agent** (`r:check-in`):

> "Check progress on this task.
> - Notepad: {path}
> - Plan: {path}
> - Decision tree: {path}"

Also run:
```bash
r-check-notepad-format {notepad_path}
```

If check-in says SPINNING or OFF-TRACK → stop, prune the approach, try something different.
If notepad format drifted → fix before continuing.

---

## Stage Judgment (Staged Plans)

After each stage checkpoint:

### 1. Verify Checkpoint Items

All stage outputs exist, tests pass, no regressions.

### 2. Assess Approach

- **Does the approach still make sense?**
- **Any callers or consumers affected?**
- **Is there a simpler path?**

If adjustments needed → note in notepad, adapt.

### 3. Correction Propagation

If a fix changes behavior that prior stages assumed:
- List affected code paths
- Re-run relevant tests
- Update notepad with what changed

---

## Completion

### 1. Check Success Criteria

For each criterion: find specific evidence. No evidence → go back and do the work.

### 2. Remaining Concerns

"What could still be wrong? What haven't I tested?"
- Edge cases, callers/consumers, error paths, performance

### 3. Post-Execution Verification (MANDATORY)

Spawn a **verifier** agent on all code changes:
1. Enumerate what could be wrong
2. Read actual code to check each
3. Report: SHIP / FIX FIRST / RETHINK

Fix bugs found. Don't mark complete until verifier passes.

### 4. Final Format Check

```bash
r-check-notepad-format {notepad_path}
```

Must pass before declaring complete.

### 5. Final Report + Completion Signal

```
### [YYYY-MM-DD HH:MM PST] COMPLETE

## Success Criteria
- [x] Criteria 1: {evidence}

## Summary
{What changed, 3-5 bullets}

## Testing
{What was tested, how, results}

## Remaining Concerns
{Anything worth noting}
```

Update task index if it exists.

**Emit the ralph-loop completion signal:**
```
<promise>DONE</promise>
```

**Do not emit unless:** all success criteria met with evidence, verifier passed, notepad format check passed.

---

## Error Handling

**Step fails:** "If wrong" → "If Stuck" → fix (3x) → RECORD FAILURE → STOP.

**Test regressions:** Fix before proceeding.

**Overnight / autonomous runs:** Decide autonomously, document reasoning via `r-append-notepad`. Don't block on user for judgment calls.

---

## Guidelines

- **The bin/ scripts are the enforcement.** `r-init-task-files`, `r-append-notepad`, `r-check-notepad-format`. Use them.
- **Run tests early and often.**
- **Check callers.** When you change an interface, verify everything that uses it.
- **Assess at stage boundaries.** Don't follow a broken plan.
- **Trace corrections.** When a fix changes behavior, check what depends on it.
- **Evidence, not claims.** Test output > "I verified it works."
- **Verifier is mandatory.** Don't skip it.
- **`<promise>DONE</promise>` is a commitment.** Only emit when actually done.
