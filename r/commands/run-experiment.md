---
description: Execute a plan autonomously. Runs steps, verifies outputs, uses analyst to check results. Only stops if something goes wrong.
allowed-tools: ["Task", "Read", "Write", "Bash", "Glob", "Grep", "TaskCreate", "TaskUpdate", "TaskList"]
---

# Run Experiment

Target: $ARGUMENTS

If no argument provided, look for a plan file (`*_plan.md` or `PLAN.md`) in the current directory.

## Startup

### 1. Load System Spec

Read the autonomous workflow system spec at `${CLAUDE_PLUGIN_ROOT}/docs/system.md`. Pay attention to:
- Failure modes F1-F12 (especially F1: fake verification, F3: skipping hard parts)
- Verification requirements (evidence, not claims)
- Anti-patterns table

### 2. Check Environment

Log platform and compute resources:
```bash
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    echo "CPU-only or Mac environment"
fi
```

### 3. Load Plan

Read the plan file. Parse:
- **Stages** and their names (if hierarchical plan)
- **Steps** within each stage (numbered 1.1, 1.2, ... or flat 1, 2, ...)
- **Checkpoints** between stages (blocking verification gates)
- **Dependencies** per step (`Depends on` field)
- **Expected outputs** and verification criteria per step
- **"If wrong"** fields per step (what failure looks like)
- **"If Stuck"** section (global fallback guidance)
- **Complexity tier** if present (Small/Medium/Large)

Also read:
- **Notepad** (`*_notepad.md`) — catch up on progress if resuming
- **Decision tree** (`*_decision_tree.md`) — check for pruned approaches before attempting anything

### 4. Create Task List

Create tasks grouped by stage (if stages exist):
- For staged plans: one task per step, subject includes stage context (e.g., "Stage 1 / 1.1: Extract vectors")
- For flat plans: one task per step

### 5. Initialize or Resume Notepad

If notepad exists and has entries → **resume from last verified step** (append, don't archive).
If notepad exists with header only → start fresh (append-only).
If no notepad exists → create one:

```markdown
# {Task Name} — Notepad

## Status: IN_PROGRESS
## Started: {YYYY-MM-DD HH:MM PST}
## Last updated: {YYYY-MM-DD HH:MM PST}

---
```

## Execution Loop

For each step in the plan (respecting stage order):

### 1. Check Dependencies

Read the `**Depends on**` field. If it references a prior step:
- Confirm that step is marked PASSED in the notepad
- If dependency not met → STOP, report which dependency is unresolved

### 2. Check Decision Tree

Read the decision tree for any pruned approaches related to this step.
- If the approach we're about to try appears under a `D{N}-PRUNED` section, check the `DO NOT RETRY UNLESS` condition
- If condition is not met → skip, note in notepad, escalate

### 3. Re-Anchor

Re-read the plan (current step section) and notepad (last few entries).
This prevents context drift on long tasks. [Addresses F6]

### 4. Mark In Progress

Update the task to `in_progress`. Add a notepad entry:
```
### [YYYY-MM-DD HH:MM PST] Step N: {name} — STARTED
- Action: {what is being done}
```

### 5. Read Before Run

If step involves running a script:
- Read the script's argparse/flags
- Verify flags match what's in the plan
- Check existing outputs (don't re-run if already done)

### 6. Execute

Run the step. For code changes, make the edits. For scripts, run the command.

### 7. Verify Output

**Verification must produce EVIDENCE, not claims.** [Addresses F1]

Check the plan's `**Verify**` field for this step. Also check `**If wrong**` to know what failure looks like.

```
IF oracle/reference exists:
  COMPARE output vs oracle → record evidence
ELSE IF automated test/command exists:
  RUN it → record output
ELSE:
  SPAWN critic: "verify this result. evidence: {X}. expected: {Y}"
```

**"Check again" loop:** After finding and fixing issues, re-verify. Repeat until clean (max 3 iterations). [Addresses F5]

Add notepad entry:
```
### [YYYY-MM-DD HH:MM PST] Step N: {name} — VERIFIED
- Method: {how verified}
- Evidence: {specific — test output, diff, metric, command output}
- Clean: {yes | no — if no, details}
```

### 8. Spawn Side-Thoughts

After each major step, spawn 2-3 background agents:
- "Is there a simpler approach to what we just did?"
- "What could go wrong with this result downstream?"
- "What related thing should we check?"

Log results in notepad when they return. [Addresses P4, P6]

### 9. Decision Point

**If verified and clean:**
- Mark task complete
- Continue to next step

**If something is wrong:**
- Check `**If wrong**` field in the plan for this step
- Check `## If Stuck` section for general guidance
- Try fix if applicable (max 3 attempts)
- If still failing → record FAILURE in notepad + decision tree, STOP and report

Record failures:
```
### [YYYY-MM-DD HH:MM PST] FAILURE: {what failed}
- Attempted: {what was tried}
- Error: {specific error/evidence}
- Root cause: {analysis}
- Rules out: {what this means for future attempts}
- → See decision_tree.md D{N}
```

### 10. At Checkpoints (Staged Plans)

When reaching a `### Checkpoint: After Stage N` section:

**This is a BLOCKING gate, not a summary step.**

1. Verify every checklist item in the checkpoint block
2. Run analyst on all outputs from this stage
3. Confirm no error patterns carried forward from earlier stages
4. Update notepad with checkpoint status

**Only proceed to next stage if ALL checkpoint items pass.** If any fail → treat as a failed step (fix or STOP).

## Completion (Ralph Protocol)

When all steps are done:

### 1. Check Success Criteria

Read the `## Success Criteria` section from the plan.

For EACH criterion:
- Find specific evidence it was met
- If evidence exists and valid → PASS
- If evidence is unclear → SPAWN critic to assess
- If no evidence → FAIL (go back to execute)

### 2. Meta-Check

Ask: "What else could be wrong? What haven't I checked?"
If new concerns → address, re-verify.

### 3. Final Notepad Update

```
### [YYYY-MM-DD HH:MM PST] COMPLETE
## Final Status: COMPLETE

## Success Criteria
- [x] Criteria 1: {evidence}
- [x] Criteria 2: {evidence}

## Summary
{Key outcomes in 3-5 bullets}
```

### 4. Update Task Index

If `task_index.md` exists, update the task's status to COMPLETE.

### 5. Report

Provide final summary:
- What was accomplished
- Key results with evidence
- Any issues encountered
- Suggested next steps

## Error Handling

**Step fails:**
- Check `**If wrong**` field for this step (inline guidance)
- Check `## If Stuck` section (global fallback)
- Try fix if applicable
- Otherwise STOP and report

**Output doesn't match expected:**
- Spawn analyst to compare actual vs expected
- Spawn critic if results seem suspicious
- STOP and report with details

**Out of memory / resource issues:**
- Log to notepad
- STOP and report constraints

## Guidelines

- **Update notepad on every step** — it survives compaction. Include PST timestamps with HH:MM.
- **Don't continue past failures** — stop and report clearly
- **Spawn agents freely** — analyst for output verification, critic for suspicious results, investigator for unknowns, reflector if approach needs rethinking
- **Evidence, not claims** — "verified" is meaningless without specific proof
- **Check decision tree before every step** — don't re-attempt pruned approaches
- **Semantic verification** — grep for removed strings is necessary but not sufficient. Verify the MEANING is correct.
