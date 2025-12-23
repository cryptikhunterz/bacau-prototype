# Shape Graph Architecture

## Overview

Shape Graph Visualization is a Streamlit-based application for visualizing football/soccer tracking data. It displays team formations as convex hull shapes, tracks ball position and possession, and synchronizes PFF event data with frame-by-frame tracking.

## System Architecture

```
+------------------+     +------------------+     +------------------+
|   PFF Data       |     |   Kloppy         |     |   Streamlit      |
|   (JSON/BZ2)     | --> |   Loader         | --> |   App            |
+------------------+     +------------------+     +------------------+
                                                          |
                         +--------------------------------+
                         |
          +--------------+--------------+--------------+
          |              |              |              |
    +-----v----+  +------v-----+  +-----v----+  +-----v----+
    | Pitch    |  | Markers    |  | Stats    |  | Events   |
    | Renderer |  | Renderer   |  | Computer |  | Loader   |
    +----------+  +------------+  +----------+  +----------+
```

## Data Flow

1. **Data Loading**: PFF tracking data loaded via kloppy library
2. **Frame Extraction**: Player positions extracted per frame (normalized 0-1 coordinates)
3. **Coordinate Scaling**: Positions scaled to pitch dimensions (105x68 meters)
4. **Shape Computation**: Convex hull calculated for outfield players
5. **Stats Calculation**: Area, compactness, width, depth computed per frame
6. **Event Sync**: Events matched to current video timestamp
7. **Rendering**: Matplotlib figures rendered to Streamlit

## File Structure

```
shape-graph-animation/
├── app.py                 # Main Streamlit application
├── src/
│   ├── pitch.py           # Pitch drawing functions
│   ├── markers.py         # Player marker rendering
│   ├── colors.py          # Color definitions
│   ├── position_classifier.py  # Formation detection
│   └── shape_lines.py     # Shape line utilities
├── docs/                  # Documentation
│   ├── shape_graph_architecture.md
│   ├── pff_data_integration.md
│   ├── tracking_stats.md
│   ├── event_sync.md
│   └── streamlit_patterns.md
├── Fifa world cup 2022 data/  # PFF data (not in repo)
│   ├── Metadata/          # Match metadata JSON
│   ├── Rosters/           # Player roster JSON
│   ├── Tracking Data/     # Position tracking (JSONL.BZ2)
│   └── Event Data/        # Game events JSON
└── requirements.txt       # Python dependencies
```

## Core Components

### app.py (Main Application)

| Function | Purpose |
|----------|---------|
| `load_data()` | Cached PFF data loader via kloppy |
| `extract_positions()` | Extract player x,y from frame |
| `get_ball_position()` | Extract ball coordinates |
| `get_possession()` | Determine possession by proximity |
| `compute_team_stats()` | Calculate shape metrics |
| `get_ball_carrier()` | Identify closest player to ball |
| `load_events()` | Load PFF event JSON |
| `get_events_near_time()` | Filter events by timestamp |
| `draw_team_shape()` | Render convex hull polygon |
| `render_frame()` | Full frame rendering pipeline |

### src/pitch.py

Renders the football pitch with standard markings:
- Pitch outline (105x68m)
- Center circle and spot
- Penalty areas and spots
- Goal areas
- Corner arcs

### src/markers.py

Renders player markers with:
- Position-based coloring (defense/midfield/attack)
- Jersey number labels
- Radius scaling

### src/colors.py

Color palette definitions:
- `BACKGROUND_COLOR`: Dark theme background (#0d1117)
- Team colors: Blue (#3498db) for home, Red (#e74c3c) for away
- Position gradients for player markers

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web UI framework |
| matplotlib | Pitch and player rendering |
| numpy | Numerical operations |
| scipy | Convex hull computation |
| kloppy | Football tracking data loading |
| certifi | SSL certificate handling |

## Performance Considerations

- **Caching**: `@st.cache_resource` for data loading (only loads once)
- **Frame Skip**: Autoplay skips frames for smoother playback
- **Minimum Delay**: 50ms minimum between reruns for UI responsiveness
- **Figure Cleanup**: `plt.close(fig)` prevents memory leaks
