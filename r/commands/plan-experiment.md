---
description: Collaborative experiment planning. Explores codebase, interviews you about requirements, proposes approaches, and writes a detailed PLAN.md.
allowed-tools: ["Task", "Read", "Write", "Glob", "Grep", "AskUserQuestion"]
---

# Plan Experiment

Experiment goal: $ARGUMENTS

## Setup: Load System Spec

Read the autonomous workflow system spec at `${CLAUDE_PLUGIN_ROOT}/docs/system.md`. This contains failure modes (F1-F12), verification requirements, anti-patterns, and file formats. Reference it throughout planning.

## Setup: Locate Task Directory

Before planning, find where tasks live:

1. Search for `task_index.md` in the repo: `find . -name "task_index.md" -not -path "*/node_modules/*" | head -1`
2. If found → task directory is its parent
3. If not found → use AskUserQuestion: "Where should task directories live? (e.g., dev/autonomous-workflow/tasks/)"

Store the path for Phase 7.

## Questioning Philosophy

This skill prioritizes THOROUGH questioning over speed. Ask many questions, get explicit answers.

- **Default: Ask, don't assume.** If a decision could go multiple ways, ask.
- **Block on answers.** Don't proceed with assumptions - wait for user input.
- **Fine-grained decisions.** Break big choices into specific sub-questions.
- **The more questions the better.** Users want precise plans, not fast plans.

Every phase should generate questions. If a phase produces no questions, you probably missed something.

## Process

### Phase 0: Assess Complexity

Before anything else, estimate the scale of this task:

| Tier | Signals | Planning depth | Example |
|---|---|---|---|
| **Small** | Single script, known method, <1 day | 5-15 steps, 1 stage | "Run extraction for trait X" |
| **Medium** | Multiple scripts, some unknowns, 1-3 days | 15-40 steps, 2-3 stages | "Compare steering across 3 models" |
| **Large** | Novel methodology, many unknowns, 3+ days | 40-100+ steps, 4-7 stages | "Build new evaluation pipeline" |

Use AskUserQuestion: "I'd estimate this is [tier] complexity. Does that match your expectation? Any constraints on timeline?"

**Scaling rule:** Planning effort scales with tier. Large tasks can take 100+ messages and days to plan. That's fine. A bad plan executed fast is worse than a good plan that took a week.

### Phase 1: Understand the Goal

Parse the experiment goal. Use AskUserQuestion to clarify ALL of:

**Scope:**
- What exactly are we doing?
- What does success look like? (measurable — numbers, tests passing, specific behavior)
- What does failure look like?

**Constraints:**
- What tools/frameworks/APIs are involved?
- What can't we change? (dependencies, interfaces, data formats)
- Time/compute budget?

**Methodology:**
- What approach are we taking? Are there alternatives?
- What prior work exists (in this repo or elsewhere)?
- Any conventions or patterns we must follow?

**Edge cases:**
- What if the approach doesn't work?
- What could silently produce wrong results?
- What are the riskiest assumptions?

DO NOT proceed until these are answered. It's better to ask too many questions than to make assumptions.

### Phase 2: Explore the Codebase

Launch 2-3 investigator agents to understand:
- What code/tools exist for this kind of work
- What similar work has been done before (check git log, existing dirs)
- What dependencies, APIs, or data are involved

Each investigator should take a DIFFERENT angle — don't overlap.

### Phase 2.5: Synthesize Findings

**MANDATORY**: Launch a reflector agent to synthesize investigator findings:
- What's the coherent picture?
- What gaps remain?
- What assumptions are we making?

Use this synthesis to inform approach proposals. Do not proceed to Phase 3 until synthesis is complete.

### Phase 3: Check Prerequisites

Identify what needs to exist before running:
- Required files, configs, dependencies
- Required APIs, services, or access
- Required data or test fixtures

Use investigator agents to verify these exist or note what's missing.

**Questioning checkpoint:** Before proceeding, ask about any decisions that were made implicitly. Surface all assumptions about data formats, file locations, naming conventions.

### Phase 4: Propose Approaches

Based on codebase exploration, propose 2-3 approaches:
- Different methods, positions, or configurations
- Different analysis strategies
- Trade-offs between them

Use AskUserQuestion to let user choose or suggest modifications.

**Questioning checkpoint:** For the chosen approach, ask about every parameter that has a default. Don't assume defaults are correct for this experiment.

### Phase 5: Stress-Test the Approach

**MANDATORY**: Launch the critic agent to review the proposed approach before detailing steps:
- Are there flaws in the methodology?
- What could go wrong?
- What assumptions are we making?

DO NOT proceed to Phase 6 until critical issues are addressed.

If critic identifies gaps in understanding, GO BACK to Phase 2 and spawn more investigators. Phases are not strictly linear.

**Loop limit:** If you've done 3 Phase 2→5 cycles without resolution, STOP and use AskUserQuestion to get user guidance on how to proceed.

### Phase 6: Decompose into Stages and Steps

**This is the most important phase.** A plan fails or succeeds based on decomposition quality.

#### 6a: Break into Stages

Group work into sequential stages. Each stage has a clear deliverable and can be verified independently.

Example (from a real physics paper done with Claude — 102 tasks across 7 stages):
```
Stage 1: Kinematics (14 tasks)
Stage 2: NLO Structure (12 tasks)
Stage 3: SCET Factorization (18 tasks)
Stage 4: Anomalous Dimensions (15 tasks)
Stage 5: Resummation (20 tasks)
Stage 6: Matching + Numerics (13 tasks)
Stage 7: Documentation (10 tasks)
```

For Medium/Large tasks, use AskUserQuestion: "Here are the stages I see: [list]. Does this decomposition make sense? What's missing?"

#### 6b: Break Each Stage into Steps

**Stage 1** gets full detail — exact commands, expected outputs, verification. Later stages get lighter treatment.

**For Stage 1 steps (and any stage where the approach is clear):**

The atomic step test: Can Claude complete this step in ~30 min without losing direction? If not, break smaller.

For EACH step:
1. Read the relevant script's argparse to understand exact flags
2. Write the exact command with all flags resolved (no placeholders that require judgment)
3. List exact expected outputs (file paths, row counts, value ranges)
4. Define verification: what to check AND what "wrong" looks like
5. State dependencies: which prior steps must be verified before this one starts

**For later stages (where approach depends on earlier results):**

Don't over-specify. Later stages often depend on what Stage 1 reveals. Write:
1. **Stage purpose** — what this stage accomplishes
2. **Key steps** — what needs to happen (not exact commands)
3. **Stopping criteria** — how to know this stage is done (semantic, not step count)
4. **Depends on** — what from prior stages this stage needs
5. **Predictions** — what results you expect, so run-experiment can judge whether to adjust

Run-experiment will decompose later stages into atomic steps at execution time, when it has context from prior stages. A plan that over-specifies later stages is fragile — it assumes you know the results before running.

**For steps with LLM scoring/evaluation:**
- Add a `#### Verify` block that prints actual data (input, output, scores)
- Sample 3-5 results so run-experiment can check if scores match content
- Document expected score ranges if known

**Before writing custom code:**
1. Check if existing scripts handle your use case (even partially)
2. If writing custom code: read the IMPLEMENTATION of the most similar existing function and copy its patterns
3. Custom code will be reviewed for bugs in Phase 7.5

Custom code is acceptable when format conversion would be more complex than the custom code itself, or when combining parts from multiple existing functions.

#### 6c: Question Every Step

For EACH step, ask yourself (and the user if unsure):
- "Is there anything about this step that could silently produce wrong results?" (wrong sign, wrong direction, off-by-one, wrong file)
- "What's the dumbest mistake Claude could make here?" Then add a verification check for it.
- "If this step fails, what's the fallback?" Document in the plan's "If Stuck" section.

**For Large tasks:** Use AskUserQuestion to walk through the steps with the user. Show 5-10 steps at a time, get feedback, iterate. Don't dump 80 steps and ask "looks good?"

#### 6d: Add Checkpoints Between Stages

After every stage boundary, insert a checkpoint:
```markdown
### Checkpoint: After Stage N
Stop and verify before proceeding:
- [ ] All Stage N outputs exist and are verified
- [ ] No error patterns carried forward from earlier stages
- [ ] Results so far are consistent with hypothesis
- [ ] Notepad is up to date with all step results
- [ ] Stage judgment complete (what did we learn? any leads to investigate?)
```

Checkpoints are where run-experiment pauses, reflects on results, investigates leads, and decides whether the plan for the next stage still makes sense. This is the most important moment in adaptive execution — don't reduce it to a checkbox exercise.

### Phase 7: Create Task Directory and Write Plan

Using the task directory found in Setup, create `{tasks_dir}/{kebab-case-name}/`:

1. Create the directory
2. Write `{name}_plan.md` (the plan — see template below)
3. Write `{name}_notepad.md` (header only: Status: NOT_STARTED, Started/Updated timestamps)
4. Write `{name}_findings.md` (header only: Observations + Findings sections)
5. Write `{name}_decision_tree.md` (header only: "# {Task Name} — Decision Tree")
6. Write `{name}_user_messages.md` (capture the original user goal from $ARGUMENTS)
7. Create `results/` subdirectory
8. Add a row to `task_index.md`: task name, IN_PROGRESS, start time PST, one-line description

Plan template:

```markdown
# Experiment: [Name]

## Goal
[One sentence]

## Hypothesis
[What we expect to find]

## Complexity
[Small / Medium / Large] — [N] stages, [N] steps, estimated [N] hours

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Prerequisites
- [What must exist before starting]
- Commands to verify they exist

## Stopping Criteria
[When is this experiment done? Semantic conditions, not step counts.]
- [Condition 1: e.g., "trait vectors validated with >0.7 AUC"]
- [Condition 2: e.g., "steering shows causal effect in expected direction"]

## Stage 1: [Name] ([N] steps)
_Full detail — exact commands, outputs, verification._

### 1.1: [Name]
**Purpose**: [Why this step]
**Depends on**: [none / step X.Y verified]
**Predicts**: [What result we expect — so run-experiment can judge if results match]

**Read first**:
- `path/to/script.py` - check args

**Command**:
```bash
python path/to/script.py --flag value
```

**Expected output**:
- `path/to/output/` - [description, specific: N files, ~X rows each]

**Verify**:
```bash
ls path/to/output/ | wc -l  # Should be N
```

**If wrong**: [What "wrong" looks like and what to check]

### 1.2: [Name]
...

### Checkpoint: After Stage 1
- [ ] All Stage 1 outputs exist and are verified
- [ ] Results consistent with hypothesis
- [ ] No error patterns carried forward
- [ ] Notepad updated with all results
- [ ] Stage judgment complete (what did we learn? any leads to investigate?)

## Stage 2: [Name]
_Lighter — key steps and stopping criteria. Run-experiment decomposes at runtime._

**Purpose**: [What this stage accomplishes]
**Depends on**: [What from Stage 1 this needs]
**Predicts**: [What we expect to find based on hypothesis]

**Key steps**:
1. [What needs to happen — not exact commands]
2. [...]

**Stopping criteria**: [How to know this stage is done]

**If results differ from predictions**: [What to investigate, what to adjust]

### Checkpoint: After Stage 2
- [ ] Stage purpose achieved
- [ ] Stopping criteria met
- [ ] Results consistent with or update hypothesis
- [ ] Stage judgment complete

## If Stuck
- [Common error] → [Fix]
- [Unexpected result] → [What to check]

## Notes
[Space for observations during run]
```

### Phase 7.5: Final Critic Review + Loop Back

**MANDATORY**: After writing PLAN.md, launch critic agent to verify:
- Are success criteria measurable and realistic?
- Are expected values consistent with prior data?
- Any logical contradictions in the plan?
- If custom code was written: review for bugs and pattern violations

**If critic finds issues:**
1. Categorize: Is this a methodology flaw, missing info, or implementation bug?
2. For methodology flaws → GO BACK to Phase 4 or 5
3. For missing info → Use AskUserQuestion immediately
4. For implementation bugs → Fix and re-run critic

DO NOT proceed to Phase 8 until critic passes or user explicitly approves despite issues.

Report critic findings to user along with plan summary.

### Phase 8: Confirm with User

Show summary of the plan AND critic findings, then ask for approval.
Use AskUserQuestion with options:
- Approve plan as-is
- Address critic issues first
- Modify [specific aspect]
- Start over with different approach

## Guidelines

- **Ask aggressively** - More questions = better plans. Don't optimize for speed.
- **Block on answers** - Never proceed with assumptions. Wait for user input.
- **Question your questions** - If you're not sure what to ask, ask what to ask.
- Always read script argparse before including commands
- Include verification steps for each major step
- **P8: Predict before executing.** Every plan MUST include: hypothesis (what we expect and why), per-step/stage predictions, at least one alternative approach considered and rejected with reason, semantic stopping criteria, time/compute budget. Run-experiment will reject incomplete plans.
- **Stage 1 must be detailed enough for run-experiment to execute without judgment calls.** Later stages can be lighter — run-experiment will decompose them at runtime with context from earlier results.
- Critic is MANDATORY at Phase 5 and Phase 7.5 - do not skip
- Phase 7.5 can loop back - phases are not strictly linear
