---
description: Collaborative experiment planning. Explores codebase, interviews you about requirements, proposes approaches, and writes a detailed PLAN.md.
allowed-tools: ["Task", "Read", "Write", "Glob", "Grep", "AskUserQuestion"]
---

# Plan Experiment

Experiment goal: $ARGUMENTS

## Process

### Phase 1: Understand the Goal

Parse the experiment goal. If unclear or too vague, use AskUserQuestion to clarify:
- What hypothesis are we testing?
- What would success look like?
- Any constraints or preferences?

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

Launch a reflector agent to synthesize investigator findings:
- What's the coherent picture?
- What gaps remain?
- What assumptions are we making?

Use this synthesis to inform approach proposals.

### Phase 3: Check Prerequisites

Identify what needs to exist before running:
- Required trait datasets in `datasets/traits/`
- Required model configs in `experiments/*/config.json`
- Required calibration files, vectors, etc.

Use investigator agents to verify these exist or note what's missing.

### Phase 4: Propose Approaches

Based on codebase exploration, propose 2-3 approaches:
- Different methods, positions, or configurations
- Different analysis strategies
- Trade-offs between them

Use AskUserQuestion to let user choose or suggest modifications.

### Phase 5: Stress-Test the Approach

**MANDATORY**: Launch the critic agent to review the proposed approach before detailing steps:
- Are there flaws in the methodology?
- What could go wrong?
- What assumptions are we making?

DO NOT proceed to Phase 6 until critical issues are addressed.

### Phase 6: Detail the Steps

For each step in the plan:
1. Read the relevant script's argparse to understand exact flags
2. Check what outputs would be created
3. Define verification criteria

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

### Phase 7.5: Final Critic Review

**MANDATORY**: After writing PLAN.md, launch critic agent to verify:
- Are success criteria measurable and realistic?
- Are expected values consistent with prior data?
- Any logical contradictions in the plan?

Report critic findings to user along with plan summary.

### Phase 8: Confirm with User

Show summary of the plan AND critic findings, then ask for approval.
Use AskUserQuestion with options:
- Approve plan as-is
- Address critic issues first
- Modify [specific aspect]
- Start over with different approach

## Guidelines

- **Ask questions whenever uncertain** - Don't wait for designated phases. If you need clarification about scope, priorities, constraints, or approach at ANY point, use AskUserQuestion immediately.
- Always read script argparse before including commands
- Include verification steps for each major step
- The plan should be detailed enough for /r:run-experiment to execute
- Critic is MANDATORY at Phase 5 and Phase 7.5 - do not skip
