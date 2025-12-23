# Event Synchronization

## Overview

PFF event data is synchronized with tracking frames using video timestamps.

## Event Data Structure

Events are stored in JSON format:

```json
{
  "startTime": 125.5,
  "gameEvents": {
    "gameEventType": "OTB",
    "startFormattedGameClock": "00:45",
    "playerName": "Kai Havertz",
    "teamName": "Germany"
  },
  "possessionEvents": {
    "possessionEventType": "PA",
    "targetPlayerName": "Joshua Kimmich"
  }
}
```

## Event Types

### Game Event Types

| Code | Name | Description |
|------|------|-------------|
| OTB | On The Ball | Generic ball action |
| OUT | Out of Play | Ball out of bounds |
| SUB | Substitution | Player substitution |
| END | Period End | End of half |
| FIRSTKICKOFF | Kickoff (1H) | First half kickoff |
| SECONDKICKOFF | Kickoff (2H) | Second half kickoff |

### Possession Event Types

| Code | Full Name | Description |
|------|-----------|-------------|
| PA | Pass | Ball passed to teammate |
| CR | Cross | Ball crossed into box |
| SH | Shot | Shot on goal |
| CL | Clearance | Defensive clear |
| IT | Interception | Ball won from opponent |
| TC | Tackle | Ball tackled away |
| CH | Challenge | 50/50 duel for ball |
| RE | Reception | Ball received |
| BC | Ball Control | Touch/dribble |

## Timestamp Conversion

### Frame to Video Time

```python
fps = 29.97
start_period1 = 118.719  # Video time when 1st half starts

# Convert frame index to video time
video_time = start_period1 + (frame_idx / fps)
```

### Video Time to Game Clock

The `startFormattedGameClock` field provides match time (e.g., "45:32").

## Loading Events

```python
@st.cache_resource
def load_events():
    """Load PFF event data for game 3821."""
    import json
    event_path = "Fifa world cup 2022 data/Event Data/3821.json"
    with open(event_path) as f:
        return json.load(f)
```

## Filtering Events by Time

```python
def get_events_near_time(events, video_time, window_seconds=3):
    """Get events within window_seconds of the given video time."""
    nearby = []
    for e in events:
        event_time = e.get('startTime', 0)
        if abs(event_time - video_time) <= window_seconds:
            ge = e.get('gameEvents', {})
            pe = e.get('possessionEvents', {})
            nearby.append({
                'time': event_time,
                'game_clock': ge.get('startFormattedGameClock', '??:??'),
                'event_type': ge.get('gameEventType', 'Unknown'),
                'poss_name': POSSESSION_EVENT_NAMES.get(pe.get('possessionEventType')),
                'player': ge.get('playerName', 'Unknown'),
                'team': ge.get('teamName', 'Unknown'),
                'target': pe.get('targetPlayerName')
            })
    return sorted(nearby, key=lambda x: x['time'])
```

## Event Name Mapping

```python
POSSESSION_EVENT_NAMES = {
    'PA': 'Pass',
    'IT': 'Interception',
    'CH': 'Challenge',
    'RE': 'Reception',
    'CL': 'Clearance',
    'CR': 'Cross',
    'TC': 'Tackle',
    'SH': 'Shot',
    'BC': 'Ball Control',
}
```

## UI Display

Events are displayed with:
- Game clock timestamp `[00:45]`
- Full event name (bolded)
- Player name (color-coded by team)
- Target player (for passes/crosses)

```python
# Format: [00:45] **Pass**: Kai Havertz → Joshua Kimmich
evt_str = f"[{clock}] **{poss_name}**: {player}"
if target:
    evt_str += f" → {target}"
st.markdown(evt_str, unsafe_allow_html=True)
```

## Event Legend

The UI includes a collapsible legend explaining event types:

```python
with st.expander("Event Legend", expanded=False):
    st.markdown("""
    **Ball Actions:**
    - **Pass** - Ball passed to teammate
    - **Cross** - Ball crossed into box
    - **Shot** - Shot on goal
    - **Clearance** - Defensive clear
    
    **Defensive:**
    - **Interception** - Ball won
    - **Tackle** - Ball tackled away
    - **Challenge** - 50/50 duel
    - **Reception** - Ball received
    """)
```

## Event Statistics

For game 3821 (Germany vs Japan):
- Total events: 2,296
- Pass events (PA): 1,087
- Interceptions (IT): 727
- Challenges (CH): 162
- Shots (SH): 28
