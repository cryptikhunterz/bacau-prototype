"""Bi-colored semi-circle marker drawing for shape graph."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

try:
    from .colors import VERTICAL_COLORS, HORIZONTAL_COLORS
except ImportError:
    from colors import VERTICAL_COLORS, HORIZONTAL_COLORS


def draw_bicolor_marker(ax, x, y, top_color, bottom_color, radius=3,
                        edge_color='white', edge_width=1.5):
    """
    Draw a bi-colored circle marker with upper and lower semi-circles.

    Args:
        ax: Matplotlib axes
        x, y: Center position
        top_color: Color for upper semi-circle (vertical position)
        bottom_color: Color for lower semi-circle (horizontal position)
        radius: Marker radius
        edge_color: Border color
        edge_width: Border width

    Returns:
        Tuple of (top_wedge, bottom_wedge) patches
    """
    # Upper semi-circle (vertical/attacking position)
    top_wedge = mpatches.Wedge(
        (x, y), radius,
        theta1=0, theta2=180,  # Upper half
        facecolor=top_color,
        edgecolor=edge_color,
        linewidth=edge_width
    )

    # Lower semi-circle (horizontal/left-right position)
    bottom_wedge = mpatches.Wedge(
        (x, y), radius,
        theta1=180, theta2=360,  # Lower half
        facecolor=bottom_color,
        edgecolor=edge_color,
        linewidth=edge_width
    )

    ax.add_patch(top_wedge)
    ax.add_patch(bottom_wedge)

    return top_wedge, bottom_wedge


def draw_player_marker(ax, x, y, v_bucket, h_bucket, player_num=None,
                       radius=3, show_number=True):
    """
    Draw complete player marker with optional jersey number.

    Args:
        ax: Matplotlib axes
        x, y: Player position
        v_bucket: Vertical position bucket (0-4)
        h_bucket: Horizontal position bucket (0-4)
        player_num: Jersey number to display
        radius: Marker radius
        show_number: Whether to display jersey number
    """
    top_color = VERTICAL_COLORS.get(v_bucket, VERTICAL_COLORS[2])
    bottom_color = HORIZONTAL_COLORS.get(h_bucket, HORIZONTAL_COLORS[2])

    draw_bicolor_marker(ax, x, y, top_color, bottom_color, radius)

    if show_number and player_num is not None:
        ax.text(x, y, str(player_num),
                ha='center', va='center',
                fontsize=8, fontweight='bold', color='white',
                zorder=10)


def create_legend(ax, position='upper left'):
    """
    Create a legend explaining the color system.

    Args:
        ax: Matplotlib axes
        position: Legend position
    """
    from matplotlib.lines import Line2D

    # Create legend elements
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Upper: Attacking Position',
               markerfacecolor='gray', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Lower: Left/Right Position',
               markerfacecolor='gray', markersize=10),
    ]

    # Vertical colors legend
    for bucket, color in VERTICAL_COLORS.items():
        try:
            from .colors import VERTICAL_LABELS
        except ImportError:
            from colors import VERTICAL_LABELS
        label = VERTICAL_LABELS.get(bucket, str(bucket))
        legend_elements.append(
            Line2D([0], [0], marker='s', color='w', label=f'V{bucket}: {label}',
                   markerfacecolor=color, markersize=8)
        )

    ax.legend(handles=legend_elements, loc=position, fontsize=8,
              facecolor='#333333', edgecolor='white', labelcolor='white')


if __name__ == "__main__":
    # Test marker drawing
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_facecolor('#1a472a')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Draw test markers
    for v in range(5):
        for h in range(5):
            x = 10 + v * 20
            y = 10 + h * 20
            draw_player_marker(ax, x, y, v, h, player_num=v*5+h+1, radius=5)

    ax.set_title('Marker Test Grid (V: vertical, H: horizontal)',
                color='white', fontsize=14)
    ax.set_aspect('equal')

    fig.patch.set_facecolor('#0d1117')
    plt.savefig('marker_test.png', dpi=150,
                facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.show()
