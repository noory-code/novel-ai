---
name: init
description: Set up Solera in a project — install rules and create the workspace folder structure.
metadata:
  version: "1.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [set up solera, initialize solera, install solera, solera init, solera 설치, solera 설정, solera 초기화]
  uses: []
---

# Solera Init

> Sets up Solera in the current project by installing rules and creating the workspace structure.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root (where `workspace/` will live) | . |

## Output

| Step | Output | Path |
|------|--------|------|
| Rules | Workflow rule | `.claude/rules/solera-workflow.md` |
| Folders | Workspace skeleton | `{project_path}/workspace/` |
| State | Progress file | `{project_path}/progress.md` |

## Procedure

### Step 1. Check existing setup

- [ ] Check if `.claude/rules/solera-workflow.md` already exists
  - If exists: ask user whether to overwrite or skip
- [ ] Check if `{project_path}/workspace/` already exists
  - If exists: skip folder creation, proceed to rule installation

### Step 2. Install rules

- [ ] Create `.claude/rules/` directory (if not exists)
- [ ] Write `.claude/rules/solera-workflow.md` — ref: [assets/solera-workflow.md](assets/solera-workflow.md)
  - Copy the asset content as-is (no variable substitution needed)

### Step 3. Create workspace structure

- [ ] Create folder structure:
  ```
  {project_path}/
  ├── progress.md
  └── workspace/
      ├── identity/
      ├── initiative/
      └── catalog/
          └── published/
  ```
- [ ] Write initial `progress.md`:
  ```markdown
  # Progress

  > Phase: (none)
  > Goal: (none)
  > Epic: (none)
  > Story: (none)
  > Action Item: (none)
  ```

### Step 4. Verify

- [ ] `.claude/rules/solera-workflow.md` exists and is non-empty
- [ ] `{project_path}/workspace/` directory exists
- [ ] `{project_path}/progress.md` exists

## Completion Checklist

- [ ] Rule file installed at `.claude/rules/solera-workflow.md`
- [ ] Workspace folder structure created
- [ ] `progress.md` initialized
- [ ] User informed of next step: "Run `write-identity` to define your service identity"
