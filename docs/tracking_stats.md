# Tracking Stats Calculation

## Overview

The application computes real-time team shape statistics from player positions each frame.

## Statistics Computed

| Stat | Unit | Description |
|------|------|-------------|
| Area | m² | Convex hull area of outfield players |
| Compactness | m | Average distance from team centroid |
| Width | m | Lateral spread (max Y - min Y) |
| Depth | m | Vertical spread (max X - min X) |
| Ball Carrier | - | Closest player to ball |

## Area Calculation

Uses scipy ConvexHull to compute the area enclosed by outfield players:

```python
from scipy.spatial import ConvexHull
import numpy as np

def compute_area(positions):
    points = np.array(list(positions.values()))
    hull = ConvexHull(points)
    area = hull.volume  # In 2D, .volume returns area
    return area
```

**Note**: The goalkeeper is excluded from shape calculations:

```python
# Find goalkeeper (closest to own goal)
goal_x = 0 if is_home else 105
gk_id = min(positions.keys(), key=lambda pid: abs(positions[pid][0] - goal_x))
outfield = {pid: pos for pid, pos in positions.items() if pid != gk_id}
```

## Compactness Calculation

Average distance from each player to the team centroid:

```python
import math

def compute_compactness(positions):
    # Calculate centroid
    xs = [pos[0] for pos in positions.values()]
    ys = [pos[1] for pos in positions.values()]
    centroid = (np.mean(xs), np.mean(ys))
    
    # Average distance from centroid
    distances = [
        math.sqrt((x - centroid[0])**2 + (y - centroid[1])**2)
        for x, y in positions.values()
    ]
    return np.mean(distances)
```

**Interpretation:**
- **Low compactness** (~10-15m): Team is compact, pressing high
- **High compactness** (~20-30m): Team is spread out, stretched

## Width Calculation

Lateral spread across the pitch:

```python
def compute_width(positions):
    ys = [pos[1] for pos in positions.values()]
    return max(ys) - min(ys)
```

**Interpretation:**
- **Wide** (~50-60m): Team stretching the play
- **Narrow** (~20-30m): Team compact centrally

## Depth Calculation

Vertical spread from defense to attack:

```python
def compute_depth(positions):
    xs = [pos[0] for pos in positions.values()]
    return max(xs) - min(xs)
```

**Interpretation:**
- **Deep** (~40-50m): Team stretched vertically
- **Shallow** (~20-30m): Compact defensive block

## Ball Carrier Detection

Identifies the player closest to the ball:

```python
def get_ball_carrier(frame, pitch_length=105, pitch_width=68):
    ball_x = frame.ball_coordinates.x * pitch_length
    ball_y = frame.ball_coordinates.y * pitch_width
    
    closest_dist = float('inf')
    closest_player = None
    
    for player, data in frame.players_data.items():
        if data.coordinates:
            px = data.coordinates.x * pitch_length
            py = data.coordinates.y * pitch_width
            dist = math.sqrt((px - ball_x)**2 + (py - ball_y)**2)
            if dist < closest_dist:
                closest_dist = dist
                closest_player = player
    
    # Only count if within 5 meters
    if closest_dist < 5:
        return f"#{closest_player.jersey_no} {closest_player.name}"
    return None
```

## Possession Detection

Based on closest player to ball within 3 meters:

```python
def get_possession(frame):
    # Find closest player to ball
    closest_dist = float('inf')
    closest_team = None
    
    for player, data in frame.players_data.items():
        dist = distance_to_ball(data, frame.ball_coordinates)
        if dist < closest_dist:
            closest_dist = dist
            closest_team = player.team.ground
    
    # Must be within 3m for possession
    if closest_dist < 3:
        return closest_team  # 'home' or 'away'
    return 'contested'
```

## Full Stats Function

```python
def compute_team_stats(positions):
    """Compute team shape statistics from positions dict."""
    from scipy.spatial import ConvexHull
    
    if len(positions) < 3:
        return {'area': 0, 'compactness': 0, 'width': 0, 'depth': 0}
    
    points = np.array(list(positions.values()))
    xs, ys = points[:, 0], points[:, 1]
    
    centroid = (np.mean(xs), np.mean(ys))
    width = np.max(ys) - np.min(ys)
    depth = np.max(xs) - np.min(xs)
    
    distances = [math.sqrt((x - centroid[0])**2 + (y - centroid[1])**2) 
                 for x, y in positions.values()]
    compactness = np.mean(distances)
    
    try:
        hull = ConvexHull(points)
        area = hull.volume
    except:
        area = 0
    
    return {
        'area': area,
        'compactness': compactness,
        'width': width,
        'depth': depth,
        'centroid': centroid
    }
```

## UI Display

Stats are displayed in a two-column layout comparing home vs away:

```python
st.metric("Area", f"{home_stats['area']:.0f} m²")
st.metric("Compactness", f"{home_stats['compactness']:.1f} m")
st.metric("Width", f"{home_stats['width']:.1f} m")
st.metric("Depth", f"{home_stats['depth']:.1f} m")
```
