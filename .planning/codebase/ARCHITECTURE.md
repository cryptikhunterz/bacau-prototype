# Architecture

**Analysis Date:** 2026-01-09

## Pattern Overview

**Overall:** Monolithic Web Application with Modular Utilities

**Key Characteristics:**
- Single-entry-point Streamlit web app (`app.py`)
- Functional programming approach
- Clean separation of concerns across utility modules
- Two entry points: Web (Streamlit) and Desktop (Tkinter)

## Layers

**UI/Presentation Layer:**
- Purpose: User interface and interaction
- Contains: Frame navigation, playback controls, sidebar panels
- Location: `app.py`, `src/ui.py`
- Depends on: Visualization and Data Processing layers
- Used by: End users

**Visualization/Rendering Layer:**
- Purpose: Football pitch and player visualization
- Contains: Pitch drawing, player markers, team shapes, convex hulls
- Location: `src/pitch.py`, `src/markers.py`, `src/shape_lines.py`, `src/visualize.py`
- Depends on: Colors, matplotlib
- Used by: UI layer

**Data Processing/Analysis Layer:**
- Purpose: Position classification, metrics calculation
- Contains: Formation detection, compactness index, team stats
- Location: `src/position_classifier.py`, `src/compactness.py`
- Depends on: NumPy, SciPy
- Used by: UI layer, Visualization layer

**Data Loading/Integration Layer:**
- Purpose: Load and parse tracking data
- Contains: PFF/Metrica data loading, frame extraction
- Location: `src/data_loader.py`, data loading in `app.py`
- Depends on: Kloppy, pandas
- Used by: All layers

**Utility Layer:**
- Purpose: Cross-cutting concerns
- Contains: Colors, time conversion, logging
- Location: `src/colors.py`, `src/time_utils.py`, `src/activity_logger.py`
- Depends on: Nothing (pure utilities)
- Used by: All layers

## Data Flow

**Frame Visualization Request:**

1. User selects frame via slider
2. `load_data()` returns cached dataset (kloppy)
3. `extract_positions(frame)` extracts home/away coordinates
4. `get_ball_position(frame)` extracts ball location
5. `get_possession(frame)` calculates closest player to ball
6. Parallel processing:
   - `classify_team_vertical()` & `classify_team_horizontal()`
   - `get_outfield_positions()` extracts 10 field players
   - `compute_ci()` calculates compactness metrics
   - `detect_formation()` infers team structure
7. Matplotlib rendering: pitch, markers, ball, shapes
8. Streamlit displays figure + logs activity

**State Management:**
- File-based: All data lives in local files
- Streamlit session state for frame navigation
- No persistent in-memory state between sessions

## Key Abstractions

**Position Bucketing:**
- Purpose: Classify players into 5x5 grid for color-coding
- Examples: `classify_team_vertical()`, `classify_team_horizontal()`
- Pattern: Rank-based percentile bucketing (0-4)

**Bi-color Marker:**
- Purpose: Encode two dimensions (attacking/horizontal) simultaneously
- Examples: `draw_bicolor_marker()`, `draw_player_marker()`
- Pattern: Split semi-circles with color lookup

**Convex Hull Shape:**
- Purpose: Represent team defensive shape
- Examples: `compute_convex_hull()`, `draw_team_shape()`
- Pattern: SciPy ConvexHull on outfield positions

**Compactness Index:**
- Purpose: Quantify defensive compactness (0-100)
- Examples: `compute_ci()`, `classify_block()`
- Pattern: Area-based calculation with balance penalty

## Entry Points

**Primary - Streamlit Web App:**
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: Load data, render UI, handle interactions

**Secondary - Desktop UI:**
- Location: `main.py` → `src/ui.py`
- Triggers: `python main.py`
- Responsibilities: Tkinter GUI with matplotlib canvas

## Error Handling

**Strategy:** Defensive programming with fallbacks

**Patterns:**
- Guard clauses for empty data (`if not positions: return {}`)
- Bare `except:` blocks (needs improvement)
- Default values for missing data
- Silently handle ConvexHull failures

## Cross-Cutting Concerns

**Logging:**
- Custom `ActivityLogger` class
- File-based logging with timestamps
- Optional UI callback for real-time display

**Validation:**
- Guard clauses at function entry
- Edge case handling (< 3 players, collinear points)
- No formal validation library

**Configuration:**
- Streamlit `.streamlit/config.toml`
- Hardcoded game metadata in `app.py`
- `DEFAULT_CONFIG` dict in `src/compactness.py`

---

*Architecture analysis: 2026-01-09*
*Update when major patterns change*
