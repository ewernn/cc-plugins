---
description: Execute a plan as a research agent. Runs steps, analyzes results, investigates leads, and adapts. Produces useful findings even on incomplete runs.
allowed-tools: ["Task", "Read", "Write", "Bash", "Glob", "Grep", "TaskCreate", "TaskUpdate", "TaskList"]
---

# Run Experiment

Target: $ARGUMENTS

If no argument provided, look for a plan file (`*_plan.md` or `PLAN.md`) in the current directory.

---

## Core Rules (these override your instinct to skip documentation)

**P1: Externalize all state.** Context compacts and drifts. Files survive.
**P2: Verify structurally.** "Verified" means specific evidence, never a claim.
**P4: Diverge then converge.** Always consider alternatives before committing.
**P5: Never trust completion claims.** Loop until success criteria met with evidence.
**P6: Spawn subagents liberally.** Fresh context is cheap, stale parent context is expensive.
**P8: Predict before executing.** No hypothesis + budget + alternative = no experiment.

**Key failure modes you WILL hit if you're not careful:**
- **F1**: claiming "verified" without checking
- **F3**: skipping hard parts for easier ones
- **F4**: premature completion claims
- **F6**: losing direction on long tasks
- **F11**: re-attempting previously failed approaches

The file infrastructure below is the countermeasure to these. It is not optional.

---

## File Structure (MANDATORY)

Every task directory contains these 5 files plus `results/`:

```
{task_dir}/{name}/
├── {name}_plan.md           # From plan-experiment (already exists)
├── {name}_notepad.md        # Timestamped execution log (append every step)
├── {name}_findings.md       # Observations + reconciled findings
├── {name}_decision_tree.md  # Branch points (D{N}) + pruned approaches
├── {name}_user_messages.md  # Verbatim user inputs
└── results/                 # Output artifacts
```

**Each file has a purpose. None are optional.**

---

## Startup

### 1. Check Environment

```bash
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    echo "CPU-only or Mac environment"
fi
```

### 2. Load Plan

Read the plan file. Identify:
- Task directory and task name
- Hypothesis, stages, steps, checkpoints
- Dependencies, verification criteria, "If wrong" fields
- Stopping criteria, "If Stuck" section

### 3. P8 Compliance Check (BLOCKING)

Run the deterministic P8 check on the plan:

```bash
r-check-plan-p8 {path to plan}
```

**If this exits non-zero**, the plan is missing required sections (hypothesis, predictions, alternatives, stopping criteria, or budget). You cannot execute an incomplete plan. Do one of:
- Stop and report to user with the specific missing sections
- If running autonomously (ralph-loop / overnight), spawn investigator + critic to propose the missing sections, update the plan, re-run `r-check-plan-p8`, then proceed

An experiment without predictions is an experiment without a hypothesis. Do not skip this.

### 4. Initialize Task Files (DETERMINISTIC)

Run the initialization script. It's idempotent — safe to run every time:

```bash
r-init-task-files {task_dir} {task_name}
```

This creates the 5 mandatory files with correct templates if they don't exist. **You do not write them by hand.** The script is the source of truth for format.

### 5. Load State

```
Read {task_dir}/{name}_notepad.md       # catch up on progress
Read {task_dir}/{name}_decision_tree.md # check for pruned approaches
Read {task_dir}/{name}_findings.md      # review prior observations
```

### 6. Create Task List

One task per step in the plan, grouped by stage if applicable.

---

## Execution Loop

For each step in the plan (respecting stage order).

**If a stage has only key steps (no exact commands):** Decompose it into atomic steps before executing. Read relevant scripts' argparse, write exact commands, define expected outputs and verification. You have context from prior stages that the planner didn't have.

For each step:

### 1. Check Dependencies

Confirm referenced prior steps are marked VERIFIED in the notepad.
If dependency not met → STOP, report which dependency is unresolved.

### 2. Check Decision Tree

If the approach you're about to try appears under a `D{N}-PRUNED` section, check the `DO NOT RETRY UNLESS` condition. If not met → skip this approach, note in notepad.

### 3. Re-Anchor

Re-read the plan (current step + hypothesis) and the last ~10 notepad entries.
Prevents context drift on long tasks. [Addresses F6]

### 4. Execute

If step involves a script:
- Read the script's argparse/flags first
- Verify flags match the plan
- Check existing outputs (don't re-run completed work)

Then run the step.

### 5. Verify

**Produce evidence, not claims.** [Addresses F1]

Check the plan's verification criteria and "If wrong" field.

```
IF oracle/reference exists:
  COMPARE output vs oracle → record evidence
ELSE IF automated test exists:
  RUN it → record output
ELSE:
  SPAWN analyst or critic to verify
```

"Check again" loop: after fixing issues, re-verify (max 3 iterations). [Addresses F5]

### 6. RECORD (MANDATORY GATE — via script)

**You cannot execute step N+1 until step N is recorded.** Use the deterministic script:

```bash
r-append-notepad {notepad_path} {step_num} "{step_name}" VERIFIED \
  "{how verified}" "{specific evidence}" "{yes | no — details}"
```

This writes the entry in the exact required format, increments `Steps completed`, and updates `Last updated`. **Do not write notepad entries by hand** — the script is the enforcement.

**If a decision was made between approaches**, also append to the decision tree. Write the D{N} block directly to `{name}_decision_tree.md`:

```
## D{N}: {decision context}
| Option | Description |
|---|---|
| A | {approach 1} |
| B | {approach 2} |
**Chosen:** {which and why}
**Outcome:** SUCCEEDED
```

### 7. Decision Point

**Verified and clean** → continue to next step.

**Something wrong:**
- Check plan's "If wrong" field
- Check "If Stuck" section
- Try fix (max 3 attempts)
- If still failing → record FAILURE via `r-append-notepad` with status `FAILURE`, add a D{N}-PRUNED entry to the decision tree, STOP

**Something surprising** (result is correct but unexpected):
- Append an observation to `{name}_findings.md` (the "## Observations" section)
- Continue — the stage judgment will handle deeper investigation

Record pruned approaches in the decision tree:
```
### D{N}-PRUNED: {approach name}
- Status: ATTEMPTED_AND_FAILED
- Reason: {specific evidence — error message, wrong output}
- DO NOT RETRY UNLESS: {what would need to change}
```

---

## Progress Checkpoint (Every 5 Steps)

**Every 5 completed steps, STOP and run this check.** This catches "stuck doing useless work under false pretenses" — where steps look productive but don't advance the goal.

Spawn a background **check-in agent** (`r:check-in`) with:

> "Check progress on this experiment.
> - Notepad: {path}
> - Plan: {path}
> - Decision tree: {path}
> - Findings: {path}"

The check-in agent has fresh context, can spawn its own investigators and critics, and returns a verdict: GOOD / SLOW / SPINNING / OFF-TRACK.

**Also run the deterministic format check:**
```bash
r-check-notepad-format {notepad_path}
```

If this exits non-zero, the notepad has drifted from the required format. Fix it before continuing.

**If the check-in agent says SPINNING or OFF-TRACK:**
- STOP execution
- Re-read the plan's hypothesis and success criteria
- Re-read the "If Stuck" section
- Write to notepad via `r-append-notepad` with status `PROGRESS_CHECK`
- Add a D{N}-PRUNED entry for the approach that wasn't working
- Continue with a different approach

---

## Stage Judgment

**After completing each stage checkpoint — this is the core of the research agent.**

Don't just verify outputs exist. Think about what the results mean.

### 1. Verify the Checkpoint

Confirm all checkpoint items pass. Run analyst on stage outputs if applicable.

### 2. Reflect on Results

Answer these questions (write answers to notepad via `r-append-notepad` with status `STAGE_JUDGMENT`):

- **What did this stage reveal?** 2-3 sentences on what we learned.
- **Does the hypothesis still hold?** If results contradict expectations, say so explicitly.
- **What assumptions were violated?** Anything surprising.
- **What questions did this raise?** List them — even obvious ones.

### 3. Investigate Leads

Look at the questions from step 2. For the top 2-3 substantive questions:

- Spawn investigator agents (parallel where independent)
- Wait for results
- Write findings to notepad via `r-append-notepad`

**Do not skip this.** The failure mode we're preventing: agent identifies 5 gaps in its own analysis but never investigates any of them, because "the plan's step list doesn't include them." Research means following the questions your results raise.

### 4. Assess Next Stage

Based on what you learned:

- **Plan still makes sense** → continue
- **Adjustments needed** → document the adjustment in notepad, adapt your approach, continue
- **Fundamentally broken** → write what you've learned to findings.md and stop. A well-documented partial result is valuable.

### 5. Correction Propagation

If any result from this stage corrects or changes a prior finding:
- List all downstream work that depends on the changed result
- Mark those results as potentially stale in notepad
- Re-verify where practical, or flag clearly

---

## Completion

When all steps are done (or stopping criteria met):

### 1. Check Success Criteria

For EACH criterion in the plan:
- Find specific evidence it was met
- If unclear → spawn critic to assess
- If no evidence → go back and do the work

### 2. Investigate Remaining Leads

**"What questions did this experiment raise that I haven't answered?"**

List them. For the top 2-3 substantive questions, investigate now. This is the final forcing function — don't declare victory while interesting leads sit uninvestigated.

If questions remain but are genuinely out of scope, note them in findings.md under "Future Directions."

### 3. Write Reconciled Findings

Review all observations from findings.md. Write the **Findings** section:
- Reconcile any contradictions between early and late observations
- For each finding: claim, evidence, implication
- Status: CONFIRMED / REFUTED / INCONCLUSIVE
- Note any corrections made during the run and what they affected

### 4. Hypothesis Assessment

Append to notepad:
```
## Hypothesis Assessment
- Hypothesis: {verbatim from plan}
- Result: CONFIRMED | REFUTED | INCONCLUSIVE | PARTIALLY_CONFIRMED
- Evidence: {specific results}
- Caveats: {limitations}
```

### 5. Post-Execution Verification (for code changes)

Spawn a **verifier** agent on all code changes:
1. Enumerate possible bugs (data flow, state, API contracts, semantics)
2. Read actual code to check each
3. Report: SHIP / FIX FIRST / RETHINK

Fix any bugs found. Don't mark complete until verifier passes.

### 6. Final Format Check

```bash
r-check-notepad-format {notepad_path}
```

Must exit 0 before you can declare complete.

### 7. Final Report + Completion Signal

Write the final report to the notepad, then emit the ralph-loop completion promise:

```
### [YYYY-MM-DD HH:MM PST] COMPLETE

## Success Criteria
- [x] Criteria 1: {evidence}

## Hypothesis Assessment
{from step 4}

## Key Findings
{top 3-5 from findings.md}

## Adjustments Made
{any deviations from original plan and why}

## Remaining Questions
{leads not investigated, future directions}
```

Update task index if it exists.

**Finally, emit the ralph-loop completion signal on its own line:**
```
<promise>DONE</promise>
```

**Do not emit `<promise>DONE</promise>` unless:**
- All success criteria met with specific evidence
- `r-check-notepad-format` passed
- findings.md has a reconciled Findings section
- Post-execution verifier (if applicable) passed
- No uninvestigated leads remain

Emitting `<promise>DONE</promise>` prematurely breaks the ralph-loop. If you're not sure, don't emit it.

---

## Error Handling

**Step fails:** Check "If wrong" → "If Stuck" → try fix (3x) → record FAILURE via `r-append-notepad`, add D-PRUNED to decision tree, STOP.

**Out of resources:** Log to notepad, STOP, report constraints.

**Overnight / autonomous runs:** Do NOT stop and wait for user input on non-fatal issues. Make your best judgment, document the reasoning via `r-append-notepad`, and continue. A partial run with documented decisions is more valuable than a stopped run waiting for a sleeping user. Reserve stopping for: (a) resource failures, (b) cascading errors where continuing would waste significant compute, (c) results so unexpected that any direction could be wrong.

---

## Guidelines

- **The bin/ scripts are the enforcement.** `r-init-task-files`, `r-check-plan-p8`, `r-append-notepad`, `r-check-notepad-format`. Use them. Don't write notepad/plan-check logic by hand.
- **Stage judgment is mandatory.** Don't reduce it to "outputs exist, moving on."
- **Investigate leads before moving on.** When you identify a gap or question, explore it.
- **Trace corrections.** When you fix a number, ask "what else used this number?" and check those too.
- **Decide autonomously on overnight runs.** Document your reasoning in the notepad.
- **Evidence, not claims.** "Verified" without specific proof is meaningless.
- **`<promise>DONE</promise>` is a commitment, not a hope.** Only emit when actually done.
