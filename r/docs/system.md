# Autonomous Workflow System v0.1

General-purpose framework for autonomous Claude Code execution on well-defined tasks.
Repo-agnostic. Counters known LLM failure modes through structural enforcement, not agent memory.

**Design axiom:** If the agent needs to "remember" something to behave correctly, the system is broken. Externalize everything.

**Timestamp convention:** All timestamps in PST (Pacific Standard Time), format: `YYYY-MM-DD HH:MM PST`. Not just dates — include time.

---

## Design Principles

| # | Principle | Rationale |
|---|---|---|
| P1 | Externalize all state | Agent context compacts/drifts. All progress, decisions, failures → files. |
| P2 | Verify structurally | "Verified" is evidence (test output, diff, metric), never a claim. [F1] |
| P3 | Document failures equally | Failed approaches prevent re-attempts by future agents. [F11] |
| P4 | Diverge then converge | Multiple approaches → critique all → pick best. Never commit to first idea. |
| P5 | Never trust completion claims | Ralph protocol: loop until success criteria met with evidence. [F4] |
| P6 | Maximize token utilization | Spawn subagents freely. Side-thoughts are cheap. Idle subscriptions = waste. |
| P7 | Show work or say "I don't know" | No "this becomes", "for consistency", or unsupported claims. [F9, R15] |
| P8 | Predict before executing | Every experiment states: expected result + why, time/compute budget, alternative considered and rejected, what would invalidate the hypothesis. No predictions = no hypothesis. |

---

## Known LLM Failure Modes

| ID | Failure Mode | Countermeasure |
|----|---|---|
| F1 | Claims "verified" without checking | Require evidence artifacts for every verification |
| F2 | Adjusts results to look good (faked plots) | Cross-verify with independent agent; compare against oracle |
| F3 | Skips hard parts, moves to easier ones | Dependency enforcement: step N requires step N-1 verified |
| F4 | Premature completion claims | Ralph protocol: check all success criteria with evidence |
| F5 | Finds one error and stops looking | "Check again" loop until no new issues (max 3 passes) |
| F6 | Loses direction on long tasks | Small steps; notepad re-reads after compaction; plan as north star |
| F7 | Reverts to defaults over custom conventions | Conventions live in plan.md, not agent memory [R16] |
| F8 | Gives answer you seem to want | Critic agent as independent check; explicit honesty requirements |
| F9 | Invents plausible-sounding justifications | "Show work or say 'I don't know'" rule [P7] |
| F10 | Zombie sections / inconsistent state | Regular cleanup passes; decision tree tracks what's live vs pruned |
| F11 | Re-attempts previously failed approaches | Failure log in notepad + decision tree; read before attempting |
| F12 | Oversimplifies via pattern-matching | Read actual code/formulas; don't assume from similar-looking patterns |

---

## Task Lifecycle

```
DEFINE ──→ PLAN ──→ EXECUTE ──→ VERIFY ──→ RECORD ──→ next step
  │          │         │           │          │
  │          │         │           ├─ FAIL → decision_tree PRUNE → back to EXECUTE or PLAN
  │          │         │           └─ PASS → notepad + decision_tree (if branch point)
  │          │         │
  │          │         ├─ every 5 steps: PROGRESS CHECK (reflector)
  │          │         └─ at stage boundary: STAGE JUDGMENT (reflect → investigate → assess)
  │          │
  │          └─ critic review (mandatory)
  └─ investigator exploration
                                           COMPLETE? → Ralph check → findings.md → DONE or ITERATE
```

### Phase 1: DEFINE

**Input:** User task description
**Output:** `{name}_plan.md` (draft), `{name}_user_messages.md`

1. Capture user description verbatim → `{name}_user_messages.md`
2. Spawn 2-3 investigator agents (different angles on the problem)
3. Spawn reflector to synthesize investigator findings
4. Draft plan:
   - Goal (one sentence)
   - Success criteria (measurable — numbers, tests, diffs)
   - Approach options (minimum 2)
   - Risk assessment per approach

### Phase 2: PLAN

**Input:** Draft plan + approach options
**Output:** `{name}_plan.md` (finalized), `{name}_decision_tree.md` (initialized)

1. Spawn critic on each approach option
2. Select approach:
   - IF interactive: user chooses
   - IF autonomous: best-scored by critic (document reasoning)
3. Record selection + pruned options in decision tree
4. Break chosen approach into ordered steps:
   - Per-step: what, why, success criterion, verification method, dependencies
5. Final critic review of complete plan [mandatory — addresses F8]
6. User approval OR auto-proceed

### Phase 3: EXECUTE

**Input:** Finalized plan
**Output:** Step results + notepad entries + decision tree entries + findings observations

For each step:
1. Re-read `{name}_plan.md` (re-anchor — addresses F6)
2. Re-read `{name}_notepad.md` (catch up on progress)
3. Check `{name}_decision_tree.md` for relevant pruned approaches (addresses F11)
4. Execute step
5. Proceed to VERIFY
6. **RECORD (mandatory gate):** Write notepad entry + decision tree entry (if branch point) + update step counter. Cannot proceed to next step until this is done.
7. If something surprising → write observation to `{name}_findings.md`

**Every 5 steps:** Spawn reflector to check progress AND file infrastructure compliance. If stuck → prune approach in decision tree, try something different. If files not maintained → catch up before continuing.

**At stage boundaries:** Stage judgment — reflect on results → investigate top 2-3 leads → assess whether next stage's plan still makes sense.

### Phase 4: VERIFY

**Input:** Step output
**Output:** Verification evidence in notepad

```
evidence = NONE

IF oracle/reference exists:
  COMPARE output vs oracle → evidence
  REQUIRE: match within threshold

ELSE IF automated test exists:
  RUN test → evidence
  REQUIRE: pass

ELSE:
  SPAWN critic: "verify claim: {X}. evidence so far: {Y}"
  evidence = critic assessment

IF evidence shows issues:
  FIX issues
  RE-VERIFY (loop)
  REPEAT until clean (max 3 iterations) [addresses F5]

RECORD in notepad:
  - method used
  - evidence produced
  - issues found (if any)
  - resolution (if any)
```

### Phase 5: COMPLETE OR ITERATE (Ralph Protocol)

```
WHEN all steps done OR agent claims "done":

  READ success criteria from plan.md

  FOR EACH criterion:
    evidence = find_evidence(criterion)
    IF evidence AND valid:     → PASS
    IF evidence but unclear:   → SPAWN critic to assess → PASS or FAIL
    IF no evidence:            → FAIL (back to EXECUTE)

  IF any FAIL:
    ITERATE (update plan if needed, re-execute failed steps)

  IF all PASS:
    SPAWN verifier on all code changes (MANDATORY)
    Verifier enumerates possible bugs → reads code → checks each
    IF verifier finds bugs → fix, re-run verifier
    IF verifier passes → COMPLETE

  MAX iterations: 5 (configurable per task)
  IF max reached without all PASS → ESCALATE to user with status report
```

---

## File Structure

### Task Registry

```
{task_dir}/
├── index.md                         # Cross-task registry (if maintained)
└── {kebab-case-name}/               # Per-task directory
        ├── {name}_plan.md           # Goal, hypothesis, criteria, stages, steps
        ├── {name}_notepad.md        # Timestamped execution log (append-only, survives compaction)
        ├── {name}_findings.md       # Observations (during run) + reconciled findings (at completion)
        ├── {name}_decision_tree.md  # Branch points (D{N}) + pruned approaches (DO NOT RETRY UNLESS)
        ├── {name}_user_messages.md  # Verbatim user inputs about THIS task
        └── results/                 # Output artifacts (code, data, reports)
```

### Naming Rules

| Rule | Example | Rationale |
|---|---|---|
| Dirs: kebab-case | `weather-api-caching/` | Consistent, shell-friendly |
| No dates in dir names | NOT `2026-03-25-weather-fix/` | Dates go stale; notepad has timestamps |
| Files: prefixed with task name | `weather-api_plan.md` not `plan.md` | Context preserved when opened outside the directory |
| Differentiate by specificity | `weather-api-caching` vs `weather-api-retry` | NOT `weather-api-2` |

### User Message Routing

| Message scope | Goes to | Example |
|---|---|---|
| About the system/framework | `user_inputs.md` (root) | "Add a new agent role" |
| About a specific task | `{task}/user_messages.md` | "Change success criteria for X" |
| Ambiguous | Per-task if task exists; global otherwise | Default to specificity |

### Index Format (`tasks/index.md`)

```markdown
# Task Index

| Task | Status | Started | Description |
|---|---|---|---|
| [weather-api-caching](./weather-api-caching/) | IN_PROGRESS | 2026-03-25 14:00 PST | Cache weather API responses with 15min TTL |
| [pipeline-phase-fix](./pipeline-phase-fix/) | COMPLETE | 2026-03-24 10:00 PST | Fix phase 3 timeout on large payloads |
```

**Index rules:**
- One row per task. Link to task directory.
- Update index when creating or completing a task.
- Completed tasks stay (marked COMPLETE). Do NOT move dirs or create `_completed/` partitions.
- Delete a task dir ONLY if created in error (never started). Document in commit message.

### Per-Task Files

| File | Purpose | Access pattern |
|---|---|---|
| `{name}_plan.md` | Goal, hypothesis, success criteria, stages, steps | Read at start of every step (re-anchor) |
| `{name}_notepad.md` | Append-only timestamped execution log, evidence, failures | Read after compaction; written every step (mandatory gate) |
| `{name}_findings.md` | Observations (during run) + reconciled findings (at completion) | Written on surprises + at end; survives partial runs |
| `{name}_decision_tree.md` | Branch points (D{N}), pruned approaches + DO NOT RETRY UNLESS | Read before attempting anything; written at branch points and failures |
| `{name}_user_messages.md` | Verbatim user inputs + outcome annotations | Read during planning; written on user input |
| `results/` | Output artifacts: code patches, data files, reports | Written during execution; referenced from notepad |

### What This Does NOT Include (and Why)

| Omitted | Reason |
|---|---|
| `_completed/` partition | Just mark COMPLETE in index. Flat archive dirs degrade fast without indexes. |
| `meta.json` sidecar | Creates dual source of truth with notepad header. Ralph reads markdown fine. |
| Compaction protocol | Largest empirical notepad (trait-interp, weeks of work) is 1219 lines. Not needed yet. |
| Cross-task learnings file | Zero evidence of need. Task B reads Task A's notepad directly if needed. |

### Notepad Format

Header: Status, Started, Last updated, Steps completed (PST timestamps). Then append-only entries.

Entry format: `### [YYYY-MM-DD HH:MM PST] Step N: {name} — STATUS`

| Entry type | Required fields |
|---|---|
| VERIFIED | Method, Evidence, Clean |
| FAILURE | Attempted, Error, Root cause, Rules out, → decision_tree ref |
| STAGE_JUDGMENT | What revealed, Hypothesis status, Questions raised, Leads investigated |
| PROGRESS_CHECK | Steps since last check, Progress assessment, Stuck? (yes/no + what to change) |

**Writing the notepad entry is a mandatory gate** — cannot execute step N+1 until step N's entry is written and the "Steps completed" counter is incremented.

### Decision Tree Format

Each decision numbered D{N}:
```
## D{N}: {decision context}
| Option | Description |
|---|---|
| A | {approach 1} |
| B | {approach 2} |
**Chosen:** {which and why}
**Outcome:** {SUCCEEDED / FAILED — filled after}
```

Pruned approaches:
```
### D{N}-PRUNED: {approach name}
- Status: NOT_ATTEMPTED | ATTEMPTED_AND_FAILED
- Reason: {specific evidence}
- DO NOT RETRY UNLESS: {condition that would make it worth trying again}
```

### Findings Format

Two sections, written at different times:
- **Observations** (append during run) — brief notes when something surprising happens
- **Findings** (written at completion) — reconciled claims with evidence, CONFIRMED / REFUTED / INCONCLUSIVE status

### User Messages Format

Each entry: `### [YYYY-MM-DD HH:MM PST] Input` followed by verbatim message, then `**Outcome:**` filled in after.

---

## Agent Roles

| Agent | Role | When | Addresses |
|---|---|---|---|
| Investigator (×2-3) | Explore codebase/context, different angles | Phase 1, stage judgment leads, progress check unknowns | F6, F12 |
| Critic | Challenge plans and assumptions | Phase 2 (mandatory), Phase 5, stage judgment | F1, F2, F8, F9 |
| Reflector | Synthesize findings, identify gaps, check progress | After investigation waves, every 5 steps (progress check), stage judgment | F3, F6, F10 |
| Analyst | Parse outputs, extract metrics, compare | Phase 4 complex outputs | F1, F2 |
| Verifier | Post-execution code verification — enumerates all possible bugs, reads code, checks each | After execution, before COMPLETE (mandatory) | F1, F12 |

**Spawning rules:**
- Investigator: always parallel, different angles, no overlap
- Critic: always after plans — never skip [mandatory]
- Reflector: at stage boundaries (mandatory) + every 5 steps (progress check + file compliance)
- Verifier: always after execution, before marking COMPLETE — never skip [mandatory]. Catches logic bugs tsc misses.
- OK to block-wait on subagent output when it's a dependency

---

## Investigation Wave Patterns

Standard templates for multi-agent investigation. Choose pattern based on question complexity.

### Standard Pattern (5 waves, 8-10 agents)

**Use for:** Design decisions, architectural questions, non-trivial choices.

```
Wave 1: EXPLORE (3 investigators, parallel)
  ├── Inv-A: primary angle
  ├── Inv-B: alternative angle
  └── Inv-C: atypical/contrarian (MANDATORY — force non-obvious thinking)

Wave 2: SYNTHESIZE (1 reflector)
  └── Merge findings → gaps → contradictions → open questions

Wave 3: CHALLENGE (1 critic)
  └── Stress-test synthesis → weak points → assumptions → missed angles

Wave 4: DEEPEN (2-3 investigators, targeted at gaps from W2+W3)
  ├── Inv-D: address reflector gap 1
  ├── Inv-E: address critic concern 1
  └── Inv-F: (optional) new angle surfaced by critic

Wave 5: CONVERGE (reflector → critic, sequential)
  ├── Reflector: final synthesis + recommendation with confidence
  └── Critic: final review — solid or needs more work?
```

### Quick Pattern (3 waves, 5 agents)

**Use for:** Simple A-vs-B decisions, time-constrained choices.

```
Wave 1: EXPLORE (3 investigators, one per option)
Wave 2: CHALLENGE (1 critic — compare all options)
Wave 3: SYNTHESIZE (1 reflector — decide)
```

### Deep Pattern (7 waves, 12+ agents)

**Use for:** Complex research, multi-day investigations, high-stakes decisions.

```
Wave 1: BROAD EXPLORE (3 investigators)
Wave 2: SYNTHESIZE (1 reflector)
Wave 3: CHALLENGE (1 critic)
Wave 4: DEEP EXPLORE (3 investigators, targeted)
Wave 5: RE-SYNTHESIZE (1 reflector)
Wave 6: FINAL CHALLENGE (1 critic)
Wave 7: RECOMMEND (1 reflector — final output)
```

### Wave Rules

| Rule | Rationale |
|---|---|
| Wave 1 MUST include one atypical/contrarian investigator | Prevents groupthink; surfaces non-obvious options [user req] |
| Critic is never optional | Can say "this is solid" if it is — but must be asked [F8] |
| Reflector decides: continue or stop (based on gap count) | Prevents both premature convergence and infinite loops |
| Agents within a wave run in parallel | Efficiency; independent angles |
| Waves run sequentially | Each wave depends on prior wave's output |
| All findings → task notepad with PST timestamps | Externalized state [P1] |

---

## Anti-Patterns

| DO NOT | WHY | INSTEAD |
|---|---|---|
| Self-verify without evidence | F1: agents lie | Produce artifacts |
| Skip critic on plans | F8: first plan rarely best | Critique before executing |
| Delete failure records | F11: future agents retry | Append-only failure log |
| Keep state only in context | F6: compacts/drifts | Write to files immediately |
| Trust "it looks right" | F2: agents fake results | Compare against oracle/test |
| Move past blockers | F3: hard things get skipped | Block and escalate if stuck |
| Single approach only | P4: diverge then converge | Always consider alternatives |
| Say "verified" | F1: meaningless without evidence | Say "verified — evidence: {X}" |
| Use "this becomes" / "for consistency" | F9: hides skipped steps | Show every step or say "I don't know" |
| Assume from pattern-match | F12: different context = different answer | Read actual code/formula |
| Skip post-execution verifier | tsc misses logic bugs (stale closures, dropped fields, wrong UUIDs) | Spawn verifier before COMPLETE — always |

---

## Integration

### How This Relates to r Plugin Commands

This system.md IS the r plugin's framework spec. The commands implement it:
- `/r:plan-experiment` + `/r:plan-task` → Phase 1-2 (DEFINE + PLAN)
- `/r:run-experiment` + `/r:run-task` → Phase 3-5 (EXECUTE + VERIFY + COMPLETE)
- `/r:swarm` → investigation waves (used during planning and stage judgment)
- All agent roles (investigator, critic, reflector, analyst, verifier) → used throughout

### With Ralph Wiggum Loop

The `ralph-loop` plugin provides an external bash iterator (outer loop). This system provides the internal execution structure (inner loop). They stack:
- Ralph Wiggum Loop: keeps the agent re-running with fresh context until `<promise>DONE</promise>`
- This system: ensures each run uses the file infrastructure, checks progress, and doesn't claim completion without evidence

### CLAUDE.md Reference

Add to any project's CLAUDE.md to enable:

```markdown
## Autonomous Tasks
Use `/r:plan-experiment` + `/r:run-experiment` for multi-step research.
Use `/r:plan-task` + `/r:run-task` for code tasks.
```
