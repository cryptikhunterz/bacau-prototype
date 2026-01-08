# shape_lines.py - Technical Reference

## Purpose

Provides geometric analysis functions for team shape visualization, including goalkeeper identification and outfield player extraction.

## Functions

### identify_goalkeeper(positions, is_home) → player_id

**What:** Finds the goalkeeper by identifying the player closest to the team's goal line.

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| positions | dict | {player_id: (x, y)} for all 11 players |
| is_home | bool | True if home team (GK near x=0) |

**Returns:** Player ID of identified goalkeeper, or None if positions is empty

**Logic:**
- Home team: Player with minimum x coordinate (closest to x=0)
- Away team: Player with maximum x coordinate (closest to x=105)

**Note:** Identifies by position, not jersey number. If GK moves forward (corner kick, set piece), a different player may be identified as "deepest."

---

### get_outfield_positions(positions, is_home) → dict

**What:** Extracts the 10 outfield players (excluding goalkeeper).

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| positions | dict | {player_id: (x, y)} for all 11 players |
| is_home | bool | True if home team (GK near x=0) |

**Returns:** Dict of {player_id: (x, y)} for 10 outfield players

**Edge case handling:**

| Input | Behavior |
|-------|----------|
| Empty dict | Returns empty dict |
| None | Returns empty dict |
| < 11 players | Returns all except deepest |

**Important:** This function identifies the deepest player by position, not by jersey number. During set pieces when the actual GK moves forward, a different player will be excluded. This is intentional for CI calculation purposes.

---

## Dependencies

**Imports:** numpy, scipy.spatial.ConvexHull, matplotlib.patches

**Used by:**
- app.py (for CI calculation and shape rendering)
- src/compactness.py (compute_ci expects outfield positions)

---

## Real Data Behavior (Game 3821)

| Frame | Home GK ID | Home GK x | Away GK ID | Away GK x |
|-------|------------|-----------|------------|-----------|
| 1000 | 4602 | 18.1 | 13799 | 86.3 |
| 5000 | 4602 | 4.2 | 13799 | 83.4 |
| 50000 | 4602 | 20.1 | 13799 | 100.1 |
| 100000 | 4623 | 22.3 | 2099 | 52.5 |

**Frame 100000 note:** Different player IDs because actual GK moved forward (likely set piece). Function correctly identifies deepest player regardless.

---

## Quick Test

```python
from src.shape_lines import get_outfield_positions, identify_goalkeeper

# Test with home team positions
positions = {
    'gk': (2, 34),
    'p1': (20, 30), 'p2': (25, 40), 'p3': (30, 25),
    'p4': (35, 45), 'p5': (40, 35), 'p6': (45, 30),
    'p7': (50, 40), 'p8': (55, 25), 'p9': (60, 45),
    'p10': (65, 35)
}

gk_id = identify_goalkeeper(positions, is_home=True)
outfield = get_outfield_positions(positions, is_home=True)

print(f"GK: {gk_id}")                          # 'gk'
print(f"Outfield: {len(outfield)}")            # 10
print(f"GK excluded: {gk_id not in outfield}") # True

# Test away team
away_positions = {
    'gk': (103, 34),
    'p1': (85, 30), 'p2': (80, 40), 'p3': (75, 25),
    'p4': (70, 45), 'p5': (65, 35), 'p6': (60, 30),
    'p7': (55, 40), 'p8': (50, 25), 'p9': (45, 45),
    'p10': (40, 35)
}

away_gk = identify_goalkeeper(away_positions, is_home=False)
print(f"Away GK: {away_gk}")  # 'gk' (nearest to x=105)
```

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Returns 11 players | GK not found | Check is_home flag matches team |
| Wrong player excluded | is_home flag inverted | Home=x=0, Away=x=105 |
| Empty result | Empty input dict | Check upstream data loading |
| Different GK each frame | GK moved forward (set piece) | Expected behavior |
| GK at x=50 | Set piece or unusual play | Normal - function works correctly |

---

## Integration with CI

```python
from src.shape_lines import get_outfield_positions
from src.compactness import compute_ci, is_defending

# Get frame data
home_positions = extract_positions(frame, team='home')
away_positions = extract_positions(frame, team='away')

# Get outfield only (for CI calculation)
home_outfield = get_outfield_positions(home_positions, is_home=True)
away_outfield = get_outfield_positions(away_positions, is_home=False)

# Calculate CI if defending
if is_defending(possession, ball_x, is_home=True):
    home_ci = compute_ci(home_outfield, is_home=True, config=ci_config)
```

---

*File: src/shape_lines.py (209 lines)*
*Function added: get_outfield_positions() at lines 41-56*
*Last updated: January 8, 2026*
