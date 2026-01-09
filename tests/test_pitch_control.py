"""
Comprehensive tests for pitch control module.

Tests:
1. Grid dimensions
2. Time to intercept - stationary player
3. Time to intercept - moving toward target
4. Time to intercept - moving away from target
5. Player influence range
6. Pitch control output range
7. Symmetric test
8. Dominant position test
9. Empty team handling
10. Integration with velocity module
11. Visual output test
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
from pitch_control import (
    create_pitch_grid,
    time_to_intercept,
    player_influence,
    compute_pitch_control,
    REACTION_TIME,
    MAX_SPEED,
    GRID_RESOLUTION,
    PITCH_LENGTH,
    PITCH_WIDTH
)
from velocity import calculate_velocities, smooth_velocities, clamp_velocities
from data_loader import generate_synthetic_tracking, get_frame_positions


def test_grid_dimensions():
    """
    TEST 1: Grid dimensions.
    Verify grid covers 0-105m (x) and 0-68m (y) at 2m resolution.
    """
    x_grid, y_grid = create_pitch_grid()

    # Check x range covers pitch length
    assert x_grid.min() == 0, f"X should start at 0, got {x_grid.min()}"
    assert x_grid.max() >= PITCH_LENGTH - GRID_RESOLUTION, \
        f"X should cover pitch, max={x_grid.max()}"

    # Check y range covers pitch width
    assert y_grid.min() == 0, f"Y should start at 0, got {y_grid.min()}"
    assert y_grid.max() >= PITCH_WIDTH - GRID_RESOLUTION, \
        f"Y should cover pitch, max={y_grid.max()}"

    # Check shape (should be approximately 35×54 for 2m resolution)
    expected_rows = int(PITCH_WIDTH / GRID_RESOLUTION) + 1
    expected_cols = int(PITCH_LENGTH / GRID_RESOLUTION) + 1
    assert abs(x_grid.shape[0] - expected_rows) <= 1, \
        f"Expected ~{expected_rows} rows, got {x_grid.shape[0]}"
    assert abs(x_grid.shape[1] - expected_cols) <= 1, \
        f"Expected ~{expected_cols} cols, got {x_grid.shape[1]}"

    print(f"PASS Test 1: Grid dimensions ({x_grid.shape}, x: 0-{x_grid.max()}, y: 0-{y_grid.max()})")
    return True


def test_tti_stationary():
    """
    TEST 2: Time to intercept - stationary player.
    Verify time = REACTION_TIME + distance/MAX_SPEED
    """
    player_pos = (50.0, 34.0)
    target_pos = (60.0, 34.0)
    player_vel = (0.0, 0.0)

    distance = 10.0  # 10 meters
    expected_time = REACTION_TIME + distance / MAX_SPEED

    tti = time_to_intercept(player_pos, player_vel, target_pos)

    assert abs(tti - expected_time) < 0.01, \
        f"Expected {expected_time:.3f}, got {tti:.3f}"

    print(f"PASS Test 2: TTI stationary (distance=10m, time={tti:.3f}s)")
    return True


def test_tti_moving_toward():
    """
    TEST 3: Time to intercept - moving toward target.
    Player moving toward target should have LESS time.
    """
    player_pos = (50.0, 34.0)
    target_pos = (60.0, 34.0)
    stationary_vel = (0.0, 0.0)
    toward_vel = (10.0, 0.0)  # Moving toward target

    tti_stationary = time_to_intercept(player_pos, stationary_vel, target_pos)
    tti_moving = time_to_intercept(player_pos, toward_vel, target_pos)

    assert tti_moving < tti_stationary, \
        f"Moving toward should be faster: moving={tti_moving:.3f} < stationary={tti_stationary:.3f}"

    print(f"PASS Test 3: TTI moving toward (stationary={tti_stationary:.3f}, moving={tti_moving:.3f})")
    return True


def test_tti_moving_away():
    """
    TEST 4: Time to intercept - moving away from target.
    Player moving away should have MORE time (or same if velocity not considered).
    """
    player_pos = (50.0, 34.0)
    target_pos = (60.0, 34.0)
    stationary_vel = (0.0, 0.0)
    away_vel = (-10.0, 0.0)  # Moving away from target

    tti_stationary = time_to_intercept(player_pos, stationary_vel, target_pos)
    tti_moving = time_to_intercept(player_pos, away_vel, target_pos)

    # Moving away should be same or more time
    assert tti_moving >= tti_stationary - 0.01, \
        f"Moving away should not be faster: moving={tti_moving:.3f}, stationary={tti_stationary:.3f}"

    print(f"PASS Test 4: TTI moving away (stationary={tti_stationary:.3f}, moving={tti_moving:.3f})")
    return True


def test_influence_range():
    """
    TEST 5: Player influence range.
    Verify influence returns values between 0 and 1, closer = higher.
    """
    # Test various TTI values
    tti_values = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    influences = [player_influence(tti) for tti in tti_values]

    # All should be between 0 and 1
    for tti, inf in zip(tti_values, influences):
        assert 0 <= inf <= 1, f"Influence {inf} out of range for TTI={tti}"

    # Should be monotonically decreasing
    for i in range(len(influences) - 1):
        assert influences[i] >= influences[i + 1], \
            f"Influence should decrease: {influences[i]} >= {influences[i + 1]}"

    print(f"PASS Test 5: Influence range (min={min(influences):.4f}, max={max(influences):.4f})")
    return True


def test_control_output_range():
    """
    TEST 6: Pitch control output range.
    Verify all values in control grid are between 0 and 1.
    (0 = full away, 0.5 = contested, 1 = full home)
    """
    home_positions = {1: (30.0, 34.0), 2: (40.0, 20.0)}
    away_positions = {1: (70.0, 34.0), 2: (60.0, 48.0)}

    control = compute_pitch_control(home_positions, away_positions)

    assert control.min() >= 0, f"Min control {control.min()} should be >= 0"
    assert control.max() <= 1, f"Max control {control.max()} should be <= 1"

    # Check no NaN or Inf
    assert not np.isnan(control).any(), "Control contains NaN values"
    assert not np.isinf(control).any(), "Control contains Inf values"

    print(f"PASS Test 6: Control output range (min={control.min():.3f}, max={control.max():.3f})")
    return True


def test_symmetric_positions():
    """
    TEST 7: Symmetric test.
    Home and away at mirror positions, center should be ~0.5.
    """
    # Symmetric positions around center (52.5, 34)
    home_positions = {1: (30.0, 34.0)}
    away_positions = {1: (75.0, 34.0)}

    control = compute_pitch_control(home_positions, away_positions)

    # Center point (approximately index [17, 26] for 2m grid)
    center_x = PITCH_LENGTH / 2
    center_idx_x = int(center_x / GRID_RESOLUTION)
    center_idx_y = int((PITCH_WIDTH / 2) / GRID_RESOLUTION)

    center_control = control[center_idx_y, center_idx_x]

    # Should be reasonably close to 0.5 (contested)
    # Note: May not be exactly 0.5 due to asymmetric distances
    assert 0.3 <= center_control <= 0.7, \
        f"Center should be contested (~0.5), got {center_control:.3f}"

    print(f"PASS Test 7: Symmetric positions (center control={center_control:.3f})")
    return True


def test_dominant_position():
    """
    TEST 8: Dominant position test.
    One home player near a point, no away players nearby.
    """
    # Home player at center, away player far away
    home_positions = {1: (52.5, 34.0)}
    away_positions = {1: (10.0, 10.0)}  # Far corner

    control = compute_pitch_control(home_positions, away_positions)

    # Control near home player should be high
    home_idx_x = int(52.5 / GRID_RESOLUTION)
    home_idx_y = int(34.0 / GRID_RESOLUTION)
    home_control = control[home_idx_y, home_idx_x]

    assert home_control > 0.8, \
        f"Near home player should be home controlled (>0.8), got {home_control:.3f}"

    print(f"PASS Test 8: Dominant position (home control={home_control:.3f})")
    return True


def test_empty_team():
    """
    TEST 9: Empty team handling.
    One team has no players - should not crash.
    """
    home_positions = {1: (50.0, 34.0)}
    away_positions = {}  # Empty away team

    try:
        control = compute_pitch_control(home_positions, away_positions)

        # All positions should be home controlled (1.0)
        # Since away has no influence, home has all influence
        assert control.min() >= 0.99, \
            f"Empty away team means full home control, min={control.min()}"

        print("PASS Test 9: Empty team handling (no crash, full home control)")
        return True
    except Exception as e:
        print(f"FAIL Test 9: Empty team crashed: {e}")
        return False


def test_velocity_integration():
    """
    TEST 10: Integration with velocity module.
    Use calculate_velocities() output as input to pitch control.
    """
    # Generate two frames of synthetic data
    df = generate_synthetic_tracking(n_frames=100, fps=29.97)

    prev_positions = get_frame_positions(df, 50, 'home')
    curr_positions = get_frame_positions(df, 51, 'home')

    # Calculate velocities
    raw_velocities = calculate_velocities(curr_positions, prev_positions, fps=29.97)
    smoothed = smooth_velocities(raw_velocities, raw_velocities, alpha=0.3)
    final_velocities = clamp_velocities(smoothed, max_speed=13.0)

    # Use with pitch control
    home_positions = curr_positions
    away_positions = get_frame_positions(df, 51, 'away')
    away_velocities = {pid: (0.0, 0.0) for pid in away_positions}

    control = compute_pitch_control(
        home_positions, away_positions,
        final_velocities, away_velocities
    )

    # Just verify no crash and valid output
    assert control.shape[0] > 0, "Control should have data"
    assert not np.isnan(control).any(), "Control contains NaN"
    assert not np.isinf(control).any(), "Control contains Inf"

    print(f"PASS Test 10: Velocity integration (control shape={control.shape})")
    return True


def test_visual_output():
    """
    TEST 11: Visual output test.
    Generate and save a pitch control heatmap.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
    except ImportError:
        print("SKIP Test 11: matplotlib not available")
        return True

    # Generate synthetic data
    df = generate_synthetic_tracking(n_frames=100, fps=29.97)

    home_positions = get_frame_positions(df, 50, 'home')
    away_positions = get_frame_positions(df, 50, 'away')

    # Compute pitch control
    control = compute_pitch_control(home_positions, away_positions)
    x_grid, y_grid = create_pitch_grid()

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Blue-white-red colormap (0=away/red, 0.5=white, 1=home/blue)
    colors = ['#FF0000', '#FFFFFF', '#0000FF']
    cmap = LinearSegmentedColormap.from_list('pitch_control', colors)

    # Plot heatmap
    im = ax.pcolormesh(x_grid, y_grid, control, cmap=cmap, vmin=0, vmax=1, alpha=0.7)

    # Plot player positions
    for pid, pos in home_positions.items():
        ax.plot(pos[0], pos[1], 'bo', markersize=10)
    for pid, pos in away_positions.items():
        ax.plot(pos[0], pos[1], 'ro', markersize=10)

    ax.set_xlim(0, PITCH_LENGTH)
    ax.set_ylim(0, PITCH_WIDTH)
    ax.set_aspect('equal')
    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_title('Pitch Control Test - Blue=Home, Red=Away')

    plt.colorbar(im, ax=ax, label='Home Control')

    # Save
    output_path = Path(__file__).parent / 'pitch_control_output.png'
    fig.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()

    assert output_path.exists(), "Output file not created"

    print(f"PASS Test 11: Visual output saved to {output_path}")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("PITCH CONTROL MODULE - COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("Test 1: Grid dimensions", test_grid_dimensions),
        ("Test 2: TTI stationary player", test_tti_stationary),
        ("Test 3: TTI moving toward", test_tti_moving_toward),
        ("Test 4: TTI moving away", test_tti_moving_away),
        ("Test 5: Influence range", test_influence_range),
        ("Test 6: Control output range", test_control_output_range),
        ("Test 7: Symmetric positions", test_symmetric_positions),
        ("Test 8: Dominant position", test_dominant_position),
        ("Test 9: Empty team handling", test_empty_team),
        ("Test 10: Velocity integration", test_velocity_integration),
        ("Test 11: Visual output", test_visual_output),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, "PASS" if passed else "FAIL"))
        except AssertionError as e:
            print(f"FAIL {name}: {e}")
            results.append((name, "FAIL"))
        except Exception as e:
            print(f"ERROR {name}: {e}")
            results.append((name, "ERROR"))

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)

    for name, status in results:
        icon = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "ERROR"
        print(f"  [{icon}] {name}")

    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
