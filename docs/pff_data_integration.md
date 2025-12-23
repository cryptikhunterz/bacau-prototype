# PFF Data Integration

## Overview

This application uses PFF (Pro Football Focus) FIFA World Cup 2022 tracking data loaded via the kloppy library.

## Data Folder Structure

```
Fifa world cup 2022 data/
├── Metadata/
│   └── {game_id}.json      # Match metadata (teams, stadium, timing)
├── Rosters/
│   └── {game_id}.json      # Player rosters with jersey numbers
├── Tracking Data/
│   └── {game_id}.jsonl.bz2 # Position tracking (compressed)
└── Event Data/
    └── {game_id}.json      # Game events (passes, shots, etc.)
```

## Available Matches

Only **16 group stage matches** have tracking data (game IDs 3814-3833, 3843-3844).

**Notable matches with tracking:**
- `3819` - France vs Australia
- `3821` - Germany vs Japan (default)
- `3814` - Qatar vs Ecuador (Opening Match)

**Knockout rounds do NOT have tracking data**, including the Argentina vs France final.

## Loading Data with Kloppy

```python
from kloppy import pff

dataset = pff.load_tracking(
    meta_data="Fifa world cup 2022 data/Metadata/3821.json",
    roster_meta_data="Fifa world cup 2022 data/Rosters/3821.json",
    raw_data="Fifa world cup 2022 data/Tracking Data/3821.jsonl.bz2"
)
```

## Coordinate System

| Source | X Range | Y Range | Origin |
|--------|---------|---------|--------|
| Raw PFF | 0-105m | 0-68m | Bottom-left |
| Kloppy (normalized) | 0-1 | 0-1 | Bottom-left |
| Application | 0-105m | 0-68m | Bottom-left |

Kloppy normalizes PFF coordinates to 0-1 range. We scale back to meters:

```python
x = data.coordinates.x * pitch_length  # 105m
y = data.coordinates.y * pitch_width   # 68m
```

## Frame Structure

Each frame contains:

```python
frame = dataset.frames[frame_idx]

# Player data
for player, data in frame.players_data.items():
    coords = data.coordinates  # x, y (normalized 0-1)
    jersey = player.jersey_no
    team = player.team.ground  # 'home' or 'away'
    name = player.name

# Ball data
ball_coords = frame.ball_coordinates  # x, y (normalized 0-1)
```

## Player ID Format

| Data Source | Format | Example |
|-------------|--------|---------|
| Metrica | String `"home_11"` | `"home_11"`, `"away_7"` |
| PFF | Jersey number int | `11`, `7` |

The application handles both formats:

```python
# PFF format (preferred)
if hasattr(player, 'jersey_no') and player.jersey_no:
    pid = int(player.jersey_no)
# Metrica format (fallback)
elif '_' in str(player.player_id):
    pid = int(player.player_id.split('_')[1])
```

## Team Detection

```python
# Via kloppy team.ground attribute
if hasattr(player, 'team') and player.team:
    is_home = player.team.ground.value == 'home'
```

## Metadata Access

```python
# Team names
home_team = dataset.metadata.teams[0].name  # "Germany"
away_team = dataset.metadata.teams[1].name  # "Japan"

# Player roster
for player in dataset.metadata.teams[0].players:
    print(f"#{player.jersey_no} {player.name}")

# Frame count
total_frames = len(dataset.frames)
```

## FPS and Timing

| Parameter | Value |
|-----------|-------|
| FPS | 29.97 |
| startPeriod1 | 118.719s (video time when 1st half starts) |
| startPeriod2 | 3244.244s (video time when 2nd half starts) |

Convert frame index to video time:
```python
video_time = start_period1 + (frame_idx / fps)
```

## Caching Strategy

Data loading is cached with `@st.cache_resource`:

```python
@st.cache_resource
def load_data():
    """Load PFF World Cup 2022 tracking data (cached)."""
    from kloppy import pff
    return pff.load_tracking(...)
```

Clear cache if needed:
```bash
rm -rf ~/.streamlit/cache
```
