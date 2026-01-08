# CI Calibration Guide

## What is Compactness Index (CI)?

CI measures how tight your team's defensive shape is.

| Score | Meaning |
|-------|---------|
| 80-100 | Excellent — compact, hard to play through |
| 60-80 | Good — solid shape |
| 40-60 | Average — some gaps |
| 20-40 | Poor — stretched, vulnerable |
| 0-20 | Very poor — disorganized |

CI only shows when a team is **defending**. When you see "In Possession", that team has the ball.

---

## Block Types

The app detects three defensive positions based on where your team is on the pitch:

- **Low Block:** Defending in your own third
- **Mid Block:** Defending in the middle third
- **High Press:** Pressing in opponent's third

---

## Using the Calibration Sliders

Find **"CI Calibration"** in the sidebar (click to expand).

### Reference Areas

These set the "ideal" shape size for each block type. Smaller values expect a tighter shape, making it harder to score a high CI.

| Slider | Default | When to Adjust |
|--------|---------|----------------|
| High Press | 600 m² | Lower if you want tighter pressing shape |
| Mid Block | 450 m² | Lower for teams that should be more compact |
| Low Block | 300 m² | Lower for very defensive teams |

**Example:** If your team should be very compact in low block, change from 300 to 200. The CI will be harder to score high.

### Balance Sensitivity

Controls how much the width-to-depth ratio affects CI. A balanced shape (not too wide, not too deep) scores higher.

| Value | Effect |
|-------|--------|
| 0.1-0.3 | Strict — shape must be well balanced |
| 0.5 | Moderate (default) |
| 0.7-1.0 | Lenient — ratio matters less |

### Block Boundaries

Where on the pitch each block type starts (measured from your own goal):

- **Low/Mid Boundary (35%):** Below this = low block
- **Mid/High Boundary (65%):** Above this = high press

Adjust based on how your team defines their pressing triggers.

---

## Practical Tips

1. **Start with defaults** — they work for most teams
2. **Compare multiple frames** — if CI seems consistently too high or low, adjust reference areas
3. **Team style matters** — compact teams need lower reference areas
4. **Reset by refreshing** — page refresh restores all defaults

---

## Example Adjustments

**Very defensive team (parks the bus):**
- Low Block: 300 → 200
- Balance: 0.5 → 0.3 (stricter)

**High pressing team:**
- High Press: 600 → 500
- Mid/High Boundary: 65% → 60%

**Team with good shape but low scores:**
- Increase all reference areas by 100-150
- Or increase Balance to 0.7

---

*Last updated: January 8, 2026*
