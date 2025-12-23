# Zone Analysis Feature

## Overview

The Zone Analysis tab provides scatter plot visualization showing WHERE on the pitch events occur. Users can filter by:
- **Team**: Germany or Japan
- **Player**: Individual player analysis
- **Event Type**: Pass, Reception, Shot, Tackle, Challenge, Interception, Clearance, Cross
- **Match Half**: Full Match, 1st Half, or 2nd Half

This enables tactical analysis of team and player positioning patterns during different phases of the match.

## Data Source

- **File**: `Fifa world cup 2022 data/Event Data/3821.json`
- **Match**: Germany vs Japan (Group Stage, Nov 23, 2022)
- **Total Events**: 2,296

### Key Fields Used

| Field Path | Description | Example |
|------------|-------------|---------|
| `gameEvents.teamId` | Team identifier | 368 (Germany), 57 (Japan) |
| `gameEvents.teamName` | Team name | "Germany", "Japan" |
| `gameEvents.playerId` | Player ID (integer) | 1937, 4616 |
| `gameEvents.playerName` | Player name | "Kai Havertz" |
| `gameEvents.period` | Match half | 1 (1st half), 2 (2nd half) |
| `possessionEvents.possessionEventType` | Event code | "PA", "RE", "SH", etc. |
| `ball[0].x` | Ball X coordinate (centered) | -52.5 to +52.5 |
| `ball[0].y` | Ball Y coordinate (centered) | -34 to +34 |

## Event Type Mapping

| UI Label | Code | Description |
|----------|------|-------------|
| Pass | PA | Ball passed to teammate |
| Reception | RE | Ball received from pass |
| Shot | SH | Shot on goal |
| Tackle | TC | Ball tackled from opponent |
| Challenge | CH | 50/50 duel for ball |
| Interception | IT | Ball intercepted |
| Clearance | CL | Defensive clearance |
| Cross | CR | Ball crossed into box |

### Event Counts by Half (Germany vs Japan)

| Metric | Full Match | 1st Half | 2nd Half |
|--------|------------|----------|----------|
| Total Events | 2,296 | 1,218 | 1,078 |
| Germany Passes | 754 | 460 | 294 |
| Japan Passes | 260 | 92 | 168 |

*Note: Germany dominated possession in the 1st half, Japan increased share in the 2nd half (matching the comeback narrative).*

## Key Functions

### `draw_event_scatter(positions, title, team_color)`

Draws a football pitch with event locations as colored scatter dots.

```python
def draw_event_scatter(positions, title, team_color='#FFFFFF'):
    """
    Args:
        positions: List of (x, y) tuples in normalized 0-1 coordinates
        title: Chart title
        team_color: Color for dots (e.g., '#FFFFFF' for Germany, '#0066CC' for Japan)

    Returns:
        matplotlib figure with pitch and scatter overlay
    """
```

**Pitch Elements Drawn:**
- Outer boundary
- Halfway line
- Center circle and spot
- Penalty areas (left and right)
- Goal areas (left and right)
- Goals (extending outside pitch)
- Penalty spots

### `collect_team_event_positions(events, team_name, event_type_code)`

Collects x,y positions for all events of a specific type for a team.

```python
def collect_team_event_positions(events, team_name, event_type_code):
    """
    Args:
        events: List of PFF events
        team_name: 'Germany' or 'Japan'
        event_type_code: Event type code ('PA', 'RE', 'SH', etc.)

    Returns:
        List of (x, y) tuples normalized to 0-1 range
    """
```

### `collect_player_event_positions(events, player_id, event_type_code)`

Collects x,y positions for all events of a specific type for a player.

```python
def collect_player_event_positions(events, player_id, event_type_code):
    """
    Args:
        events: List of PFF events
        player_id: Player ID to filter by (string from kloppy, converted to int)
        event_type_code: Event type code ('PA', 'RE', 'SH', etc.)

    Returns:
        List of (x, y) tuples normalized to 0-1 range
    """
```

### `filter_events_by_half(events, half_selection)`

Filters events by match period.

```python
def filter_events_by_half(events, half_selection):
    """
    Args:
        events: List of PFF events
        half_selection: "Full Match", "1st Half", or "2nd Half"

    Returns:
        Filtered list of events

    Logic:
        - "Full Match": returns all events unchanged
        - "1st Half": filters where gameEvents.period == 1
        - "2nd Half": filters where gameEvents.period == 2
    """
```

## Coordinate Normalization

PFF uses **centered coordinates** where (0, 0) is the pitch center:
- X: -52.5 to +52.5 (pitch length = 105m)
- Y: -34 to +34 (pitch width = 68m)

Normalization to 0-1 range for plotting:

```python
# PFF centered -> 0-1 normalized
x_norm = (x + 52.5) / 105.0  # shift from -52.5..+52.5 to 0..1
y_norm = (y + 34) / 68.0     # shift from -34..+34 to 0..1

# Clamp to valid range
x_norm = max(0, min(1, x_norm))
y_norm = max(0, min(1, y_norm))
```

## UI Structure

```
Zone Analysis Tab
├── Germany Column (zone_col1)
│   ├── Team Half Selector (key="home_team_half")
│   ├── Team Event Type Selector (key="home_team_event")
│   ├── Team Scatter Plot
│   ├── --- divider ---
│   ├── Player Analysis Section
│   │   ├── Player Selector (key="home_player_select")
│   │   ├── Player Half Selector (key="home_player_half")
│   │   ├── Player Event Selector (key="home_player_event")
│   │   └── Player Scatter Plot
│
└── Japan Column (zone_col2)
    ├── Team Half Selector (key="away_team_half")
    ├── Team Event Type Selector (key="away_team_event")
    ├── Team Scatter Plot
    ├── --- divider ---
    └── Player Analysis Section
        ├── Player Selector (key="away_player_select")
        ├── Player Half Selector (key="away_player_half")
        ├── Player Event Selector (key="away_player_event")
        └── Player Scatter Plot
```

**Note**: Team and player half selectors are independent - you can view team 1st half while viewing player 2nd half.

## Team ID Mapping

```python
TEAM_IDS = {
    'Germany': 368,
    'Japan': 57
}
```

## Gotchas / Lessons Learned

### 1. Player ID Type Mismatch

**Problem**: Player scatter plots returned "0 events" for all players.

**Root Cause**: Kloppy stores player IDs as **strings** (e.g., `'1937'`), but PFF events store them as **integers** (e.g., `1937`). Direct comparison always failed.

**Fix**: Convert player_id to int before comparison:
```python
try:
    player_id_int = int(player_id)
except (ValueError, TypeError):
    return []  # or return empty stats

# Then compare:
if ge.get('playerId') != player_id_int:
    continue
```

### 2. Coordinate System Confusion

**Problem**: Initial scatter plots showed events clustered incorrectly.

**Root Cause**: PFF uses centered coordinates (0,0 at pitch center), not corner-origin coordinates.

**Fix**: Added proper normalization from centered to 0-1 range (see Coordinate Normalization section).

### 3. Half Context Matters

**Issue**: Teams switch sides at halftime, so the same physical zone (e.g., "attacking third") is on opposite ends of the pitch in each half.

**Current Approach**: Half selector allows filtering to see patterns within each half separately. Future enhancement could flip coordinates for 2nd half visualization.

### 4. Team Name vs Team ID

**Problem**: Initially tried matching by `teamName` but this is less reliable.

**Fix**: Use `teamId` for matching (368 for Germany, 57 for Japan). Team IDs are integers in the event data.

### 5. Ball Position vs Player Position

**Note**: Event positions come from `ball[0].x/y`, not player position. This is the ball location when the event occurred.

## File References

- **Main app**: `app.py` (lines 372-508 for collection/filter functions, lines 511-623 for draw_event_scatter, lines 602-768 for Zone Analysis tab)
- **Event data**: `Fifa world cup 2022 data/Event Data/3821.json`
- **Team colors**: Germany = `#FFFFFF` (white), Japan = `#0066CC` (blue)

## Future Enhancements

1. **Heatmap overlay**: Show density rather than individual dots
2. **Direction arrows**: Show pass direction on pass events
3. **Time range filter**: Filter by game clock range
4. **Zone statistics overlay**: Show counts per tactical zone
5. **Flip coordinates for 2nd half**: Account for team side switch
6. **Event sequence animation**: Animate event progression over time
