# Skill Validation Tests

## Overview

This test suite automates parameter validation for Solera workflow skills.

## Validation Items

### 1. Required Parameter Validation
- Prevents skills from being invoked without required parameters
- solera-write-story: project_path, phase_id, goal_id, epic_name, story_id, story_name
- solera-execute-action-item: epic_name, story_id, action_item_id, action_item_name

### 2. Parameter Format Validation
- phase_id: `YYYY-PX-name` (e.g., 2026-P1-foundation)
- goal_id: `GX-name` (e.g., G1-search-liquor)
- story_id: `US-NNN` or `TS-NNN` (e.g., US-001)
- action_item_id: `ACT-NNN` (e.g., ACT-001)

### 3. Prerequisites Validation
- Verifies required conditions before skill execution
- solera-write-story: mission.md exists, _epic.md exists
- solera-execute-action-item: _story.md exists, dependent ACTs complete

### 4. Output Validation
- Verifies that skills produce expected outputs
- solera-write-story: _story.md, ACT-NNN-{name}.md, RETROSPECTIVE.md
- solera-execute-action-item: code changes, git commit, status update

### 5. Commit Message Format Validation
- Format: `[epic-name][US-NNN][ACT-NNN] title`
- Example: `[01-auth][US-001][ACT-001] Create login form`

## How to Run

### Direct execution
```bash
python3 tests/test_skill_validation.py
```

### Run with pytest (recommended)
```bash
pytest tests/test_skill_validation.py -v
```

### Run all tests
```bash
pytest tests/ -v
```

## Adding Tests

When adding a new skill, add validation tests in `test_skill_validation.py`:

1. `test_{skill_name}_required_parameters()` - Required parameters
2. `test_{skill_name}_parameter_formats()` - Format validation
3. `test_{skill_name}_prerequisites()` - Prerequisites
4. `test_{skill_name}_expected_outputs()` - Output validation

## Dependencies

- Python 3.8+
- pytest (optional, recommended for better test reporting)

```bash
pip install pytest
```
