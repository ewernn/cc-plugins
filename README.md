# Claude Code Plugins

Personal Claude Code plugin marketplace.

## Installation

```bash
/plugin marketplace add ewern/cc-plugins
/plugin install r@ewern
```

## Available Plugins

### r - Research Tools

Experiment planning, parallel investigation swarms, and specialized agents.

**Commands:**
- `/r:swarm <topic>` - Parallel investigation with reflection waves
- `/r:plan-experiment <goal>` - Collaborative experiment planning
- `/r:run-experiment [plan.md]` - Execute experiment plan autonomously

**Agents:**
- `investigator` - Deep exploration (codebase, arxiv, web)
- `reflector` - Synthesize findings, find gaps
- `critic` - Devil's advocate, stress-test plans
- `analyst` - Verify experiment outputs, write parsing scripts

**Skills:**
- `read-before-run` - Auto-invoke before running experiment scripts

**MCP:**
- `arxiv` - Fetch arxiv papers as text
