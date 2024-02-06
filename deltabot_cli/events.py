"""High-level classes for event processing and filtering."""

import re
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
    Iterator,
    Optional,
    Set,
    Tuple,
    Union,
)

from .const import EventType

if TYPE_CHECKING:
    from ._utils import AttrDict
    from .client import Bot
FilterCallback = Callable[["Bot", "AttrDict"], bool]
HookCallback = Callable[["Bot", int, "AttrDict"], None]
HookDecorator = Callable[[HookCallback], HookCallback]


def _tuple_of(obj, type_: type) -> tuple:
    if not obj:
        return ()
    if isinstance(obj, type_):
        obj = (obj,)

    if not all(isinstance(elem, type_) for elem in obj):
        raise TypeError()
    return tuple(obj)


class EventFilter(ABC):
    """The base event filter.

    :param func: A Callable that should accept the bot and event as input parameters,
                 and return a bool value indicating whether the event should be dispatched or not.
    """

    def __init__(self, func: Optional[FilterCallback] = None):
        self.func = func

    @abstractmethod
    def __hash__(self) -> int:
        """Object's unique hash"""

    @abstractmethod
    def __eq__(self, other) -> bool:
        """Return True if two event filters are equal."""

    def __ne__(self, other):
        return not self == other

    def _call_func(self, bot: "Bot", event: "AttrDict") -> bool:
        if not self.func:
            return True
        return self.func(bot, event)

    @abstractmethod
    def filter(self, bot: "Bot", event: "AttrDict"):
        """Return True-like value if the event passed the filter and should be
        used, or False-like value otherwise.
        """


class RawEvent(EventFilter):
    """Matches raw core events.

    :param types: The types of event to match.
    :param func: A Callable that should accept the bot and event as input parameter,
                 and return a bool value indicating whether the event should be dispatched or not.
    """

    def __init__(
        self,
        types: Union[None, EventType, Iterable[EventType]] = None,
        func: Optional[FilterCallback] = None,
    ):
        super().__init__(func=func)
        try:
            self.types = _tuple_of(types, EventType)
        except TypeError as err:
            raise TypeError(f"Invalid event type given: {types}") from err

    def __hash__(self) -> int:
        return hash((self.types, self.func))

    def __eq__(self, other) -> bool:
        if isinstance(other, RawEvent):
            return (self.types, self.func) == (other.types, other.func)
        return False

    def filter(self, bot: "Bot", event: "AttrDict") -> bool:
        if self.types and event.kind not in self.types:
            return False
        return self._call_func(bot, event)


class NewMessage(EventFilter):
    """Matches whenever a new message arrives.

    :param pattern: if set, this Pattern will be used to filter the message by its text
                    content.
    :param command: If set, only match messages with the given command (ex. /help).
                    Setting this property implies `is_info==False`.
    :param is_bot: If set to True only match messages sent by bots, if set to None
                   match messages from bots and users. If omitted or set to False
                   only messages from users will be matched.
    :param is_info: If set to True only match info/system messages, if set to False
                    only match messages that are not info/system messages. If omitted
                    info/system messages as well as normal messages will be matched.
    :param func: A Callable that should accept the bot and the event as input parameter,
                 and return a bool value indicating whether the event should be dispatched or not.
    """

    def __init__(
        self,
        pattern: Union[
            None,
            str,
            Callable[[str], bool],
            re.Pattern,
        ] = None,
        command: Optional[str] = None,
        is_bot: Optional[bool] = False,
        is_info: Optional[bool] = None,
        func: Optional[FilterCallback] = None,
    ) -> None:
        super().__init__(func=func)
        self.is_bot = is_bot
        self.is_info = is_info
        if command is not None and not isinstance(command, str):
            raise TypeError("Invalid command")
        self.command = command
        if self.is_info and self.command:
            raise AttributeError("Can not use command and is_info at the same time.")
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if isinstance(pattern, re.Pattern):
            self.pattern: Optional[Callable] = pattern.match
        elif not pattern or callable(pattern):
            self.pattern = pattern
        else:
            raise TypeError("Invalid pattern type")

    def __hash__(self) -> int:
        return hash((self.pattern, self.command, self.is_bot, self.is_info, self.func))

    def __eq__(self, other) -> bool:
        if isinstance(other, NewMessage):
            return (
                self.pattern,
                self.command,
                self.is_bot,
                self.is_info,
                self.func,
            ) == (
                other.pattern,
                other.command,
                other.is_bot,
                other.is_info,
                other.func,
            )
        return False

    def filter(self, bot: "Bot", event: "AttrDict") -> bool:
        if self.is_bot is not None and self.is_bot != event.msg.is_bot:
            return False
        if self.is_info is not None and self.is_info != event.msg.is_info:
            return False
        if self.command and self.command != event.command:
            return False
        if self.pattern:
            match = self.pattern(event.msg.text)
            if not match:
                return False
        return super()._call_func(bot, event)


class MemberListChanged(EventFilter):
    """Matches when a group member is added or removed.

    :param added: If set to True only match if a member was added, if set to False
                  only match if a member was removed. If omitted both, member additions
                  and removals, will be matched.
    :param func: A Callable that should accept the bot and event as input parameter,
                 and return a bool value indicating whether the event should be dispatched or not.
    """

    def __init__(self, added: Optional[bool] = None, **kwargs):
        super().__init__(**kwargs)
        self.added = added

    def __hash__(self) -> int:
        return hash((self.added, self.func))

    def __eq__(self, other) -> bool:
        if isinstance(other, MemberListChanged):
            return (self.added, self.func) == (other.added, other.func)
        return False

    def filter(self, bot: "Bot", event: "AttrDict") -> bool:
        if self.added is not None and self.added != event.member_added:
            return False
        return self._call_func(bot, event)


class GroupImageChanged(EventFilter):
    """Matches when the group image is changed.

    :param deleted: If set to True only match if the image was deleted, if set to False
                    only match if a new image was set. If omitted both, image changes and
                    removals, will be matched.
    :param func: A Callable that should accept the bot and event as input parameter,
                 and return a bool value indicating whether the event should be dispatched or not.
    """

    def __init__(self, deleted: Optional[bool] = None, **kwargs):
        super().__init__(**kwargs)
        self.deleted = deleted

    def __hash__(self) -> int:
        return hash((self.deleted, self.func))

    def __eq__(self, other) -> bool:
        if isinstance(other, GroupImageChanged):
            return (self.deleted, self.func) == (other.deleted, other.func)
        return False

    def filter(self, bot: "Bot", event: "AttrDict") -> bool:
        if self.deleted is not None and self.deleted != event.image_deleted:
            return False
        return self._call_func(bot, event)


class GroupNameChanged(EventFilter):
    """Matches when the group name is changed.

    :param func: A Callable that should accept the bot and event as input parameter,
                 and return a bool value indicating whether the event should be dispatched or not.
    """

    def __hash__(self) -> int:
        return hash((GroupNameChanged, self.func))

    def __eq__(self, other) -> bool:
        if isinstance(other, GroupNameChanged):
            return self.func == other.func
        return False

    def filter(self, bot: "Bot", event: "AttrDict") -> bool:
        return self._call_func(bot, event)


class HookCollection:
    """
    Helper class to collect event hooks that can later be added to a Delta Chat client.
    """

    def __init__(self) -> None:
        self._hooks: Set[Tuple[HookCallback, Union[type, EventFilter]]] = set()

    def __iter__(self) -> Iterator[Tuple[HookCallback, Union[type, EventFilter]]]:
        return iter(self._hooks)

    def on(self, event: Union[type, EventFilter]) -> HookDecorator:  # noqa
        """Register decorated function as listener for the given event."""
        if isinstance(event, type):
            event = event()
        assert isinstance(event, EventFilter), "Invalid event filter"

        def _decorator(func: HookCallback) -> HookCallback:
            self._hooks.add((func, event))
            return func

        return _decorator
