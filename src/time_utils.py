"""Time utilities for converting frame indices to match time format."""


def frame_to_match_time(frame_idx: int, metadata: dict) -> str:
    """
    Convert frame index to match time string in [MM:SS] format.

    Args:
        frame_idx: Current frame number (0-indexed)
        metadata: Dict containing timing information:
            - fps: Frames per second (default 29.97 if missing)
            - startPeriod1: Video time when 1st half starts (seconds)
            - endPeriod1: Video time when 1st half ends (seconds)
            - startPeriod2: Video time when 2nd half starts (seconds)
            - endPeriod2: Video time when 2nd half ends (seconds)

    Returns:
        String in format "[MM:SS]" with continuous time (0-90+).
        Examples: "[02:45]", "[48:15]"
    """
    # Handle negative frame index
    if frame_idx < 0:
        return "[00:00]"

    # Get timing parameters with defaults
    fps = metadata.get('fps', 29.97)
    if fps <= 0:
        fps = 29.97  # Guard against invalid fps

    start_period1 = metadata.get('startPeriod1', 0)
    end_period1 = metadata.get('endPeriod1', float('inf'))
    start_period2 = metadata.get('startPeriod2', 0)

    # Calculate video time from frame index
    video_time = start_period1 + (frame_idx / fps)

    # Determine period and calculate elapsed time
    if video_time < end_period1:
        # First half: 0-45 minutes
        elapsed_sec = video_time - start_period1
        base_minutes = 0
    else:
        # Second half: 45-90+ minutes
        elapsed_sec = video_time - start_period2
        base_minutes = 45

    # Ensure non-negative elapsed time
    elapsed_sec = max(0, elapsed_sec)

    # Round to nearest second for more intuitive display
    total_secs = round(elapsed_sec)

    # Convert to minutes and seconds
    mins = base_minutes + (total_secs // 60)
    secs = total_secs % 60

    return f"[{mins:02d}:{secs:02d}]"
