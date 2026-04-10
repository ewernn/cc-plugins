---
description: Execute a plan as a research agent. Runs steps, analyzes results, investigates leads, and adapts. Produces useful findings even on incomplete runs.
allowed-tools: ["Task", "Read", "Write", "Bash", "Glob", "Grep", "TaskCreate", "TaskUpdate", "TaskList"]
---

# Run Experiment

Target: $ARGUMENTS

If no argument provided, look for a plan file (`*_plan.md` or `PLAN.md`) in the current directory.

## Startup

### 1. Load System Spec

Read `${CLAUDE_PLUGIN_ROOT}/docs/system.md`. Focus on:
- Failure modes F1-F12 (especially F1: fake verification, F3: skipping hard parts, F4: premature completion)
- Evidence-based verification (not claims)
- Anti-patterns table

### 2. Check Environment

```bash
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    echo "CPU-only or Mac environment"
fi
```

### 3. Load Plan

Read the plan file. Parse:
- **Hypothesis** — the scientific prediction
- **Stages** and steps within each stage
- **Checkpoints** between stages
- **Dependencies**, expected outputs, verification criteria, "If wrong" fields
- **"If Stuck"** section
- **Stopping criteria** — what "done" looks like (semantic, not just step count)

Also read:
- **Notepad** (`*_notepad.md`) — catch up on progress if resuming
- **Decision tree** (`*_decision_tree.md`) — check for pruned approaches

### 4. Initialize File Structure

**All files below are MANDATORY. Create any that don't exist. These are not optional documentation — they are the execution infrastructure.**

The task directory should contain:
```
{task_dir}/
├── {name}_plan.md           # Already exists (from plan-experiment)
├── {name}_notepad.md        # Timestamped execution log (append-only)
├── {name}_findings.md       # Observations + reconciled findings
├── {name}_decision_tree.md  # Branch points, pruned approaches, DO NOT RETRY conditions
├── {name}_user_messages.md  # Verbatim user inputs about this task
└── results/                 # Output artifacts
```

**Notepad** (if new):
```markdown
# {Task Name} — Notepad

## Status: IN_PROGRESS
## Started: {YYYY-MM-DD HH:MM PST}
## Last updated: {YYYY-MM-DD HH:MM PST}
## Steps completed: 0

---
```

**Findings** (if new):
```markdown
# {Task Name} — Findings

## Observations
_Append here during the run when something notable happens._

## Findings
_Written at completion — reconciled claims with evidence._
```

**Decision Tree** (if new):
```markdown
# {Task Name} — Decision Tree

_Record branch points (choices between approaches) and pruned approaches (failed or rejected, with DO NOT RETRY UNLESS conditions)._
```

**User Messages** (if new — capture the original goal):
```markdown
# {Task Name} — User Messages

### [{YYYY-MM-DD HH:MM PST}] Original Goal
{verbatim from plan or user input}
```

Also update **task_index.md** if it exists.

### 5. Create Task List

One task per step, grouped by stage if applicable.

---

## Execution Loop

For each step in the plan (respecting stage order).

**If a stage has only key steps (no exact commands):** Decompose it into atomic steps before executing. Use the same criteria as plan-experiment Phase 6b — read relevant scripts' argparse, write exact commands, define expected outputs and verification. You have context from prior stages that the planner didn't have. Use it.

For each step:

### 1. Check Dependencies

Confirm referenced prior steps are marked PASSED in the notepad.
If dependency not met → STOP, report which dependency is unresolved.

### 2. Check Decision Tree

If the approach appears under a pruned section, check the `DO NOT RETRY UNLESS` condition.
If not met → skip, note in notepad.

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

Record in notepad:
```
### [YYYY-MM-DD HH:MM PST] Step N: {name} — VERIFIED
- Method: {how verified}
- Evidence: {specific output, metric, diff}
- Clean: {yes | no — details if no}
```

### 6. Record (MANDATORY — before proceeding to next step)

**You cannot execute step N+1 until you have completed these writes for step N:**

a) **Notepad entry** with timestamp, method, evidence, clean status (template in step 5 above)
b) **Decision tree entry** if you made a choice between approaches or rejected an approach. Format:
```
## D{N}: {decision context}
| Option | Description |
|---|---|
| A | {approach 1} |
| B | {approach 2} |
**Chosen:** {which and why}
**Outcome:** {filled after — SUCCEEDED / FAILED}
```
c) **Update "Steps completed" counter** in notepad header
d) **Update "Last updated" timestamp** in notepad header

If no decision was made (straightforward step with one obvious approach), skip (b) but still do (a), (c), (d).

### 7. Decision Point

**Verified and clean** → continue to next step.

**Something wrong:**
- Check plan's "If wrong" field
- Check "If Stuck" section
- Try fix (max 3 attempts)
- If still failing → record FAILURE in notepad + decision tree, STOP

**Something surprising** (result is correct but unexpected):
- Write an observation to findings.md
- Continue — the stage judgment will handle deeper investigation

Record failures in notepad AND decision tree:
```
### D{N}-PRUNED: {approach name}
- Status: ATTEMPTED_AND_FAILED
- Reason: {specific evidence — error message, wrong output, etc.}
- DO NOT RETRY UNLESS: {what would need to change}
```

---

## Progress Checkpoint (Every 5 Steps)

**Every 5 completed steps, STOP and run this check.** This catches the "stuck doing useless work under false pretenses" failure mode — where the agent keeps executing steps that look productive but aren't advancing the goal.

Spawn a **background reflector** with this prompt:

> "Read the notepad's last 10 entries and the plan's hypothesis/success criteria. Answer:
> 1. Is the agent making real progress toward the success criteria, or repeating similar actions?
> 2. What concretely changed in the last 5 steps? (specific outputs, not 'made progress')
> 3. Are the file infrastructure requirements being followed? (timestamped notepad entries, decision tree populated at branch points, findings.md updated on surprises)
> 4. If stuck or spinning: what should change?"

**If the reflector says stuck or spinning:**
- STOP execution
- Re-read the plan's hypothesis and success criteria
- Re-read the "If Stuck" section
- Write to notepad: what you were doing, why it wasn't working, what you'll do differently
- Write to decision tree: prune the approach that wasn't working
- Only then continue with a different approach

**If the reflector flags missing file infrastructure:**
- Catch up on all missing writes before continuing
- This is non-negotiable — the files are how progress survives context compaction

---

## Stage Judgment

**After completing each stage checkpoint — this is the core of the research agent.**

Don't just verify outputs exist. Think about what the results mean.

### 1. Verify the Checkpoint

Confirm all checkpoint items pass. Run analyst on stage outputs if applicable.

### 2. Reflect on Results

Answer these questions (write answers to notepad):

- **What did this stage reveal?** 2-3 sentences on what we learned.
- **Does the hypothesis still hold?** If results contradict expectations, say so explicitly.
- **What assumptions were violated?** Anything surprising or different from what the plan predicted.
- **What questions did this raise?** List them — even obvious ones.

### 3. Investigate Leads

Look at the questions from step 2. For the top 2-3 substantive questions:

- Spawn investigator agents (parallel where independent)
- Wait for results
- Write findings to notepad

This is what separates a research agent from a plan executor. **Do not skip this.** The OA experiment case study: the agent identified 5 gaps in its own analysis but never investigated any of them. The user had to ask "should we investigate these?" That failure is what this step prevents.

### 4. Assess Next Stage

Based on what you learned:

- **Plan still makes sense** → continue to next stage
- **Adjustments needed** → document what changes and why in notepad, adapt your approach for the next stage. You don't need to formally amend the plan — just note the adjustment and proceed intelligently.
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
- Include: CONFIRMED / REFUTED / INCONCLUSIVE status
- Note any corrections made during the run and what they affected

### 4. Hypothesis Assessment

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

### 6. Final Report

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

---

## Error Handling

**Step fails:** Check "If wrong" → "If Stuck" → try fix (3x) → STOP and report.

**Out of resources:** Log to notepad, STOP, report constraints.

**Overnight / autonomous runs:** Do NOT stop and wait for user input on non-fatal issues. Make your best judgment, document the reasoning in notepad, and continue. A partial run with documented decisions is more valuable than a stopped run waiting for a sleeping user. Reserve stopping for: (a) resource failures, (b) cascading errors where continuing would waste significant compute, (c) results so unexpected that any direction could be wrong.

---

## Guidelines

- **Stage judgment is mandatory.** This is what makes it a research agent. Don't reduce it to "outputs exist, moving on."
- **Investigate leads before moving on.** When you identify a gap or question, explore it. The biggest failure mode is identifying problems and not pursuing them.
- **Write observations when surprised, not per-step.** Most steps will go as expected. Write to findings.md when something genuinely notable happens.
- **Trace corrections.** When you fix a number, ask "what else used this number?" and check those too.
- **Decide autonomously on overnight runs.** Document your reasoning. Don't block on user input for judgment calls.
- **Evidence, not claims.** "Verified" without specific proof is meaningless.
- **Check decision tree before every step.** Don't re-attempt pruned approaches.
- **Proportional investigation.** A small surprise gets a quick check. A big surprise gets deep investigation. Use judgment, not budgets.
