"""Utilities"""
import asyncio
from typing import Coroutine

from rich.progress import track

_background_tasks = set()


def run_in_background(coro: Coroutine) -> None:
    """Schedule the execution of a coroutine object in a spawn task, keeping a
    reference to the task to avoid it disappearing mid-execution due to GC.
    """
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


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
