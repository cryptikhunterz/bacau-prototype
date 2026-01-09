"""
Comprehensive tests for velocity module.

Tests:
1. Basic velocity calculation
2. Zero movement
3. Missing player in current frame
4. Missing player in previous frame
5. EMA smoothing verification
6. Speed clamping
7. Empty inputs
8. Integration with synthetic tracking data
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
from velocity import (
    calculate_velocities,
    smooth_velocities,
    clamp_velocities,
    MAX_SPEED,
    EMA_ALPHA,
    FPS
)
from data_loader import generate_synthetic_tracking, get_frame_positions


def test_basic_velocity_calculation():
    """
    TEST 1: Basic velocity calculation.
    Two frames with known positions, verify v = (pos2 - pos1) / dt
    """
    dt = 1.0 / FPS  # ~0.0334 seconds

    # Player moves 1 meter in x direction over one frame
    prev = {"p1": (10.0, 20.0)}
    curr = {"p1": (11.0, 20.0)}

    velocities = calculate_velocities(curr, prev, fps=FPS)

    expected_vx = 1.0 / dt  # ~29.97 m/s (very fast, but math check)
    expected_vy = 0.0

    assert abs(velocities["p1"][0] - expected_vx) < 0.01, \
        f"Expected vx={expected_vx:.2f}, got {velocities['p1'][0]:.2f}"
    assert abs(velocities["p1"][1] - expected_vy) < 0.01, \
        f"Expected vy={expected_vy:.2f}, got {velocities['p1'][1]:.2f}"

    print("PASS Test 1: Basic velocity calculation")
    return True


def test_zero_movement():
    """
    TEST 2: Zero movement.
    Same position in both frames, verify velocity = (0, 0)
    """
    prev = {"p1": (50.0, 30.0), "p2": (25.0, 15.0)}
    curr = {"p1": (50.0, 30.0), "p2": (25.0, 15.0)}

    velocities = calculate_velocities(curr, prev, fps=FPS)

    for pid in ["p1", "p2"]:
        assert velocities[pid] == (0.0, 0.0), \
            f"Expected (0,0) for {pid}, got {velocities[pid]}"

    print("PASS Test 2: Zero movement")
    return True


def test_missing_player_current():
    """
    TEST 3: Missing player in current frame.
    Player exists in prev, not in curr - should not crash, skip that player.
    """
    prev = {"p1": (10.0, 20.0), "p2": (30.0, 40.0)}
    curr = {"p1": (11.0, 21.0)}  # p2 missing

    velocities = calculate_velocities(curr, prev, fps=FPS)

    assert "p1" in velocities, "p1 should be in output"
    assert "p2" not in velocities, "p2 should NOT be in output (not in current)"

    print("PASS Test 3: Missing player in current frame")
    return True


def test_missing_player_previous():
    """
    TEST 4: Missing player in previous frame.
    Player exists in curr, not in prev - should return zero velocity.
    """
    prev = {"p1": (10.0, 20.0)}
    curr = {"p1": (11.0, 21.0), "p2": (50.0, 50.0)}  # p2 is new

    velocities = calculate_velocities(curr, prev, fps=FPS)

    assert "p1" in velocities, "p1 should be in output"
    assert "p2" in velocities, "p2 should be in output"
    assert velocities["p2"] == (0.0, 0.0), \
        f"New player should have zero velocity, got {velocities['p2']}"

    print("PASS Test 4: Missing player in previous frame")
    return True


def test_ema_smoothing():
    """
    TEST 5: EMA smoothing verification.
    v_smooth = alpha * v_curr + (1 - alpha) * v_prev
    With alpha=0.3: v_smooth = 0.3 * curr + 0.7 * prev
    """
    prev_smoothed = {"p1": (10.0, 5.0)}
    current_raw = {"p1": (4.0, 11.0)}

    smoothed = smooth_velocities(current_raw, prev_smoothed, alpha=EMA_ALPHA)

    expected_vx = EMA_ALPHA * 4.0 + (1 - EMA_ALPHA) * 10.0  # 0.3*4 + 0.7*10 = 8.2
    expected_vy = EMA_ALPHA * 11.0 + (1 - EMA_ALPHA) * 5.0   # 0.3*11 + 0.7*5 = 6.8

    assert abs(smoothed["p1"][0] - expected_vx) < 0.001, \
        f"Expected vx={expected_vx}, got {smoothed['p1'][0]}"
    assert abs(smoothed["p1"][1] - expected_vy) < 0.001, \
        f"Expected vy={expected_vy}, got {smoothed['p1'][1]}"

    print("PASS Test 5: EMA smoothing verification")
    return True


def test_speed_clamping():
    """
    TEST 6: Speed clamping.
    Create velocity exceeding MAX_SPEED, verify clamped and direction preserved.
    """
    # 20 m/s at 45 degrees
    vx = 20.0 * np.cos(np.pi/4)  # ~14.14
    vy = 20.0 * np.sin(np.pi/4)  # ~14.14
    velocities = {"p1": (vx, vy)}

    clamped = clamp_velocities(velocities, max_speed=MAX_SPEED)

    clamped_vx, clamped_vy = clamped["p1"]
    clamped_speed = np.sqrt(clamped_vx**2 + clamped_vy**2)

    # Speed should be MAX_SPEED (13.0)
    assert abs(clamped_speed - MAX_SPEED) < 0.001, \
        f"Expected speed={MAX_SPEED}, got {clamped_speed:.3f}"

    # Direction should be preserved (still 45 degrees)
    original_angle = np.arctan2(vy, vx)
    clamped_angle = np.arctan2(clamped_vy, clamped_vx)
    assert abs(original_angle - clamped_angle) < 0.001, \
        f"Direction changed: original={original_angle:.3f}, clamped={clamped_angle:.3f}"

    print("PASS Test 6: Speed clamping (magnitude limited, direction preserved)")
    return True


def test_empty_inputs():
    """
    TEST 7: Empty inputs.
    Empty dicts for positions - should return empty dict, no crash.
    """
    # Empty current positions
    velocities = calculate_velocities({}, {"p1": (10.0, 20.0)}, fps=FPS)
    assert velocities == {}, "Should return empty dict for empty current"

    # Empty previous positions
    velocities = calculate_velocities({"p1": (10.0, 20.0)}, {}, fps=FPS)
    assert velocities["p1"] == (0.0, 0.0), "New player should have zero velocity"

    # Both empty
    velocities = calculate_velocities({}, {}, fps=FPS)
    assert velocities == {}, "Should return empty dict for both empty"

    # Empty for smoothing
    smoothed = smooth_velocities({}, {"p1": (5.0, 5.0)}, alpha=EMA_ALPHA)
    assert "p1" in smoothed, "Should decay previous velocity"

    # Empty for clamping
    clamped = clamp_velocities({}, max_speed=MAX_SPEED)
    assert clamped == {}, "Should return empty dict"

    print("PASS Test 7: Empty inputs handled correctly")
    return True


def test_integration_synthetic_data():
    """
    TEST 8: Integration with synthetic tracking data.
    Load frames, calculate velocities, verify reasonable values (0-13 m/s).
    """
    # Generate synthetic tracking data at 29.97 fps
    df = generate_synthetic_tracking(n_frames=100, fps=FPS)

    # Get positions for two consecutive frames
    prev_positions = get_frame_positions(df, 50, 'home')
    curr_positions = get_frame_positions(df, 51, 'home')

    # Calculate raw velocities
    raw_velocities = calculate_velocities(curr_positions, prev_positions, fps=FPS)

    # Smooth velocities (simulating previous smoothed = raw for first iteration)
    smoothed = smooth_velocities(raw_velocities, raw_velocities, alpha=EMA_ALPHA)

    # Clamp to max speed
    final_velocities = clamp_velocities(smoothed, max_speed=MAX_SPEED)

    print(f"\n  Frame 50→51 velocities for home team:")
    all_reasonable = True
    for pid, (vx, vy) in final_velocities.items():
        speed = np.sqrt(vx**2 + vy**2)
        status = "OK" if speed <= MAX_SPEED + 0.001 else "OVER MAX"
        print(f"    Player {pid}: vx={vx:6.2f}, vy={vy:6.2f}, speed={speed:5.2f} m/s [{status}]")

        if speed > MAX_SPEED + 0.01:
            all_reasonable = False

    assert all_reasonable, "Some velocities exceed MAX_SPEED after clamping"
    assert len(final_velocities) > 0, "Should have velocities for players"

    print("PASS Test 8: Integration with synthetic data")
    return True


def test_nan_handling():
    """
    BONUS TEST: NaN/Inf handling.
    Ensure no NaN or Inf values in output.
    """
    prev = {"p1": (0.0, 0.0)}
    curr = {"p1": (0.0, 0.0)}

    velocities = calculate_velocities(curr, prev, fps=FPS)

    for pid, (vx, vy) in velocities.items():
        assert not np.isnan(vx), f"NaN detected in vx for {pid}"
        assert not np.isnan(vy), f"NaN detected in vy for {pid}"
        assert not np.isinf(vx), f"Inf detected in vx for {pid}"
        assert not np.isinf(vy), f"Inf detected in vy for {pid}"

    # Test clamping with zero velocity (could cause division by zero)
    clamped = clamp_velocities({"p1": (0.0, 0.0)}, max_speed=MAX_SPEED)
    assert clamped["p1"] == (0.0, 0.0), "Zero velocity should remain zero"

    print("PASS Bonus: NaN/Inf handling")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("VELOCITY MODULE - COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("Test 1: Basic velocity calculation", test_basic_velocity_calculation),
        ("Test 2: Zero movement", test_zero_movement),
        ("Test 3: Missing player in current", test_missing_player_current),
        ("Test 4: Missing player in previous", test_missing_player_previous),
        ("Test 5: EMA smoothing verification", test_ema_smoothing),
        ("Test 6: Speed clamping", test_speed_clamping),
        ("Test 7: Empty inputs", test_empty_inputs),
        ("Test 8: Integration synthetic data", test_integration_synthetic_data),
        ("Bonus: NaN/Inf handling", test_nan_handling),
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
