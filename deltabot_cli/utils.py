"""Utilities"""

from ._utils import AttrDict
from .client import Bot
from .const import COMMAND_PREFIX
from .events import NewMessage


def is_not_known_command(bot: Bot, event: AttrDict) -> bool:
    """Filter helper to be used by NewMessage filters.
    Matches all NewMessage that don't match a previously registered command filter."""
    if not event.command.startswith(COMMAND_PREFIX):
        return True
    for hook in bot._hooks.get(NewMessage, []):  # pylint:disable=W0212
        if event.command == hook[1].command:
            return False
    return True
