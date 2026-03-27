---
description: Collaborative task planning. Explores codebase, interviews you about requirements, proposes approaches, and writes a detailed plan. For general codebase tasks (bugs, features, refactors).
allowed-tools: ["Task", "Read", "Write", "Glob", "Grep", "AskUserQuestion"]
---

# Plan Task

Task goal: $ARGUMENTS

## Setup: Locate Task Directory

Before planning, find where tasks live:

1. Search for `task_index.md` in the repo: `find . -name "task_index.md" -not -path "*/node_modules/*" | head -1`
2. If found → task directory is its parent
3. If not found → use AskUserQuestion: "Where should task directories live? (default: dev/autonomous-workflow/tasks/)"
4. If directory doesn't exist → create it + create `task_index.md` with empty table header

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
| **Small** | One file, known pattern, <2 hours | 3-8 steps, 1 stage | "Fix auth check on one route" |
| **Medium** | Multiple files, some investigation needed, <1 day | 8-20 steps, 2-3 stages | "Refactor duplicate routes" |
| **Large** | Cross-cutting, unknowns, multi-day | 20-60+ steps, 3-5 stages | "Add time awareness to chat context" |

Use AskUserQuestion: "I'd estimate this is [tier] complexity. Does that match? Any constraints?"

**Tier gating:**
- **Small:** Skip Phase 2.5 (synthesis). Use simplified plan template (no stages, no checkpoints). Critic (Phase 5) is still MANDATORY — a 2-minute critic call caught a data corruption bug that execution missed.
- **Medium:** Full process but 1 investigator instead of 2-3.
- **Large:** Full process. Take your time. 100+ messages is fine.

**NEVER skip critic review. For any tier.** The cost of one subagent call is negligible. The cost of a missed bug is not.

### Phase 1: Understand the Goal

Parse the task goal. Use AskUserQuestion to clarify:

**Scope:**
- What exactly are we doing?
- What does "done" look like? (measurable — tests pass, build succeeds, specific behavior)
- What should NOT change?

**Constraints:**
- What files/modules are involved?
- Any patterns or conventions to follow? (check CLAUDE.md, main.md)
- Any related work in progress?

**Risks:**
- What could break?
- What could silently go wrong?
- Are there callers/consumers that depend on what we're changing?

DO NOT proceed until these are answered.

### Phase 2: Explore the Codebase

Launch investigator agents to understand:
- The code we're changing (read the actual files, not just descriptions)
- All callers/consumers of what we're touching
- Similar patterns elsewhere in the codebase

Each investigator should take a DIFFERENT angle — don't overlap.

### Phase 2.5: Synthesize Findings (Medium/Large only)

**MANDATORY for Medium/Large**: Launch a reflector agent to synthesize investigator findings:
- What's the coherent picture?
- What gaps remain?
- What assumptions are we making?

### Phase 3: Check Prerequisites

Identify what needs to exist before starting:
- Required files, configs, dependencies
- Required test fixtures or data
- Any migrations or schema changes needed

**Questioning checkpoint:** Surface all implicit assumptions. Ask about anything unclear.

### Phase 4: Propose Approaches

Propose 2-3 approaches with trade-offs. Use AskUserQuestion to let user choose.

**Questioning checkpoint:** For the chosen approach, ask about every detail that has a default or assumption.

### Phase 5: Stress-Test the Approach

**MANDATORY for ALL tiers**: Launch the critic agent to review the approach:
- Are there flaws?
- What could go wrong?
- What assumptions are we making?

If critic identifies gaps, GO BACK to Phase 2. Phases are not strictly linear.

**Loop limit:** 3 cycles of Phase 2→5 without resolution → STOP and ask user.

### Phase 6: Decompose into Steps

**This is the most important phase.**

**The atomic step test:** Can Claude complete this step without losing direction? If not, break it smaller.

For EACH step:
1. Read the actual files involved
2. Describe the exact change (not vague — specific lines, specific logic)
3. Define expected outcome (test passes, grep confirms, build succeeds)
4. Define what "wrong" looks like
5. State dependencies on prior steps

For Medium/Large tasks, group steps into stages with checkpoints between them.

**For each step, ask:** "What's the dumbest mistake Claude could make here?" Add a verification check for it.

### Phase 7: Create Task Directory and Write Plan

Using the task directory found in Setup, create `{tasks_dir}/{kebab-case-name}/`:

1. Create the directory
2. Write `{name}_plan.md` (see templates below)
3. Write `{name}_notepad.md` (header only: Status: NOT_STARTED, timestamps PST)
4. Write `{name}_decision_tree.md` (header only)
5. Write `{name}_user_messages.md` (capture the original user goal + all Q&A from planning)
6. Create `results/` subdirectory
7. Add a row to `task_index.md`: task name, NOT_STARTED, timestamp PST, one-line description

**Small plan template:**

```markdown
# Task: [Name]

## Goal
[One sentence]

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Steps

### 1: [Name]
**Change**: [Exact description of what changes]
**File(s)**: [paths]
**Verify**: [How to confirm it worked]
**If wrong**: [What failure looks like]

### 2: [Name]
...

## If Stuck
- [Common error] → [Fix]
```

**Medium/Large plan template:**

```markdown
# Task: [Name]

## Goal
[One sentence]

## Complexity
[Small / Medium / Large] — [N] stages, [N] steps

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Prerequisites
- [What must exist before starting]

## Stage 1: [Name] ([N] steps)

### 1.1: [Name]
**Purpose**: [Why this step]
**Depends on**: [none / step X.Y verified]
**Change**: [Exact description]
**File(s)**: [paths]
**Verify**: [How to confirm]
**If wrong**: [What failure looks like]

### Checkpoint: After Stage 1
- [ ] All changes verified
- [ ] No regressions introduced
- [ ] Build/tests still pass

## Stage 2: [Name] ([N] steps)
...

## If Stuck
- [Common error] → [Fix]
```

### Phase 7.5: Final Critic Review

**MANDATORY for ALL tiers**: Launch critic agent to verify:
- Are success criteria measurable?
- Any logical contradictions?
- Any missed edge cases?

**If critic finds issues:** fix them or ask user. DO NOT proceed until resolved.

### Phase 8: Confirm with User

Show summary of the plan, then ask for approval:
- Approve as-is
- Modify [specific aspect]
- Start over with different approach

## Guidelines

- **Ask aggressively** - More questions = better plans. Don't optimize for speed.
- **Block on answers** - Never proceed with assumptions. Wait for user input.
- **Question your questions** - If you're not sure what to ask, ask what to ask.
- The plan should be detailed enough for someone (or run-experiment) to execute without judgment calls
- Critic is MANDATORY for ALL tiers at Phase 5 and Phase 7.5 — no exceptions
- Phase 7.5 can loop back - phases are not strictly linear
