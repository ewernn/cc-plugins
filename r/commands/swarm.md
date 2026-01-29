---
description: Parallel investigation with reflection waves. Spawns multiple investigator agents, synthesizes findings, identifies gaps, and repeats until sufficient understanding.
allowed-tools: ["Task", "Read", "Glob", "Grep"]
---

# Swarm Investigation

Topic to investigate: $ARGUMENTS

## Process

Execute 1-5 investigation waves until sufficient understanding is reached.

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
- Note contradictions
- Decide if another wave is needed

**4. Decide: Continue or Complete**

Continue if:
- Significant gaps remain
- Contradictions need resolution
- New important questions emerged
- Less than 5 waves completed

Complete if:
- Core question is answered
- Gaps are minor or out of scope
- Sufficient confidence in understanding
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
- `path/file:line` - [what's there]
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
