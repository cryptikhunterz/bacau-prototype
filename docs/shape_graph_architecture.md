# Shape Graph Architecture

## Overview

A Streamlit-based football tracking visualization app that shows team formations as "shape graphs" with bi-colored player markers and convex hull team shapes.

## Project Structure

```
~/Desktop/shape-graph-animation/
├── app.py                 # Streamlit UI entry point
├── main.py                # Tkinter UI entry point (alternative)
├── src/
│   ├── __init__.py
│   ├── activity_logger.py # Logging to file + UI
│   ├── animate.py         # Animation export (GIF/MP4)
│   ├── colors.py          # Color definitions
│   ├── data_loader.py     # Data loading utilities
│   ├── markers.py         # Bi-colored semi-circle markers
│   ├── pitch.py           # Football pitch drawing
│   ├── position_classifier.py  # Position classification
│   ├── shape_lines.py     # Convex hull team shapes
│   ├── ui.py              # Tkinter UI wrapper
│   └── visualize.py       # Static frame visualization
├── outputs/
│   ├── frames/            # PNG exports
│   └── videos/            # GIF/MP4 exports
├── logs/
│   └── activity_log.md    # Activity log file
└── docs/                  # Documentation
```

## Data Flow

```
Kloppy (metrica.load_open_data())
    ↓
TrackingDataset (145K frames)
    ↓
frame.players_data → extract_positions()
    ↓
{player_id: (x, y)} dict (normalized 0-1)
    ↓
Convert to pitch coords (0-105, 0-68)
    ↓
classify_team_vertical() → bucket 0-4 (back→front)
classify_team_horizontal() → bucket 0-4 (left→right)
    ↓
draw_player_marker() → bi-colored wedges
draw_team_shape() → convex hull polygon
    ↓
matplotlib Figure → st.pyplot()
```

## Key Files

### app.py (Streamlit UI)
- Main entry point for web UI
- Frame scrubbing slider
- Auto-play with session state pattern
- Team shape toggle
- Ball visualization toggle
- Activity log + debug trace panels

### src/markers.py
- `draw_bicolor_marker()` - Upper/lower semi-circle wedges
- `draw_player_marker()` - Complete marker with jersey number
- Uses matplotlib.patches.Wedge for semi-circles

### src/position_classifier.py
- `classify_team_vertical()` - Back (0) to Front (4)
- `classify_team_horizontal()` - Left (0) to Right (4)
- `detect_formation()` - Returns "4-3-3", "4-4-2", etc.

### src/shape_lines.py
- `compute_convex_hull()` - scipy.spatial.ConvexHull
- `draw_team_shape()` - Filled polygon with outline
- `identify_goalkeeper()` - Excludes GK from hull

### src/pitch.py
- `draw_pitch()` - Full pitch with markings
- 105m x 68m standard dimensions
- Penalty areas, center circle, goals

## Session State Keys

| Key | Purpose |
|-----|---------|
| `current_frame` | Source of truth for frame index |
| `_slider_widget` | Internal slider widget key |
| `log` | Activity log messages (list) |
| `debug_log` | Debug trace messages (list) |

## Color Scheme

### Vertical (Back → Front)
- 0: #1565C0 (Deep Blue) - Defensive
- 1: #42A5F5 (Light Blue) - Defensive Mid
- 2: #AB47BC (Purple) - Central Mid
- 3: #EF5350 (Light Red) - Attacking Mid
- 4: #C62828 (Deep Red) - Forward

### Horizontal (Left → Right)
- 0: #795548 (Brown) - Left
- 1: #8D6E63 (Light Brown) - Left-Center
- 2: #78909C (Blue-Grey) - Center
- 3: #81C784 (Light Green) - Right-Center
- 4: #2E7D32 (Deep Green) - Right

## Running the App

```bash
cd ~/Desktop/shape-graph-animation
source venv/bin/activate
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
streamlit run app.py
```

Open http://localhost:8501
