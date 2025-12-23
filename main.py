#!/usr/bin/env python3
"""Main entry point for Shape Graph Visualization UI."""

import os
import sys

# Fix SSL certificates on macOS
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kloppy import metrica
from ui import ShapeGraphUI


def main():
    """Main entry point."""
    print("=" * 50)
    print("Shape Graph Visualization")
    print("=" * 50)

    print("\nLoading Metrica tracking data...")
    dataset = metrica.load_open_data()
    print(f"Loaded {len(dataset.frames)} frames")

    print("\nStarting UI...")
    print("Controls:")
    print("  Space    - Play/Pause")
    print("  Left/Right - Step frame")
    print("  Escape   - Stop playback")
    print()

    app = ShapeGraphUI(dataset, "Home Team", "Away Team")
    app.run()


if __name__ == "__main__":
    main()
