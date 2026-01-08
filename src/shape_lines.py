"""Convex hull shape lines for team visualization."""

import numpy as np
from scipy.spatial import ConvexHull
import matplotlib.patches as mpatches

# Team colors with transparency
HOME_COLOR = '#3498db'  # Blue
AWAY_COLOR = '#e74c3c'  # Red


def identify_goalkeeper(positions, is_home=True):
    """
    Identify goalkeeper as player closest to own goal line.

    Args:
        positions: Dict of {player_id: (x, y)}
        is_home: True if home team (attacking left to right)

    Returns:
        Player ID of likely goalkeeper
    """
    if not positions:
        return None

    # Home team: GK near x=0, Away team: GK near x=105
    goal_x = 0 if is_home else 105

    gk_id = None
    min_dist = float('inf')

    for pid, (x, y) in positions.items():
        dist = abs(x - goal_x)
        if dist < min_dist:
            min_dist = dist
            gk_id = pid

    return gk_id


def get_outfield_positions(positions: dict, is_home: bool = True) -> dict:
    """
    Extract outfield player positions (excluding goalkeeper).

    Args:
        positions: Dict of {player_id: (x, y)} for all 11 players
        is_home: True if home team (GK near x=0), False for away (GK near x=105)

    Returns:
        Dict of {player_id: (x, y)} for 10 outfield players
    """
    if not positions:
        return {}

    gk_id = identify_goalkeeper(positions, is_home)
    return {pid: pos for pid, pos in positions.items() if pid != gk_id}


def compute_convex_hull(positions, exclude_gk=True, is_home=True):
    """
    Compute convex hull of team positions.

    Args:
        positions: Dict of {player_id: (x, y)}
        exclude_gk: Whether to exclude goalkeeper
        is_home: True if home team

    Returns:
        List of (x, y) points forming hull polygon, or None if not enough points
    """
    if not positions:
        return None

    # Get outfield positions
    if exclude_gk:
        gk_id = identify_goalkeeper(positions, is_home)
        outfield = {pid: pos for pid, pos in positions.items() if pid != gk_id}
    else:
        outfield = positions

    if len(outfield) < 3:
        return None

    # Convert to array
    points = np.array(list(outfield.values()))

    try:
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        # Close the polygon
        hull_points = np.vstack([hull_points, hull_points[0]])
        return hull_points
    except Exception:
        return None


def draw_team_shape(ax, positions, is_home=True, fill_alpha=0.2, line_alpha=0.7):
    """
    Draw convex hull shape for a team.

    Args:
        ax: Matplotlib axes
        positions: Dict of {player_id: (x, y)}
        is_home: True if home team
        fill_alpha: Transparency for fill
        line_alpha: Transparency for lines

    Returns:
        Polygon patch if drawn, None otherwise
    """
    hull_points = compute_convex_hull(positions, exclude_gk=True, is_home=is_home)

    if hull_points is None:
        return None

    color = HOME_COLOR if is_home else AWAY_COLOR

    # Draw filled polygon
    polygon = mpatches.Polygon(
        hull_points,
        closed=True,
        facecolor=color,
        edgecolor=color,
        alpha=fill_alpha,
        linewidth=2,
        zorder=2  # Below player markers
    )
    ax.add_patch(polygon)

    # Draw lines with higher opacity
    ax.plot(hull_points[:, 0], hull_points[:, 1],
            color=color, linewidth=2, alpha=line_alpha, zorder=3)

    return polygon


def draw_both_team_shapes(ax, home_positions, away_positions):
    """
    Draw shapes for both teams on single pitch.

    Args:
        ax: Matplotlib axes
        home_positions: Home team positions
        away_positions: Away team positions
    """
    draw_team_shape(ax, home_positions, is_home=True)
    draw_team_shape(ax, away_positions, is_home=False)


if __name__ == "__main__":
    # Test with sample data
    import matplotlib.pyplot as plt
    import sys
    sys.path.insert(0, '.')
    from pitch import draw_pitch
    from markers import draw_player_marker
    from position_classifier import classify_team_vertical, classify_team_horizontal
    from colors import BACKGROUND_COLOR

    # Sample positions (4-3-3)
    home_positions = {
        1: (5, 34),    # GK - should be excluded
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
    }

    away_positions = {
        1: (100, 34),  # GK - should be excluded
        2: (85, 58),   # LB
        3: (83, 43),   # CB
        4: (83, 25),   # CB
        5: (85, 10),   # RB
        6: (65, 48),   # LM
        7: (60, 34),   # CM
        8: (65, 20),   # RM
        9: (40, 40),   # ST
        10: (35, 28),  # ST
        11: (45, 34),  # AM
    }

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    draw_pitch(ax)

    # Draw shapes FIRST (lower zorder)
    draw_team_shape(ax, home_positions, is_home=True)
    draw_team_shape(ax, away_positions, is_home=False)

    # Draw players SECOND (higher zorder)
    for positions, is_home in [(home_positions, True), (away_positions, False)]:
        v_buckets = classify_team_vertical(positions)
        h_buckets = classify_team_horizontal(positions)
        for pid, (x, y) in positions.items():
            draw_player_marker(ax, x, y, v_buckets.get(pid, 2), h_buckets.get(pid, 2),
                             player_num=pid, radius=3)

    ax.set_title("Team Shapes (Convex Hull)", color='white', fontsize=16, pad=15)
    fig.tight_layout()
    fig.savefig('outputs/frames/test_shape_lines.png', dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
    print("Saved: outputs/frames/test_shape_lines.png")
    plt.close()
