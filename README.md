# Shape Graph Visualization

Real-time football/soccer tracking visualization with team shape analysis, powered by PFF FIFA World Cup 2022 data.

## Features

- **Team Shape Visualization**: Convex hull polygons showing team formation shape
- **Real-time Tracking Stats**: Area, compactness, width, depth metrics per team
- **Ball Tracking**: Ball position with possession indicator
- **Event Log**: PFF events synchronized to current frame (passes, shots, tackles, etc.)
- **Player Rosters**: Full player lists with jersey numbers
- **Autoplay**: Frame-by-frame animation with adjustable speed
- **Formation Detection**: Automatic formation pattern recognition
- **Zone Analysis**: Scatter plot visualization of event locations with team/player/half filtering
- **Pitch Control**: Spatial dominance heatmap showing which team controls each area of the pitch

## Demo Match

**Germany vs Japan** (Group Stage, Nov 23, 2022)
- Famous upset: Japan won 2-1
- Full tracking data at 29.97 fps

## Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  ⚽ Shape Graph Visualization                           │
├──────────────────────────────────┬──────────────────────┤
│                                  │  Activity Log        │
│   [Germany Pitch View]           │  Frame 5000 | HOME   │
│   - Blue convex hull             │  Frame 5010 | AWAY   │
│   - Player markers               │  ...                 │
│   - Ball position                │                      │
│                                  ├──────────────────────┤
│   [Japan Pitch View]             │  Performance         │
│   - Red convex hull              │  FPS: 12.5           │
│   - Player markers               │                      │
│                                  │                      │
├──────────────────────────────────┴──────────────────────┤
│  Match Analysis                                         │
│  ┌─────────────────────┐  ┌───────────────────────────┐ │
│  │ Team Shape Stats    │  │ Event Log (PFF)           │ │
│  │ Germany | Japan     │  │ [00:45] Pass: Havertz →   │ │
│  │ Area: 850 | 720 m²  │  │ [00:46] Reception: Kimmich│ │
│  │ Compact: 18 | 15 m  │  │ [00:47] Pass: Kimmich →   │ │
│  │ Width: 45 | 40 m    │  │                           │ │
│  │ Depth: 35 | 32 m    │  │ Total events: 2,296       │ │
│  └─────────────────────┘  └───────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- PFF FIFA World Cup 2022 data (not included)

### Setup

```bash
# Clone repository
git clone https://github.com/cryptikhunterz/bacau-prototype.git
cd bacau-prototype

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Data Setup

Place PFF World Cup 2022 data in the project root:

```
shape-graph-animation/
└── Fifa world cup 2022 data/
    ├── Metadata/
    │   └── 3821.json
    ├── Rosters/
    │   └── 3821.json
    ├── Tracking Data/
    │   └── 3821.jsonl.bz2
    └── Event Data/
        └── 3821.json
```

## Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### Controls

| Control | Description |
|---------|-------------|
| Frame Slider | Scrub to any frame |
| Auto-play | Toggle animation |
| Speed | Frames per update (1-50) |
| Show team shapes | Toggle convex hull display |
| Show ball | Toggle ball marker |
| Show pitch control | Toggle pitch control heatmap overlay |
| Pitch control opacity | Adjust overlay transparency (0.1-0.9) |

## Project Structure

```
shape-graph-animation/
├── app.py              # Main Streamlit application
├── src/
│   ├── pitch.py        # Pitch rendering
│   ├── markers.py      # Player markers
│   ├── colors.py       # Color palette
│   ├── position_classifier.py  # Formation detection
│   ├── velocity.py     # Player velocity calculation
│   └── pitch_control.py # Pitch control algorithm
├── docs/
│   ├── shape_graph_architecture.md
│   ├── pff_data_integration.md
│   ├── tracking_stats.md
│   ├── event_sync.md
│   ├── streamlit_patterns.md
│   └── zone_analysis.md
└── requirements.txt
```

## Documentation

- [Architecture Overview](docs/shape_graph_architecture.md)
- [PFF Data Integration](docs/pff_data_integration.md)
- [Tracking Stats Calculation](docs/tracking_stats.md)
- [Event Synchronization](docs/event_sync.md)
- [Streamlit Patterns](docs/streamlit_patterns.md)
- [Zone Analysis](docs/zone_analysis.md)
- [Pitch Control](docs/technical/pitch_control.md)

## Dependencies

```
streamlit>=1.28.0
matplotlib>=3.7.0
numpy>=1.24.0
scipy>=1.10.0
kloppy>=3.0.0
certifi
```

## Available Matches

Only 16 group stage matches have tracking data:

| Game ID | Match | Notes |
|---------|-------|-------|
| 3821 | Germany vs Japan | Default (famous upset) |
| 3819 | France vs Australia | |
| 3814 | Qatar vs Ecuador | Opening match |

*Knockout rounds do NOT have tracking data.*

## Technical Notes

- **FPS**: 29.97 (PFF standard)
- **Pitch**: 105m x 68m (FIFA standard)
- **Coordinates**: Normalized 0-1 by kloppy, scaled to meters
- **Caching**: Data loaded once via `@st.cache_resource`

## License

MIT

## Acknowledgments

- [kloppy](https://github.com/PySport/kloppy) - Football tracking data loading
- [Streamlit](https://streamlit.io/) - Web application framework
- [PFF](https://www.pff.com/) - FIFA World Cup 2022 tracking data
