# Codebase Concerns

**Analysis Date:** 2026-01-09

## Tech Debt

**Bare except clauses in app.py:**
- Issue: Silently catches all exceptions without specific handling
- Files: `app.py` lines 182, 235, 989
- Why: Quick development, error suppression for demo
- Impact: Hidden failures make debugging difficult; errors go unreported
- Fix approach: Replace with specific exceptions (`except ValueError:`, `except FileNotFoundError:`)

**Repeated math imports within functions:**
- Issue: `import math` appears at lines 116, 158, 196 inside functions
- Files: `app.py`
- Why: Copy-paste development
- Impact: Inefficient, violates DRY principle
- Fix approach: Move `import math` to top of file

**Large monolithic file (1,679 lines):**
- Issue: `app.py` contains data loading, visualization, UI, and statistics
- Files: `app.py`
- Why: Rapid prototyping without refactoring
- Impact: Difficult to test, maintain, and reuse code
- Fix approach: Extract functions into `src/` modules (e.g., `src/stats.py`, `src/events.py`)

**Duplicated distance calculation pattern:**
- Issue: `math.sqrt((px - ball_x)**2 + (py - ball_y)**2)` appears 3+ times
- Files: `app.py` lines 130, 175, 211
- Why: Each function implements its own distance calculation
- Impact: Code duplication, risk of inconsistent implementations
- Fix approach: Create `src/geometry.py` with `distance()` utility function

## Known Bugs

**None identified during analysis**

## Security Considerations

**No hardcoded secrets:**
- Risk: None (positive finding)
- Current mitigation: No API keys, passwords, or tokens in code
- Recommendations: Maintain this practice

**No input validation on file paths:**
- Risk: User could potentially manipulate file paths (low risk for local app)
- Files: `app.py` line 232 (`load_events()`)
- Current mitigation: File paths are hardcoded
- Recommendations: Add path validation if user input is added later

## Performance Bottlenecks

**@st.cache_resource overhead:**
- Problem: Large dataset cached in memory
- Files: `app.py` lines 61-69 (`load_data()`)
- Measurement: Not profiled
- Cause: Kloppy loads full match data (~57 MB)
- Improvement path: Consider lazy loading or frame-range queries

**Convex hull calculation per frame:**
- Problem: SciPy ConvexHull computed on every frame render
- Files: `src/shape_lines.py`, `src/compactness.py`
- Measurement: Not profiled
- Cause: No caching of hull results
- Improvement path: Cache hull results for static team positions

## Fragile Areas

**Complex team detection logic:**
- Files: `app.py` lines 94-96, 134-137, 215-218
- Why fragile: Deeply nested conditional with `.value` attribute checks
- Common failures: AttributeError if kloppy data format changes
- Safe modification: Extract to helper function `is_home_team(player)`
- Test coverage: None

**Hardcoded game metadata:**
- Files: `app.py` lines 29-35 (FPS, timestamps), lines 271-275 (team IDs)
- Why fragile: Requires code changes to analyze different matches
- Common failures: Wrong stats if metadata doesn't match data
- Safe modification: Extract to config file or derive from data
- Test coverage: None

## Scaling Limits

**Single-match memory:**
- Current capacity: ~57 MB for one match
- Limit: Would struggle with multiple matches simultaneously
- Symptoms at limit: Memory pressure, slow performance
- Scaling path: Add match selection, unload previous data

## Dependencies at Risk

**kloppy library:**
- Risk: External library for sports data loading
- Impact: Core functionality depends on kloppy API stability
- Migration plan: Wrap kloppy calls in adapter functions

## Missing Critical Features

**No velocity/pitch control calculations:**
- Problem: No player velocity tracking for pitch control feature
- Current workaround: None (feature doesn't exist)
- Blocks: Pitch control visualization (planned feature)
- Implementation complexity: Medium (need frame-to-frame position deltas)

## Test Coverage Gaps

**app.py has no tests:**
- What's not tested: 1,679 lines of core application logic
- Risk: Regression bugs go unnoticed
- Priority: High
- Difficulty to test: Medium (Streamlit testing requires special setup)

**Visualization functions untested:**
- What's not tested: `draw_pitch()`, `draw_player_marker()`, rendering code
- Risk: Visual regressions
- Priority: Medium
- Difficulty to test: Requires snapshot testing or visual regression tools

---

*Concerns audit: 2026-01-09*
*Update as issues are fixed or new ones discovered*
