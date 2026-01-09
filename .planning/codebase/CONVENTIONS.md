# Coding Conventions

**Analysis Date:** 2026-01-09

## Naming Patterns

**Files:**
- snake_case for all Python modules (`data_loader.py`, `position_classifier.py`)
- UPPERCASE.md for key documentation (`README.md`, `IMPLEMENTATION_PLAN.md`)
- Tests embedded in source files (no separate test files)

**Functions:**
- snake_case for all functions
- Verb-first naming: `draw_*`, `compute_*`, `classify_*`, `get_*`, `load_*`, `extract_*`
- Examples: `draw_pitch()`, `compute_ci()`, `classify_team_vertical()`, `get_possession()`

**Variables:**
- snake_case for all variables
- Descriptive names: `home_positions`, `outfield_positions`, `frame_idx`
- Bucket variables: `v_bucket`, `h_bucket` (vertical/horizontal)

**Types:**
- PascalCase for classes: `ActivityLogger`, `ShapeGraphUI`
- No type hints used consistently (partial adoption)

**Constants:**
- UPPER_SNAKE_CASE for all constants
- Examples: `PITCH_COLOR`, `LINE_COLOR`, `VERTICAL_COLORS`, `PITCH_LENGTH`
- Location: `src/colors.py` for color constants

## Code Style

**Formatting:**
- 4-space indentation (PEP 8)
- Double quotes for strings
- No explicit formatter configured

**Linting:**
- None configured (no .pylintrc, .flake8)
- Manual PEP 8 adherence

## Import Organization

**Order:**
1. Standard library (`import os`, `import math`, `import json`)
2. Third-party (`import numpy`, `import matplotlib`, `import streamlit`)
3. Local imports (`from src.colors import ...`)

**Grouping:**
- No explicit blank lines between groups
- Try/except pattern for relative vs absolute imports

**Path Aliases:**
- None used
- Relative imports with fallback: `from .colors import ...` or `from src.colors import ...`

## Error Handling

**Patterns:**
- Guard clauses for empty data: `if not positions: return {}`
- Bare `except:` blocks (needs improvement)
- Default return values on failure

**Error Types:**
- Functions return `None`, `{}`, or `[]` on error (inconsistent)
- No custom exception classes
- Silently catch errors in visualization code

## Logging

**Framework:**
- Custom `ActivityLogger` class in `src/activity_logger.py`
- File-based logging with timestamps
- Console printing for test output

**Patterns:**
- Global logger via `get_logger()`, `init_logger()`
- Methods: `log_startup()`, `log_frame_render()`, `log_error()`
- Optional UI callback for real-time display

## Comments

**When to Comment:**
- Module docstrings at file head
- Function docstrings for public functions
- Inline comments for complex logic (sparse)

**Docstring Style:**
- Google-style docstrings with Args, Returns
- Example from `src/data_loader.py`:
  ```python
  def generate_synthetic_tracking(n_frames=100, fps=25):
      """
      Generate realistic-looking tracking data for testing.

      Args:
          n_frames: Number of frames to generate
          fps: Frames per second

      Returns:
          pandas DataFrame with tracking data
      """
  ```

**TODO Comments:**
- Pattern: Not established (few TODOs found)

## Function Design

**Size:**
- Most functions under 50 lines
- Exception: `app.py` has large functions (needs refactoring)

**Parameters:**
- Max 5-6 parameters typically
- Config dict pattern for complex settings (`src/compactness.py`)

**Return Values:**
- Dict return for complex data: `{'ci': 0-100, 'area': m², ...}`
- Explicit returns (no implicit None)
- Guard clauses with early returns

## Module Design

**Exports:**
- No barrel files (no `__init__.py` re-exports)
- Direct imports from modules

**Patterns:**
- Try/except for import compatibility (package vs standalone)
- `if __name__ == "__main__":` for embedded tests
- Single responsibility per module

---

*Convention analysis: 2026-01-09*
*Update when patterns change*
