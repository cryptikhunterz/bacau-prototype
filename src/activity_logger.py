"""Activity logging system for shape graph UI."""

import os
from datetime import datetime
from typing import Callable, Optional


class ActivityLogger:
    """Logs activity to both file and optional UI callback."""

    def __init__(self, log_file: str = "logs/activity_log.md",
                 ui_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize activity logger.

        Args:
            log_file: Path to log file
            ui_callback: Optional callback function to send logs to UI
        """
        self.log_file = log_file
        self.ui_callback = ui_callback

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Write header if new file
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("# Shape Graph Activity Log\n\n")

    def set_ui_callback(self, callback: Callable[[str], None]):
        """Set the UI callback for real-time display."""
        self.ui_callback = callback

    def log(self, task: str, action: str, result: str = "Success",
            files: str = "", details: str = ""):
        """
        Log an activity.

        Args:
            task: Task identifier (e.g., "Task 1.1")
            action: What was done
            result: Success/Fail/Info
            files: Files changed (optional)
            details: Additional details (optional)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format log entry
        entry = f"""---
[{timestamp}] shape-graph | {task}
ACTION: {action}
RESULT: {result}"""

        if files:
            entry += f"\nFILES: {files}"
        if details:
            entry += f"\nDETAILS: {details}"

        entry += "\n"

        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(entry)

        # Send to UI if callback set
        if self.ui_callback:
            # Shorter format for UI
            ui_msg = f"[{timestamp[-8:]}] {task}: {action} - {result}"
            self.ui_callback(ui_msg)

    def log_startup(self):
        """Log application startup."""
        self.log("Startup", "Application started", "Success")

    def log_data_loaded(self, frames: int, home_players: int, away_players: int):
        """Log data loading."""
        self.log(
            "Data Load",
            f"Loaded tracking data",
            "Success",
            details=f"Frames: {frames}, Home: {home_players}, Away: {away_players}"
        )

    def log_frame_render(self, frame_num: int, possession: str = "Unknown"):
        """Log frame rendering."""
        self.log(
            "Render",
            f"Frame {frame_num}",
            "Success",
            details=f"Possession: {possession}"
        )

    def log_user_action(self, action: str):
        """Log user interaction."""
        self.log("User", action, "Info")

    def log_error(self, task: str, error: str):
        """Log an error."""
        self.log(task, f"Error: {error}", "FAIL")


# Global logger instance
_logger: Optional[ActivityLogger] = None


def get_logger() -> ActivityLogger:
    """Get or create global logger instance."""
    global _logger
    if _logger is None:
        _logger = ActivityLogger()
    return _logger


def init_logger(log_file: str = "logs/activity_log.md",
                ui_callback: Optional[Callable[[str], None]] = None) -> ActivityLogger:
    """Initialize global logger with custom settings."""
    global _logger
    _logger = ActivityLogger(log_file, ui_callback)
    return _logger
