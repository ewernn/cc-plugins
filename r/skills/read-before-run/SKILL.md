---
name: read-before-run
description: Before running any Python script in extraction/, inference/, or analysis/ directories, read the script's argparse section to understand available flags. Auto-invokes for experiment scripts.
---

# Read Before Run

Before running any experiment or analysis script, follow this checklist:

## 1. Read the Script's Arguments

Find and read the argparse or CLI argument definitions:

```python
# Look for patterns like:
parser = argparse.ArgumentParser()
parser.add_argument("--experiment", ...)
parser.add_argument("--traits", ...)
```

List all available flags and their purposes.

## 2. Check Existing Outputs

Before running, check if outputs already exist:

```bash
ls experiments/{experiment}/extraction/{trait}/
ls experiments/{experiment}/steering/{trait}/
```

Avoid re-running completed steps unless explicitly requested.

## 3. Understand Required vs Optional

Identify:
- Required arguments (no default)
- Optional arguments (have defaults)
- Common flag combinations

## 4. Check Related Config Files

Look for:
- `experiments/{experiment}/config.json` - experiment settings
- `config/paths.yaml` - path configuration
- Any referenced YAML/JSON configs in the script

## 5. Construct Command

Only after understanding the above, construct the command with:
- All required arguments
- Relevant optional arguments based on the task
- Correct paths and experiment names

## Example

Before running:
```bash
python extraction/run_pipeline.py --experiment foo --traits bar
```

First:
1. Read `extraction/run_pipeline.py` to find all flags
2. Check what `--methods`, `--position`, `--component` options exist
3. Check if `experiments/foo/extraction/bar/` already has outputs
4. Then construct the full command
