---
description: Parallel investigation with reflection waves. Spawns multiple investigator agents, synthesizes findings, identifies gaps, and repeats until sufficient understanding.
allowed-tools: ["Task", "Read", "Glob", "Grep"]
---

# Swarm Investigation

Topic to investigate: $ARGUMENTS

## Process

Execute 1-5 investigation waves until sufficient understanding is reached.

### Phase 0: Reconnaissance (Optional)

Before spawning investigators, do a quick orientation to improve angle selection.

**When to use:**
- Open-ended topics where you don't know what exists
- Unfamiliar codebases or domains
- When the topic could mean many things

**When to skip:**
- Well-scoped questions with clear targets
- Follow-up investigations where context is fresh
- Time-sensitive requests

**Reconnaissance steps:**
1. Quick glob for relevant directories/files
2. Grep for key terms from the topic
3. Skim 2-3 most relevant files

**Output:** Brief orientation (1-2 sentences) + refined investigator angles based on what actually exists.

**Depth:** Scale to situation. 30 seconds for simple topics, 2-3 minutes for complex/unfamiliar ones.

### For Each Wave:

**1. Spawn Investigators (Parallel)**

Launch 3+ investigator agents in parallel, each with a DIFFERENT angle on the topic:

- Different aspects of the problem
- Different parts of the codebase
- Different sources (code vs docs vs papers)
- Different levels of abstraction

Example angles for a codebase investigation:
- "How is [X] implemented? Trace the code path."
- "What are the edge cases and error handling for [X]?"
- "How does [X] connect to the rest of the system?"

For research topics, include:
- "Search arxiv for recent papers on [X]"
- "What are the main approaches to [X]?"

**2. Wait for Results**

Collect all investigator findings.

**3. Reflect**

Launch a reflector agent to:
- Synthesize findings across all investigators
- Identify gaps in understanding
- Note contradictions and assumptions to verify

**4. Stress-Test (Final Wave Only)**

On the final wave (when reflector says gaps are minor or 5 waves reached), launch a critic agent to:
- Verify key claims from the synthesized findings
- Check for falsehoods or unsupported conclusions
- Ensure the understanding is solid before completing

If critic finds significant issues, continue investigating.

**Critic cycle limit:** After 2 critic cycles finding issues, report current findings to user and ask whether to continue or conclude with caveats.

**5. Decide: Continue or Complete**

Continue if:
- Significant gaps remain
- Contradictions need resolution
- New important questions emerged
- Critic found issues that need investigation
- Less than 5 waves completed

Complete if:
- Core question is answered
- Gaps are minor or out of scope
- Critic verified findings are solid
- 5 waves reached

### Final Output

After all waves complete:

```
## Investigation Summary

### Topic
[What was investigated]

### Key Findings
1. [Major finding]
2. [Major finding]
...

### Code/Source References
- `/absolute/path/file:line` - [what's there]
...

### Remaining Uncertainties
- [What we still don't know]

### Waves Completed
[N] waves, [M] total investigators spawned
```

## Guidelines

- Each investigator should have a DISTINCT angle - no overlap
- Reflect honestly about gaps - don't pretend understanding is complete
- Stop early if the question is answered (don't always do 5 waves)
- Include file:line references for all code findings
- Phase 0 is optional - use judgment on when it adds value vs slows things down
