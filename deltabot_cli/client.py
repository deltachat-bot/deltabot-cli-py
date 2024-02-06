"""Event loop implementations offering high level event handling/hooking."""

import logging
from typing import Callable, Dict, Iterable, Optional, Set, Tuple, Type, Union

from ._utils import (
    AttrDict,
    parse_system_add_remove,
    parse_system_image_changed,
    parse_system_title_changed,
)
from .const import COMMAND_PREFIX, EventType, SpecialContactId, SystemMessageType
from .events import (
    EventFilter,
    GroupImageChanged,
    GroupNameChanged,
    HookCallback,
    MemberListChanged,
    NewMessage,
    RawEvent,
)
from .rpc import Rpc


class Client:
    """Delta Chat client that listen to events for multiple account."""

    def __init__(
        self,
        rpc: Rpc,
        hooks: Optional[Iterable[Tuple[HookCallback, Union[type, EventFilter]]]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.rpc = rpc
        self.logger = logger or logging
        self._hooks: Dict[type, Set[tuple]] = {}
        self.add_hooks(hooks or [])

    def add_hooks(self, hooks: Iterable[Tuple[HookCallback, Union[type, EventFilter]]]) -> None:
        for hook, event in hooks:
            self.add_hook(hook, event)

    def add_hook(self, hook: HookCallback, event: Union[type, EventFilter] = RawEvent) -> None:
        """Register hook for the given event filter."""
        if isinstance(event, type):
            event = event()
        assert isinstance(event, EventFilter)
        self._hooks.setdefault(type(event), set()).add((hook, event))

    def remove_hook(self, hook: HookCallback, event: Union[type, EventFilter]) -> None:
        """Unregister hook from the given event filter."""
        if isinstance(event, type):
            event = event()
        self._hooks.get(type(event), set()).remove((hook, event))

    def configure(self, accid: int, email: str, password: str, **kwargs) -> None:
        self.rpc.set_config(accid, "addr", email)
        self.rpc.set_config(accid, "mail_pw", password)
        if kwargs:
            self.rpc.batch_set_config(accid, kwargs)
        self.rpc.configure(accid)
        self.logger.debug(f"Account {accid} configured")

    def run_forever(self, accid: int = 0) -> None:
        """Process events forever.
        if accid != 0, only that account will be started.
        """
        self.run_until(lambda _: False, accid)

    def run_until(self, func: Callable[[AttrDict], bool], accid: int = 0) -> AttrDict:
        """Process events until the given callable evaluates to True.

        The callable should accept an AttrDict object representing the
        last processed event. The event is returned when the callable
        evaluates to True.
        """
        self.logger.debug("Listening to incoming events...")
        if accid:
            self.rpc.start_io(accid)
            if self.rpc.is_configured(accid):
                self._process_messages(accid)  # Process old messages.
        else:
            self.rpc.start_io_for_all_accounts()
            for acc_id in self.rpc.get_all_account_ids():
                if self.rpc.is_configured(acc_id):
                    self._process_messages(acc_id)  # Process old messages.
        while True:
            raw_event = self.rpc.get_next_event()
            accid = raw_event.context_id
            event = raw_event.event
            self._on_event(accid, event)
            if event.kind == EventType.INCOMING_MSG:
                self._process_messages(accid)

            if func(event):
                return event

    def _on_event(
        self, accid: int, event: AttrDict, filter_type: Type[EventFilter] = RawEvent
    ) -> None:
        for hook, evfilter in self._hooks.get(filter_type, []):
            if evfilter.filter(self, event):
                try:
                    hook(self, accid, event)
                except Exception as ex:
                    self.logger.exception(ex)

    def _parse_command(self, accid: int, event: AttrDict) -> None:
        cmds = [hook[1].command for hook in self._hooks.get(NewMessage, []) if hook[1].command]
        parts = event.msg.text.split(maxsplit=1)
        payload = parts[1] if len(parts) > 1 else ""
        cmd = parts.pop(0)

        if "@" in cmd:
            suffix = "@" + self.rpc.get_contact(accid, SpecialContactId.SELF).address
            if cmd.endswith(suffix):
                cmd = cmd[: -len(suffix)]
            else:
                return

        parts = cmd.split("_")
        _payload = payload
        while parts:
            _cmd = "_".join(parts)
            if _cmd in cmds:
                break
            _payload = (parts.pop() + " " + _payload).rstrip()

        if parts:
            cmd = _cmd
            payload = _payload

        event["command"], event["payload"] = cmd, payload

    def _on_new_msg(self, accid: int, msg: AttrDict) -> None:
        event = AttrDict(command="", payload="", msg=msg)
        if not msg.is_info and msg.text.startswith(COMMAND_PREFIX):
            self._parse_command(accid, event)
        self._on_event(accid, event, NewMessage)

    def _handle_info_msg(self, accid: int, snapshot: AttrDict) -> None:
        event = AttrDict(msg=snapshot)

        img_changed = parse_system_image_changed(snapshot.text)
        if img_changed:
            _, event["image_deleted"] = img_changed
            self._on_event(accid, event, GroupImageChanged)
            return

        title_changed = parse_system_title_changed(snapshot.text)
        if title_changed:
            _, event["old_name"] = title_changed
            self._on_event(accid, event, GroupNameChanged)
            return

        members_changed = parse_system_add_remove(snapshot.text)
        if members_changed:
            action, event["member"], _ = members_changed
            event["member_added"] = action == "added"
            self._on_event(accid, event, MemberListChanged)
            return

        self.logger.warning(
            "ignoring unsupported system message id=%s text=%s",
            snapshot.id,
            snapshot.text,
        )

    def _process_messages(self, accid: int) -> None:
        for msgid in self.rpc.get_next_msgs(accid):
            msg = self.rpc.get_message(accid, msgid)
            if msg.from_id not in [SpecialContactId.SELF, SpecialContactId.DEVICE]:
                self._on_new_msg(accid, msg)
            if msg.is_info and msg.system_message_type != SystemMessageType.WEBXDC_INFO_MESSAGE:
                self._handle_info_msg(accid, msg)
            self.rpc.set_config(accid, "last_msg_id", str(msgid))


class Bot(Client):
    """A Delta Chat client with the bot flag set."""

    def configure(self, accid: int, email: str, password: str, **kwargs) -> None:
        kwargs.setdefault("bot", "1")
        super().configure(accid, email, password, **kwargs)
