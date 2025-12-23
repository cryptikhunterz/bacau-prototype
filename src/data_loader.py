"""Data loading utilities for tracking data."""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_synthetic_tracking(n_frames=100, fps=25):
    """
    Generate realistic-looking tracking data for testing.

    Args:
        n_frames: Number of frames to generate
        fps: Frames per second (for timestamp calculation)

    Returns:
        pandas DataFrame with tracking data
    """
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


def load_pff_tracking(meta_path, roster_path, tracking_path):
    """
    Load PFF FC tracking data using kloppy.

    Args:
        meta_path: Path to metadata JSON file
        roster_path: Path to roster JSON file
        tracking_path: Path to tracking .jsonl.bz2 file

    Returns:
        pandas DataFrame with tracking data
    """
    try:
        from kloppy import pff

        dataset = pff.load_tracking(
            meta_data=str(meta_path),
            roster_meta_data=str(roster_path),
            raw_data=str(tracking_path)
        )

        return dataset.to_df()
    except ImportError:
        print("kloppy not installed. Run: pip install kloppy")
        return None
    except Exception as e:
        print(f"Error loading PFF data: {e}")
        return None


def get_frame_positions(df, frame_idx, team_prefix='home'):
    """
    Extract player positions for a specific frame.

    Args:
        df: Tracking DataFrame
        frame_idx: Frame index
        team_prefix: 'home' or 'away'

    Returns:
        Dict of {player_id: (x, y)}
    """
    row = df.iloc[frame_idx]
    positions = {}

    for i in range(1, 12):
        x_col = f'{team_prefix}_{i}_x'
        y_col = f'{team_prefix}_{i}_y'

        if x_col in df.columns and y_col in df.columns:
            x, y = row[x_col], row[y_col]
            if not (np.isnan(x) or np.isnan(y)):
                positions[i] = (x, y)

    return positions


if __name__ == "__main__":
    # Test synthetic data generation
    df = generate_synthetic_tracking(n_frames=250)
    print(f"Generated {len(df)} frames")
    print(f"Columns: {list(df.columns)[:10]}...")

    # Test position extraction
    positions = get_frame_positions(df, 0, 'home')
    print(f"\nHome team positions (frame 0):")
    for pid, (x, y) in positions.items():
        print(f"  Player {pid}: ({x:.1f}, {y:.1f})")

    # Save synthetic data
    output_path = Path(__file__).parent.parent / 'data' / 'synthetic' / 'tracking.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
