"""Custom Compactness Index (CI) calculation for defensive shape analysis."""

import math
import numpy as np
from scipy.spatial import ConvexHull


# Pitch dimensions (meters)
PITCH_LENGTH = 105
PITCH_WIDTH = 68

# Default calibration configuration
DEFAULT_CONFIG = {
    'ref_area_high': 600,       # Reference area for high press (m²)
    'ref_area_mid': 450,        # Reference area for mid block (m²)
    'ref_area_low': 300,        # Reference area for low block (m²)
    'sigma': 0.5,               # Balance penalty sensitivity
    'boundary_low_mid': 0.35,   # Low/Mid boundary (% from own goal)
    'boundary_mid_high': 0.65,  # Mid/High boundary (% from own goal)
}


def classify_block(centroid_x: float, is_home: bool, config: dict = None) -> str:
    """
    Classify defensive block by team centroid position.

    Args:
        centroid_x: X coordinate of team centroid (meters)
        is_home: True if home team (defends goal at x=0)
        config: Calibration dict (uses DEFAULT_CONFIG if None)

    Returns:
        'low_block', 'mid_block', or 'high_press'
    """
    cfg = config or DEFAULT_CONFIG

    # Calculate percentage distance from own goal
    if is_home:
        # Home team: own goal at x=0
        pct = centroid_x / PITCH_LENGTH
    else:
        # Away team: own goal at x=105
        pct = (PITCH_LENGTH - centroid_x) / PITCH_LENGTH

    # Classify based on boundaries
    boundary_low_mid = cfg.get('boundary_low_mid', 0.35)
    boundary_mid_high = cfg.get('boundary_mid_high', 0.65)

    if pct < boundary_low_mid:
        return 'low_block'
    elif pct < boundary_mid_high:
        return 'mid_block'
    else:
        return 'high_press'


def is_defending(possession: str, ball_x: float, is_home: bool) -> bool:
    """
    Check if team is in defending state.

    A team is defending when:
    - They do NOT have possession (opponent has ball or contested), OR
    - They have possession but ball is in their own half

    Args:
        possession: 'home', 'away', or 'contested'
        ball_x: X coordinate of ball (meters)
        is_home: True if checking home team's defending state

    Returns:
        True if team is defending (CI should be calculated)
    """
    half_pitch = PITCH_LENGTH / 2  # 52.5m

    # Check if team has possession
    has_possession = (is_home and possession == 'home') or \
                     (not is_home and possession == 'away')

    if not has_possession:
        return True  # Not in possession = defending

    # Has possession but check if ball in own half
    if is_home:
        # Home's own half is x < 52.5
        return ball_x < half_pitch
    else:
        # Away's own half is x > 52.5
        return ball_x > half_pitch


def compute_ci(outfield_positions: dict, is_home: bool, config: dict = None) -> dict:
    """
    Compute Custom Compactness Index (0-100).

    The CI measures how compact a team's defensive shape is relative to
    a reference area for their current block type. A balance factor
    penalizes shapes that are too wide or too deep.

    Formula:
        1. Compute convex hull area (Ah)
        2. Classify block by centroid position
        3. CI_raw = 100 * (ref_area / Ah), capped at 100
        4. Balance factor B = exp(-ln(W/D)² / 2σ²)
        5. Final CI = CI_raw * B

    Args:
        outfield_positions: Dict of {player_id: (x, y)} - typically 10 outfield players
        is_home: True if home team (defends goal at x=0)
        config: Calibration dict with keys:
            - ref_area_high, ref_area_mid, ref_area_low (m²)
            - sigma (balance penalty sensitivity)
            - boundary_low_mid, boundary_mid_high (% thresholds)

    Returns:
        Dict with keys:
            - ci: Final compactness index (0-100)
            - ci_raw: Unbalanced CI before penalty
            - block: Block classification string
            - area: Convex hull area (m²)
            - width: Team width - Y spread (m)
            - depth: Team depth - X spread (m)
            - balance_factor: B value (0-1)
    """
    cfg = config or DEFAULT_CONFIG

    # Handle insufficient players
    if len(outfield_positions) < 3:
        return {
            'ci': 0,
            'ci_raw': 0,
            'block': 'unknown',
            'area': 0,
            'width': 0,
            'depth': 0,
            'balance_factor': 0
        }

    # Convert positions to numpy array
    points = np.array(list(outfield_positions.values()))
    xs = points[:, 0]
    ys = points[:, 1]

    # Calculate convex hull area
    try:
        hull = ConvexHull(points)
        area = hull.volume  # In 2D, .volume gives area
    except Exception:
        # ConvexHull fails for collinear points or other edge cases
        area = 0

    # Calculate dimensions
    width = float(np.max(ys) - np.min(ys))   # Y spread (lateral)
    depth = float(np.max(xs) - np.min(xs))   # X spread (vertical)
    centroid_x = float(np.mean(xs))

    # Classify block using centroid
    block = classify_block(centroid_x, is_home, cfg)

    # Get reference area for this block type
    ref_area_map = {
        'high_press': cfg.get('ref_area_high', 600),
        'mid_block': cfg.get('ref_area_mid', 450),
        'low_block': cfg.get('ref_area_low', 300),
    }
    ref_area = ref_area_map.get(block, cfg.get('ref_area_mid', 450))

    # Calculate base CI (capped at 100)
    if area > 0:
        ci_raw = 100 * (ref_area / area)
        ci_raw = min(ci_raw, 100)
    else:
        ci_raw = 0

    # Calculate balance factor
    sigma = cfg.get('sigma', 0.5)
    if depth > 0 and width > 0 and sigma > 0:
        r = width / depth  # aspect ratio
        try:
            ln_r = math.log(r)
            balance_factor = math.exp(-(ln_r ** 2) / (2 * sigma ** 2))
        except (ValueError, ZeroDivisionError):
            balance_factor = 0
    else:
        balance_factor = 0

    # Final CI
    ci = ci_raw * balance_factor

    return {
        'ci': round(ci, 1),
        'ci_raw': round(ci_raw, 1),
        'block': block,
        'area': round(area, 1),
        'width': round(width, 1),
        'depth': round(depth, 1),
        'balance_factor': round(balance_factor, 3)
    }


if __name__ == "__main__":
    print("=" * 60)
    print("COMPACTNESS MODULE TESTS")
    print("=" * 60)

    # Test 1: Perfect square where area = ref_area and W/D = 1
    print("\n--- Test 1: Perfect shape (area=450, W/D=1) ---")
    # Create a square with area ≈ 450 m² (side ≈ 21.2m)
    # Place at mid-block position (centroid at x=52.5)
    side = math.sqrt(450)
    cx, cy = 52.5, 34  # Center of pitch
    positions_perfect = {
        1: (cx - side/2, cy - side/2),
        2: (cx + side/2, cy - side/2),
        3: (cx + side/2, cy + side/2),
        4: (cx - side/2, cy + side/2),
    }
    result = compute_ci(positions_perfect, is_home=True)
    print(f"  CI: {result['ci']} (expected ~100)")
    print(f"  Block: {result['block']}")
    print(f"  Area: {result['area']} m²")
    print(f"  W/D ratio: {result['width']/result['depth']:.2f}")
    print(f"  Balance factor: {result['balance_factor']}")
    status = "✅ PASS" if result['ci'] > 95 else "❌ FAIL"
    print(f"  {status}")

    # Test 2: Area = 2x reference, W/D = 1
    print("\n--- Test 2: Double area (area=900, W/D=1) ---")
    side = math.sqrt(900)  # 30m
    positions_double = {
        1: (cx - side/2, cy - side/2),
        2: (cx + side/2, cy - side/2),
        3: (cx + side/2, cy + side/2),
        4: (cx - side/2, cy + side/2),
    }
    result = compute_ci(positions_double, is_home=True)
    print(f"  CI: {result['ci']} (expected ~50)")
    print(f"  CI_raw: {result['ci_raw']}")
    print(f"  Area: {result['area']} m²")
    status = "✅ PASS" if 45 <= result['ci'] <= 55 else "❌ FAIL"
    print(f"  {status}")

    # Test 3: Area = ref but W/D = 2 (unbalanced)
    print("\n--- Test 3: Unbalanced shape (area=450, W/D=2) ---")
    # Rectangle: width=30, depth=15 → area=450
    w, d = 30, 15
    positions_unbalanced = {
        1: (cx - d/2, cy - w/2),
        2: (cx + d/2, cy - w/2),
        3: (cx + d/2, cy + w/2),
        4: (cx - d/2, cy + w/2),
    }
    result = compute_ci(positions_unbalanced, is_home=True)
    print(f"  CI: {result['ci']} (expected < 100 due to penalty)")
    print(f"  CI_raw: {result['ci_raw']}")
    print(f"  W/D ratio: {result['width']/result['depth']:.2f}")
    print(f"  Balance factor: {result['balance_factor']}")
    status = "✅ PASS" if result['ci'] < result['ci_raw'] else "❌ FAIL"
    print(f"  {status}")

    # Test 4: classify_block with centroid at x=20 (home team)
    print("\n--- Test 4: classify_block(x=20, home) ---")
    block = classify_block(20, is_home=True)
    pct = 20 / 105
    print(f"  Centroid x=20, pct={pct:.2f}")
    print(f"  Block: {block} (expected 'low_block')")
    status = "✅ PASS" if block == 'low_block' else "❌ FAIL"
    print(f"  {status}")

    # Test 5: classify_block with centroid at x=80 (home team)
    print("\n--- Test 5: classify_block(x=80, home) ---")
    block = classify_block(80, is_home=True)
    pct = 80 / 105
    print(f"  Centroid x=80, pct={pct:.2f}")
    print(f"  Block: {block} (expected 'high_press')")
    status = "✅ PASS" if block == 'high_press' else "❌ FAIL"
    print(f"  {status}")

    # Test 6: is_defending - opponent has ball
    print("\n--- Test 6: is_defending('away', 30, home) ---")
    defending = is_defending('away', 30, is_home=True)
    print(f"  Home team, away has possession")
    print(f"  Result: {defending} (expected True)")
    status = "✅ PASS" if defending == True else "❌ FAIL"
    print(f"  {status}")

    # Test 7: is_defending - has ball in own half
    print("\n--- Test 7: is_defending('home', 30, home) ---")
    defending = is_defending('home', 30, is_home=True)
    print(f"  Home team has possession, ball at x=30 (own half)")
    print(f"  Result: {defending} (expected True)")
    status = "✅ PASS" if defending == True else "❌ FAIL"
    print(f"  {status}")

    # Test 8: is_defending - has ball in opponent half
    print("\n--- Test 8: is_defending('home', 70, home) ---")
    defending = is_defending('home', 70, is_home=True)
    print(f"  Home team has possession, ball at x=70 (opponent half)")
    print(f"  Result: {defending} (expected False)")
    status = "✅ PASS" if defending == False else "❌ FAIL"
    print(f"  {status}")

    # Test 9: Less than 3 players
    print("\n--- Test 9: < 3 players ---")
    positions_few = {1: (50, 34), 2: (60, 34)}
    result = compute_ci(positions_few, is_home=True)
    print(f"  CI: {result['ci']} (expected 0)")
    print(f"  Block: {result['block']} (expected 'unknown')")
    status = "✅ PASS" if result['ci'] == 0 and result['block'] == 'unknown' else "❌ FAIL"
    print(f"  {status}")

    # Test 10: Custom config overrides defaults
    print("\n--- Test 10: Custom config override ---")
    # Use double-area shape so CI isn't at the cap
    custom_config = {
        'ref_area_high': 600,
        'ref_area_mid': 900,  # Double the default (450 → 900)
        'ref_area_low': 300,
        'sigma': 0.5,
        'boundary_low_mid': 0.35,
        'boundary_mid_high': 0.65,
    }
    # positions_double has area=900, mid_block
    # Default: CI = 100 * (450/900) = 50
    # Custom: CI = 100 * (900/900) = 100
    result_default = compute_ci(positions_double, is_home=True)
    result_custom = compute_ci(positions_double, is_home=True, config=custom_config)
    print(f"  Shape area: 900 m² (mid_block)")
    print(f"  Default ref_area_mid=450: CI={result_default['ci']} (expected ~50)")
    print(f"  Custom ref_area_mid=900: CI={result_custom['ci']} (expected ~100)")
    status = "✅ PASS" if result_custom['ci'] > result_default['ci'] * 1.5 else "❌ FAIL"
    print(f"  {status}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
