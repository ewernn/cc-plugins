---
description: Execute a PLAN.md autonomously. Runs steps, verifies outputs, uses analyst to check results. Only stops if something goes wrong.
allowed-tools: ["Task", "Read", "Write", "Bash", "Glob", "Grep", "TaskCreate", "TaskUpdate", "TaskList"]
---

# Run Experiment

Target: $ARGUMENTS

If no argument provided, look for PLAN.md in current experiment directory.

## Startup

### 1. Check Environment

Check platform and log compute resources:
```bash
# Check if GPU available (Linux/CUDA)
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    # Mac or CPU-only
    echo "No nvidia-smi - checking for Mac GPU..."
    system_profiler SPDisplaysDataType 2>/dev/null || echo "CPU-only environment"
fi
```

Note the machine and available resources.

### 2. Load Plan

Read the PLAN.md file. Parse:
- Steps to execute
- Checkpoints
- Expected outputs
- Verification criteria

### 3. Create Task List

Create a task for each step in the plan using TaskCreate:
- Subject: Step name
- Description: What the step does

This provides real-time visibility into progress.

### 4. Initialize Notepad

If `experiments/{name}/notepad.md` already exists, archive it first:
```bash
[ -f notepad.md ] && mv notepad.md notepad_$(date +%Y%m%d_%H%M%S).md
```

Create fresh `experiments/{name}/notepad.md`:

```markdown
# Experiment Notepad

## Machine
[GPU info from nvidia-smi]
[Date/time started]

## Progress
- [ ] Step 1: [name]
- [ ] Step 2: [name]
...

## Observations
[To be filled during run]
```

## Execution Loop

For each step in the plan:

### 1. Mark In Progress

Update the task to `in_progress`. Update notepad.

### 2. Read Before Run

If step involves running a script, apply read-before-run:
- Read the script's argparse
- Verify flags match what's in PLAN.md
- Check existing outputs

### 3. Execute

Run the command from PLAN.md.

### 4. Verify Output

Check expected outputs exist:
```bash
ls [expected_path] | wc -l
```

Compare to what PLAN.md says should be there.

**For scored/evaluated outputs:**
Execute any `#### Verify` blocks in PLAN.md that print actual data.
- Read the printed samples
- Ask: Does this score match this content?
- Look for: repetition loops, empty values, scores clustering at exact boundaries
- If 2+ samples look wrong, STOP and report

### 5. Analyze If Needed

For steps with complex outputs:
- Launch analyst agent to verify results
- **Include in analyst prompt:** path to PLAN.md and the specific expected outcomes for this step
- Analyst writes parsing script, checks metrics
- Analyst reports if anything looks wrong

**Result interpretation (all steps):**
- Don't just check files exist — print summary stats + a few raw examples
- For plots/images: read the image, check axes make sense, expected trends visible
- If something looks off, note in notepad. If pattern persists across samples, STOP.

### 6. Decision Point

**If everything matches expected:**
- Mark task complete
- Update notepad with "PASSED"
- Continue to next step

**If something is wrong:**
- Update notepad with details of what's wrong
- STOP and report the issue
- Include: what was expected, what happened, suggested fixes

### 7. At Checkpoints

At checkpoint steps in PLAN.md:
- Summarize progress so far
- Run analyst on key outputs
- Update notepad with checkpoint status
- Continue unless issues found

## Completion

When all steps complete:

### 1. Final Analysis

Launch analyst to review overall results:
- **Include in analyst prompt:** full path to PLAN.md and its Success Criteria section
- Do results match Success Criteria?
- Any anomalies across the experiment?
- Generate summary plots if applicable

### 2. Update Notepad

Write final status to notepad.md:

```markdown
## Final Status
[COMPLETE / PARTIAL / FAILED]

## Results Summary
[Key metrics and outcomes]

## Success Criteria
- [x] Criteria 1: [result]
- [x] Criteria 2: [result]

## Time
Started: [time]
Completed: [time]
```

### 3. Mark All Tasks Complete

Update all tasks to `completed`.

### 4. Report

Provide final summary:
- What was accomplished
- Key results
- Any issues encountered
- Suggested next steps

## Error Handling

**Script fails:**
- Capture error message
- Check "If Stuck" section in PLAN.md
- Try suggested fix if applicable
- Otherwise STOP and report

**Output doesn't match expected:**
- Run analyst to understand what's there vs expected
- Check if it's a real problem or plan was wrong
- STOP and report with details

**Out of memory / resource issues:**
- Log to notepad
- STOP and report machine constraints

## Guidelines

- Update notepad frequently - it survives context compaction
- Don't continue past failures - stop and report clearly
- Include specific file paths and metrics in all reports
- For LLM-scored outputs: always read actual samples, not just aggregate metrics

**Use agents as needed:**
- **analyst** - Verify outputs, parse complex results, generate plots
- **investigator** - If you need to understand unfamiliar code/scripts before running
- **critic** - If results seem suspicious and you're unsure if it's a real problem
- **reflector** - If mid-experiment findings suggest the approach needs rethinking

You have Task tool - spawn agents whenever it would help, don't wait for designated steps.
