# Streamlit Patterns

## Overview

This document covers Streamlit-specific patterns used in the Shape Graph application.

## Session State Pattern for Autoplay

### The Problem

When using a slider with autoplay, directly updating `st.session_state.slider` causes:
1. Widget value updates
2. Widget's internal on_change fires
3. Conflict between autoplay update and widget state

### The Solution: Dual-Key Pattern

Use separate keys for source-of-truth and widget:

```python
# Source of truth (updated by autoplay)
if 'current_frame' not in st.session_state:
    st.session_state.current_frame = 0

# Widget callback (user interaction)
def on_slider_change():
    st.session_state.current_frame = st.session_state._slider_widget

# Slider with separate widget key
frame_idx = st.slider(
    "Frame",
    min_value=0,
    max_value=len(dataset.frames) - 1,
    value=st.session_state.current_frame,  # Source of truth
    key="_slider_widget",                   # Widget key
    on_change=on_slider_change
)

# Autoplay updates source of truth
if auto_play:
    st.session_state.current_frame = (st.session_state.current_frame + speed) % total_frames
    st.rerun()
```

## Caching Strategies

### @st.cache_resource (Heavy Objects)

For expensive-to-create objects that should persist across reruns:

```python
@st.cache_resource
def load_data():
    """Load PFF tracking data (cached)."""
    from kloppy import pff
    return pff.load_tracking(
        meta_data="path/to/metadata.json",
        roster_meta_data="path/to/roster.json",
        raw_data="path/to/tracking.jsonl.bz2"
    )
```

### @st.cache_data (Serializable Data)

For data that can be serialized (not used here, but useful for DataFrames):

```python
@st.cache_data
def load_events():
    with open("events.json") as f:
        return json.load(f)
```

### Clearing Cache

```bash
rm -rf ~/.streamlit/cache
```

Or programmatically:
```python
st.cache_resource.clear()
```

## Autoplay with UI Responsiveness

### The Problem

Continuous `st.rerun()` without delay freezes the UI.

### The Solution: Minimum Delay

```python
if auto_play:
    # Update frame
    st.session_state.current_frame = (old_frame + speed) % total_frames
    
    # CRITICAL: Allow browser to process events
    time.sleep(0.05)  # 50ms minimum
    
    st.rerun()
```

## Layout Patterns

### Two-Column Layout

```python
col1, col2 = st.columns([3, 1])  # 3:1 ratio

with col1:
    st.pyplot(fig)  # Main visualization

with col2:
    st.subheader("Activity Log")
    # Sidebar content
```

### Nested Columns

```python
with stats_col:
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Home Area", f"{home_area:.0f} m²")
    with metric_col2:
        st.metric("Away Area", f"{away_area:.0f} m²")
```

## Sidebar Organization

```python
with st.sidebar:
    st.header("Controls")
    
    # Data loading with spinner
    with st.spinner("Loading data..."):
        dataset = load_data()
    st.success(f"Loaded {len(dataset.frames):,} frames")
    
    # Controls
    frame_idx = st.slider("Frame", 0, len(dataset.frames) - 1)
    auto_play = st.checkbox("Auto-play")
    speed = st.slider("Speed", 1, 50, 10)
    
    # Display options
    st.subheader("Display Options")
    show_shapes = st.checkbox("Show team shapes", True)
    
    # Expandable sections
    with st.expander("Player Roster"):
        for player in players:
            st.caption(f"#{player.jersey_no} {player.name}")
```

## Performance Display

```python
# Timing metrics
t0 = time.perf_counter()
# ... do work ...
t1 = time.perf_counter()
elapsed_ms = (t1 - t0) * 1000

# Display in sidebar
st.metric("FPS", f"{1000/elapsed_ms:.1f}")
st.caption(f"Render: {elapsed_ms:.1f}ms")
```

## Matplotlib Integration

### Figure Cleanup

Always close figures to prevent memory leaks:

```python
fig = render_frame(frame_data)
st.pyplot(fig)
plt.close(fig)  # IMPORTANT
```

### Dark Theme

```python
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')
```

## Custom CSS

```python
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
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)
```

## HTML in Markdown

```python
# Colored text
st.markdown(
    f"<span style='color:#3498db'>{player_name}</span>",
    unsafe_allow_html=True
)

# Log container with scroll
log_html = "<div class='log-container'>"
for entry in log_entries:
    log_html += f"<div>{entry}</div>"
log_html += "</div>"
st.markdown(log_html, unsafe_allow_html=True)
```

## Expanders for Optional Content

```python
with st.expander("Debug Trace", expanded=False):
    for entry in debug_log:
        st.caption(entry)

with st.expander("Event Legend", expanded=False):
    st.markdown("**PA** = Pass | **SH** = Shot | ...")
```

## Error Handling

```python
@st.cache_resource
def load_events():
    try:
        with open(event_path) as f:
            return json.load(f)
    except:
        return []  # Graceful fallback
```
