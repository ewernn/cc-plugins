---
description: Collaborative experiment planning. Explores codebase, interviews you about requirements, proposes approaches, and writes a detailed PLAN.md.
allowed-tools: ["Task", "Read", "Write", "Glob", "Grep", "AskUserQuestion"]
---

# Plan Experiment

Experiment goal: $ARGUMENTS

## Questioning Philosophy

This skill prioritizes THOROUGH questioning over speed. Ask many questions, get explicit answers.

- **Default: Ask, don't assume.** If a decision could go multiple ways, ask.
- **Block on answers.** Don't proceed with assumptions - wait for user input.
- **Fine-grained decisions.** Break big choices into specific sub-questions.
- **The more questions the better.** Users want precise plans, not fast plans.

Every phase should generate questions. If a phase produces no questions, you probably missed something.

## Process

### Phase 1: Understand the Goal

Parse the experiment goal. Use AskUserQuestion to clarify ALL of:

**Scope:**
- What exactly are we measuring/testing?
- What would success look like numerically?
- What would failure look like?

**Constraints:**
- Which models/variants to use?
- Which layers/positions to target?
- Time/compute budget?

**Methodology:**
- Extraction method preference (mean_diff, probe, gradient)?
- Steering direction (induce vs suppress)?
- Coefficient search strategy (adaptive vs fixed)?

**Edge cases:**
- What if baseline is already saturated (score ~0 or ~100)?
- What if coherence drops below threshold?
- What if results contradict hypothesis?

DO NOT proceed until these are answered. It's better to ask too many questions than to make assumptions.

### Phase 2: Explore the Codebase

Launch 2-3 investigator agents to understand:
- What scripts/tools exist for this kind of experiment
- What similar experiments have been done before
- What data/vectors/models are available

Key areas to explore:
- `extraction/` - vector extraction pipeline
- `inference/` - activation capture and projection
- `analysis/` - steering, benchmarks, model comparison
- `experiments/` - existing experiment configs and outputs

### Phase 2.5: Synthesize Findings

**MANDATORY**: Launch a reflector agent to synthesize investigator findings:
- What's the coherent picture?
- What gaps remain?
- What assumptions are we making?

Use this synthesis to inform approach proposals. Do not proceed to Phase 3 until synthesis is complete.

### Phase 3: Check Prerequisites

Identify what needs to exist before running:
- Required trait datasets in `datasets/traits/`
- Required model configs in `experiments/*/config.json`
- Required calibration files, vectors, etc.

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

### Phase 6: Detail the Steps

For each step in the plan:
1. Read the relevant script's argparse to understand exact flags
2. Check what outputs would be created
3. Define verification criteria

**For steps with LLM scoring/evaluation:**
- Add a `#### Verify` block that prints actual data (input, output, scores)
- Sample 3-5 results so run-experiment can check if scores match content
- Document expected score ranges if known

**Before writing custom code:**
1. Check if existing scripts handle your use case (even partially)
2. If writing custom code: read the IMPLEMENTATION of the most similar existing function and copy its patterns
3. Custom code will be reviewed for bugs in Phase 7.5

Custom code is acceptable when format conversion would be more complex than the custom code itself, or when combining parts from multiple existing functions.

**Questioning checkpoint:** For each step, ask: "Is there anything about this step that could silently produce wrong results?" (e.g., wrong sign, wrong direction, off-by-one, wrong file)

### Phase 7: Write PLAN.md

Create `experiments/{experiment_name}/PLAN.md` with:

```markdown
# Experiment: [Name]

## Goal
[One sentence]

## Hypothesis
[What we expect to find]

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Prerequisites
- [What must exist before starting]
- Commands to verify they exist

## Steps

### Step 1: [Name]
**Purpose**: [Why this step]

**Read first**:
- `path/to/script.py` - check args

**Command**:
```bash
python path/to/script.py --flag value
```

**Expected output**:
- `path/to/output/` - [description]

**Verify**:
```bash
ls path/to/output/ | wc -l  # Should be N
```

### Step 2: [Name]
...

### Checkpoint: [After Step N]
Stop and verify:
- [What to check]
- [What to look for]

## Expected Results
[Table of expected vs what would indicate success/failure]

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
- The plan should be detailed enough for /r:run-experiment to execute
- Critic is MANDATORY at Phase 5 and Phase 7.5 - do not skip
- Phase 7.5 can loop back - phases are not strictly linear
