# Roadmap: Shape Graph - Pitch Control

## Milestone 1: Pitch Control Feature (v1.0)

### Phase 1: Velocity Module ✅
**Directory:** `.planning/phases/01-velocity-module/`

Create velocity calculation module for player movement tracking.

**Scope:**
- Calculate player velocities from frame-to-frame position deltas
- EMA smoothing to reduce noise in tracking data
- Clamp extreme values to MAX_SPEED (13.0 m/s)
- Clean module interface for pitch control consumption

**Output:** `src/velocity.py`

**Completed:** 2026-01-09

---

### Phase 2: Pitch Control Module ✅
**Directory:** `.planning/phases/02-pitch-control-module/`

Implement Spearman 2017 influence-based pitch control algorithm.

**Scope:**
- Grid generation at 2m resolution (53×34 points)
- Influence function based on time-to-intercept
- Team control probability at each grid point
- Efficient computation for real-time use

**Output:** `src/pitch_control.py`

**Completed:** 2026-01-09

---

### Phase 3: App Integration ✅
**Directory:** `.planning/phases/03-app-integration/`

Integrate pitch control visualization into Streamlit app.

**Scope:**
- Sidebar toggle checkbox for pitch control overlay
- Alpha slider for overlay opacity control
- State management for previous frame positions
- Render pitch control heatmap in render_frame()
- Blue-white-red colormap implementation

**Output:** Modified `app.py`

**Completed:** 2026-01-09

---

### Phase 4: Documentation ✅
**Directory:** `.planning/phases/04-documentation/`

Create technical documentation for the pitch control feature.

**Scope:**
- Algorithm documentation (Spearman 2017 model)
- Usage guide for new UI controls
- Code documentation and docstrings
- Update README with new feature

**Output:** `docs/technical/pitch_control.md`

**Completed:** 2026-01-09

---

## Progress

| Phase | Status | Plans | Completed |
|-------|--------|-------|-----------|
| 1. Velocity Module | ✅ Complete | 1 | 1 |
| 2. Pitch Control Module | ✅ Complete | 1 | 1 |
| 3. App Integration | ✅ Complete | 1 | 1 |
| 4. Documentation | ✅ Complete | 1 | 1 |

**Milestone Progress:** 4/4 phases complete ✅

---

*Roadmap created: 2026-01-09*
*Update phase status as work progresses*
