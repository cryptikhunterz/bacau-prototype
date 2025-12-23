"""Football pitch drawing utilities."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

try:
    from .colors import PITCH_COLOR, LINE_COLOR
except ImportError:
    from colors import PITCH_COLOR, LINE_COLOR


def draw_pitch(ax, pitch_length=105, pitch_width=68,
               line_color=LINE_COLOR, pitch_color=PITCH_COLOR,
               show_zones=False):
    """
    Draw a football pitch on the given axes.

    Args:
        ax: Matplotlib axes
        pitch_length: Pitch length in meters (default 105)
        pitch_width: Pitch width in meters (default 68)
        line_color: Color for pitch lines
        pitch_color: Background color of pitch
        show_zones: Whether to show tactical zone lines (default False)

    Returns:
        The axes object
    """
    ax.set_facecolor(pitch_color)

    lw = 2  # Line width

    # Pitch outline
    ax.plot([0, 0], [0, pitch_width], color=line_color, linewidth=lw)
    ax.plot([0, pitch_length], [pitch_width, pitch_width], color=line_color, linewidth=lw)
    ax.plot([pitch_length, pitch_length], [pitch_width, 0], color=line_color, linewidth=lw)
    ax.plot([pitch_length, 0], [0, 0], color=line_color, linewidth=lw)

    # Halfway line
    ax.plot([pitch_length/2, pitch_length/2], [0, pitch_width],
            color=line_color, linewidth=lw)

    # Center circle
    center_circle = plt.Circle((pitch_length/2, pitch_width/2), 9.15,
                                 fill=False, color=line_color, linewidth=lw)
    ax.add_patch(center_circle)

    # Center spot
    ax.scatter(pitch_length/2, pitch_width/2, color=line_color, s=20, zorder=5)

    # Left penalty area
    pa_width = 40.3  # 16.5m each side from center
    pa_depth = 16.5
    ax.plot([0, pa_depth], [pitch_width/2 - pa_width/2, pitch_width/2 - pa_width/2],
            color=line_color, linewidth=lw)
    ax.plot([pa_depth, pa_depth], [pitch_width/2 - pa_width/2, pitch_width/2 + pa_width/2],
            color=line_color, linewidth=lw)
    ax.plot([pa_depth, 0], [pitch_width/2 + pa_width/2, pitch_width/2 + pa_width/2],
            color=line_color, linewidth=lw)

    # Right penalty area
    ax.plot([pitch_length, pitch_length - pa_depth],
            [pitch_width/2 - pa_width/2, pitch_width/2 - pa_width/2],
            color=line_color, linewidth=lw)
    ax.plot([pitch_length - pa_depth, pitch_length - pa_depth],
            [pitch_width/2 - pa_width/2, pitch_width/2 + pa_width/2],
            color=line_color, linewidth=lw)
    ax.plot([pitch_length - pa_depth, pitch_length],
            [pitch_width/2 + pa_width/2, pitch_width/2 + pa_width/2],
            color=line_color, linewidth=lw)

    # Left goal area
    ga_width = 18.32
    ga_depth = 5.5
    ax.plot([0, ga_depth], [pitch_width/2 - ga_width/2, pitch_width/2 - ga_width/2],
            color=line_color, linewidth=lw)
    ax.plot([ga_depth, ga_depth], [pitch_width/2 - ga_width/2, pitch_width/2 + ga_width/2],
            color=line_color, linewidth=lw)
    ax.plot([ga_depth, 0], [pitch_width/2 + ga_width/2, pitch_width/2 + ga_width/2],
            color=line_color, linewidth=lw)

    # Right goal area
    ax.plot([pitch_length, pitch_length - ga_depth],
            [pitch_width/2 - ga_width/2, pitch_width/2 - ga_width/2],
            color=line_color, linewidth=lw)
    ax.plot([pitch_length - ga_depth, pitch_length - ga_depth],
            [pitch_width/2 - ga_width/2, pitch_width/2 + ga_width/2],
            color=line_color, linewidth=lw)
    ax.plot([pitch_length - ga_depth, pitch_length],
            [pitch_width/2 + ga_width/2, pitch_width/2 + ga_width/2],
            color=line_color, linewidth=lw)

    # Goals
    goal_width = 7.32
    goal_depth = 2
    # Left goal
    ax.plot([0, -goal_depth], [pitch_width/2 - goal_width/2, pitch_width/2 - goal_width/2],
            color=line_color, linewidth=3)
    ax.plot([-goal_depth, -goal_depth], [pitch_width/2 - goal_width/2, pitch_width/2 + goal_width/2],
            color=line_color, linewidth=3)
    ax.plot([-goal_depth, 0], [pitch_width/2 + goal_width/2, pitch_width/2 + goal_width/2],
            color=line_color, linewidth=3)

    # Right goal
    ax.plot([pitch_length, pitch_length + goal_depth],
            [pitch_width/2 - goal_width/2, pitch_width/2 - goal_width/2],
            color=line_color, linewidth=3)
    ax.plot([pitch_length + goal_depth, pitch_length + goal_depth],
            [pitch_width/2 - goal_width/2, pitch_width/2 + goal_width/2],
            color=line_color, linewidth=3)
    ax.plot([pitch_length + goal_depth, pitch_length],
            [pitch_width/2 + goal_width/2, pitch_width/2 + goal_width/2],
            color=line_color, linewidth=3)

    # Penalty spots
    ax.scatter(11, pitch_width/2, color=line_color, s=15, zorder=5)
    ax.scatter(pitch_length - 11, pitch_width/2, color=line_color, s=15, zorder=5)

    # Tactical zone lines (optional)
    if show_zones:
        # Zone boundaries (normalized positions across width)
        # LW | LHS | C | RHS | RW
        zone_boundaries = [0.18, 0.36, 0.64, 0.82]
        for y_norm in zone_boundaries:
            y = y_norm * pitch_width
            ax.plot([0, pitch_length], [y, y],
                    linestyle='--', linewidth=1, alpha=0.4, color='white', zorder=1)

        # Zone labels at top of pitch
        zone_labels = ['LW', 'LHS', 'C', 'RHS', 'RW']
        zone_centers = [0.09, 0.27, 0.50, 0.73, 0.91]
        for label, y_norm in zip(zone_labels, zone_centers):
            y = y_norm * pitch_width
            ax.text(pitch_length / 2, y, label,
                    ha='center', va='center', fontsize=9, fontweight='bold',
                    color='white', alpha=0.5, zorder=1)

    # Set limits and aspect
    ax.set_xlim(-5, pitch_length + 5)
    ax.set_ylim(-5, pitch_width + 5)
    ax.set_aspect('equal')
    ax.axis('off')

    return ax


def draw_half_pitch(ax, side='left', pitch_length=105, pitch_width=68,
                    line_color=LINE_COLOR, pitch_color=PITCH_COLOR):
    """
    Draw a half pitch (useful for some visualizations).

    Args:
        ax: Matplotlib axes
        side: 'left' or 'right' half
        Other args same as draw_pitch
    """
    ax.set_facecolor(pitch_color)

    half_length = pitch_length / 2
    lw = 2

    if side == 'left':
        # Draw left half
        ax.plot([0, 0], [0, pitch_width], color=line_color, linewidth=lw)
        ax.plot([0, half_length], [pitch_width, pitch_width], color=line_color, linewidth=lw)
        ax.plot([half_length, half_length], [pitch_width, 0], color=line_color, linewidth=lw)
        ax.plot([half_length, 0], [0, 0], color=line_color, linewidth=lw)

        # Center circle (half)
        center_circle = mpatches.Arc((half_length, pitch_width/2), 18.3, 18.3,
                                      angle=0, theta1=90, theta2=270,
                                      color=line_color, linewidth=lw)
        ax.add_patch(center_circle)

        ax.set_xlim(-5, half_length + 5)
    else:
        # Draw right half (mirrored)
        ax.plot([half_length, half_length], [0, pitch_width], color=line_color, linewidth=lw)
        ax.plot([half_length, pitch_length], [pitch_width, pitch_width], color=line_color, linewidth=lw)
        ax.plot([pitch_length, pitch_length], [pitch_width, 0], color=line_color, linewidth=lw)
        ax.plot([pitch_length, half_length], [0, 0], color=line_color, linewidth=lw)

        ax.set_xlim(half_length - 5, pitch_length + 5)

    ax.set_ylim(-5, pitch_width + 5)
    ax.set_aspect('equal')
    ax.axis('off')

    return ax


if __name__ == "__main__":
    # Test pitch drawing
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    draw_pitch(ax1)
    ax1.set_title('Full Pitch', color='white', fontsize=14)

    draw_pitch(ax2)
    ax2.set_title('Full Pitch (Right Team)', color='white', fontsize=14)

    fig.patch.set_facecolor('#0d1117')
    plt.tight_layout()
    plt.savefig('pitch_test.png', dpi=150,
                facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.show()
