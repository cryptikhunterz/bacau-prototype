# Streamlit Autoplay Pattern

## Problem

When implementing auto-play animation in Streamlit, you need to programmatically update a slider's value. However, Streamlit throws this error:

```
StreamlitAPIException: `st.session_state.frame_slider` cannot be modified
after the widget with key `frame_slider` is instantiated.
```

## Root Cause

Streamlit binds widget values to session state keys. Once a widget with `key="X"` is rendered, you cannot directly modify `st.session_state.X` in the same script run. This is by design to prevent state conflicts.

## Solution Pattern

Use a **separate source-of-truth key** that the widget reads from, but isn't directly bound to:

```python
# 1. Initialize separate source-of-truth key
if 'current_frame' not in st.session_state:
    st.session_state.current_frame = 0

# 2. Callback to sync manual slider changes
def on_slider_change():
    st.session_state.current_frame = st.session_state._slider_widget

# 3. Slider reads from current_frame, uses different internal key
frame_idx = st.slider(
    "Frame",
    min_value=0,
    max_value=1000,
    value=st.session_state.current_frame,  # Reads from source-of-truth
    key="_slider_widget",                   # Different internal key
    on_change=on_slider_change              # Syncs manual changes back
)

# 4. Autoplay updates source-of-truth, then reruns
if auto_play:
    st.session_state.current_frame = new_frame  # Update source-of-truth
    st.rerun()  # Slider will read new value on next run
```

## Key Points

1. **`value=`** - Widget reads initial value from here on each render
2. **`key=`** - Internal widget key (use underscore prefix like `_slider_widget`)
3. **`on_change=`** - Callback to sync manual user changes to source-of-truth
4. **Autoplay** - Modify source-of-truth key, NOT the widget key

## When to Use

- Auto-play/animation features
- Programmatic slider/input updates
- Any case where code needs to change widget value

## Anti-Pattern (Don't Do This)

```python
# DON'T: Modify widget key directly
st.slider(..., key="my_slider")
st.session_state.my_slider = new_value  # ERROR!
```

## File Reference

See `app.py` lines 173-210, 248-268 for working implementation.
