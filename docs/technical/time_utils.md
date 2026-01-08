# time_utils.py - Technical Reference

## Purpose

Converts frame indices to human-readable match time format for the Activity Log display.

## Functions

### frame_to_match_time(frame_idx, metadata) → str

**What:** Converts frame number to continuous [MM:SS] format (0-90+ minutes).

**Args:**

| Arg | Type | Description |
|-----|------|-------------|
| frame_idx | int | Current frame number (0-indexed) |
| metadata | dict | Timing info (fps, startPeriod1, etc.) |

**Returns:** String like "[02:45]" or "[53:32]" (continuous time, no prefix)

**Metadata dict keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| fps | float | 29.97 | Frames per second |
| startPeriod1 | float | 0 | Video time when 1st half starts (seconds) |
| endPeriod1 | float | inf | Video time when 1st half ends (seconds) |
| startPeriod2 | float | 0 | Video time when 2nd half starts (seconds) |
| endPeriod2 | float | - | Video time when 2nd half ends (seconds) |

**Formula:**

```
video_time = startPeriod1 + (frame_idx / fps)

if video_time < endPeriod1:
    elapsed = video_time - startPeriod1
    base_minutes = 0
else:
    elapsed = video_time - startPeriod2
    base_minutes = 45

minutes = base_minutes + (elapsed_seconds // 60)
format: "[MM:SS]"
```

**Edge case handling:**

| Input | Behavior |
|-------|----------|
| frame_idx < 0 | Returns "[00:00]" |
| fps missing | Defaults to 29.97 |
| fps <= 0 | Defaults to 29.97 |
| Fractional seconds | Rounded to nearest second |
| Beyond endPeriod2 | Continues counting (no cap) |

---

## Dependencies

**Imports:** None (standard library only)

**Imported by:** app.py (Activity Log display)

---

## Game 3821 Metadata Reference

```python
GAME_METADATA = {
    'fps': 29.97,
    'startPeriod1': 118.719,
    'endPeriod1': 3177.578,
    'startPeriod2': 3244.244,
    'endPeriod2': 6434.634
}
```

**Key frame numbers for Game 3821:**

| Frame | Match Time | Notes |
|-------|------------|-------|
| 0 | [00:00] | Start of tracking |
| 2697 | [01:30] | 90 seconds into match |
| 91674 | [50:59] | Last frame of first half |
| 91675 | [45:00] | First frame of second half |
| 100000 | [48:31] | ~3.5 mins into second half |
| 109012 | [53:32] | End of available tracking data |

---

## Data Coverage Note

**Important:** Game 3821 tracking data does not cover the full 90-minute match.

| Metric | Value |
|--------|-------|
| Total frames available | 109,013 |
| First half coverage | Full (~51 minutes) |
| Second half coverage | Partial (~8.5 minutes) |
| Last frame match time | [53:32] |

The metadata describes a full 90+ minute match, but the tracking data file ends at frame 109,012. This is a data availability limitation, not a calculation error.

---

## Quick Test

```python
from src.time_utils import frame_to_match_time

metadata = {
    'fps': 29.97,
    'startPeriod1': 118.719,
    'endPeriod1': 3177.578,
    'startPeriod2': 3244.244,
    'endPeriod2': 6434.634
}

print(frame_to_match_time(0, metadata))      # "[00:00]"
print(frame_to_match_time(2697, metadata))   # "[01:30]"
print(frame_to_match_time(91675, metadata))  # "[45:00]"
print(frame_to_match_time(100000, metadata)) # "[48:31]"
print(frame_to_match_time(-10, metadata))    # "[00:00]"
```

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Wrong time displayed | Incorrect metadata values | Verify startPeriod1 matches video |
| Time shows [45:00] unexpectedly | Frame crossed into second half | Check endPeriod1 in metadata |
| Time jumps at halftime | Normal behavior | Gap is halftime break in video |
| Max time ~[53:32] | Data ends at frame 109,012 | Normal - partial game data |

---

## File Location

`src/time_utils.py` (57 lines)

## Last Updated

January 8, 2026 - Updated to continuous 0-90+ format (removed 45+ prefix)
