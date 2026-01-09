"""
Velocity calculation module for pitch control analysis.

Computes player velocities from frame-to-frame position deltas,
with EMA smoothing to handle noisy tracking data.

Used by the pitch control algorithm to calculate time-to-intercept
for influence-based spatial dominance visualization.
"""

import numpy as np

# Constants
MAX_SPEED = 13.0  # Maximum realistic player speed in m/s
EMA_ALPHA = 0.3   # EMA smoothing factor (higher = more responsive)
FPS = 29.97       # PFF tracking data frame rate


def calculate_velocities(
    current_positions: dict,
    previous_positions: dict,
    fps: float = FPS
) -> dict:
    """
    Calculate raw velocities from position deltas.

    Args:
        current_positions: {player_id: (x, y)} current frame
        previous_positions: {player_id: (x, y)} previous frame
        fps: Frames per second

    Returns:
        {player_id: (vx, vy)} velocities in m/s
    """
    velocities = {}
    time_delta = 1.0 / fps

    for player_id, current_pos in current_positions.items():
        if player_id in previous_positions:
            prev_pos = previous_positions[player_id]
            vx = (current_pos[0] - prev_pos[0]) / time_delta
            vy = (current_pos[1] - prev_pos[1]) / time_delta
            velocities[player_id] = (vx, vy)
        else:
            # New player, assume stationary
            velocities[player_id] = (0.0, 0.0)

    return velocities


def smooth_velocities(
    current_velocities: dict,
    previous_smoothed: dict,
    alpha: float = EMA_ALPHA
) -> dict:
    """
    Apply EMA smoothing to velocities.

    Args:
        current_velocities: Raw velocities this frame
        previous_smoothed: Smoothed velocities from previous frame
        alpha: EMA smoothing factor (higher = more responsive)

    Returns:
        {player_id: (vx, vy)} smoothed velocities
    """
    smoothed = {}

    # Process players in current frame
    for player_id, current_vel in current_velocities.items():
        if player_id in previous_smoothed:
            prev_vel = previous_smoothed[player_id]
            # EMA: smoothed = alpha * current + (1 - alpha) * previous
            vx = alpha * current_vel[0] + (1 - alpha) * prev_vel[0]
            vy = alpha * current_vel[1] + (1 - alpha) * prev_vel[1]
            smoothed[player_id] = (vx, vy)
        else:
            # New player, use current as initial
            smoothed[player_id] = current_vel

    # Decay velocities for missing players (still in previous but not current)
    for player_id, prev_vel in previous_smoothed.items():
        if player_id not in current_velocities:
            # Decay toward zero
            vx = (1 - alpha) * prev_vel[0]
            vy = (1 - alpha) * prev_vel[1]
            smoothed[player_id] = (vx, vy)

    return smoothed


def clamp_velocities(
    velocities: dict,
    max_speed: float = MAX_SPEED
) -> dict:
    """
    Clamp velocity magnitudes to maximum realistic speed.

    Args:
        velocities: {player_id: (vx, vy)}
        max_speed: Maximum allowed speed in m/s

    Returns:
        {player_id: (vx, vy)} clamped velocities
    """
    clamped = {}

    for player_id, vel in velocities.items():
        vx, vy = vel
        speed = np.sqrt(vx**2 + vy**2)

        if speed > max_speed:
            # Scale down proportionally, preserve direction
            scale = max_speed / speed
            clamped[player_id] = (vx * scale, vy * scale)
        else:
            clamped[player_id] = vel

    return clamped


if __name__ == "__main__":
    """Module tests for velocity calculation functions."""

    def test_basic_velocity_calculation():
        """Test 1: Basic velocity calculation from known positions."""
        prev = {"p1": (0.0, 0.0)}
        curr = {"p1": (1.0, 0.0)}  # Moved 1m in x direction

        velocities = calculate_velocities(curr, prev, fps=1.0)  # 1 fps for easy math

        assert abs(velocities["p1"][0] - 1.0) < 0.001, "Expected vx=1.0 m/s"
        assert abs(velocities["p1"][1] - 0.0) < 0.001, "Expected vy=0.0 m/s"
        print("✅ Test 1: Basic velocity calculation passed")

    def test_ema_smoothing():
        """Test 2: EMA smoothing reduces noise."""
        # Noisy velocity sequence
        prev_smoothed = {"p1": (5.0, 0.0)}
        current_raw = {"p1": (10.0, 0.0)}  # Sudden spike

        smoothed = smooth_velocities(current_raw, prev_smoothed, alpha=0.3)

        # With alpha=0.3: 0.3*10 + 0.7*5 = 3 + 3.5 = 6.5
        expected_vx = 0.3 * 10.0 + 0.7 * 5.0
        assert abs(smoothed["p1"][0] - expected_vx) < 0.001, f"Expected vx={expected_vx}"
        print("✅ Test 2: EMA smoothing passed")

    def test_velocity_clamping():
        """Test 3: Extreme velocities are clamped to MAX_SPEED."""
        velocities = {"p1": (20.0, 0.0)}  # 20 m/s exceeds MAX_SPEED

        clamped = clamp_velocities(velocities, max_speed=13.0)

        speed = np.sqrt(clamped["p1"][0]**2 + clamped["p1"][1]**2)
        assert abs(speed - 13.0) < 0.001, f"Expected speed=13.0, got {speed}"
        print("✅ Test 3: Velocity clamping passed")

    def test_missing_player_handling():
        """Test 4: Missing players handled correctly."""
        prev = {"p1": (0.0, 0.0), "p2": (10.0, 10.0)}
        curr = {"p1": (1.0, 0.0), "p3": (5.0, 5.0)}  # p2 missing, p3 new

        velocities = calculate_velocities(curr, prev, fps=1.0)

        # p1 should have velocity
        assert "p1" in velocities, "p1 should have velocity"
        # p3 is new, should have zero velocity
        assert velocities["p3"] == (0.0, 0.0), "New player should have zero velocity"
        # p2 not in current, should not be in output
        assert "p2" not in velocities, "Missing player should not be in output"
        print("✅ Test 4: Missing player handling passed")

    # Run all tests
    print("\n" + "=" * 50)
    print("Running velocity module tests...")
    print("=" * 50 + "\n")

    test_basic_velocity_calculation()
    test_ema_smoothing()
    test_velocity_clamping()
    test_missing_player_handling()

    print("\n" + "=" * 50)
    print("All tests passed! ✅")
    print("=" * 50)
