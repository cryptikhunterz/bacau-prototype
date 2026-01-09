# Pitch Control Visualization

Technical documentation for the pitch control feature in Shape Graph.

## Overview

Pitch control visualization shows which team controls each area of the football pitch at any given moment. This spatial dominance metric helps coaches and analysts understand:

- **Defensive coverage** - Where are the gaps in defensive shape?
- **Attacking opportunities** - Which areas are available for progression?
- **Pressing effectiveness** - How much space is the pressing team controlling?
- **Build-up patterns** - Where can the team in possession find space?

The visualization uses a heatmap overlay with a blue-white-red color gradient:
- **Blue** = Home team control
- **White** = Contested/neutral zone
- **Red** = Away team control

## Algorithm

This implementation uses the **Spearman 2017 influence-based pitch control model**, which calculates spatial dominance based on player positions and velocities.

### Core Concept

For each point on the pitch, we calculate how quickly each player can reach that point. Players who can arrive faster have more "influence" over that area. The team with greater total influence controls the area.

### Time-to-Intercept

The time for a player to reach a target point:

```
tti = reaction_time + adjusted_distance / max_speed
```

Where:
- `reaction_time` = 0.7 seconds (human reaction delay)
- `max_speed` = 13.0 m/s (elite athlete sprint speed)
- `adjusted_distance` = accounts for current velocity direction

**Velocity Adjustment:**

If a player is already moving toward the target, they have an advantage:

```
velocity_toward_target = (vx * dx + vy * dy) / distance
velocity_adjustment = velocity_toward_target * reaction_time
adjusted_distance = max(0, distance - velocity_adjustment)
```

### Influence Function

Convert time-to-intercept to influence using a sigmoid:

```
influence = 1 / (1 + exp(tti / sigma))
```

Where `sigma = 0.5` controls the steepness of the falloff.

**Properties:**
- Lower TTI = Higher influence (closer players dominate)
- Smooth transition (no sharp boundaries)
- Values between 0 and 1

### Control Calculation

For each grid point:

```
home_influence = sum(player_influence(tti) for player in home_team)
away_influence = sum(player_influence(tti) for player in away_team)

control = home_influence / (home_influence + away_influence)
```

**Control values:**
- `0.0` = Full away team control
- `0.5` = Contested (equal influence)
- `1.0` = Full home team control

## Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| `REACTION_TIME` | 0.7 seconds | Average human reaction time before movement can begin |
| `MAX_SPEED` | 13.0 m/s | Elite athlete maximum sprint speed (~46 km/h) |
| `GRID_RESOLUTION` | 2 meters | Balance between visual quality and computation speed |
| `PITCH_LENGTH` | 105 meters | Standard FIFA pitch length |
| `PITCH_WIDTH` | 68 meters | Standard FIFA pitch width |
| `EMA_ALPHA` | 0.3 | Velocity smoothing factor (higher = more responsive to changes) |

## Module API

### velocity.py

Functions for calculating player velocities from tracking data.

```python
def calculate_velocities(
    current_positions: dict,
    previous_positions: dict,
    fps: float = 29.97
) -> dict:
    """
    Calculate raw velocities from position deltas.

    Args:
        current_positions: {player_id: (x, y)} current frame
        previous_positions: {player_id: (x, y)} previous frame
        fps: Frames per second

    Returns:
        {player_id: (vx, vy)} velocities in m/s
    """

def smooth_velocities(
    current_velocities: dict,
    previous_smoothed: dict,
    alpha: float = 0.3
) -> dict:
    """
    Apply EMA smoothing to reduce tracking noise.

    The exponential moving average formula:
    smoothed = alpha * current + (1 - alpha) * previous
    """

def clamp_velocities(
    velocities: dict,
    max_speed: float = 13.0
) -> dict:
    """
    Limit velocity magnitudes to realistic maximum.

    Preserves velocity direction while capping magnitude.
    """
```

### pitch_control.py

Core pitch control calculation functions.

```python
def create_pitch_grid(
    pitch_length: float = 105,
    pitch_width: float = 68,
    resolution: float = 2
) -> tuple:
    """
    Generate 2D coordinate grid covering the pitch.

    Returns:
        (x_grid, y_grid): numpy arrays of grid coordinates
    """

def time_to_intercept(
    player_pos: tuple,
    player_vel: tuple,
    target_pos: tuple,
    reaction_time: float = 0.7,
    max_speed: float = 13.0
) -> float:
    """
    Calculate time for player to reach target position.

    Accounts for player's current velocity direction.
    """

def player_influence(tti: float, sigma: float = 0.5) -> float:
    """
    Convert time-to-intercept to influence value.

    Uses sigmoid: 1 / (1 + exp(tti / sigma))
    """

def compute_pitch_control(
    home_positions: dict,
    away_positions: dict,
    home_velocities: dict = None,
    away_velocities: dict = None
) -> np.ndarray:
    """
    Compute pitch control for entire grid.

    Returns:
        2D array of control values [0=away, 0.5=contested, 1=home]
    """
```

## UI Controls

### Enabling Pitch Control

1. Open the Shape Graph Visualization app
2. In the sidebar, find **Display Options**
3. Check **"Show pitch control"** checkbox
4. The heatmap overlay appears on both pitch views

### Adjusting Opacity

When pitch control is enabled:
1. A slider appears: **"Pitch control opacity"**
2. Range: 0.1 (nearly transparent) to 0.9 (nearly opaque)
3. Default: 0.5 (semi-transparent)

### Color Interpretation

| Color | Meaning | Control Value |
|-------|---------|---------------|
| Deep Blue | Strong home control | > 0.7 |
| Light Blue | Slight home advantage | 0.5 - 0.7 |
| White | Contested | ~0.5 |
| Light Red | Slight away advantage | 0.3 - 0.5 |
| Deep Red | Strong away control | < 0.3 |

## Performance Notes

- **Grid size:** 35 × 54 = 1,890 points
- **Per frame:** ~22 players × 1,890 grid points = ~41,580 influence calculations
- **Optimization:** Uses numpy vectorization where possible
- **Frame rate impact:** Minimal on modern hardware

## References

- Spearman, W. (2017). "Beyond Expected Goals." MIT Sloan Sports Analytics Conference.
- Fernández, J., & Bornn, L. (2018). "Wide Open Spaces: A statistical technique for measuring space creation in professional soccer."

---

*Documentation generated: 2026-01-09*
