"""Color definitions for shape graph visualization."""

# Vertical Colors (Blue → Red: Back to Front)
VERTICAL_COLORS = {
    0: '#1565C0',  # Back - Deep Blue (Defensive)
    1: '#42A5F5',  # Defensive Mid - Light Blue
    2: '#AB47BC',  # Central Mid - Purple
    3: '#EF5350',  # Attacking Mid - Light Red
    4: '#C62828',  # Front - Deep Red (Attacking)
}

VERTICAL_LABELS = {
    0: 'DEF',
    1: 'DM',
    2: 'MID',
    3: 'AM',
    4: 'FWD'
}

# Horizontal Colors (Brown → Green: Left to Right)
HORIZONTAL_COLORS = {
    0: '#795548',  # Left - Brown
    1: '#8D6E63',  # Left-Center - Light Brown
    2: '#78909C',  # Center - Blue-Grey
    3: '#81C784',  # Right-Center - Light Green
    4: '#2E7D32',  # Right - Deep Green
}

HORIZONTAL_LABELS = {
    0: 'L',
    1: 'LC',
    2: 'C',
    3: 'RC',
    4: 'R'
}

# Pitch colors
PITCH_COLOR = '#1a472a'
LINE_COLOR = 'white'
BACKGROUND_COLOR = '#0d1117'
