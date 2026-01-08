# compactness.py - Technical Reference

## Purpose

Calculates Custom Compactness Index (CI) for defensive shape analysis. CI is a normalized 0-100 score measuring how compact a team's defensive shape is relative to a reference area for their block type.

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| PITCH_LENGTH | 105 | Pitch length in meters |
| PITCH_WIDTH | 68 | Pitch width in meters |

## DEFAULT_CONFIG

| Key | Default | Description |
|-----|---------|-------------|
| ref_area_high | 600 | Reference area for high press (m²) |
| ref_area_mid | 450 | Reference area for mid block (m²) |
| ref_area_low | 300 | Reference area for low block (m²) |
| sigma | 0.5 | Balance penalty sensitivity |
| boundary_low_mid | 0.35 | Low/Mid boundary (% from own goal) |
| boundary_mid_high | 0.65 | Mid/High boundary (% from own goal) |

---

## Functions

### classify_block(centroid_x, is_home, config=None) → str

**What:** Determines defensive block type based on team centroid position.

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| centroid_x | float | X coordinate of team centroid (meters) |
| is_home | bool | True if home team (defends x=0) |
| config | dict | Optional calibration config |

**Returns:** `'low_block'`, `'mid_block'`, or `'high_press'`

**Logic:**

```
Home team: pct = centroid_x / 105
Away team: pct = (105 - centroid_x) / 105

if pct < boundary_low_mid (0.35):
    return 'low_block'
elif pct < boundary_mid_high (0.65):
    return 'mid_block'
else:
    return 'high_press'
```

**Examples:**

| centroid_x | is_home | pct | Result |
|------------|---------|-----|--------|
| 20 | True | 0.19 | low_block |
| 50 | True | 0.48 | mid_block |
| 80 | True | 0.76 | high_press |
| 85 | False | 0.19 | low_block |

---

### is_defending(possession, ball_x, is_home) → bool

**What:** Checks if team should display CI (is in defending state).

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| possession | str | 'home', 'away', or 'contested' |
| ball_x | float | X coordinate of ball (meters) |
| is_home | bool | True if checking home team |

**Returns:** True if team is defending

**Logic:**

- True if team does NOT have possession
- True if team has possession but ball in own half
- False if team has possession and ball in opponent half

**Truth table:**

| possession | ball_x | is_home | Result | Reason |
|------------|--------|---------|--------|--------|
| 'home' | 30 | True | True | Own half |
| 'home' | 70 | True | False | Opponent half |
| 'away' | 50 | True | True | No possession |
| 'contested' | 50 | True | True | No possession |

---

### compute_ci(outfield_positions, is_home, config=None) → dict

**What:** Calculates the Compactness Index (0-100).

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| outfield_positions | dict | {player_id: (x, y)} - 10 outfield players |
| is_home | bool | True if home team |
| config | dict | Optional calibration config |

**Returns:**

| Key | Type | Description |
|-----|------|-------------|
| ci | float | Final CI score (0-100), rounded to 1 decimal |
| ci_raw | float | CI before balance penalty |
| block | str | Block classification |
| area | float | ConvexHull area (m²) |
| width | float | Shape width - Y spread (m) |
| depth | float | Shape depth - X spread (m) |
| balance_factor | float | Balance penalty (0-1), rounded to 3 decimals |

**Formula (step-by-step):**

```
1. Ah = ConvexHull(outfield_positions).volume  # 2D area
2. width = max(y) - min(y)
3. depth = max(x) - min(x)
4. centroid_x = mean(x values)
5. block = classify_block(centroid_x, is_home, config)
6. ref_area = config[block_type]  # 600/450/300
7. CI_raw = min(100 × (ref_area / Ah), 100)
8. r = width / depth  # aspect ratio
9. B = exp(-(ln(r))² / (2 × σ²))  # balance factor
10. CI = CI_raw × B
```

**Balance factor behavior:**

| W/D Ratio | Balance Factor | Effect |
|-----------|----------------|--------|
| 1.0 | 1.000 | No penalty (perfect balance) |
| 1.5 | 0.852 | Slight penalty |
| 2.0 | 0.383 | Significant penalty |
| 3.0 | 0.055 | Heavy penalty |

**Edge case handling:**

| Input | Behavior |
|-------|----------|
| < 3 players | Returns {ci: 0, block: 'unknown', ...} |
| ConvexHull fails | Returns area=0, ci=0 |
| depth=0 or area=0 | Guards against division by zero |
| r ≤ 0 | Balance factor = 0 |
| sigma ≤ 0 | Balance factor = 0 |

---

## Dependencies

**Imports:** numpy, scipy.spatial.ConvexHull, math

**Imported by:** app.py (Stats Display)

---

## Quick Test

```python
from src.compactness import classify_block, is_defending, compute_ci

# Test block classification
print(classify_block(20, is_home=True))   # 'low_block'
print(classify_block(50, is_home=True))   # 'mid_block'
print(classify_block(80, is_home=True))   # 'high_press'

# Test defending state
print(is_defending('away', 50, is_home=True))   # True
print(is_defending('home', 70, is_home=True))   # False

# Test CI calculation
positions = {
    'p1': (45, 28), 'p2': (48, 35), 'p3': (50, 40), 'p4': (52, 45),
    'p5': (46, 32), 'p6': (54, 38), 'p7': (49, 30), 'p8': (51, 42),
    'p9': (47, 36), 'p10': (53, 34)
}
result = compute_ci(positions, is_home=True)
print(f"CI: {result['ci']}, Block: {result['block']}")
```

---

## Realistic CI Values

| Scenario | Area (m²) | CI | Interpretation |
|----------|-----------|-----|----------------|
| Compact low block | ~130 | 75-85 | Excellent defensive shape |
| Compact mid block | ~70 | 40-50 | Good shape (W/D penalty) |
| High press | ~670 | 55-65 | Normal for pressing |
| Stretched/poor | ~1200 | 25-35 | Poor defensive structure |

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| CI always 0 | < 3 players passed | Check GK filtering logic |
| CI always 100 | Reference area too large | Reduce ref_area values |
| CI always low | Reference area too small | Increase ref_area values |
| Wrong block type | Boundaries misconfigured | Check boundary_low_mid/high |
| "unknown" block | < 3 players | Ensure 10 outfield passed |
| Balance factor = 0 | Width or depth is 0 | Check position data validity |
| Away team wrong block | is_home flag incorrect | Verify team identification |

---

## File Location

`src/compactness.py` (335 lines including tests)

## Last Updated

January 8, 2026 - CI-2 Implementation
