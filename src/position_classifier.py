"""Position classification algorithms for shape graph."""


def classify_vertical_position(player_x, team_x_positions, n_buckets=5):
    """
    Classify player's vertical (attacking) position relative to teammates.

    Args:
        player_x: Player's x-coordinate (attacking direction)
        team_x_positions: List of all team x-coordinates
        n_buckets: Number of classification buckets

    Returns:
        int: 0 (Back/Defensive) to 4 (Front/Attacking)
    """
    sorted_positions = sorted(team_x_positions)
    rank = sorted_positions.index(player_x)
    bucket = int(rank / len(sorted_positions) * n_buckets)
    return min(bucket, n_buckets - 1)


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


def classify_team_vertical(team_positions):
    """
    Classify all players' vertical positions at once.

    Args:
        team_positions: Dict of {player_id: (x, y)}

    Returns:
        Dict of {player_id: vertical_bucket (0-4)}
    """
    if not team_positions:
        return {}

    # Extract x positions
    x_values = list(set(pos[0] for pos in team_positions.values()))
    sorted_x = sorted(x_values)

    result = {}
    for pid, (x, y) in team_positions.items():
        rank = sorted_x.index(x)
        bucket = int(rank / len(sorted_x) * 5)
        result[pid] = min(bucket, 4)

    return result


def classify_team_horizontal(team_positions):
    """
    Classify all players' horizontal positions at once.

    Args:
        team_positions: Dict of {player_id: (x, y)}

    Returns:
        Dict of {player_id: horizontal_bucket (0-4)}
    """
    if not team_positions:
        return {}

    # Extract y positions
    y_values = list(set(pos[1] for pos in team_positions.values()))
    sorted_y = sorted(y_values)

    result = {}
    for pid, (x, y) in team_positions.items():
        rank = sorted_y.index(y)
        bucket = int(rank / len(sorted_y) * 5)
        result[pid] = min(bucket, 4)

    return result


def detect_formation(team_positions):
    """
    Detect formation from player positions.

    Args:
        team_positions: Dict of {player_id: (x, y)}

    Returns:
        String like "4-3-3", "4-4-2", etc.
    """
    if len(team_positions) < 10:
        return "Unknown"

    # Get all x positions
    x_positions = [pos[0] for pos in team_positions.values()]

    # Sort and exclude goalkeeper (usually furthest back)
    sorted_x = sorted(x_positions)
    outfield_x = sorted_x[1:]  # Exclude first (GK assumed)

    if len(outfield_x) != 10:
        return "Unknown"

    # Normalize to 0-1 scale
    min_x, max_x = min(outfield_x), max(outfield_x)
    range_x = max_x - min_x
    if range_x < 0.001:
        range_x = 1

    normalized = [(x - min_x) / range_x for x in outfield_x]

    # Count players in thirds (defense, midfield, attack)
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
        (4, 2, 4): "4-2-3-1",
        (3, 3, 4): "3-4-3",
        (2, 5, 3): "4-2-3-1",
    }

    key = (def_count, mid_count, fwd_count)
    return formations.get(key, f"{def_count}-{mid_count}-{fwd_count}")


if __name__ == "__main__":
    # Test with sample data
    test_positions = {
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
    }

    v_buckets = classify_team_vertical(test_positions)
    h_buckets = classify_team_horizontal(test_positions)
    formation = detect_formation(test_positions)

    print("Position Classification Test")
    print("=" * 40)
    print(f"Formation: {formation}")
    print()
    print("Player | Vertical | Horizontal")
    print("-" * 40)
    for pid in sorted(test_positions.keys()):
        print(f"  {pid:2d}   |    {v_buckets[pid]}     |     {h_buckets[pid]}")
