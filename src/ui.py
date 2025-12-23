"""Tkinter UI wrapper for shape graph visualization."""

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time

try:
    from .activity_logger import init_logger, get_logger
    from .pitch import draw_pitch
    from .markers import draw_player_marker
    from .position_classifier import classify_team_vertical, classify_team_horizontal, detect_formation
    from .colors import BACKGROUND_COLOR
except ImportError:
    from activity_logger import init_logger, get_logger
    from pitch import draw_pitch
    from markers import draw_player_marker
    from position_classifier import classify_team_vertical, classify_team_horizontal, detect_formation
    from colors import BACKGROUND_COLOR


class ShapeGraphUI:
    """Main UI class for shape graph visualization."""

    def __init__(self, dataset, home_name="Home", away_name="Away"):
        """
        Initialize the UI.

        Args:
            dataset: Kloppy TrackingDataset
            home_name: Home team display name
            away_name: Away team display name
        """
        self.dataset = dataset
        self.home_name = home_name
        self.away_name = away_name

        self.current_frame = 0
        self.is_playing = False
        self.playback_speed = 1.0  # 1.0 = normal speed
        self.fps = 25

        # Create main window
        self.root = tk.Tk()
        self.root.title("Shape Graph Visualization")
        self.root.geometry("1400x800")
        self.root.configure(bg='#1a1a2e')

        # Initialize logger with UI callback
        self.logger = init_logger(
            log_file="logs/activity_log.md",
            ui_callback=self._log_to_ui
        )

        self._create_widgets()
        self._bind_events()

        # Log startup
        self.logger.log_startup()
        self.logger.log_data_loaded(
            len(dataset.frames),
            11,  # Assuming 11 players per team
            11
        )

    def _create_widgets(self):
        """Create UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Visualization
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create matplotlib figure
        self.fig = Figure(figsize=(14, 7), facecolor=BACKGROUND_COLOR)
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)

        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Controls frame
        controls_frame = ttk.Frame(viz_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        # Playback controls
        self.play_btn = ttk.Button(controls_frame, text="▶ Play", command=self._toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(controls_frame, text="◀◀", command=self._step_back_10).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="◀", command=self._step_back).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="▶", command=self._step_forward).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="▶▶", command=self._step_forward_10).pack(side=tk.LEFT, padx=2)

        # Frame slider
        self.frame_var = tk.IntVar(value=0)
        self.frame_slider = ttk.Scale(
            controls_frame,
            from_=0,
            to=len(self.dataset.frames) - 1,
            variable=self.frame_var,
            orient=tk.HORIZONTAL,
            command=self._on_slider_change
        )
        self.frame_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Frame label
        self.frame_label = ttk.Label(controls_frame, text="Frame: 0")
        self.frame_label.pack(side=tk.LEFT, padx=5)

        # Speed control
        ttk.Label(controls_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = ttk.Scale(
            controls_frame,
            from_=0.1,
            to=3.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=100
        )
        speed_slider.pack(side=tk.LEFT, padx=5)

        # Right panel - Log
        log_frame = ttk.Frame(main_frame, width=300)
        log_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        log_frame.pack_propagate(False)

        ttk.Label(log_frame, text="Activity Log", font=('Arial', 12, 'bold')).pack(pady=5)

        self.log_text = ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=40,
            height=40,
            bg='#0d1117',
            fg='#c9d1d9',
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Initial render
        self._render_frame(0)

    def _bind_events(self):
        """Bind keyboard events."""
        self.root.bind('<space>', lambda e: self._toggle_play())
        self.root.bind('<Left>', lambda e: self._step_back())
        self.root.bind('<Right>', lambda e: self._step_forward())
        self.root.bind('<Escape>', lambda e: self._stop_play())

    def _log_to_ui(self, message: str):
        """Add message to UI log panel."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _extract_frame_positions(self, frame):
        """Extract player positions from kloppy frame."""
        PITCH_LENGTH = 105
        PITCH_WIDTH = 68

        home_positions = {}
        away_positions = {}

        for player, data in frame.players_data.items():
            if data.coordinates:
                x = data.coordinates.x * PITCH_LENGTH
                y = data.coordinates.y * PITCH_WIDTH
                pid = int(player.player_id.split('_')[1])

                if 'home' in player.player_id:
                    home_positions[pid] = (x, y)
                else:
                    away_positions[pid] = (x, y)

        return {'home': home_positions, 'away': away_positions}

    def _render_frame(self, frame_idx: int):
        """Render a single frame."""
        if frame_idx < 0 or frame_idx >= len(self.dataset.frames):
            return

        frame = self.dataset.frames[frame_idx]
        frame_data = self._extract_frame_positions(frame)

        # Clear axes
        self.ax1.clear()
        self.ax2.clear()

        # Draw pitches and players
        for ax, team_key, team_name in [(self.ax1, 'home', self.home_name),
                                         (self.ax2, 'away', self.away_name)]:
            draw_pitch(ax)

            positions = frame_data.get(team_key, {})

            if positions:
                v_buckets = classify_team_vertical(positions)
                h_buckets = classify_team_horizontal(positions)
                formation = detect_formation(positions)

                for pid, (x, y) in positions.items():
                    v_bucket = v_buckets.get(pid, 2)
                    h_bucket = h_buckets.get(pid, 2)
                    draw_player_marker(ax, x, y, v_bucket, h_bucket,
                                     player_num=pid, radius=2.5)

                title = f"{team_name}"
                if formation:
                    title += f"\n{formation}"
                ax.set_title(title, fontsize=14, fontweight='bold',
                           color='white', pad=15)

        self.fig.suptitle(f"Frame {frame_idx}", fontsize=10, color='gray')
        self.fig.tight_layout()
        self.canvas.draw()

        # Update UI
        self.current_frame = frame_idx
        self.frame_var.set(frame_idx)
        self.frame_label.config(text=f"Frame: {frame_idx}")

    def _toggle_play(self):
        """Toggle play/pause."""
        if self.is_playing:
            self._stop_play()
        else:
            self._start_play()

    def _start_play(self):
        """Start playback."""
        self.is_playing = True
        self.play_btn.config(text="⏸ Pause")
        self.logger.log_user_action("Started playback")

        # Start playback thread
        self.play_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.play_thread.start()

    def _stop_play(self):
        """Stop playback."""
        self.is_playing = False
        self.play_btn.config(text="▶ Play")
        self.logger.log_user_action("Paused playback")

    def _playback_loop(self):
        """Main playback loop (runs in separate thread)."""
        while self.is_playing:
            next_frame = self.current_frame + 1
            if next_frame >= len(self.dataset.frames):
                next_frame = 0  # Loop

            # Schedule render on main thread
            self.root.after(0, lambda f=next_frame: self._render_frame(f))

            # Wait based on speed
            delay = 1.0 / (self.fps * self.speed_var.get())
            time.sleep(delay)

    def _step_forward(self):
        """Step forward one frame."""
        self.logger.log_user_action("Step forward")
        self._render_frame(self.current_frame + 1)

    def _step_back(self):
        """Step back one frame."""
        self.logger.log_user_action("Step back")
        self._render_frame(max(0, self.current_frame - 1))

    def _step_forward_10(self):
        """Step forward 10 frames."""
        self.logger.log_user_action("Step forward 10")
        self._render_frame(min(len(self.dataset.frames) - 1, self.current_frame + 10))

    def _step_back_10(self):
        """Step back 10 frames."""
        self.logger.log_user_action("Step back 10")
        self._render_frame(max(0, self.current_frame - 10))

    def _on_slider_change(self, value):
        """Handle slider change."""
        frame = int(float(value))
        if frame != self.current_frame:
            self._render_frame(frame)

    def run(self):
        """Start the UI main loop."""
        self.logger.log("UI", "Main loop started", "Success")
        self.root.mainloop()


if __name__ == "__main__":
    # Test UI standalone
    import sys
    import os
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from kloppy import metrica

    print("Loading data...")
    dataset = metrica.load_open_data()
    print(f"Loaded {len(dataset.frames)} frames")

    print("Starting UI...")
    app = ShapeGraphUI(dataset, "Home Team", "Away Team")
    app.run()
