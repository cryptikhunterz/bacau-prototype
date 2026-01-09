"""
Pitch control calculation module using Spearman 2017 influence model.

Computes team control probability at each grid point based on player
positions and velocities. Control is determined by time-to-intercept
with sigmoid influence transformation.

Used by app.py to render pitch control heatmap overlay.
"""

import numpy as np

# Constants
REACTION_TIME = 0.7   # Seconds before player can react
MAX_SPEED = 13.0      # Maximum player speed in m/s
GRID_RESOLUTION = 2   # Grid spacing in meters
PITCH_LENGTH = 105    # Standard pitch length in meters
PITCH_WIDTH = 68      # Standard pitch width in meters


def create_pitch_grid(
    pitch_length: float = PITCH_LENGTH,
    pitch_width: float = PITCH_WIDTH,
    resolution: float = GRID_RESOLUTION
) -> tuple:
    """
    Generate grid points for pitch control calculation.

    Args:
        pitch_length: Pitch length in meters (default 105)
        pitch_width: Pitch width in meters (default 68)
        resolution: Grid spacing in meters (default 2)

    Returns:
        (x_grid, y_grid): 2D numpy arrays of grid coordinates
    """
    x_points = np.arange(0, pitch_length + resolution, resolution, dtype=float)
    y_points = np.arange(0, pitch_width + resolution, resolution, dtype=float)
    x_grid, y_grid = np.meshgrid(x_points, y_points)
    return x_grid, y_grid


def time_to_intercept(
    player_pos: tuple,
    player_vel: tuple,
    target_pos: tuple,
    reaction_time: float = REACTION_TIME,
    max_speed: float = MAX_SPEED
) -> float:
    """
    Calculate time for player to reach target position.

    Uses a simplified model: time = reaction_time + distance / max_speed
    Velocity is used to adjust effective distance based on movement direction.

    Args:
        player_pos: (x, y) player position in meters
        player_vel: (vx, vy) player velocity in m/s
        target_pos: (x, y) target grid point in meters
        reaction_time: Time before player can react (default 0.7s)
        max_speed: Maximum player speed (default 13.0 m/s)

    Returns:
        Time in seconds to reach target
    """
    # Direction vector from player to target
    dx = target_pos[0] - player_pos[0]
    dy = target_pos[1] - player_pos[1]
    distance = np.sqrt(dx**2 + dy**2)

    if distance < 0.1:
        # Player essentially at target
        return reaction_time

    # Velocity component toward target (positive = moving toward)
    if player_vel is not None and (player_vel[0] != 0 or player_vel[1] != 0):
        vel_toward = (player_vel[0] * dx + player_vel[1] * dy) / distance
    else:
        vel_toward = 0.0

    # Effective speed (current velocity component + acceleration to max)
    # Simple model: assume player can reach max_speed
    effective_speed = max_speed

    # Adjust distance for current velocity direction
    # If moving toward target, reduce effective distance
    velocity_adjustment = vel_toward * reaction_time
    adjusted_distance = max(0, distance - velocity_adjustment)

    # Time = reaction + travel
    travel_time = adjusted_distance / effective_speed
    return reaction_time + travel_time


def player_influence(
    tti: float,
    sigma: float = 0.5
) -> float:
    """
    Convert time-to-intercept to influence value using sigmoid.

    Influence decreases with time-to-intercept. Players closer to a
    point have higher influence.

    Args:
        tti: Time-to-intercept in seconds
        sigma: Sigmoid steepness parameter (lower = steeper)

    Returns:
        Influence value between 0 and 1
    """
    # Sigmoid: 1 / (1 + exp(tti / sigma))
    # Lower tti = higher influence
    return 1.0 / (1.0 + np.exp(tti / sigma))


def compute_pitch_control(
    home_positions: dict,
    away_positions: dict,
    home_velocities: dict = None,
    away_velocities: dict = None
) -> np.ndarray:
    """
    Compute pitch control for each grid point.

    Args:
        home_positions: {player_id: (x, y)} home team positions in meters
        away_positions: {player_id: (x, y)} away team positions in meters
        home_velocities: {player_id: (vx, vy)} home velocities (optional)
        away_velocities: {player_id: (vx, vy)} away velocities (optional)

    Returns:
        2D numpy array of control values:
        - 0.0 = full away control
        - 0.5 = contested
        - 1.0 = full home control
    """
    # Default to zero velocities if not provided
    if home_velocities is None:
        home_velocities = {pid: (0.0, 0.0) for pid in home_positions}
    if away_velocities is None:
        away_velocities = {pid: (0.0, 0.0) for pid in away_positions}

    # Generate grid
    x_grid, y_grid = create_pitch_grid()
    control = np.zeros_like(x_grid)

    # Iterate over grid points
    for i in range(x_grid.shape[0]):
        for j in range(x_grid.shape[1]):
            target = (x_grid[i, j], y_grid[i, j])

            # Sum home team influence
            home_influence = 0.0
            for pid, pos in home_positions.items():
                vel = home_velocities.get(pid, (0.0, 0.0))
                tti = time_to_intercept(pos, vel, target)
                home_influence += player_influence(tti)

            # Sum away team influence
            away_influence = 0.0
            for pid, pos in away_positions.items():
                vel = away_velocities.get(pid, (0.0, 0.0))
                tti = time_to_intercept(pos, vel, target)
                away_influence += player_influence(tti)

            # Calculate control ratio
            total_influence = home_influence + away_influence
            if total_influence > 0:
                control[i, j] = home_influence / total_influence
            else:
                control[i, j] = 0.5  # No influence = contested

    return control


if __name__ == "__main__":
    """Module tests for pitch control functions."""

    def test_grid_generation():
        """Test 1: Grid generation returns correct shape and bounds."""
        x_grid, y_grid = create_pitch_grid()

        # Check shape (should be approximately 34×53)
        assert x_grid.shape[0] >= 30, f"Grid too small: {x_grid.shape}"
        assert x_grid.shape[1] >= 50, f"Grid too small: {x_grid.shape}"

        # Check bounds
        assert x_grid.min() == 0, "X should start at 0"
        assert y_grid.min() == 0, "Y should start at 0"
        assert x_grid.max() >= PITCH_LENGTH - GRID_RESOLUTION, "X should cover pitch"
        assert y_grid.max() >= PITCH_WIDTH - GRID_RESOLUTION, "Y should cover pitch"

        print(f"✅ Test 1: Grid generation passed ({x_grid.shape})")

    def test_time_to_intercept():
        """Test 2: Time-to-intercept calculation."""
        # Player at (0, 0), target at (13, 0) = 13m away
        # At max_speed 13 m/s, travel time = 1s
        # Total = reaction (0.7s) + travel (1s) = 1.7s
        player_pos = (0.0, 0.0)
        player_vel = (0.0, 0.0)
        target_pos = (13.0, 0.0)

        tti = time_to_intercept(player_pos, player_vel, target_pos)
        expected = 0.7 + 1.0  # reaction + travel

        assert abs(tti - expected) < 0.01, f"Expected {expected}, got {tti}"
        print("✅ Test 2: Time-to-intercept passed")

    def test_player_influence():
        """Test 3: Player influence sigmoid behavior."""
        # Low TTI = high influence
        influence_close = player_influence(0.7)
        influence_far = player_influence(3.0)

        assert influence_close > influence_far, "Closer should have higher influence"
        assert 0 < influence_close < 1, "Influence should be between 0 and 1"
        assert 0 < influence_far < 1, "Influence should be between 0 and 1"

        print(f"✅ Test 3: Player influence passed (close={influence_close:.3f}, far={influence_far:.3f})")

    def test_pitch_control_simple():
        """Test 4: Pitch control with simple scenario."""
        # Home player at (20, 34), away player at (80, 34)
        # Point at (20, 34) should be home controlled
        # Point at (80, 34) should be away controlled
        # Point at (52.5, 34) should be contested

        home_positions = {1: (20.0, 34.0)}
        away_positions = {1: (80.0, 34.0)}

        control = compute_pitch_control(home_positions, away_positions)

        # Find indices for test points (approximate)
        home_idx = (17, 10)  # Near (20, 34)
        away_idx = (17, 40)  # Near (80, 34)
        mid_idx = (17, 26)   # Near (52, 34)

        home_control = control[home_idx]
        away_control = control[away_idx]
        mid_control = control[mid_idx]

        assert home_control > 0.7, f"Home area should be home controlled: {home_control}"
        assert away_control < 0.3, f"Away area should be away controlled: {away_control}"
        assert 0.3 < mid_control < 0.7, f"Mid area should be contested: {mid_control}"

        print(f"✅ Test 4: Pitch control passed (home={home_control:.2f}, mid={mid_control:.2f}, away={away_control:.2f})")

    def test_pitch_control_with_velocities():
        """Test 5: Pitch control with player velocities."""
        # Two players equidistant from center
        # Home player moving toward center, away moving away
        # Center should favor home team

        home_positions = {1: (30.0, 34.0)}
        away_positions = {1: (75.0, 34.0)}

        # Home moving right (toward center), away moving right (away from center)
        home_velocities = {1: (10.0, 0.0)}
        away_velocities = {1: (10.0, 0.0)}

        control = compute_pitch_control(
            home_positions, away_positions,
            home_velocities, away_velocities
        )

        # Center should slightly favor home due to velocity direction
        mid_idx = (17, 26)  # Near (52, 34)
        mid_control = control[mid_idx]

        # Home is closer and moving toward, should have slight advantage
        assert mid_control > 0.45, f"Home should have slight advantage: {mid_control}"

        print(f"✅ Test 5: Velocity-adjusted control passed (mid={mid_control:.3f})")

    # Run all tests
    print("\n" + "=" * 50)
    print("Running pitch control module tests...")
    print("=" * 50 + "\n")

    test_grid_generation()
    test_time_to_intercept()
    test_player_influence()
    test_pitch_control_simple()
    test_pitch_control_with_velocities()

    print("\n" + "=" * 50)
    print("All tests passed! ✅")
    print("=" * 50)
