"""Internal utilities"""

from rich.progress import track


class ConfigProgressBar:
    """Display a configuration Progress Bar."""

    def __init__(self) -> None:
        self.progress = 0
        self.total = 1000
        self.tracker = track(range(self.total), description="Configuring...")

    def set_progress(self, progress: int) -> None:
        """Set the progress bar progress."""
        if progress == 0:
            self.progress = -1
        else:
            progress = progress - self.progress
            for _ in zip(self.tracker, range(progress)):
                pass
            self.progress += progress

    def close(self) -> None:
        """Finish the progress bar"""
        self.tracker.close()


def parse_docstring(txt) -> tuple:
    """parse docstring, returning a tuple with short and long description"""
    description = txt
    i = txt.find(".")
    if i == -1:
        help_ = txt
    else:
        help_ = txt[: i + 1]
    return help_, description
