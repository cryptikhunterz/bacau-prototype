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
from time_utils import frame_to_match_time
from compactness import compute_ci, is_defending
from shape_lines import get_outfield_positions

# Game metadata for time conversion (Game 3821)
GAME_METADATA = {
    'fps': 29.97,
    'startPeriod1': 118.719,
    'endPeriod1': 3177.578,
    'startPeriod2': 3244.244,
    'endPeriod2': 6434.634
}

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
    """Load PFF World Cup 2022 tracking data (cached)."""
    from kloppy import pff
    base_path = "Fifa world cup 2022 data"
    game_id = "3821"  # Germany vs Japan (famous upset - Japan won 2-1)
    return pff.load_tracking(
        meta_data=os.path.join(base_path, "Metadata", f"{game_id}.json"),
        roster_meta_data=os.path.join(base_path, "Rosters", f"{game_id}.json"),
        raw_data=os.path.join(base_path, "Tracking Data", f"{game_id}.jsonl.bz2")
    )


def extract_positions(frame, pitch_length=105, pitch_width=68):
    """Extract player positions from frame."""
    home = {}
    away = {}
    for player, data in frame.players_data.items():
        if data.coordinates:
            x = data.coordinates.x * pitch_length
            y = data.coordinates.y * pitch_width
            # Get jersey number - try jersey_no first, then parse player_id
            if hasattr(player, 'jersey_no') and player.jersey_no:
                pid = int(player.jersey_no)
            elif '_' in str(player.player_id):
                pid = int(player.player_id.split('_')[1])
            else:
                pid = int(player.player_id) if str(player.player_id).isdigit() else 0
            # Determine team from player's team attribute or player_id
            if hasattr(player, 'team') and player.team:
                is_home = player.team.ground.value == 'home' if hasattr(player.team.ground, 'value') else str(player.team.ground) == 'home'
            else:
                is_home = 'home' in str(player.player_id).lower()
            if is_home:
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
                # Determine team from player's team attribute or player_id
                if hasattr(player, 'team') and player.team:
                    closest_team = 'home' if (player.team.ground.value == 'home' if hasattr(player.team.ground, 'value') else str(player.team.ground) == 'home') else 'away'
                else:
                    closest_team = 'home' if 'home' in str(player.player_id).lower() else 'away'

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


def compute_team_stats(positions):
    """Compute team shape statistics from positions dict."""
    from scipy.spatial import ConvexHull
    import math

    if len(positions) < 3:
        return {'area': 0, 'compactness': 0, 'width': 0, 'depth': 0, 'centroid': (0, 0)}

    points = np.array(list(positions.values()))
    xs = points[:, 0]
    ys = points[:, 1]

    # Centroid
    centroid = (np.mean(xs), np.mean(ys))

    # Width (lateral spread) and Depth (vertical spread)
    width = np.max(ys) - np.min(ys)
    depth = np.max(xs) - np.min(xs)

    # Compactness (average distance from centroid)
    distances = [math.sqrt((x - centroid[0])**2 + (y - centroid[1])**2) for x, y in positions.values()]
    compactness = np.mean(distances)

    # Convex hull area
    try:
        hull = ConvexHull(points)
        area = hull.volume  # In 2D, volume gives area
    except:
        area = 0

    return {
        'area': area,
        'compactness': compactness,
        'width': width,
        'depth': depth,
        'centroid': centroid
    }


def get_ball_carrier(frame, pitch_length=105, pitch_width=68):
    """Get the player closest to the ball."""
    import math
    if not frame.ball_coordinates:
        return None, None, None

    ball_x = frame.ball_coordinates.x * pitch_length
    ball_y = frame.ball_coordinates.y * pitch_width

    closest_dist = float('inf')
    closest_player = None
    closest_team = None

    for player, data in frame.players_data.items():
        if data.coordinates:
            px = data.coordinates.x * pitch_length
            py = data.coordinates.y * pitch_width
            dist = math.sqrt((px - ball_x)**2 + (py - ball_y)**2)
            if dist < closest_dist:
                closest_dist = dist
                closest_player = player
                if hasattr(player, 'team') and player.team:
                    closest_team = 'home' if (player.team.ground.value == 'home' if hasattr(player.team.ground, 'value') else str(player.team.ground) == 'home') else 'away'
                else:
                    closest_team = 'home' if 'home' in str(player.player_id).lower() else 'away'

    if closest_player and closest_dist < 5:
        jersey = closest_player.jersey_no if hasattr(closest_player, 'jersey_no') else '?'
        name = closest_player.name if hasattr(closest_player, 'name') else str(closest_player.player_id)
        return f"#{jersey} {name}", closest_team, closest_dist
    return None, None, None


@st.cache_resource
def load_events():
    """Load PFF event data for game 3821."""
    import json
    event_path = "Fifa world cup 2022 data/Event Data/3821.json"
    try:
        with open(event_path) as f:
            return json.load(f)
    except:
        return []


# Event type mappings (PFF abbreviations to full names)
POSSESSION_EVENT_NAMES = {
    'PA': 'Pass',
    'IT': 'Interception',
    'CH': 'Challenge',
    'RE': 'Reception',
    'CL': 'Clearance',
    'CR': 'Cross',
    'TC': 'Tackle',
    'SH': 'Shot',
    'BC': 'Ball Control',
}

GAME_EVENT_NAMES = {
    'OTB': 'On Ball',
    'OUT': 'Out of Play',
    'SUB': 'Substitution',
    'END': 'Period End',
    'FIRSTKICKOFF': 'Kickoff (1H)',
    'SECONDKICKOFF': 'Kickoff (2H)',
}

# Zone boundaries for tactical analysis (based on pitch width normalized 0-1)
# Zones: LW (Left Wing) | LHS (Left Half Space) | C (Center) | RHS (Right Half Space) | RW (Right Wing)
ZONE_BOUNDARIES = [
    ('LW', 0, 0.18),
    ('LHS', 0.18, 0.36),
    ('C', 0.36, 0.64),
    ('RHS', 0.64, 0.82),
    ('RW', 0.82, 1.0)
]

# Team IDs for Germany vs Japan (game 3821)
TEAM_IDS = {
    'Germany': 368,
    'Japan': 57
}


def get_zone(y_meters, pitch_width=68):
    """Determine zone from y-coordinate in meters.

    PFF uses centered coordinates: y=0 at center, range approx -34 to +34.
    Convert to normalized 0-1 where 0=LW edge, 1=RW edge.
    """
    half_width = pitch_width / 2  # 34m
    # Convert from centered to 0-1 normalized
    y_normalized = (y_meters + half_width) / pitch_width
    # Clamp to 0-1 range
    y_normalized = max(0, min(1, y_normalized))
    for name, low, high in ZONE_BOUNDARIES:
        if low <= y_normalized < high:
            return name
    return 'C'  # Default to center


@st.cache_resource
def calculate_zone_stats(events, team_name):
    """
    Calculate zone-based stats for a team.

    Returns dict with zones as keys, each containing event counts:
    {
        'LW': {'PA': 0, 'RE': 0, 'SH': 0, 'TC': 0, 'CH': 0, 'IT': 0, 'CL': 0, 'CR': 0},
        'LHS': {...}, 'C': {...}, 'RHS': {...}, 'RW': {...}
    }
    """
    # Initialize stats structure
    event_types = ['PA', 'RE', 'SH', 'TC', 'CH', 'IT', 'CL', 'CR']
    stats = {zone: {et: 0 for et in event_types} for zone, _, _ in ZONE_BOUNDARIES}

    team_id = TEAM_IDS.get(team_name)
    if not team_id:
        return stats

    for event in events:
        # Check team
        ge = event.get('gameEvents', {})
        if ge.get('teamId') != team_id:
            continue

        # Get possession event type
        pe = event.get('possessionEvents', {})
        if not pe:
            continue
        event_type = pe.get('possessionEventType')
        if event_type not in event_types:
            continue

        # Get ball position for zone
        ball = event.get('ball', [])
        if not ball or len(ball) == 0:
            continue
        y = ball[0].get('y', 34)  # Default to center if missing

        # Determine zone and increment count
        zone = get_zone(y)
        stats[zone][event_type] += 1

    return stats


def calculate_player_zone_stats(events, player_id):
    """
    Calculate zone-based stats for a specific player.

    Args:
        events: List of PFF events
        player_id: Player ID to filter by (can be string from kloppy)

    Returns dict with zones as keys, each containing event counts.
    """
    event_types = ['PA', 'RE', 'SH', 'TC', 'CH', 'IT', 'CL', 'CR']
    stats = {zone: {et: 0 for et in event_types} for zone, _, _ in ZONE_BOUNDARIES}

    # Convert player_id to int for comparison (kloppy uses strings, events use ints)
    try:
        player_id_int = int(player_id)
    except (ValueError, TypeError):
        return stats

    for event in events:
        ge = event.get('gameEvents', {})
        # Check if this player is involved (compare as int)
        if ge.get('playerId') != player_id_int:
            continue

        pe = event.get('possessionEvents', {})
        if not pe:
            continue
        event_type = pe.get('possessionEventType')
        if event_type not in event_types:
            continue

        ball = event.get('ball', [])
        if not ball or len(ball) == 0:
            continue
        y = ball[0].get('y', 0)

        zone = get_zone(y)
        stats[zone][event_type] += 1

    return stats


def collect_team_event_positions(events, team_name, event_type_code):
    """
    Collect x,y positions for all events of a specific type for a team.

    Args:
        events: List of PFF events
        team_name: 'Germany' or 'Japan'
        event_type_code: Event type code ('PA', 'RE', 'SH', etc.)

    Returns:
        List of (x, y) tuples normalized to 0-1 range
    """
    positions = []
    team_id = TEAM_IDS.get(team_name)
    if not team_id:
        return positions

    for event in events:
        # Check team
        ge = event.get('gameEvents', {})
        if ge.get('teamId') != team_id:
            continue

        # Get possession event type
        pe = event.get('possessionEvents', {})
        if not pe:
            continue
        event_type = pe.get('possessionEventType')
        if event_type != event_type_code:
            continue

        # Get ball position
        ball = event.get('ball', [])
        if not ball or len(ball) == 0:
            continue

        # PFF coordinates: BOTH x and y are centered at pitch center
        # x ranges from -52.5 to +52.5 (centered)
        # y ranges from -34 to +34 (centered)
        x = ball[0].get('x', 0)  # Default to center if missing
        y = ball[0].get('y', 0)  # Default to center if missing

        # Normalize to 0-1 range (shift from centered to 0-based)
        x_norm = (x + 52.5) / 105.0  # shift from -52.5..+52.5 to 0..105, then to 0..1
        y_norm = (y + 34) / 68.0     # shift from -34..+34 to 0..68, then to 0..1

        # Clamp to valid range
        x_norm = max(0, min(1, x_norm))
        y_norm = max(0, min(1, y_norm))

        positions.append((x_norm, y_norm))

    return positions


def collect_player_event_positions(events, player_id, event_type_code):
    """
    Collect x,y positions for all events of a specific type for a player.

    Args:
        events: List of PFF events
        player_id: Player ID to filter by (can be string from kloppy)
        event_type_code: Event type code ('PA', 'RE', 'SH', etc.)

    Returns:
        List of (x, y) tuples normalized to 0-1 range
    """
    positions = []

    # Convert player_id to int for comparison (kloppy uses strings, events use ints)
    try:
        player_id_int = int(player_id)
    except (ValueError, TypeError):
        return positions

    for event in events:
        ge = event.get('gameEvents', {})
        # Check if this player is involved (compare as int)
        if ge.get('playerId') != player_id_int:
            continue

        pe = event.get('possessionEvents', {})
        if not pe:
            continue
        event_type = pe.get('possessionEventType')
        if event_type != event_type_code:
            continue

        ball = event.get('ball', [])
        if not ball or len(ball) == 0:
            continue

        # PFF coordinates: BOTH x and y are centered at pitch center
        # x ranges from -52.5 to +52.5 (centered)
        # y ranges from -34 to +34 (centered)
        x = ball[0].get('x', 0)
        y = ball[0].get('y', 0)

        # Normalize to 0-1 range (shift from centered to 0-based)
        x_norm = (x + 52.5) / 105.0
        y_norm = (y + 34) / 68.0

        # Clamp to valid range
        x_norm = max(0, min(1, x_norm))
        y_norm = max(0, min(1, y_norm))

        positions.append((x_norm, y_norm))

    return positions


def filter_events_by_half(events, half_selection):
    """
    Filter events by match half.

    Args:
        events: List of PFF events
        half_selection: "Full Match", "1st Half", or "2nd Half"

    Returns:
        Filtered list of events
    """
    if half_selection == "Full Match":
        return events

    filtered = []
    for event in events:
        # Period is in gameEvents.period (1 = 1st half, 2 = 2nd half)
        ge = event.get('gameEvents', {})
        period = ge.get('period')

        if half_selection == "1st Half" and period == 1:
            filtered.append(event)
        elif half_selection == "2nd Half" and period == 2:
            filtered.append(event)

    return filtered


def draw_event_scatter(positions, title, team_color='#FFFFFF'):
    """
    Draw a football pitch with event locations as scatter dots.

    Args:
        positions: List of (x, y) tuples in normalized 0-1 coordinates
        title: Chart title
        team_color: Color for dots

    Returns matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    # Pitch dimensions (normalized 0-1)
    pitch_color = '#2d5a27'
    line_color = 'white'
    lw = 2

    ax.set_facecolor(pitch_color)
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.12, 1.08)

    # === PITCH MARKINGS ===

    # Outer boundary
    ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color=line_color, linewidth=lw, zorder=2)

    # Halfway line
    ax.plot([0.5, 0.5], [0, 1], color=line_color, linewidth=lw, zorder=2)

    # Center circle (radius ~9.15m on 105m pitch = ~0.087)
    center_circle = plt.Circle((0.5, 0.5), 0.087, fill=False, color=line_color, linewidth=lw, zorder=2)
    ax.add_patch(center_circle)

    # Center spot
    ax.scatter(0.5, 0.5, color=line_color, s=30, zorder=3)

    # Penalty areas
    pa_depth = 0.157  # 16.5m / 105m
    pa_y_start = (1 - 0.593) / 2
    pa_y_end = 1 - pa_y_start

    # Left penalty area
    ax.plot([0, pa_depth], [pa_y_start, pa_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([pa_depth, pa_depth], [pa_y_start, pa_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([pa_depth, 0], [pa_y_end, pa_y_end], color=line_color, linewidth=lw, zorder=2)

    # Right penalty area
    ax.plot([1, 1 - pa_depth], [pa_y_start, pa_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - pa_depth, 1 - pa_depth], [pa_y_start, pa_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - pa_depth, 1], [pa_y_end, pa_y_end], color=line_color, linewidth=lw, zorder=2)

    # Goal areas
    ga_depth = 0.052  # 5.5m / 105m
    ga_y_start = (1 - 0.269) / 2
    ga_y_end = 1 - ga_y_start

    # Left goal area
    ax.plot([0, ga_depth], [ga_y_start, ga_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([ga_depth, ga_depth], [ga_y_start, ga_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([ga_depth, 0], [ga_y_end, ga_y_end], color=line_color, linewidth=lw, zorder=2)

    # Right goal area
    ax.plot([1, 1 - ga_depth], [ga_y_start, ga_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - ga_depth, 1 - ga_depth], [ga_y_start, ga_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - ga_depth, 1], [ga_y_end, ga_y_end], color=line_color, linewidth=lw, zorder=2)

    # Goals
    goal_width = 0.108
    goal_depth = 0.02
    goal_y_start = (1 - goal_width) / 2
    goal_y_end = 1 - goal_y_start

    # Left goal
    ax.plot([0, -goal_depth], [goal_y_start, goal_y_start], color=line_color, linewidth=3, zorder=2)
    ax.plot([-goal_depth, -goal_depth], [goal_y_start, goal_y_end], color=line_color, linewidth=3, zorder=2)
    ax.plot([-goal_depth, 0], [goal_y_end, goal_y_end], color=line_color, linewidth=3, zorder=2)

    # Right goal
    ax.plot([1, 1 + goal_depth], [goal_y_start, goal_y_start], color=line_color, linewidth=3, zorder=2)
    ax.plot([1 + goal_depth, 1 + goal_depth], [goal_y_start, goal_y_end], color=line_color, linewidth=3, zorder=2)
    ax.plot([1 + goal_depth, 1], [goal_y_end, goal_y_end], color=line_color, linewidth=3, zorder=2)

    # Penalty spots
    ax.scatter(0.105, 0.5, color=line_color, s=20, zorder=3)
    ax.scatter(1 - 0.105, 0.5, color=line_color, s=20, zorder=3)

    # === SCATTER DOTS ===
    if positions:
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        ax.scatter(xs, ys, c=team_color, s=50, alpha=0.6, edgecolors='white',
                   linewidths=0.5, zorder=5)

    # Count label
    count = len(positions)
    ax.text(0.5, -0.07, f"{count} events",
            ha='center', va='top', color='white', fontsize=12, fontweight='bold')

    # Goal labels
    ax.text(-0.04, 0.5, 'GOAL', ha='center', va='center', color='#888888',
            fontsize=9, fontweight='bold', rotation=90)
    ax.text(1.04, 0.5, 'GOAL', ha='center', va='center', color='#888888',
            fontsize=9, fontweight='bold', rotation=90)

    # Title
    ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=15)
    ax.axis('off')
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig


def create_zone_bar_chart(stats, title, team_color='#3498db'):
    """
    Create a horizontal bar chart showing events by zone.

    Args:
        stats: Zone stats dict from calculate_zone_stats or calculate_player_zone_stats
        title: Chart title
        team_color: Color for bars

    Returns matplotlib figure
    """
    zones = ['LW', 'LHS', 'C', 'RHS', 'RW']
    event_labels = ['PA', 'RE', 'SH', 'TC', 'CH', 'IT', 'CL', 'CR']
    event_names = ['Pass', 'Reception', 'Shot', 'Tackle', 'Challenge', 'Intercept', 'Clearance', 'Cross']

    fig, axes = plt.subplots(2, 4, figsize=(12, 6))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    fig.suptitle(title, fontsize=14, fontweight='bold', color='white')

    for idx, (et, et_name) in enumerate(zip(event_labels, event_names)):
        ax = axes[idx // 4, idx % 4]
        ax.set_facecolor(BACKGROUND_COLOR)

        values = [stats[z][et] for z in zones]
        bars = ax.barh(zones, values, color=team_color, alpha=0.8)

        ax.set_title(et_name, fontsize=10, color='white')
        ax.tick_params(axis='both', colors='white', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')

        # Add value labels
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, str(val),
                       va='center', fontsize=8, color='white')

    plt.tight_layout()
    return fig


def create_zone_heatmap(stats, title, team_color='#3498db'):
    """
    Create a compact zone summary heatmap.

    Args:
        stats: Zone stats dict
        title: Chart title
        team_color: Base color for heatmap

    Returns matplotlib figure
    """
    zones = ['LW', 'LHS', 'C', 'RHS', 'RW']
    event_labels = ['PA', 'RE', 'SH', 'TC', 'CH', 'IT', 'CL', 'CR']
    event_names = ['Pass', 'Recept', 'Shot', 'Tackle', 'Chall', 'Interc', 'Clear', 'Cross']

    # Build data matrix
    data = np.array([[stats[z][et] for z in zones] for et in event_labels])

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # Create heatmap with team color
    from matplotlib.colors import LinearSegmentedColormap
    colors = [BACKGROUND_COLOR, team_color]
    cmap = LinearSegmentedColormap.from_list('custom', colors)

    im = ax.imshow(data, cmap=cmap, aspect='auto')

    # Labels
    ax.set_xticks(np.arange(len(zones)))
    ax.set_yticks(np.arange(len(event_names)))
    ax.set_xticklabels(zones, color='white', fontsize=10)
    ax.set_yticklabels(event_names, color='white', fontsize=9)

    # Add text annotations
    for i in range(len(event_names)):
        for j in range(len(zones)):
            val = data[i, j]
            text_color = 'white' if val > data.max() * 0.3 else '#888888'
            ax.text(j, i, str(val), ha='center', va='center',
                   color=text_color, fontsize=9, fontweight='bold')

    ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.tight_layout()
    return fig


def draw_zone_pitch(zone_stats, event_type, title="Zone Activity", team_color='#3498db'):
    """
    Draw a football pitch with full markings and zone shading overlay.

    Args:
        zone_stats: Dict with zone stats from calculate_zone_stats or calculate_player_zone_stats
        event_type: Event type code ('PA', 'RE', 'SH', etc.)
        title: Chart title
        team_color: Base color for zone shading

    Returns matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    # Pitch dimensions (normalized 0-1 for x=length, y=width)
    pitch_color = '#2d5a27'
    line_color = 'white'
    lw = 2

    ax.set_facecolor(pitch_color)
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.12, 1.08)

    # === PITCH MARKINGS (draw first, before zone overlay) ===

    # Outer boundary
    ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color=line_color, linewidth=lw, zorder=2)

    # Halfway line (vertical, at x=0.5)
    ax.plot([0.5, 0.5], [0, 1], color=line_color, linewidth=lw, zorder=2)

    # Center circle (radius ~9.15m on 105m pitch = ~0.087)
    center_circle = plt.Circle((0.5, 0.5), 0.087, fill=False, color=line_color, linewidth=lw, zorder=2)
    ax.add_patch(center_circle)

    # Center spot
    ax.scatter(0.5, 0.5, color=line_color, s=30, zorder=3)

    # Penalty areas (16.5m deep on 105m = 0.157, 40.3m wide on 68m = 0.593 centered)
    pa_depth = 0.157
    pa_y_start = (1 - 0.593) / 2  # ~0.203
    pa_y_end = 1 - pa_y_start     # ~0.797

    # Left penalty area
    ax.plot([0, pa_depth], [pa_y_start, pa_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([pa_depth, pa_depth], [pa_y_start, pa_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([pa_depth, 0], [pa_y_end, pa_y_end], color=line_color, linewidth=lw, zorder=2)

    # Right penalty area
    ax.plot([1, 1 - pa_depth], [pa_y_start, pa_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - pa_depth, 1 - pa_depth], [pa_y_start, pa_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - pa_depth, 1], [pa_y_end, pa_y_end], color=line_color, linewidth=lw, zorder=2)

    # Goal areas (5.5m deep = 0.052, 18.32m wide on 68m = 0.269 centered)
    ga_depth = 0.052
    ga_y_start = (1 - 0.269) / 2  # ~0.365
    ga_y_end = 1 - ga_y_start     # ~0.635

    # Left goal area
    ax.plot([0, ga_depth], [ga_y_start, ga_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([ga_depth, ga_depth], [ga_y_start, ga_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([ga_depth, 0], [ga_y_end, ga_y_end], color=line_color, linewidth=lw, zorder=2)

    # Right goal area
    ax.plot([1, 1 - ga_depth], [ga_y_start, ga_y_start], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - ga_depth, 1 - ga_depth], [ga_y_start, ga_y_end], color=line_color, linewidth=lw, zorder=2)
    ax.plot([1 - ga_depth, 1], [ga_y_end, ga_y_end], color=line_color, linewidth=lw, zorder=2)

    # Goals (7.32m wide on 68m = 0.108 centered, extending outside pitch)
    goal_width = 0.108
    goal_depth = 0.02
    goal_y_start = (1 - goal_width) / 2  # ~0.446
    goal_y_end = 1 - goal_y_start        # ~0.554

    # Left goal (extends left of x=0)
    ax.plot([0, -goal_depth], [goal_y_start, goal_y_start], color=line_color, linewidth=3, zorder=2)
    ax.plot([-goal_depth, -goal_depth], [goal_y_start, goal_y_end], color=line_color, linewidth=3, zorder=2)
    ax.plot([-goal_depth, 0], [goal_y_end, goal_y_end], color=line_color, linewidth=3, zorder=2)

    # Right goal (extends right of x=1)
    ax.plot([1, 1 + goal_depth], [goal_y_start, goal_y_start], color=line_color, linewidth=3, zorder=2)
    ax.plot([1 + goal_depth, 1 + goal_depth], [goal_y_start, goal_y_end], color=line_color, linewidth=3, zorder=2)
    ax.plot([1 + goal_depth, 1], [goal_y_end, goal_y_end], color=line_color, linewidth=3, zorder=2)

    # Penalty spots (11m from goal = 0.105)
    ax.scatter(0.105, 0.5, color=line_color, s=20, zorder=3)
    ax.scatter(1 - 0.105, 0.5, color=line_color, s=20, zorder=3)

    # === ZONE SHADING (transparent overlay on top of pitch) ===
    # Zones are horizontal bands (y-axis) since tactical zones are based on pitch width
    zones = [
        ('LW', 0, 0.18),
        ('LHS', 0.18, 0.36),
        ('C', 0.36, 0.64),
        ('RHS', 0.64, 0.82),
        ('RW', 0.82, 1.0)
    ]

    # Get counts for each zone
    counts = [zone_stats[z][event_type] for z, _, _ in zones]
    max_count = max(counts) if max(counts) > 0 else 1

    # Create colormap from transparent to team color
    from matplotlib.colors import LinearSegmentedColormap
    colors_map = [(0.1, 0.2, 0.1, 0.0), team_color]  # Transparent to team color
    cmap = LinearSegmentedColormap.from_list('zone', colors_map)

    for (zone_name, y_start, y_end), count in zip(zones, counts):
        intensity = count / max_count if max_count > 0 else 0

        # Semi-transparent zone rectangle
        zone_alpha = 0.25 + intensity * 0.35  # Range 0.25 to 0.6
        zone_color = cmap(0.3 + intensity * 0.7)

        rect = plt.Rectangle((0, y_start), 1, y_end - y_start,
                             facecolor=zone_color, edgecolor='white',
                             linewidth=1, linestyle='--', alpha=zone_alpha, zorder=1)
        ax.add_patch(rect)

        # Zone label at bottom (outside pitch)
        ax.text(0.5, y_start - 0.03, zone_name,
               ha='center', va='top', color='white', fontsize=10, fontweight='bold', alpha=0.9)

        # Count in center of zone with background box for visibility
        y_center = (y_start + y_end) / 2
        ax.text(0.5, y_center, str(count),
               ha='center', va='center', color='white', fontsize=20, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6), zorder=4)

    # Direction arrow and goal labels
    ax.text(-0.04, 0.5, 'GOAL', ha='center', va='center', color='#888888',
           fontsize=9, fontweight='bold', rotation=90)
    ax.text(1.04, 0.5, 'GOAL', ha='center', va='center', color='#888888',
           fontsize=9, fontweight='bold', rotation=90)

    # Title
    ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=15)
    ax.axis('off')
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig


# Event type mapping for selectors
EVENT_TYPE_OPTIONS = {
    'Pass': 'PA',
    'Reception': 'RE',
    'Shot': 'SH',
    'Tackle': 'TC',
    'Challenge': 'CH',
    'Interception': 'IT',
    'Clearance': 'CL',
    'Cross': 'CR'
}


def print_zone_stats_summary(events):
    """Print zone stats to console for verification."""
    print("\n" + "="*60)
    print("ZONE STATS SUMMARY")
    print("="*60)

    for team in ['Germany', 'Japan']:
        stats = calculate_zone_stats(events, team)
        print(f"\n{team}:")
        print("-" * 50)

        # Header
        zones = ['LW', 'LHS', 'C', 'RHS', 'RW']
        print(f"{'Type':<8}", end="")
        for z in zones:
            print(f"{z:>8}", end="")
        print(f"{'Total':>10}")

        # Rows for each event type
        for et in ['PA', 'RE', 'SH', 'TC', 'CH', 'IT', 'CL', 'CR']:
            et_name = POSSESSION_EVENT_NAMES.get(et, et)[:7]
            print(f"{et_name:<8}", end="")
            total = 0
            for z in zones:
                count = stats[z][et]
                total += count
                print(f"{count:>8}", end="")
            print(f"{total:>10}")

        # Zone totals
        print(f"{'TOTAL':<8}", end="")
        grand_total = 0
        for z in zones:
            zone_total = sum(stats[z].values())
            grand_total += zone_total
            print(f"{zone_total:>8}", end="")
        print(f"{grand_total:>10}")

    print("\n" + "="*60 + "\n")


def get_events_near_time(events, video_time, window_seconds=5):
    """Get events within window_seconds of the given video time."""
    nearby = []
    for e in events:
        event_time = e.get('startTime', 0)
        if abs(event_time - video_time) <= window_seconds:
            ge = e.get('gameEvents', {})
            pe = e.get('possessionEvents', {})
            poss_code = pe.get('possessionEventType') if pe else None
            nearby.append({
                'time': event_time,
                'game_clock': ge.get('startFormattedGameClock', '??:??'),
                'event_type': ge.get('gameEventType', 'Unknown'),
                'poss_type': poss_code,
                'poss_name': POSSESSION_EVENT_NAMES.get(poss_code, poss_code) if poss_code else None,
                'player': ge.get('playerName', 'Unknown'),
                'team': ge.get('teamName', 'Unknown'),
                'target': pe.get('targetPlayerName') if pe else None
            })
    return sorted(nearby, key=lambda x: x['time'])


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


def render_frame(frame_data, ball_pos=None, home_name="Home", away_name="Away", show_shapes=True, possession=None, show_zones=False):
    """Render a single frame."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor(BACKGROUND_COLOR)

    for ax, team_key, team_name in [(ax1, 'home', home_name), (ax2, 'away', away_name)]:
        draw_pitch(ax, show_zones=show_zones)
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

    # Direction of play arrows below each pitch
    # Home team attacks RIGHT (→), Away team attacks LEFT (←)
    for ax, is_home in [(ax1, True), (ax2, False)]:
        if is_home:
            # Home: arrow pointing right
            ax.annotate('', xy=(0.85, -0.06), xytext=(0.15, -0.06),
                       arrowprops=dict(arrowstyle='->', color='white', lw=2),
                       xycoords='axes fraction')
            ax.text(0.5, -0.10, 'Direction of Play', ha='center', va='top',
                   color='#888888', fontsize=10, transform=ax.transAxes)
        else:
            # Away: arrow pointing left
            ax.annotate('', xy=(0.15, -0.06), xytext=(0.85, -0.06),
                       arrowprops=dict(arrowstyle='->', color='white', lw=2),
                       xycoords='axes fraction')
            ax.text(0.5, -0.10, 'Direction of Play', ha='center', va='top',
                   color='#888888', fontsize=10, transform=ax.transAxes)

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
if 'zone_stats_printed' not in st.session_state:
    st.session_state.zone_stats_printed = False
    # Print zone stats summary on first load
    events = load_events()
    if events:
        print_zone_stats_summary(events)

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
    with st.spinner("Loading PFF World Cup 2022 data..."):
        dataset = load_data()

    # Extract real team names from metadata
    if dataset.metadata.teams:
        default_home = dataset.metadata.teams[0].name
        default_away = dataset.metadata.teams[1].name
    else:
        default_home = "Home"
        default_away = "Away"

    st.success(f"Loaded {len(dataset.frames):,} frames")
    st.caption(f"Match: {default_home} vs {default_away}")

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
    show_zones = st.checkbox("Show tactical zones", value=True)

    # Team names (editable, with real names as default)
    home_name = st.text_input("Home Team", default_home)
    away_name = st.text_input("Away Team", default_away)

    # Player Rosters
    st.subheader("Rosters")
    with st.expander(f"{default_home} Players", expanded=False):
        if dataset.metadata.teams:
            for player in dataset.metadata.teams[0].players:
                jersey = player.jersey_no if hasattr(player, 'jersey_no') else "?"
                name = player.name if hasattr(player, 'name') else player.player_id
                st.caption(f"#{jersey} {name}")
    with st.expander(f"{default_away} Players", expanded=False):
        if dataset.metadata.teams and len(dataset.metadata.teams) > 1:
            for player in dataset.metadata.teams[1].players:
                jersey = player.jersey_no if hasattr(player, 'jersey_no') else "?"
                name = player.name if hasattr(player, 'name') else player.player_id
                st.caption(f"#{jersey} {name}")

    # Performance metrics
    st.subheader("Performance")
    pm = st.session_state.perf_metrics
    st.metric("FPS", f"{pm['fps']:.1f}")
    st.caption(f"Extract: {pm['extract']:.1f}ms | Render: {pm['render']:.1f}ms | Display: {pm['display']:.1f}ms")

    # CI Calibration section
    with st.expander("CI Calibration", expanded=False):
        st.caption("Adjust Compactness Index parameters")

        # Reference areas by block type
        st.markdown("**Reference Areas (m²)**")
        ref_area_high = st.slider(
            "High Press",
            min_value=400, max_value=1000, value=600, step=50,
            help="Target area when pressing high (smaller = stricter)"
        )
        ref_area_mid = st.slider(
            "Mid Block",
            min_value=300, max_value=800, value=450, step=50,
            help="Target area in mid block"
        )
        ref_area_low = st.slider(
            "Low Block",
            min_value=150, max_value=500, value=300, step=25,
            help="Target area when defending deep"
        )

        st.markdown("**Balance & Boundaries**")
        sigma = st.slider(
            "Balance Sensitivity (σ)",
            min_value=0.1, max_value=1.0, value=0.5, step=0.1,
            help="Lower = stricter penalty for unbalanced shapes"
        )
        boundary_low_mid = st.slider(
            "Low/Mid Boundary (%)",
            min_value=20, max_value=50, value=35, step=5,
            help="Below this = low block"
        )
        boundary_mid_high = st.slider(
            "Mid/High Boundary (%)",
            min_value=50, max_value=80, value=65, step=5,
            help="Above this = high press"
        )

    # Store CI config in session_state for use in stats display
    st.session_state.ci_config = {
        'ref_area_high': ref_area_high,
        'ref_area_mid': ref_area_mid,
        'ref_area_low': ref_area_low,
        'sigma': sigma,
        'boundary_low_mid': boundary_low_mid / 100,  # Convert % to decimal
        'boundary_mid_high': boundary_mid_high / 100  # Convert % to decimal
    }

# Main content with tabs
tab_shape, tab_zones = st.tabs(["📊 Shape Graph", "🎯 Zone Analysis"])

with tab_shape:
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
        fig = render_frame(frame_data, ball_pos, home_name, away_name, show_shapes, possession, show_zones)
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
        match_time = frame_to_match_time(current_frame, GAME_METADATA)
        log_entry = f"{match_time} | Poss: {poss_str}"
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

    # Stats and Events Panel
    st.markdown("---")
    st.subheader("Match Analysis")

    stats_col, events_col = st.columns(2)

    with stats_col:
        st.markdown("##### Team Shape Statistics")

        # Compute stats for both teams
        home_stats = compute_team_stats(frame_data.get('home', {}))
        away_stats = compute_team_stats(frame_data.get('away', {}))

        # Ball carrier info
        carrier, carrier_team, carrier_dist = get_ball_carrier(frame)

        # Get ball position and CI config for CI calculation
        ball_pos = get_ball_position(frame)
        ball_x = ball_pos[0] if ball_pos else 52.5  # Default to center if no ball
        ci_config = st.session_state.get('ci_config', None)

        # Compute CI for home team (only if defending)
        home_defending = is_defending(possession, ball_x, is_home=True)
        if home_defending:
            home_outfield = get_outfield_positions(frame_data.get('home', {}), is_home=True)
            home_ci = compute_ci(home_outfield, is_home=True, config=ci_config)
        else:
            home_ci = None

        # Compute CI for away team (only if defending)
        away_defending = is_defending(possession, ball_x, is_home=False)
        if away_defending:
            away_outfield = get_outfield_positions(frame_data.get('away', {}), is_home=False)
            away_ci = compute_ci(away_outfield, is_home=False, config=ci_config)
        else:
            away_ci = None

        # Create comparison metrics
        metric_col1, metric_col2 = st.columns(2)

        with metric_col1:
            st.markdown(f"**{home_name}**")
            st.metric("Area", f"{home_stats['area']:.0f} m²")
            # Block type (primary) with CI caption
            if home_ci:
                block_label = home_ci['block'].replace('_', ' ').title()
                st.metric("Block", block_label)
                st.caption(f"CI: {home_ci['ci']:.0f}/100")
            else:
                st.metric("Block", "In Possession")
                st.caption("CI: —")
            st.metric("Width", f"{home_stats['width']:.1f} m")
            st.metric("Depth", f"{home_stats['depth']:.1f} m")

        with metric_col2:
            st.markdown(f"**{away_name}**")
            st.metric("Area", f"{away_stats['area']:.0f} m²")
            # Block type (primary) with CI caption
            if away_ci:
                block_label = away_ci['block'].replace('_', ' ').title()
                st.metric("Block", block_label)
                st.caption(f"CI: {away_ci['ci']:.0f}/100")
            else:
                st.metric("Block", "In Possession")
                st.caption("CI: —")
            st.metric("Width", f"{away_stats['width']:.1f} m")
            st.metric("Depth", f"{away_stats['depth']:.1f} m")

        # Ball carrier
        if carrier:
            carrier_color = '#3498db' if carrier_team == 'home' else '#e74c3c'
            team_name_display = home_name if carrier_team == 'home' else away_name
            st.markdown(f"**Ball Carrier:** <span style='color:{carrier_color}'>{carrier}</span> ({team_name_display}) - {carrier_dist:.1f}m from ball", unsafe_allow_html=True)
        else:
            st.markdown("**Ball Carrier:** _None (ball loose)_")

        # CI explanation expander
        with st.expander("Understanding CI (Compactness Index)", expanded=False):
            st.markdown("""
## What is CI?

**Compactness Index** measures how tight your defensive shape is.
Higher = more compact = harder for opponents to play through.

| Score | Meaning | What it looks like |
|-------|---------|-------------------|
| **80-100** | Excellent | Bus parked, no gaps anywhere |
| **60-80** | Good | Organized shape, small gaps |
| **40-60** | Average | Shape okay but exploitable |
| **20-40** | Poor | Stretched, big spaces between lines |
| **0-20** | Very poor | Disorganized, no clear shape |

---

## Calibration Sliders (in sidebar)

### Reference Areas (m²)

These set the **target area** your team should occupy for each block type.

| Slider | Default | When to lower it |
|--------|---------|------------------|
| **High Press** | 600 m² | Your team should press tighter |
| **Mid Block** | 450 m² | You want more compact mid-block |
| **Low Block** | 300 m² | Your team parks the bus very tight |

**Example:** Your team plays very defensive. Change Low Block from 300 → 200.
Now they need to be tighter to score high CI.

---

### Balance Sensitivity (σ)

Controls how much **shape** matters vs just **size**.

Ideal defensive shape = **2:1 ratio** (twice as wide as deep)

| Value | Strictness | Use when... |
|-------|------------|-------------|
| **0.1-0.3** | Very strict | Team should maintain exact shape |
| **0.4-0.6** | Moderate | Normal use (default 0.5) |
| **0.7-1.0** | Lenient | Team often defends narrow/deep |

---

### Block Boundaries (%)

Define **where on the pitch** each block type starts.

| Slider | Default | Meaning |
|--------|---------|---------|
| **Low/Mid** | 35% | Below this = Low Block |
| **Mid/High** | 65% | Above this = High Press |

**Example:** Your team presses from halfway line → change Mid/High from 65% → 50%.

---

## Tips

- **Start with defaults** — they work for most teams
- **CI only shows when defending** — "In Possession" means that team has the ball
- **Compare across games** — if CI seems consistently off, adjust reference areas
            """)

    with events_col:
        st.markdown("##### Event Log (PFF)")

        # Event legend expander
        with st.expander("Event Legend", expanded=False):
            legend_cols = st.columns(2)
            with legend_cols[0]:
                st.markdown("""
**Ball Actions:**
- **Pass** - Ball passed to teammate
- **Cross** - Ball crossed into box
- **Shot** - Shot on goal
- **Clearance** - Defensive clear
""")
            with legend_cols[1]:
                st.markdown("""
**Defensive:**
- **Interception** - Ball won
- **Tackle** - Ball tackled away
- **Challenge** - 50/50 duel
- **Reception** - Ball received
""")

        # Load events
        events = load_events()

        # Calculate video time from frame index
        # PFF uses 29.97 fps, with startPeriod1 offset
        fps = 29.97
        start_period1 = 118.719  # From metadata for game 3821
        video_time = start_period1 + (current_frame / fps)

        # Get nearby events (within 3 seconds)
        nearby_events = get_events_near_time(events, video_time, window_seconds=3)

        st.caption(f"Video time: {video_time:.1f}s | Frame: {current_frame}")

        if nearby_events:
            for evt in nearby_events[-8:]:  # Show last 8 events
                poss_name = evt['poss_name'] or ''
                player = evt['player']
                team = evt['team']
                clock = evt['game_clock']
                target = evt['target']

                # Color by team
                if team == home_name or team == default_home:
                    color = '#3498db'
                elif team == away_name or team == default_away:
                    color = '#e74c3c'
                else:
                    color = '#888'

                # Format event string with full name
                evt_str = f"[{clock}] "
                if poss_name:
                    evt_str += f"**{poss_name}**: "
                evt_str += f"<span style='color:{color}'>{player}</span>"
                if target:
                    evt_str += f" → {target}"

                st.markdown(evt_str, unsafe_allow_html=True)
        else:
            st.caption("_No events near current time_")

        # Show total events for reference
        st.caption(f"Total events in match: {len(events)}")

# Zone Analysis Tab
with tab_zones:
    st.subheader("Event Location Analysis")
    st.caption("Scatter plot showing where events happen on the pitch. Each dot = one event location.")

    # Load events for zone analysis
    events = load_events()

    # Team columns
    zone_col1, zone_col2 = st.columns(2)

    with zone_col1:
        st.markdown(f"### {home_name}")

        # Half selector for team section
        team_half_home = st.selectbox(
            "Half",
            options=["Full Match", "1st Half", "2nd Half"],
            key="home_team_half"
        )

        # Team event selector
        team_event_home = st.selectbox(
            "Event Type",
            options=list(EVENT_TYPE_OPTIONS.keys()),
            key="home_team_event"
        )
        team_event_code_home = EVENT_TYPE_OPTIONS[team_event_home]

        # Filter events by half selection
        filtered_events_home_team = filter_events_by_half(events, team_half_home)

        # Collect event positions and draw scatter plot
        home_positions = collect_team_event_positions(filtered_events_home_team, home_name, team_event_code_home)
        fig_home = draw_event_scatter(home_positions,
                                      f"{home_name} - {team_event_home}s",
                                      team_color='#FFFFFF')  # White for Germany
        st.pyplot(fig_home)
        plt.close(fig_home)

        # Player Analysis section
        st.markdown("---")
        st.markdown("#### Player Analysis")

        # Build player list
        home_players = []
        if dataset.metadata.teams:
            for player in dataset.metadata.teams[0].players:
                jersey = player.jersey_no if hasattr(player, 'jersey_no') else "?"
                name = player.name if hasattr(player, 'name') else str(player.player_id)
                pid = player.player_id if hasattr(player, 'player_id') else None
                home_players.append((pid, f"#{jersey} {name}"))

        if home_players:
            # Player selector
            selected_home = st.selectbox(
                "Select Player",
                options=[p[0] for p in home_players],
                format_func=lambda x: next((p[1] for p in home_players if p[0] == x), str(x)),
                key="home_player_select"
            )

            # Half selector for player section (independent from team half)
            player_half_home = st.selectbox(
                "Half",
                options=["Full Match", "1st Half", "2nd Half"],
                key="home_player_half"
            )

            # Player event selector (independent from team)
            player_event_home = st.selectbox(
                "Player Event Type",
                options=list(EVENT_TYPE_OPTIONS.keys()),
                key="home_player_event"
            )
            player_event_code_home = EVENT_TYPE_OPTIONS[player_event_home]

            # Filter events by half selection
            filtered_events_home_player = filter_events_by_half(events, player_half_home)

            if selected_home:
                player_positions = collect_player_event_positions(filtered_events_home_player, selected_home, player_event_code_home)
                player_name = next((p[1] for p in home_players if p[0] == selected_home), "Player")
                fig_player = draw_event_scatter(player_positions,
                                                f"{player_name} - {player_event_home}s",
                                                team_color='#FFFFFF')  # White for Germany
                st.pyplot(fig_player)
                plt.close(fig_player)

    with zone_col2:
        st.markdown(f"### {away_name}")

        # Half selector for team section
        team_half_away = st.selectbox(
            "Half",
            options=["Full Match", "1st Half", "2nd Half"],
            key="away_team_half"
        )

        # Team event selector
        team_event_away = st.selectbox(
            "Event Type",
            options=list(EVENT_TYPE_OPTIONS.keys()),
            key="away_team_event"
        )
        team_event_code_away = EVENT_TYPE_OPTIONS[team_event_away]

        # Filter events by half selection
        filtered_events_away_team = filter_events_by_half(events, team_half_away)

        # Collect event positions and draw scatter plot
        away_positions = collect_team_event_positions(filtered_events_away_team, away_name, team_event_code_away)
        fig_away = draw_event_scatter(away_positions,
                                      f"{away_name} - {team_event_away}s",
                                      team_color='#0066CC')  # Blue for Japan
        st.pyplot(fig_away)
        plt.close(fig_away)

        # Player Analysis section
        st.markdown("---")
        st.markdown("#### Player Analysis")

        # Build player list
        away_players = []
        if dataset.metadata.teams and len(dataset.metadata.teams) > 1:
            for player in dataset.metadata.teams[1].players:
                jersey = player.jersey_no if hasattr(player, 'jersey_no') else "?"
                name = player.name if hasattr(player, 'name') else str(player.player_id)
                pid = player.player_id if hasattr(player, 'player_id') else None
                away_players.append((pid, f"#{jersey} {name}"))

        if away_players:
            # Player selector
            selected_away = st.selectbox(
                "Select Player",
                options=[p[0] for p in away_players],
                format_func=lambda x: next((p[1] for p in away_players if p[0] == x), str(x)),
                key="away_player_select"
            )

            # Half selector for player section (independent from team half)
            player_half_away = st.selectbox(
                "Half",
                options=["Full Match", "1st Half", "2nd Half"],
                key="away_player_half"
            )

            # Player event selector (independent from team)
            player_event_away = st.selectbox(
                "Player Event Type",
                options=list(EVENT_TYPE_OPTIONS.keys()),
                key="away_player_event"
            )
            player_event_code_away = EVENT_TYPE_OPTIONS[player_event_away]

            # Filter events by half selection
            filtered_events_away_player = filter_events_by_half(events, player_half_away)

            if selected_away:
                player_positions = collect_player_event_positions(filtered_events_away_player, selected_away, player_event_code_away)
                player_name = next((p[1] for p in away_players if p[0] == selected_away), "Player")
                fig_player = draw_event_scatter(player_positions,
                                                f"{player_name} - {player_event_away}s",
                                                team_color='#0066CC')  # Blue for Japan
                st.pyplot(fig_player)
                plt.close(fig_player)

# Auto-play logic
add_debug(f"auto_play={auto_play}, current_frame={current_frame}")

if auto_play:
    # Higher speed = skip more frames (speed is frames per update)
    old_frame = st.session_state.current_frame
    new_frame = (old_frame + speed) % len(dataset.frames)
    add_debug(f"Autoplay: {old_frame} -> {new_frame} (skip {speed})")
    st.session_state.current_frame = new_frame

    # Log advancement
    old_time = frame_to_match_time(old_frame, GAME_METADATA)
    new_time = frame_to_match_time(new_frame, GAME_METADATA)
    st.session_state.log.append(f"[Autoplay] {old_time} -> {new_time}")

    # Minimum delay for UI responsiveness (lets browser process events)
    time.sleep(0.05)

    add_debug("Calling st.rerun()")
    st.rerun()

# Footer
st.markdown("---")
st.caption("Shape Graph Visualization | PFF FIFA World Cup 2022")
