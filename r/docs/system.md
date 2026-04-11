# Research Workflow System (r plugin)

Framework for autonomous research and task execution. Counters known LLM failure modes through structural enforcement, not agent memory.

**Axiom:** If the agent needs to "remember" something to behave correctly, the system is broken. Externalize everything to files.

**Timestamps:** All in PST, format `YYYY-MM-DD HH:MM PST`.

---

## Design Principles

| # | Principle | Why |
|---|---|---|
| P1 | Externalize all state | Context compacts/drifts — files survive |
| P2 | Verify structurally | "Verified" = specific evidence, never a claim |
| P3 | Document failures equally | Failed approaches prevent re-attempts |
| P4 | Diverge then converge | Always consider alternatives before committing |
| P5 | Never trust completion claims | Loop until success criteria met with evidence |
| P6 | Spawn subagents liberally | Fresh context is cheap; stale parent context is expensive. See Subagent Usage below. |
| P7 | Show work or say "I don't know" | No unsupported justifications |
| P8 | Predict before executing | No hypothesis + budget + alternative = no experiment |

---

## Task Lifecycle

```
DEFINE ──→ PLAN ──→ EXECUTE ──→ VERIFY ──→ RECORD ──→ next step
  │          │         │           │          │
  │          │         │           ├─ FAIL → decision_tree PRUNE → back to EXECUTE or PLAN
  │          │         │           └─ PASS → notepad + decision_tree (if branch point)
  │          │         │
  │          │         ├─ every 5 steps: PROGRESS CHECK (check-in agent)
  │          │         └─ at stage boundary: STAGE JUDGMENT (reflect → investigate → assess)
  │          │
  │          └─ critic review (mandatory)
  └─ investigator exploration (multi-angle)
                                          COMPLETE? → Ralph check → findings.md → DONE or ITERATE
```

---

## Subagent Usage (Spawn Liberally)

**Fresh context is cheap. Stale parent context is expensive.** Default to spawning subagents when you need anything non-trivial:

- **Factual questions** → investigator, never answer from memory
- **Plan review** → critic, before execution (mandatory)
- **Stage boundaries** → reflector to synthesize + investigators for lead questions
- **Every 5 steps** → check-in agent to assess progress (mandatory)
- **Output verification** → analyst to parse + compare to expectations
- **Post-execution** → verifier to enumerate bugs, read code, check each (mandatory for code changes)
- **Ambiguous or stuck** → spawn 2-3 in parallel with different angles
- **When finished** → investigate remaining leads before claiming COMPLETE

Agents within a wave run in parallel. Waves run sequentially. Never bottleneck on one agent doing work another agent could do in parallel.

Anti-pattern: "I'll figure this out myself, I don't need a subagent." If you're uncertain whether to spawn one, spawn it.

---

## Failure Modes

| ID | Mode | Countermeasure |
|---|---|---|
| F1 | Claims "verified" without checking | Evidence artifacts required |
| F2 | Adjusts results to look good | Independent agent verification |
| F3 | Skips hard parts | Dependency enforcement between steps |
| F4 | Premature completion | Success criteria with evidence |
| F5 | One error, stops looking | "Check again" loop, max 3 passes |
| F6 | Loses direction on long tasks | Re-anchor to plan every step |
| F7 | Reverts to defaults over conventions | Conventions in plan.md, not memory |
| F8 | Gives the answer you want | Critic agent for independent check |
| F9 | Invents justifications | "Show work or I don't know" |
| F10 | Zombie sections | Decision tree tracks live vs pruned |
| F11 | Re-attempts failed approaches | Decision tree with DO NOT RETRY UNLESS |
| F12 | Pattern-matches instead of reading | Read actual code/formulas |

---

## File Structure

### Where the task directory lives

Recommendation by repo type:

| Repo type | Put tasks in | Example |
|---|---|---|
| Research/experiments repo | `experiments/{name}/` (existing pattern) or `dev/tasks/{name}/` | `experiments/sleeper-detection/` |
| Code repo | `dev/tasks/{name}/` or `.claude/tasks/{name}/` | `dev/tasks/auth-rewrite/` |
| Mixed | Separate: `experiments/` for research, `dev/tasks/` for code work | — |

Keep `task_index.md` at the tasks root if you run multiple tasks. One row per task: name, status, start time, one-line description.

### Per-task files

Every task directory has these files. **All are mandatory. Create any that don't exist at startup.**

```
{task_dir}/{kebab-case-name}/
├── {name}_plan.md           # Goal, hypothesis, criteria, stages, steps — from plan command
├── {name}_notepad.md        # Timestamped execution log — written every step (mandatory gate)
├── {name}_findings.md       # Observations during run + reconciled findings at completion
├── {name}_decision_tree.md  # Branch points (D{N}) + pruned approaches (DO NOT RETRY UNLESS)
├── {name}_user_messages.md  # Verbatim user inputs about this task
└── results/                 # Output artifacts: code patches, data, reports, plots
```

Each file has a different access pattern:
- **plan.md** — read at start of every step (re-anchor)
- **notepad.md** — read after compaction or when resuming; written continuously
- **findings.md** — written on surprises + at completion; the durable output even on partial runs
- **decision_tree.md** — read before attempting anything (check prior failures)
- **user_messages.md** — read during planning; written on user input
- **results/** — written during execution; referenced from notepad

**Naming:** kebab-case directories, no dates in names, files prefixed with task name (`weather-api_plan.md` not `plan.md`). This way files make sense when opened outside their directory.

### Notepad

Header: `Status`, `Started`, `Last updated`, `Steps completed` (all PST).

Entry format: `### [YYYY-MM-DD HH:MM PST] Step N: {name} — STATUS`

| Entry type | Required fields |
|---|---|
| VERIFIED | Method, Evidence, Clean |
| FAILURE | Attempted, Error, Root cause, Rules out, → decision_tree ref |
| STAGE_JUDGMENT | What revealed, Hypothesis status, Questions, Leads investigated |
| PROGRESS_CHECK | Steps since last check, Assessment, Stuck? (y/n + what to change) |

**Mandatory gate:** Cannot execute step N+1 until step N's notepad entry is written and `Steps completed` is incremented. This is not optional — it's how progress survives context compaction.

### Decision Tree

Branch points (when you chose between approaches):
```
## D{N}: {decision context}
| Option | Description |
|---|---|
| A | {approach 1} |
| B | {approach 2} |
**Chosen:** {which and why}
**Outcome:** {SUCCEEDED / FAILED — filled after}
```

Pruned approaches (failed or rejected):
```
### D{N}-PRUNED: {approach name}
- Status: NOT_ATTEMPTED | ATTEMPTED_AND_FAILED
- Reason: {specific evidence}
- DO NOT RETRY UNLESS: {condition that would make it worth trying again}
```

Check the decision tree before attempting anything. Don't re-attempt pruned approaches unless the DO NOT RETRY condition is met.

### Findings

Two sections, written at different times:
- **Observations** — append during run when something surprising happens (claim + brief note)
- **Findings** — written at completion, reconciled across all observations. Each finding: claim, evidence, implication, status (CONFIRMED / REFUTED / INCONCLUSIVE)

---

## Anti-Patterns

| DO NOT | WHY | INSTEAD |
|---|---|---|
| Self-verify without evidence | F1: agents lie | Produce artifacts |
| Skip critic on plans | F8: first plan rarely best | Mandatory critic review |
| Delete failure records | F11: future agents retry | Append-only failure log |
| Keep state only in context | F6: drift | Write to files every step |
| Trust "it looks right" | F2: agents fake | Compare to oracle/test |
| Move past blockers | F3: hard parts skipped | Block and escalate |
| Say "verified" alone | F1: meaningless | "Verified — evidence: {X}" |
| Pattern-match from memory | F12: different context | Read actual code |
| Claim "done" without Ralph check | F4: premature completion | Enumerate criteria with evidence |

---

## Integration

This spec is enforced by r plugin commands:
- `/r:plan-experiment` + `/r:plan-task` — DEFINE + PLAN (produce compliant plans with hypothesis, predictions, alternatives, stopping criteria, budget)
- `/r:run-experiment` + `/r:run-task` — EXECUTE + VERIFY + COMPLETE (file infrastructure + RECORD gate + stage judgment + progress checkpoints every 5 steps)
- `/r:swarm` — investigation waves during planning and stage judgment
- Agents: investigator, critic, reflector, analyst, verifier, check-in

**Stacks with external `ralph-loop`** for overnight autonomous runs. Ralph provides the outer bash iteration loop (keeps re-running with fresh context until `<promise>DONE</promise>`); this system provides the inner execution structure (file infrastructure, mandatory writes, progress checks, evidence-gated completion).
