# Football Shape Graph Animation - Implementation Plan

## Quick Start (First 30 Minutes)

```bash
# 1. Create project & virtual environment
cd ~/Desktop/shape-graph-animation
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install kloppy matplotlib numpy pandas ffmpeg-python

# 3. Download sample data (see Data Section below)

# 4. Run first test
python test_data_load.py
```

---

## 1. Data Section

### Data Source

**PFF FC 2022 World Cup Dataset** - Free broadcast tracking data for all 64 matches.

| Resource | URL |
|----------|-----|
| Official Blog | https://blog.fc.pff.com/blog/pff-fc-release-2022-world-cup-data |
| Download Form | https://www.blog.fc.pff.com/blog/enhanced-2022-world-cup-dataset |
| Kloppy Docs | https://kloppy.pysport.org/user-guide/loading-data/pff/ |

### Data Structure

```
pff_data/
├── tracking/
│   └── {game_id}.jsonl.bz2    # Tracking data per game
├── metadata/
│   └── {game_id}.json          # Game metadata
├── rosters/
│   └── {game_id}.json          # Team rosters
└── events.json                  # All events (optional)
```

### Loading Data with Kloppy

```python
from kloppy import pff

# Load tracking data for a specific game
dataset = pff.load_tracking(
    meta_data="pff_data/metadata/10517.json",
    roster_meta_data="pff_data/rosters/10517.json",
    raw_data="pff_data/tracking/10517.jsonl.bz2"
)

# Convert to pandas DataFrame for easier manipulation
df = dataset.to_df()
print(df.columns)
# Expected: frame_id, timestamp, ball_x, ball_y,
#           home_1_x, home_1_y, home_2_x, home_2_y, ...
#           away_1_x, away_1_y, away_2_x, away_2_y, ...
```

### Fallback: Synthetic Test Data

If data download is blocked, use this synthetic data generator:

```python
import numpy as np
import pandas as pd

def generate_synthetic_tracking(n_frames=100, fps=25):
    """Generate realistic-looking tracking data for testing."""
    np.random.seed(42)

    # Pitch dimensions (in meters, standard: 105x68)
    pitch_length, pitch_width = 105, 68

    # Base formations (4-3-3 for home, 4-4-2 for away)
    home_base = np.array([
        [10, 34],   # GK
        [25, 10], [25, 25], [25, 43], [25, 58],  # DEF
        [45, 20], [50, 34], [45, 48],             # MID
        [70, 15], [75, 34], [70, 53]              # FWD
    ])

    away_base = np.array([
        [95, 34],   # GK
        [80, 10], [80, 25], [80, 43], [80, 58],  # DEF
        [60, 10], [55, 25], [55, 43], [60, 58],  # MID
        [35, 25], [35, 43]                        # FWD
    ])

    frames = []
    for frame in range(n_frames):
        t = frame / fps
        row = {'frame_id': frame, 'timestamp': t}

        # Add noise and slight movement
        for i, (x, y) in enumerate(home_base):
            noise_x = np.sin(t * 2 + i) * 3 + np.random.randn() * 1
            noise_y = np.cos(t * 1.5 + i) * 2 + np.random.randn() * 1
            row[f'home_{i+1}_x'] = x + noise_x
            row[f'home_{i+1}_y'] = y + noise_y

        for i, (x, y) in enumerate(away_base):
            noise_x = np.sin(t * 2 + i + 5) * 3 + np.random.randn() * 1
            noise_y = np.cos(t * 1.5 + i + 5) * 2 + np.random.randn() * 1
            row[f'away_{i+1}_x'] = x + noise_x
            row[f'away_{i+1}_y'] = y + noise_y

        # Ball position
        row['ball_x'] = 52.5 + np.sin(t) * 30
        row['ball_y'] = 34 + np.cos(t * 0.7) * 20

        frames.append(row)

    return pd.DataFrame(frames)

# Usage
df = generate_synthetic_tracking(n_frames=250)
df.to_csv('synthetic_tracking.csv', index=False)
```

---

## 2. Position Classification Algorithms

### Vertical Position (Front ↔ Back)

Classify each player's position relative to teammates along the attacking axis.

```python
def classify_vertical_position(player_x, team_x_positions, n_buckets=5):
    """
    Classify player's vertical (attacking) position relative to teammates.

    Args:
        player_x: Player's x-coordinate (attacking direction)
        team_x_positions: List of all team x-coordinates (excluding GK)
        n_buckets: Number of classification buckets

    Returns:
        int: 0 (Back/Defensive) to 4 (Front/Attacking)
    """
    # Sort positions from back to front
    sorted_positions = sorted(team_x_positions)

    # Find player's rank
    rank = sorted_positions.index(player_x)

    # Convert to bucket (0-4)
    bucket = int(rank / len(sorted_positions) * n_buckets)
    return min(bucket, n_buckets - 1)


def classify_team_vertical(team_positions):
    """
    Classify all players' vertical positions at once.

    Args:
        team_positions: Dict of {player_id: (x, y)} or DataFrame row

    Returns:
        Dict of {player_id: vertical_bucket}
    """
    # Extract x positions (exclude goalkeeper - usually position 1)
    outfield_x = {pid: pos[0] for pid, pos in team_positions.items()
                  if pid != 1}  # Assuming GK is player 1

    sorted_x = sorted(outfield_x.values())

    result = {}
    for pid, x in outfield_x.items():
        rank = sorted_x.index(x)
        bucket = int(rank / len(sorted_x) * 5)
        result[pid] = min(bucket, 4)

    # Goalkeeper is always "Back" (0)
    result[1] = 0

    return result
```

### Horizontal Position (Left ↔ Right)

```python
def classify_horizontal_position(player_y, team_y_positions, n_buckets=5):
    """
    Classify player's horizontal (left/right) position relative to teammates.

    Args:
        player_y: Player's y-coordinate (left-right axis)
        team_y_positions: List of all team y-coordinates
        n_buckets: Number of classification buckets

    Returns:
        int: 0 (Left) to 4 (Right)
    """
    sorted_positions = sorted(team_y_positions)
    rank = sorted_positions.index(player_y)
    bucket = int(rank / len(sorted_positions) * n_buckets)
    return min(bucket, n_buckets - 1)


def classify_team_horizontal(team_positions):
    """Classify all players' horizontal positions."""
    y_positions = {pid: pos[1] for pid, pos in team_positions.items()}
    sorted_y = sorted(y_positions.values())

    result = {}
    for pid, y in y_positions.items():
        rank = sorted_y.index(y)
        bucket = int(rank / len(sorted_y) * 5)
        result[pid] = min(bucket, 4)

    return result
```

---

## 3. Color Mapping System

### Vertical Colors (Blue → Red: Back to Front)

```python
VERTICAL_COLORS = {
    0: '#1565C0',  # Back - Deep Blue (Defensive)
    1: '#42A5F5',  # Defensive Mid - Light Blue
    2: '#AB47BC',  # Central Mid - Purple
    3: '#EF5350',  # Attacking Mid - Light Red
    4: '#C62828',  # Front - Deep Red (Attacking)
}

VERTICAL_LABELS = {
    0: 'DEF',
    1: 'DM',
    2: 'MID',
    3: 'AM',
    4: 'FWD'
}
```

### Horizontal Colors (Brown → Green: Left to Right)

```python
HORIZONTAL_COLORS = {
    0: '#795548',  # Left - Brown
    1: '#8D6E63',  # Left-Center - Light Brown
    2: '#78909C',  # Center - Blue-Grey
    3: '#81C784',  # Right-Center - Light Green
    4: '#2E7D32',  # Right - Deep Green
}

HORIZONTAL_LABELS = {
    0: 'L',
    1: 'LC',
    2: 'C',
    3: 'RC',
    4: 'R'
}
```

---

## 4. Bi-Colored Semi-Circle Markers

### Custom Matplotlib Marker

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import numpy as np

def draw_bicolor_marker(ax, x, y, top_color, bottom_color, radius=3,
                        edge_color='white', edge_width=1.5):
    """
    Draw a bi-colored circle marker with upper and lower semi-circles.

    Args:
        ax: Matplotlib axes
        x, y: Center position
        top_color: Color for upper semi-circle (vertical position)
        bottom_color: Color for lower semi-circle (horizontal position)
        radius: Marker radius
        edge_color: Border color
        edge_width: Border width
    """
    # Upper semi-circle (vertical/attacking position)
    top_wedge = mpatches.Wedge(
        (x, y), radius,
        theta1=0, theta2=180,  # Upper half
        facecolor=top_color,
        edgecolor=edge_color,
        linewidth=edge_width
    )

    # Lower semi-circle (horizontal/left-right position)
    bottom_wedge = mpatches.Wedge(
        (x, y), radius,
        theta1=180, theta2=360,  # Lower half
        facecolor=bottom_color,
        edgecolor=edge_color,
        linewidth=edge_width
    )

    ax.add_patch(top_wedge)
    ax.add_patch(bottom_wedge)

    return top_wedge, bottom_wedge


def draw_player_marker(ax, x, y, v_bucket, h_bucket, player_num=None,
                       radius=3, show_number=True):
    """
    Draw complete player marker with optional jersey number.
    """
    top_color = VERTICAL_COLORS[v_bucket]
    bottom_color = HORIZONTAL_COLORS[h_bucket]

    draw_bicolor_marker(ax, x, y, top_color, bottom_color, radius)

    if show_number and player_num is not None:
        ax.text(x, y, str(player_num),
                ha='center', va='center',
                fontsize=8, fontweight='bold', color='white')
```

---

## 5. Pitch Drawing

```python
def draw_pitch(ax, pitch_length=105, pitch_width=68,
               line_color='white', pitch_color='#1a472a'):
    """
    Draw a football pitch on the given axes.
    """
    ax.set_facecolor(pitch_color)

    # Pitch outline
    ax.plot([0, 0], [0, pitch_width], color=line_color, linewidth=2)
    ax.plot([0, pitch_length], [pitch_width, pitch_width], color=line_color, linewidth=2)
    ax.plot([pitch_length, pitch_length], [pitch_width, 0], color=line_color, linewidth=2)
    ax.plot([pitch_length, 0], [0, 0], color=line_color, linewidth=2)

    # Halfway line
    ax.plot([pitch_length/2, pitch_length/2], [0, pitch_width],
            color=line_color, linewidth=2)

    # Center circle
    center_circle = plt.Circle((pitch_length/2, pitch_width/2), 9.15,
                                 fill=False, color=line_color, linewidth=2)
    ax.add_patch(center_circle)

    # Center spot
    ax.scatter(pitch_length/2, pitch_width/2, color=line_color, s=20, zorder=5)

    # Penalty areas (left)
    ax.plot([0, 16.5], [pitch_width/2 - 20.15, pitch_width/2 - 20.15],
            color=line_color, linewidth=2)
    ax.plot([16.5, 16.5], [pitch_width/2 - 20.15, pitch_width/2 + 20.15],
            color=line_color, linewidth=2)
    ax.plot([16.5, 0], [pitch_width/2 + 20.15, pitch_width/2 + 20.15],
            color=line_color, linewidth=2)

    # Penalty areas (right)
    ax.plot([pitch_length, pitch_length - 16.5],
            [pitch_width/2 - 20.15, pitch_width/2 - 20.15],
            color=line_color, linewidth=2)
    ax.plot([pitch_length - 16.5, pitch_length - 16.5],
            [pitch_width/2 - 20.15, pitch_width/2 + 20.15],
            color=line_color, linewidth=2)
    ax.plot([pitch_length - 16.5, pitch_length],
            [pitch_width/2 + 20.15, pitch_width/2 + 20.15],
            color=line_color, linewidth=2)

    # Goal areas
    ax.plot([0, 5.5], [pitch_width/2 - 9.16, pitch_width/2 - 9.16],
            color=line_color, linewidth=2)
    ax.plot([5.5, 5.5], [pitch_width/2 - 9.16, pitch_width/2 + 9.16],
            color=line_color, linewidth=2)
    ax.plot([5.5, 0], [pitch_width/2 + 9.16, pitch_width/2 + 9.16],
            color=line_color, linewidth=2)

    ax.plot([pitch_length, pitch_length - 5.5],
            [pitch_width/2 - 9.16, pitch_width/2 - 9.16],
            color=line_color, linewidth=2)
    ax.plot([pitch_length - 5.5, pitch_length - 5.5],
            [pitch_width/2 - 9.16, pitch_width/2 + 9.16],
            color=line_color, linewidth=2)
    ax.plot([pitch_length - 5.5, pitch_length],
            [pitch_width/2 + 9.16, pitch_width/2 + 9.16],
            color=line_color, linewidth=2)

    # Goals
    ax.plot([0, -2], [pitch_width/2 - 3.66, pitch_width/2 - 3.66],
            color=line_color, linewidth=3)
    ax.plot([-2, -2], [pitch_width/2 - 3.66, pitch_width/2 + 3.66],
            color=line_color, linewidth=3)
    ax.plot([-2, 0], [pitch_width/2 + 3.66, pitch_width/2 + 3.66],
            color=line_color, linewidth=3)

    ax.plot([pitch_length, pitch_length + 2],
            [pitch_width/2 - 3.66, pitch_width/2 - 3.66],
            color=line_color, linewidth=3)
    ax.plot([pitch_length + 2, pitch_length + 2],
            [pitch_width/2 - 3.66, pitch_width/2 + 3.66],
            color=line_color, linewidth=3)
    ax.plot([pitch_length + 2, pitch_length],
            [pitch_width/2 + 3.66, pitch_width/2 + 3.66],
            color=line_color, linewidth=3)

    ax.set_xlim(-5, pitch_length + 5)
    ax.set_ylim(-5, pitch_width + 5)
    ax.set_aspect('equal')
    ax.axis('off')

    return ax
```

---

## 6. Formation Detection

```python
def detect_formation(team_positions):
    """
    Detect formation from player positions.

    Returns: String like "4-3-3", "4-4-2", etc.
    """
    # Get x positions (excluding goalkeeper)
    outfield_x = [pos[0] for pid, pos in team_positions.items() if pid != 1]

    if len(outfield_x) != 10:
        return "Unknown"

    # Sort and group by x-coordinate clusters
    sorted_x = sorted(outfield_x)

    # Use k-means style clustering to find defensive lines
    # Simple approach: count players in x-ranges

    # Normalize to 0-1 scale
    min_x, max_x = min(sorted_x), max(sorted_x)
    normalized = [(x - min_x) / (max_x - min_x + 0.001) for x in sorted_x]

    # Count players in thirds
    def_count = sum(1 for x in normalized if x < 0.33)
    mid_count = sum(1 for x in normalized if 0.33 <= x < 0.66)
    fwd_count = sum(1 for x in normalized if x >= 0.66)

    # Common formations lookup
    formations = {
        (4, 3, 3): "4-3-3",
        (4, 4, 2): "4-4-2",
        (4, 5, 1): "4-5-1",
        (3, 5, 2): "3-5-2",
        (3, 4, 3): "3-4-3",
        (5, 3, 2): "5-3-2",
        (5, 4, 1): "5-4-1",
        (4, 2, 4): "4-2-3-1",  # Simplified
    }

    key = (def_count, mid_count, fwd_count)
    return formations.get(key, f"{def_count}-{mid_count}-{fwd_count}")
```

---

## 7. Complete Static Frame Visualization

```python
def visualize_frame(frame_data, home_team_name="Home", away_team_name="Away",
                    figsize=(20, 10)):
    """
    Create complete shape graph visualization for one frame.

    Args:
        frame_data: Dict with 'home' and 'away' player positions
        home_team_name: Name for home team
        away_team_name: Name for away team

    Returns:
        matplotlib Figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Draw pitches
    draw_pitch(ax1)
    draw_pitch(ax2)

    for ax, team_key, team_name in [(ax1, 'home', home_team_name),
                                     (ax2, 'away', away_team_name)]:
        positions = frame_data[team_key]

        # Classify positions
        v_buckets = classify_team_vertical(positions)
        h_buckets = classify_team_horizontal(positions)

        # Detect formation
        formation = detect_formation(positions)

        # Draw players
        for pid, (x, y) in positions.items():
            draw_player_marker(
                ax, x, y,
                v_buckets[pid], h_buckets[pid],
                player_num=pid,
                radius=2.5
            )

        # Add formation label
        ax.set_title(f"{team_name}\n{formation}",
                    fontsize=16, fontweight='bold', color='white',
                    pad=20)

    fig.patch.set_facecolor('#0d1117')
    plt.tight_layout()

    return fig


# Example usage
if __name__ == "__main__":
    # Sample frame data
    frame_data = {
        'home': {
            1: (5, 34),    # GK
            2: (20, 10),   # RB
            3: (18, 25),   # CB
            4: (18, 43),   # CB
            5: (20, 58),   # LB
            6: (40, 20),   # CM
            7: (45, 34),   # CM
            8: (40, 48),   # CM
            9: (65, 15),   # RW
            10: (70, 34),  # ST
            11: (65, 53),  # LW
        },
        'away': {
            1: (100, 34),
            2: (85, 58),
            3: (83, 43),
            4: (83, 25),
            5: (85, 10),
            6: (65, 48),
            7: (60, 34),
            8: (65, 20),
            9: (40, 40),
            10: (35, 28),
            11: (45, 34),
        }
    }

    fig = visualize_frame(frame_data, "Argentina", "France")
    fig.savefig('shape_graph_frame.png', dpi=150,
                facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.show()
```

---

## 8. Animation Pipeline

```python
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation, FFMpegWriter

class ShapeGraphAnimator:
    def __init__(self, tracking_df, home_name="Home", away_name="Away",
                 fps=25, pitch_length=105, pitch_width=68):
        self.df = tracking_df
        self.home_name = home_name
        self.away_name = away_name
        self.fps = fps
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

        # Parse player columns
        self.home_players = self._get_player_columns('home')
        self.away_players = self._get_player_columns('away')

    def _get_player_columns(self, team_prefix):
        """Extract player column indices from DataFrame."""
        players = []
        for i in range(1, 12):
            x_col = f'{team_prefix}_{i}_x'
            y_col = f'{team_prefix}_{i}_y'
            if x_col in self.df.columns:
                players.append(i)
        return players

    def _get_frame_positions(self, frame_idx, team_prefix):
        """Get player positions for a specific frame."""
        row = self.df.iloc[frame_idx]
        positions = {}

        players = self.home_players if team_prefix == 'home' else self.away_players
        for i in players:
            x = row[f'{team_prefix}_{i}_x']
            y = row[f'{team_prefix}_{i}_y']
            if not (np.isnan(x) or np.isnan(y)):
                positions[i] = (x, y)

        return positions

    def create_animation(self, start_frame=0, end_frame=None,
                        output_path='shape_graph.mp4'):
        """Create and save animation."""
        if end_frame is None:
            end_frame = len(self.df)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        fig.patch.set_facecolor('#0d1117')

        def init():
            draw_pitch(ax1)
            draw_pitch(ax2)
            return []

        def update(frame_idx):
            # Clear previous markers (keep pitch)
            for ax in [ax1, ax2]:
                # Remove all patches except pitch elements
                while len(ax.patches) > 10:  # Keep base pitch patches
                    ax.patches[-1].remove()
                # Remove text annotations
                for txt in ax.texts[:]:
                    txt.remove()

            # Get positions for this frame
            home_pos = self._get_frame_positions(frame_idx, 'home')
            away_pos = self._get_frame_positions(frame_idx, 'away')

            # Draw home team
            if home_pos:
                v_buckets = classify_team_vertical(home_pos)
                h_buckets = classify_team_horizontal(home_pos)
                formation = detect_formation(home_pos)

                for pid, (x, y) in home_pos.items():
                    draw_player_marker(ax1, x, y, v_buckets[pid],
                                      h_buckets[pid], pid, radius=2.5)

                ax1.set_title(f"{self.home_name}\n{formation}",
                            fontsize=14, fontweight='bold', color='white')

            # Draw away team
            if away_pos:
                v_buckets = classify_team_vertical(away_pos)
                h_buckets = classify_team_horizontal(away_pos)
                formation = detect_formation(away_pos)

                for pid, (x, y) in away_pos.items():
                    draw_player_marker(ax2, x, y, v_buckets[pid],
                                      h_buckets[pid], pid, radius=2.5)

                ax2.set_title(f"{self.away_name}\n{formation}",
                            fontsize=14, fontweight='bold', color='white')

            # Add timestamp
            timestamp = self.df.iloc[frame_idx].get('timestamp', frame_idx/self.fps)
            fig.suptitle(f"Time: {timestamp:.1f}s",
                        fontsize=12, color='white', y=0.02)

            return []

        frames = range(start_frame, end_frame)
        anim = FuncAnimation(fig, update, frames=frames,
                           init_func=init, blit=False,
                           interval=1000/self.fps)

        # Save animation
        if output_path.endswith('.mp4'):
            writer = FFMpegWriter(fps=self.fps, bitrate=5000)
            anim.save(output_path, writer=writer,
                     facecolor=fig.get_facecolor())
        elif output_path.endswith('.gif'):
            anim.save(output_path, writer='pillow', fps=self.fps)

        plt.close(fig)
        print(f"Animation saved to {output_path}")
        return anim


# Usage
if __name__ == "__main__":
    # Load or generate tracking data
    df = generate_synthetic_tracking(n_frames=250)

    animator = ShapeGraphAnimator(df, "Argentina", "France", fps=25)
    animator.create_animation(
        start_frame=0,
        end_frame=100,
        output_path='shape_graph_demo.mp4'
    )
```

---

## 9. File Structure

```
shape-graph-animation/
├── venv/                      # Virtual environment
├── data/
│   ├── pff/                   # PFF FC downloaded data
│   │   ├── tracking/
│   │   ├── metadata/
│   │   └── rosters/
│   └── synthetic/             # Fallback test data
├── src/
│   ├── __init__.py
│   ├── data_loader.py         # Data loading utilities
│   ├── position_classifier.py # Classification algorithms
│   ├── colors.py              # Color definitions
│   ├── markers.py             # Bi-colored marker drawing
│   ├── pitch.py               # Pitch drawing
│   ├── formation.py           # Formation detection
│   ├── visualize.py           # Static frame visualization
│   └── animate.py             # Animation pipeline
├── outputs/
│   ├── frames/                # Exported frame images
│   └── videos/                # Exported animations
├── test_data_load.py          # Quick data test
├── generate_static.py         # Generate single frame
├── generate_animation.py      # Generate full animation
├── requirements.txt
└── IMPLEMENTATION_PLAN.md     # This file
```

---

## 10. Build Order Checklist

### Day 1: Data & Static Visualization

| Step | Task | Time | Done When |
|------|------|------|-----------|
| 1 | Set up project structure | 10 min | Folders exist, venv activated |
| 2 | Install dependencies | 5 min | `pip list` shows kloppy, matplotlib |
| 3 | Download PFF data OR generate synthetic | 15 min | CSV/JSON files in data/ folder |
| 4 | Load data, print first frame | 15 min | Can see player x,y coordinates |
| 5 | Implement vertical classification | 20 min | Unit test passes |
| 6 | Implement horizontal classification | 20 min | Unit test passes |
| 7 | Draw basic pitch | 20 min | Pitch image saves correctly |
| 8 | Implement bi-colored markers | 30 min | Single marker renders correctly |
| 9 | Combine: single frame with all players | 30 min | Full frame image with colors |
| 10 | Add formation detection | 20 min | Formation label appears |
| 11 | Create dual-pitch layout | 20 min | Both teams visible side by side |

**Day 1 Milestone:** Static PNG with both teams, colored markers, formation labels

### Day 2: Animation & Polish

| Step | Task | Time | Done When |
|------|------|------|-----------|
| 12 | Set up animation framework | 30 min | Empty animation loop runs |
| 13 | Integrate frame updates | 45 min | Markers move between frames |
| 14 | Add timestamp display | 10 min | Time shows in corner |
| 15 | Export to MP4 | 30 min | Video file plays correctly |
| 16 | Tune colors/sizes | 30 min | Matches reference aesthetics |
| 17 | Test with real PFF data | 30 min | Full match segment works |
| 18 | Create GIF export option | 15 min | GIF generates successfully |

**Day 2 Milestone:** 30-second MP4 animation of a real match

---

## 11. Troubleshooting

### "ModuleNotFoundError: No module named 'kloppy'"
```bash
pip install kloppy
# or if in wrong environment:
source venv/bin/activate
pip install kloppy
```

### "FFmpeg not found"
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Windows: Download from ffmpeg.org and add to PATH
```

### "Data file not found"
- Use synthetic data generator as fallback
- Check file paths are correct
- Ensure .bz2 files are not corrupted

### "Animation too slow"
```python
# Reduce frame rate
animator = ShapeGraphAnimator(df, fps=10)

# Or render fewer frames
animator.create_animation(start_frame=0, end_frame=50)

# Or use blit=True for faster rendering (may cause artifacts)
```

### "Colors look wrong"
- Check color hex codes are correct
- Ensure bucket classification returns 0-4
- Verify VERTICAL_COLORS and HORIZONTAL_COLORS dictionaries

### "Formation detection incorrect"
- Formation detection is approximate
- Works best with clear positional separation
- Manual override available if needed

---

## 12. Dependencies (requirements.txt)

```
kloppy>=3.18.0
matplotlib>=3.7.0
numpy>=1.24.0
pandas>=2.0.0
ffmpeg-python>=0.2.0
```

---

## Sources

- [PFF FC World Cup 2022 Data Blog](https://www.blog.fc.pff.com/blog/enhanced-2022-world-cup-dataset)
- [Kloppy PFF Documentation](https://kloppy.pysport.org/user-guide/loading-data/pff/)
- [Shape Graphs Paper (Nature)](https://www.nature.com/articles/s44260-025-00047-x)
- [Kloppy GitHub](https://github.com/PySport/kloppy)

---

*Generated by Claude Code - Football Shape Graph Animation Plan*
