"""Main shape graph visualization module."""

import matplotlib.pyplot as plt

try:
    from .pitch import draw_pitch
    from .markers import draw_player_marker
    from .position_classifier import classify_team_vertical, classify_team_horizontal, detect_formation
    from .colors import BACKGROUND_COLOR
except ImportError:
    from pitch import draw_pitch
    from markers import draw_player_marker
    from position_classifier import classify_team_vertical, classify_team_horizontal, detect_formation
    from colors import BACKGROUND_COLOR


def visualize_frame(frame_data, home_team_name="Home", away_team_name="Away",
                    figsize=(20, 10), show_formation=True, marker_radius=2.5):
    """
    Create complete shape graph visualization for one frame.

    Args:
        frame_data: Dict with 'home' and 'away' player positions
                   Each is a dict of {player_id: (x, y)}
        home_team_name: Name for home team
        away_team_name: Name for away team
        figsize: Figure size tuple
        show_formation: Whether to detect and show formation
        marker_radius: Size of player markers

    Returns:
        matplotlib Figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Draw pitches
    draw_pitch(ax1)
    draw_pitch(ax2)

    for ax, team_key, team_name in [(ax1, 'home', home_team_name),
                                     (ax2, 'away', away_team_name)]:
        positions = frame_data.get(team_key, {})

        if not positions:
            ax.set_title(f"{team_name}\nNo Data",
                        fontsize=16, fontweight='bold', color='white', pad=20)
            continue

        # Classify positions
        v_buckets = classify_team_vertical(positions)
        h_buckets = classify_team_horizontal(positions)

        # Detect formation
        formation = detect_formation(positions) if show_formation else ""

        # Draw players
        for pid, (x, y) in positions.items():
            v_bucket = v_buckets.get(pid, 2)
            h_bucket = h_buckets.get(pid, 2)
            draw_player_marker(ax, x, y, v_bucket, h_bucket,
                             player_num=pid, radius=marker_radius)

        # Add team name and formation
        title = f"{team_name}"
        if formation:
            title += f"\n{formation}"
        ax.set_title(title, fontsize=16, fontweight='bold',
                    color='white', pad=20)

    fig.patch.set_facecolor(BACKGROUND_COLOR)
    plt.tight_layout()

    return fig


def visualize_single_team(team_positions, team_name="Team",
                         figsize=(12, 8), marker_radius=3):
    """
    Visualize a single team's shape graph.

    Args:
        team_positions: Dict of {player_id: (x, y)}
        team_name: Team name
        figsize: Figure size
        marker_radius: Size of player markers

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    draw_pitch(ax)

    if team_positions:
        v_buckets = classify_team_vertical(team_positions)
        h_buckets = classify_team_horizontal(team_positions)
        formation = detect_formation(team_positions)

        for pid, (x, y) in team_positions.items():
            draw_player_marker(ax, x, y,
                             v_buckets.get(pid, 2),
                             h_buckets.get(pid, 2),
                             player_num=pid,
                             radius=marker_radius)

        ax.set_title(f"{team_name}\n{formation}",
                    fontsize=18, fontweight='bold', color='white', pad=20)

    fig.patch.set_facecolor(BACKGROUND_COLOR)
    plt.tight_layout()

    return fig


if __name__ == "__main__":
    # Test with sample data
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
            1: (100, 34),  # GK
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
    }

    fig = visualize_frame(frame_data, "Argentina", "France")
    fig.savefig('outputs/frames/shape_graph_test.png', dpi=150,
                facecolor=fig.get_facecolor(), bbox_inches='tight')
    print("Saved: outputs/frames/shape_graph_test.png")
    plt.show()
