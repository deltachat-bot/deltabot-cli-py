"""Utilities"""

import argparse
import re
import sys
from threading import Thread
from typing import TYPE_CHECKING, Callable, Iterable, Optional, Tuple, Type, Union

from rich.progress import track

if TYPE_CHECKING:
    from .client import Client
    from .events import EventFilter


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


class AttrDict(dict):
    """Dictionary that allows accessing values using the "dot notation" as attributes."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            {
                _camel_to_snake(key): to_attrdict(value)
                for key, value in dict(*args, **kwargs).items()
            }
        )

    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        raise AttributeError("Attribute not found: " + str(attr))

    def __setattr__(self, attr, val):
        if attr in self:
            raise AttributeError("Attribute-style access is read only")
        super().__setattr__(attr, val)


def _camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("__([A-Z])", r"_\1", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def to_attrdict(obj):
    if isinstance(obj, AttrDict):
        return obj
    if isinstance(obj, dict):
        return AttrDict(obj)
    if isinstance(obj, list):
        return [to_attrdict(elem) for elem in obj]
    return obj


def run_client_cli(
    hooks: Optional[Iterable[Tuple[Callable, Union[type, "EventFilter"]]]] = None,
    argv: Optional[list] = None,
    **kwargs,
) -> None:
    """Run a simple command line app, using the given hooks.

    Extra keyword arguments are passed to the internal Rpc object.
    """
    from .client import Client  # noqa

    _run_cli(Client, hooks, argv, **kwargs)


def run_bot_cli(
    hooks: Optional[Iterable[Tuple[Callable, Union[type, "EventFilter"]]]] = None,
    argv: Optional[list] = None,
    **kwargs,
) -> None:
    """Run a simple bot command line using the given hooks.

    Extra keyword arguments are passed to the internal Rpc object.
    """
    from .client import Bot  # noqa

    _run_cli(Bot, hooks, argv, **kwargs)


def _run_cli(
    client_type: Type["Client"],
    hooks: Optional[Iterable[Tuple[Callable, Union[type, "EventFilter"]]]] = None,
    argv: Optional[list] = None,
    **kwargs,
) -> None:
    from .rpc import Rpc  # noqa

    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(prog=argv[0] if argv else None)
    parser.add_argument(
        "accounts_dir",
        help="accounts folder (default: current working directory)",
        nargs="?",
    )
    parser.add_argument("--email", action="store", help="email address")
    parser.add_argument("--password", action="store", help="password")
    args = parser.parse_args(argv[1:])

    with Rpc(accounts_dir=args.accounts_dir, **kwargs) as rpc:
        core_version = rpc.get_system_info().deltachat_core_version
        accounts = rpc.get_all_account_ids()
        accid = accounts[0] if accounts else rpc.add_account()

        client = client_type(rpc, hooks)
        client.logger.debug("Running deltachat core %s", core_version)
        if not rpc.is_configured(accid):
            assert args.email, "Account is not configured and email must be provided"
            assert args.password, "Account is not configured and password must be provided"
            configure_thread = Thread(
                target=client.configure, args=(accid, args.email, args.password)
            )
            configure_thread.start()
        client.run_forever()


def extract_addr(text: str) -> str:
    """extract email address from the given text."""
    match = re.match(r".*\((.+@.+)\)", text)
    if match:
        text = match.group(1)
    text = text.rstrip(".")
    return text.strip()


def parse_system_image_changed(text: str) -> Optional[Tuple[str, bool]]:
    """return image changed/deleted info from parsing the given system message text."""
    text = text.lower()
    match = re.match(r"group image (changed|deleted) by (.+).", text)
    if match:
        action, actor = match.groups()
        return (extract_addr(actor), action == "deleted")
    return None


def parse_system_title_changed(text: str) -> Optional[Tuple[str, str]]:
    text = text.lower()
    match = re.match(r'group name changed from "(.+)" to ".+" by (.+).', text)
    if match:
        old_title, actor = match.groups()
        return (extract_addr(actor), old_title)
    return None


def parse_system_add_remove(text: str) -> Optional[Tuple[str, str, str]]:
    """return add/remove info from parsing the given system message text.

    returns a (action, affected, actor) tuple.
    """
    # You removed member a@b.
    # You added member a@b.
    # Member Me (x@y) removed by a@b.
    # Member x@y added by a@b
    # Member With space (tmp1@x.org) removed by tmp2@x.org.
    # Member With space (tmp1@x.org) removed by Another member (tmp2@x.org).",
    # Group left by some one (tmp1@x.org).
    # Group left by tmp1@x.org.
    text = text.lower()

    match = re.match(r"member (.+) (removed|added) by (.+)", text)
    if match:
        affected, action, actor = match.groups()
        return action, extract_addr(affected), extract_addr(actor)

    match = re.match(r"you (removed|added) member (.+)", text)
    if match:
        action, affected = match.groups()
        return action, extract_addr(affected), "me"

    if text.startswith("group left by "):
        addr = extract_addr(text[13:])
        if addr:
            return "removed", addr, addr

    return None


def parse_docstring(txt) -> tuple:
    """parse docstring, returning a tuple with short and long description"""
    description = txt
    i = txt.find(".")
    if i == -1:
        help_ = txt
    else:
        help_ = txt[: i + 1]
    return help_, description
