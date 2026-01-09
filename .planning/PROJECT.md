# Shape Graph - Pitch Control

## Vision

Add pitch control visualization showing which team controls each area of the football pitch using a smooth gradient overlay. This extends the existing Shape Graph tactical analysis tool with real-time spatial dominance visualization.

## Core Value

Enable coaches and analysts to see at a glance which team controls different areas of the pitch during any moment of the match, complementing existing shape analysis (compactness index, formations) with spatial control metrics.

## Requirements

### Validated

- ✓ Streamlit web application — existing
- ✓ PFF World Cup 2022 tracking data loading — existing
- ✓ Player position extraction per frame — existing
- ✓ Team shape visualization (convex hull) — existing
- ✓ Compactness Index (CI) calculation — existing
- ✓ Formation detection — existing
- ✓ Frame-by-frame navigation — existing

### Active

- [ ] Player velocity calculation from position deltas
- [ ] EMA smoothing for noisy velocity data
- [ ] Influence-based pitch control algorithm (Spearman 2017)
- [ ] 2m grid resolution pitch control computation (53×34 points)
- [ ] Blue-white-red gradient colormap overlay
- [ ] Sidebar toggle for pitch control visibility
- [ ] Alpha slider for overlay opacity
- [ ] State management for previous positions (velocity calculation)

### Out of Scope

- Voronoi-based pitch control — influence model preferred for realism
- Machine learning models — keeping it deterministic
- Real-time video overlay — static frame visualization only
- Passing probability calculations — future enhancement
- Expected goals (xG) integration — separate feature

## Algorithm Specification

**Model:** Spearman 2017 influence-based pitch control

**Constants:**
- REACTION_TIME = 0.7 seconds
- MAX_SPEED = 13.0 m/s
- GRID_RESOLUTION = 2 meters

**Grid:**
- Pitch: 105m × 68m
- Grid points: 53 × 34 = 1,802 points

**Velocity Calculation:**
- Delta positions between consecutive frames
- EMA smoothing (alpha ~0.3) to reduce noise
- Clamp to MAX_SPEED

**Influence Function:**
- Time-to-intercept based on distance, velocity, and reaction time
- Sigmoid transformation for probability
- Sum influences per team, normalize to [0, 1]

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Influence model over Voronoi | More realistic, accounts for player velocity and direction | Pending |
| 2m grid resolution | Balance between accuracy and performance | Pending |
| EMA for velocity smoothing | Simple, effective for noisy tracking data | Pending |
| Blue-white-red colormap | Intuitive: blue=home, red=away, white=contested | Pending |

## Constraints

- Must integrate with existing app.py without breaking current features
- Must work with 29.97 fps PFF tracking data
- Must remain performant for interactive frame navigation
- No external API dependencies

---

*Last updated: 2026-01-09 after initialization*
