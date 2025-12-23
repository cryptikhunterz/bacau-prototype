"""Streamlit UI for Shape Graph Visualization."""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
import os
import time

# Fix SSL for macOS
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pitch import draw_pitch
from markers import draw_player_marker
from position_classifier import classify_team_vertical, classify_team_horizontal, detect_formation
from colors import BACKGROUND_COLOR

# Page config
st.set_page_config(
    page_title="Shape Graph Visualization",
    page_icon="⚽",
    layout="wide"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
    }
    .log-container {
        background-color: #1a1a2e;
        padding: 10px;
        border-radius: 5px;
        max-height: 300px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_data():
    """Load tracking data (cached)."""
    from kloppy import metrica
    return metrica.load_open_data()


def extract_positions(frame, pitch_length=105, pitch_width=68):
    """Extract player positions from frame."""
    home = {}
    away = {}
    for player, data in frame.players_data.items():
        if data.coordinates:
            x = data.coordinates.x * pitch_length
            y = data.coordinates.y * pitch_width
            pid = int(player.player_id.split('_')[1])
            if 'home' in player.player_id:
                home[pid] = (x, y)
            else:
                away[pid] = (x, y)
    return {'home': home, 'away': away}


def get_ball_position(frame, pitch_length=105, pitch_width=68):
    """Get ball coordinates from frame."""
    if frame.ball_coordinates:
        return (
            frame.ball_coordinates.x * pitch_length,
            frame.ball_coordinates.y * pitch_width
        )
    return None


def get_possession(frame, pitch_length=105, pitch_width=68):
    """Determine possession by finding closest player to ball."""
    import math
    if not frame.ball_coordinates:
        return None

    ball_x = frame.ball_coordinates.x * pitch_length
    ball_y = frame.ball_coordinates.y * pitch_width

    closest_dist = float('inf')
    closest_team = None

    for player, data in frame.players_data.items():
        if data.coordinates:
            px = data.coordinates.x * pitch_length
            py = data.coordinates.y * pitch_width
            dist = math.sqrt((px - ball_x)**2 + (py - ball_y)**2)
            if dist < closest_dist:
                closest_dist = dist
                closest_team = 'home' if 'home' in player.player_id else 'away'

    # Only count as possession if within ~3 meters
    if closest_dist < 3:
        return closest_team
    return 'contested'


def draw_ball(ax, x, y, color='white'):
    """Draw ball on pitch."""
    # Glow effect
    glow = plt.Circle((x, y), 2.5, color=color, alpha=0.3, zorder=8)
    ax.add_patch(glow)
    # Ball
    ball = plt.Circle((x, y), 1.5, color='white', ec='black', linewidth=1, zorder=9)
    ax.add_patch(ball)


def draw_team_shape(ax, positions, is_home=True):
    """Draw convex hull for team."""
    from scipy.spatial import ConvexHull

    if len(positions) < 4:
        return

    # Find goalkeeper (closest to goal)
    goal_x = 0 if is_home else 105
    gk_id = min(positions.keys(), key=lambda pid: abs(positions[pid][0] - goal_x))

    # Get outfield positions
    outfield = {pid: pos for pid, pos in positions.items() if pid != gk_id}

    if len(outfield) < 3:
        return

    points = np.array(list(outfield.values()))

    try:
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        hull_points = np.vstack([hull_points, hull_points[0]])

        color = '#3498db' if is_home else '#e74c3c'

        polygon = mpatches.Polygon(
            hull_points, closed=True,
            facecolor=color, edgecolor=color,
            alpha=0.15, linewidth=2, zorder=2
        )
        ax.add_patch(polygon)
        ax.plot(hull_points[:, 0], hull_points[:, 1],
                color=color, linewidth=2, alpha=0.6, zorder=3)
    except:
        pass


def render_frame(frame_data, ball_pos=None, home_name="Home", away_name="Away", show_shapes=True, possession=None):
    """Render a single frame."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    for ax, team_key, team_name in [(ax1, 'home', home_name), (ax2, 'away', away_name)]:
        draw_pitch(ax)
        positions = frame_data.get(team_key, {})

        if positions:
            # Draw shape lines first
            if show_shapes:
                draw_team_shape(ax, positions, is_home=(team_key == 'home'))

            # Classify and draw players
            v_buckets = classify_team_vertical(positions)
            h_buckets = classify_team_horizontal(positions)
            formation = detect_formation(positions)

            for pid, (x, y) in positions.items():
                draw_player_marker(ax, x, y,
                                 v_buckets.get(pid, 2),
                                 h_buckets.get(pid, 2),
                                 player_num=pid, radius=2.5)

            # Draw ball
            if ball_pos:
                draw_ball(ax, ball_pos[0], ball_pos[1])

            # Draw possession indicator
            if possession:
                if possession == 'home':
                    poss_text = f"⚽ {home_name}"
                    poss_color = '#3498db'  # Blue
                elif possession == 'away':
                    poss_text = f"⚽ {away_name}"
                    poss_color = '#e74c3c'  # Red
                else:
                    poss_text = "⚽ CONTESTED"
                    poss_color = '#888888'  # Gray
                ax.text(52.5, 72, poss_text, fontsize=12, fontweight='bold',
                       color=poss_color, ha='center', va='bottom', zorder=10)

            title = f"{team_name}"
            if formation:
                title += f"\n{formation}"
            ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=15)

    fig.tight_layout()
    return fig


# Main app
st.title("⚽ Shape Graph Visualization")

# Initialize session state
if 'current_frame' not in st.session_state:
    st.session_state.current_frame = 5000
if 'log' not in st.session_state:
    st.session_state.log = []
if 'debug_log' not in st.session_state:
    st.session_state.debug_log = []
if 'perf_metrics' not in st.session_state:
    st.session_state.perf_metrics = {'extract': 0, 'render': 0, 'display': 0, 'total': 0, 'fps': 0}

def add_debug(msg):
    """Add message to debug trace."""
    st.session_state.debug_log.append(f"[TRACE] {msg}")
    if len(st.session_state.debug_log) > 100:
        st.session_state.debug_log = st.session_state.debug_log[-100:]

def on_slider_change():
    """Callback when slider is manually changed."""
    st.session_state.current_frame = st.session_state._slider_widget
    add_debug(f"Slider changed to {st.session_state.current_frame}")

# Sidebar controls
with st.sidebar:
    st.header("Controls")

    # Load data
    with st.spinner("Loading tracking data..."):
        dataset = load_data()

    st.success(f"Loaded {len(dataset.frames):,} frames")

    # Frame selection - uses current_frame as value, _slider_widget as key
    frame_idx = st.slider(
        "Frame",
        min_value=0,
        max_value=len(dataset.frames) - 1,
        value=st.session_state.current_frame,
        key="_slider_widget",
        on_change=on_slider_change
    )

    # Auto-play
    auto_play = st.checkbox("Auto-play", value=False)
    speed = st.slider("Speed (frames/update)", 1, 50, 10)

    # Display options
    st.subheader("Display Options")
    show_shapes = st.checkbox("Show team shapes", value=True)
    show_ball = st.checkbox("Show ball", value=True)

    # Team names
    home_name = st.text_input("Home Team", "Home")
    away_name = st.text_input("Away Team", "Away")

    # Performance metrics
    st.subheader("Performance")
    pm = st.session_state.perf_metrics
    st.metric("FPS", f"{pm['fps']:.1f}")
    st.caption(f"Extract: {pm['extract']:.1f}ms | Render: {pm['render']:.1f}ms | Display: {pm['display']:.1f}ms")

# Main content
col1, col2 = st.columns([3, 1])

# Use current_frame from session state
current_frame = st.session_state.current_frame
add_debug(f"render_frame() called with frame={current_frame}")

with col1:
    # Time: Data extraction
    t0 = time.perf_counter()
    frame = dataset.frames[current_frame]
    frame_data = extract_positions(frame)
    ball_pos = get_ball_position(frame) if show_ball else None
    possession = get_possession(frame)
    t1 = time.perf_counter()
    extract_ms = (t1 - t0) * 1000

    # Time: Matplotlib render
    fig = render_frame(frame_data, ball_pos, home_name, away_name, show_shapes, possession)
    t2 = time.perf_counter()
    render_ms = (t2 - t1) * 1000

    # Time: Streamlit display
    st.pyplot(fig)
    plt.close(fig)
    t3 = time.perf_counter()
    display_ms = (t3 - t2) * 1000

    total_ms = (t3 - t0) * 1000
    fps = 1000 / total_ms if total_ms > 0 else 0

    # Store metrics
    st.session_state.perf_metrics = {
        'extract': extract_ms,
        'render': render_ms,
        'display': display_ms,
        'total': total_ms,
        'fps': fps
    }

with col2:
    st.subheader("Activity Log")

    # Add current frame to log with possession (avoid duplicates)
    poss_str = possession.upper() if possession else "N/A"
    log_entry = f"Frame {current_frame} | Poss: {poss_str}"
    if not st.session_state.log or st.session_state.log[-1] != log_entry:
        st.session_state.log.append(log_entry)
        if len(st.session_state.log) > 50:
            st.session_state.log = st.session_state.log[-50:]

    # Display log
    log_html = "<div class='log-container'>"
    for entry in reversed(st.session_state.log[-20:]):
        log_html += f"<div>{entry}</div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

    # Debug Trace panel
    with st.expander("Debug Trace", expanded=False):
        debug_html = "<div class='log-container'>"
        for entry in reversed(st.session_state.debug_log[-30:]):
            debug_html += f"<div style='color:#888;'>{entry}</div>"
        debug_html += "</div>"
        st.markdown(debug_html, unsafe_allow_html=True)

# Auto-play logic
add_debug(f"auto_play={auto_play}, current_frame={current_frame}")

if auto_play:
    # Higher speed = skip more frames (speed is frames per update)
    old_frame = st.session_state.current_frame
    new_frame = (old_frame + speed) % len(dataset.frames)
    add_debug(f"Autoplay: {old_frame} -> {new_frame} (skip {speed})")
    st.session_state.current_frame = new_frame

    # Log advancement
    st.session_state.log.append(f"[Autoplay] Frame {old_frame} -> {new_frame}")

    # Minimum delay for UI responsiveness (lets browser process events)
    time.sleep(0.05)

    add_debug("Calling st.rerun()")
    st.rerun()

# Footer
st.markdown("---")
st.caption("Shape Graph Visualization | Metrica Sample Data")
