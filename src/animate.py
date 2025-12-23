"""Animation pipeline for shape graph visualization."""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter

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


def extract_frame_positions(frame, pitch_length=105, pitch_width=68):
    """
    Extract player positions from a kloppy frame.

    Args:
        frame: Kloppy TrackingDataset frame
        pitch_length: Pitch length in meters
        pitch_width: Pitch width in meters

    Returns:
        Dict with 'home' and 'away' player positions
    """
    home_positions = {}
    away_positions = {}

    for player, data in frame.players_data.items():
        if data.coordinates:
            x = data.coordinates.x * pitch_length
            y = data.coordinates.y * pitch_width
            pid = int(player.player_id.split('_')[1])

            if 'home' in player.player_id:
                home_positions[pid] = (x, y)
            else:
                away_positions[pid] = (x, y)

    return {'home': home_positions, 'away': away_positions}


def create_animation(dataset, start_frame=0, num_frames=100,
                    home_name="Home", away_name="Away",
                    figsize=(20, 10), marker_radius=2.5, fps=25):
    """
    Create animation from tracking dataset.

    Args:
        dataset: Kloppy TrackingDataset
        start_frame: Starting frame index
        num_frames: Number of frames to animate
        home_name: Home team display name
        away_name: Away team display name
        figsize: Figure size
        marker_radius: Player marker radius
        fps: Frames per second

    Returns:
        Tuple of (fig, animation)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    # Store axes for update function
    axes = {'home': ax1, 'away': ax2}

    def update(frame_idx):
        """Update function for animation."""
        # Get actual frame from dataset
        actual_idx = start_frame + frame_idx
        if actual_idx >= len(dataset.frames):
            return

        frame = dataset.frames[actual_idx]
        frame_data = extract_frame_positions(frame)

        # Clear and redraw each pitch
        for ax, team_key, team_name in [(ax1, 'home', home_name),
                                         (ax2, 'away', away_name)]:
            ax.clear()
            draw_pitch(ax)

            positions = frame_data.get(team_key, {})

            if not positions:
                ax.set_title(f"{team_name}\nNo Data",
                            fontsize=16, fontweight='bold', color='white', pad=20)
                continue

            # Classify positions
            v_buckets = classify_team_vertical(positions)
            h_buckets = classify_team_horizontal(positions)
            formation = detect_formation(positions)

            # Draw players
            for pid, (x, y) in positions.items():
                v_bucket = v_buckets.get(pid, 2)
                h_bucket = h_buckets.get(pid, 2)
                draw_player_marker(ax, x, y, v_bucket, h_bucket,
                                 player_num=pid, radius=marker_radius)

            # Title with formation
            title = f"{team_name}"
            if formation:
                title += f"\n{formation}"
            ax.set_title(title, fontsize=16, fontweight='bold',
                        color='white', pad=20)

        # Add frame counter
        fig.suptitle(f"Frame {actual_idx}", fontsize=12, color='gray')

        plt.tight_layout()
        return []

    # Create animation
    anim = FuncAnimation(fig, update, frames=num_frames,
                        interval=1000/fps, blit=False)

    return fig, anim


def save_gif(anim, output_path, fps=15):
    """Save animation as GIF."""
    writer = PillowWriter(fps=fps)
    anim.save(output_path, writer=writer)
    print(f"Saved GIF: {output_path}")


def save_mp4(anim, output_path, fps=25):
    """Save animation as MP4."""
    writer = FFMpegWriter(fps=fps, metadata={'title': 'Shape Graph Animation'})
    anim.save(output_path, writer=writer)
    print(f"Saved MP4: {output_path}")


if __name__ == "__main__":
    # Test animation
    import sys
    import os

    # Need to set SSL cert for macOS
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()

    from kloppy import metrica

    print("Loading Metrica tracking data...")
    dataset = metrica.load_open_data()
    print(f"Loaded {len(dataset.frames)} frames")

    print("Creating animation (100 frames)...")
    fig, anim = create_animation(dataset, start_frame=1000, num_frames=100)

    # Save as GIF
    save_gif(anim, 'outputs/videos/shape_graph_test.gif', fps=15)

    print("Done!")
    plt.close()
