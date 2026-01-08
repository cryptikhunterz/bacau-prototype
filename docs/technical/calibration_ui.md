# Calibration UI - Technical Reference

## Purpose

Provides user-adjustable sliders in the sidebar for tuning Compactness Index (CI) parameters without editing code.

## Location

- **File:** app.py
- **Lines:** 1155-1202
- **Sidebar section:** "CI Calibration" (collapsed expander)

## Parameters

| Slider | Key | Min | Max | Default | Step | Description |
|--------|-----|-----|-----|---------|------|-------------|
| High Press | ref_area_high | 400 | 1000 | 600 | 50 | Reference area for high press (m²) |
| Mid Block | ref_area_mid | 300 | 800 | 450 | 50 | Reference area for mid block (m²) |
| Low Block | ref_area_low | 150 | 500 | 300 | 25 | Reference area for low block (m²) |
| Balance Sensitivity (σ) | sigma | 0.1 | 1.0 | 0.5 | 0.1 | Balance penalty strictness |
| Low/Mid Boundary (%) | boundary_low_mid | 20 | 50 | 35 | 5 | Threshold for low vs mid block |
| Mid/High Boundary (%) | boundary_mid_high | 50 | 80 | 65 | 5 | Threshold for mid vs high press |

## Session State

Config stored in `st.session_state.ci_config`:

```python
st.session_state.ci_config = {
    'ref_area_high': 600,      # From slider (int)
    'ref_area_mid': 450,       # From slider (int)
    'ref_area_low': 300,       # From slider (int)
    'sigma': 0.5,              # From slider (float)
    'boundary_low_mid': 0.35,  # Converted from % to decimal
    'boundary_mid_high': 0.65  # Converted from % to decimal
}
```

**Note:** Boundary values are converted from percentage (35%) to decimal (0.35) when stored.

## Usage

To access config from elsewhere in app.py:

```python
# Get current config (or defaults if not set)
config = st.session_state.get('ci_config', None)

# Pass to compute_ci
from src.compactness import compute_ci
result = compute_ci(outfield_positions, is_home=True, config=config)
```

## UI Behavior

- Expander collapsed by default (doesn't clutter sidebar)
- Changes take effect immediately (Streamlit reactivity)
- Values persist during session
- Reset to defaults on page refresh

## Dependencies

**Imports:** None additional (uses existing st.sidebar)

**Used by:** CI-5 Stats Display (passes config to compute_ci)

**Depends on:** src/compactness.py DEFAULT_CONFIG (matching keys)

## Matching Keys

Config keys must match those in src/compactness.py DEFAULT_CONFIG:

| UI Key | compactness.py Key | Match |
|--------|-------------------|-------|
| ref_area_high | ref_area_high | Yes |
| ref_area_mid | ref_area_mid | Yes |
| ref_area_low | ref_area_low | Yes |
| sigma | sigma | Yes |
| boundary_low_mid | boundary_low_mid | Yes |
| boundary_mid_high | boundary_mid_high | Yes |

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Config not found | Session state not initialized | Use .get() with default |
| Boundaries as integers | Forgot /100 conversion | Check storage code |
| Sliders reset on frame change | Not using session_state | Verify st.session_state usage |
| CI values unchanged | Config not passed to compute_ci | Check CI-5 integration |

---

*File: app.py (lines 1155-1202)*
*Last updated: January 8, 2026*
