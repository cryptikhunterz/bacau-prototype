# velocity.py - Technical Reference

## Purpose

Calculates player velocities from frame-to-frame position deltas for pitch control analysis. Velocities are smoothed using EMA to handle noisy tracking data, then clamped to realistic maximum speeds.

**Use case:** Input for pitch control influence model (time-to-intercept calculation).

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| MAX_SPEED | 13.0 | Maximum realistic player speed (m/s) |
| EMA_ALPHA | 0.3 | EMA smoothing factor (higher = more responsive) |
| FPS | 29.97 | PFF tracking data frame rate |

---

## Functions

### calculate_velocities(current_positions, previous_positions, fps=FPS) -> dict

**What:** Computes raw velocities from position changes between frames.

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| current_positions | dict | {player_id: (x, y)} - Current frame positions |
| previous_positions | dict | {player_id: (x, y)} - Previous frame positions |
| fps | float | Frames per second (default: 29.97) |

**Returns:** `{player_id: (vx, vy)}` - Velocities in m/s

**Formula:**

```
dt = 1 / fps  # ~0.0334 seconds at 29.97 fps
vx = (current_x - previous_x) / dt
vy = (current_y - previous_y) / dt
```

**Edge case handling:**

| Input | Behavior |
|-------|----------|
| Player in current but not previous | Returns (0.0, 0.0) for that player |
| Player in previous but not current | Player omitted from output |
| Empty current_positions | Returns empty dict |

---

### smooth_velocities(current_velocities, previous_smoothed, alpha=EMA_ALPHA) -> dict

**What:** Applies Exponential Moving Average (EMA) smoothing to reduce noise.

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| current_velocities | dict | {player_id: (vx, vy)} - Raw velocities this frame |
| previous_smoothed | dict | {player_id: (vx, vy)} - Smoothed velocities from previous frame |
| alpha | float | Smoothing factor 0-1 (default: 0.3) |

**Returns:** `{player_id: (vx, vy)}` - Smoothed velocities

**Formula:**

```
v_smooth = alpha * v_current + (1 - alpha) * v_previous
```

With alpha=0.3: `v_smooth = 0.3 * v_current + 0.7 * v_previous`

**Why smoothing is needed:** Tracking data contains measurement noise that causes velocity spikes. EMA dampens sudden changes while remaining responsive to real movement.

**Alpha behavior:**

| Alpha | Effect |
|-------|--------|
| 0.1 | Very smooth, slow response |
| 0.3 | Balanced (default) |
| 0.5 | More responsive, less smooth |
| 1.0 | No smoothing (raw values) |

**Edge case handling:**

| Input | Behavior |
|-------|----------|
| New player (not in previous) | Uses current velocity as initial |
| Missing player (in previous, not current) | Decays velocity toward zero |

---

### clamp_velocities(velocities, max_speed=MAX_SPEED) -> dict

**What:** Limits velocity magnitudes to maximum realistic speed while preserving direction.

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| velocities | dict | {player_id: (vx, vy)} |
| max_speed | float | Maximum allowed speed in m/s (default: 13.0) |

**Returns:** `{player_id: (vx, vy)}` - Clamped velocities

**Formula:**

```
speed = sqrt(vx^2 + vy^2)
if speed > max_speed:
    scale = max_speed / speed
    vx_clamped = vx * scale
    vy_clamped = vy * scale
```

**Why 13.0 m/s:** Elite sprinters reach ~12-13 m/s. This caps unrealistic velocities from tracking errors while allowing maximum player speeds.

**Behavior:**

| Input Speed | Output Speed | Direction |
|-------------|--------------|-----------|
| 5.0 m/s | 5.0 m/s | Unchanged |
| 13.0 m/s | 13.0 m/s | Unchanged |
| 20.0 m/s | 13.0 m/s | Preserved |

---

## Usage Example

```python
from src.velocity import (
    calculate_velocities,
    smooth_velocities,
    clamp_velocities,
    FPS
)

# Frame-by-frame velocity pipeline
prev_positions = {1: (50.0, 30.0), 2: (45.0, 35.0)}
curr_positions = {1: (50.5, 30.2), 2: (45.3, 35.1)}

# Step 1: Calculate raw velocities
raw_velocities = calculate_velocities(curr_positions, prev_positions, fps=FPS)

# Step 2: Smooth velocities (use raw as initial if first frame)
prev_smoothed = {}  # Empty on first frame
smoothed = smooth_velocities(raw_velocities, prev_smoothed)

# Step 3: Clamp to realistic speeds
final_velocities = clamp_velocities(smoothed)

# Result: {1: (vx, vy), 2: (vx, vy)} in m/s
```

---

## Integration Notes

**Pitch Control Pipeline:**

```
Positions -> Velocities -> Time-to-Intercept -> Influence -> Control
```

**State Management (Streamlit):**

```python
# In app.py, store previous values in session_state
if 'prev_positions' not in st.session_state:
    st.session_state.prev_positions = {}
if 'prev_smoothed' not in st.session_state:
    st.session_state.prev_smoothed = {}

# After processing each frame:
st.session_state.prev_positions = current_positions.copy()
st.session_state.prev_smoothed = smoothed_velocities.copy()
```

---

## Dependencies

**Imports:** numpy

**Imported by:** pitch_control.py (Phase 2)

---

## Quick Test

```python
python src/velocity.py
# Runs 4 embedded tests
```

Or comprehensive tests:

```python
python tests/test_velocity.py
# Runs 9 tests including integration
```

---

## File Location

`src/velocity.py` (186 lines including tests)

## Last Updated

January 9, 2026 - Phase 1 Implementation
