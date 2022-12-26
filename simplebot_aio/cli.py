"""Command Line Interface application"""
import asyncio
import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from typing import Callable, Coroutine, Optional, Set, Union

from appdirs import user_config_dir
from deltachat_rpc_client import AttrDict, Bot, DeltaChat, EventType, Rpc, events
from deltachat_rpc_client.rpc import JsonRpcError
from rich.logging import RichHandler

from ._utils import ConfigProgressBar, parse_docstring


class BotCli:
    """Class implementing a bot CLI.

    You can register additional CLI arguments and subcommands.
    Register event handlers with `on()`.
    Start running the bot with `start()`.
    """

    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self._parser = ArgumentParser(app_name)
        self._subparsers = self._parser.add_subparsers(title="subcommands")
        self._hooks = events.HookCollection()
        self._init_hooks: Set[Callable[[Bot, Namespace], Coroutine]] = set()
        self._start_hooks: Set[Callable[[Bot, Namespace], Coroutine]] = set()

    def on(self, event: Union[type, events.EventFilter]) -> Callable:  # noqa
        """Register decorated function as listener for the given event."""
        return self._hooks.on(event)

    def on_init(self, func: Callable[[Bot, Namespace], Coroutine]) -> Callable:
        """Register function to be called before the bot starts serving requests.

        The function will receive the bot instance and the CLI arguments received.
        """
        self._init_hooks.add(func)
        return func

    async def _on_init(self, bot: Bot, args: Namespace) -> None:
        for func in self._init_hooks:
            await func(bot, args)

    def on_start(self, func: Callable[[Bot, Namespace], Coroutine]) -> Callable:
        """Register function to be called when the bot is about to start serving requests.

        The function will receive the bot instance.
        """
        self._start_hooks.add(func)
        return func

    async def _on_start(self, bot: Bot, args: Namespace) -> None:
        for func in self._start_hooks:
            await func(bot, args)

    def add_generic_option(self, *flags, **kwargs) -> None:
        """Add a generic argument option to the CLI."""
        if not (flags and flags[0].startswith("-")):
            raise ValueError("can not generically add positional args")
        self._parser.add_argument(*flags, **kwargs)

    def add_subcommand(
        self,
        func: Callable[[Bot, Namespace], Coroutine],
        **kwargs,
    ) -> ArgumentParser:
        """Add a subcommand to the CLI."""
        if not kwargs.get("name"):
            kwargs["name"] = func.__name__
        if not kwargs.get("help") and not kwargs.get("description"):
            kwargs["help"], kwargs["description"] = parse_docstring(func.__doc__)
        subparser = self._subparsers.add_parser(**kwargs)
        subparser.set_defaults(cmd=func)
        return subparser

    async def init_parser(self) -> None:
        """Add some default options and subcommands.

        You don't have to call this method manually. Overwrite this method
        if you don't want the default options and subcommand.
        """
        config_dir = user_config_dir(self.app_name)
        self.add_generic_option(
            "--config-dir",
            "-c",
            help="Program configuration folder (default: %(default)s)",
            metavar="PATH",
            default=config_dir,
        )

        init_parser = self.add_subcommand(_init_cmd, name="init")
        init_parser.add_argument("addr", help="the e-mail address to use")
        init_parser.add_argument("password", help="account password")

        config_parser = self.add_subcommand(_config_cmd, name="config")
        config_parser.add_argument("option", help="option name", nargs="?")
        config_parser.add_argument("value", help="option value to set", nargs="?")

        avatar_parser = self.add_subcommand(_set_avatar_cmd, name="set_avatar")
        avatar_parser.add_argument("path", help="path to avatar image", nargs="?")

        self.add_subcommand(_qr_cmd, name="qr")

    async def get_accounts_dir(self, args: Namespace) -> str:
        """Get bot's account folder."""
        if not os.path.exists(args.config_dir):
            os.makedirs(args.config_dir)
        return os.path.join(args.config_dir, "accounts")

    async def start(self) -> None:
        """Start running the bot and processing incoming messages."""
        await self.init_parser()
        args = self._parser.parse_args()
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(show_path=False)],
        )
        accounts_dir = await self.get_accounts_dir(args)

        async with Rpc(accounts_dir=accounts_dir) as rpc:
            deltachat = DeltaChat(rpc)
            accounts = await deltachat.get_all_accounts()
            account = accounts[0] if accounts else await deltachat.add_account()

            bot = Bot(account, self._hooks)
            await self._on_init(bot, args)

            core_version = (await deltachat.get_system_info()).deltachat_core_version
            bot.logger.debug("Running deltachat core %s", core_version)
            if "cmd" in args:
                await args.cmd(bot, args)
            else:
                if await bot.is_configured():
                    await self._on_start(bot, args)
                    await bot.run_forever()
                else:
                    logging.error("Account is not configured")


async def _init_cmd(bot: Bot, args: Namespace) -> None:
    """initialize the account"""

    async def on_progress(event: AttrDict) -> None:
        if event.comment:
            logging.info(event.comment)
        pbar.set_progress(event.progress)

    async def configure() -> None:
        try:
            await bot.configure(email=args.addr, password=args.password)
        except JsonRpcError as err:
            logging.error(err)

    logging.info("Starting configuration process...")
    pbar = ConfigProgressBar()
    bot.add_hook(on_progress, events.RawEvent(EventType.CONFIGURE_PROGRESS))
    task = asyncio.create_task(configure())
    await bot.run_until(lambda _: pbar.progress in (-1, pbar.total))
    await task
    pbar.close()
    if pbar.progress == -1:
        logging.error("Configuration failed.")
    else:
        logging.info("Account configured successfully.")


async def _config_cmd(bot: Bot, args: Namespace) -> None:
    """set/get account configuration values"""
    if args.value:
        await bot.account.set_config(args.option, args.value)

    if args.option:
        try:
            value = await bot.account.get_config(args.option)
            print(f"{args.option}={value!r}")
        except JsonRpcError:
            logging.error("Unknown configuration option: %s", args.option)
    else:
        keys = (await bot.account.get_config("sys.config_keys")) or ""
        for key in keys.split():
            value = await bot.account.get_config(key)
            print(f"{key}={value!r}")


async def _set_avatar_cmd(bot: Bot, args: Namespace) -> None:
    """set account avatar"""
    await bot.account.set_avatar(args.path)
    if args.path:
        logging.info("Avatar updated.")
    else:
        logging.info("Avatar removed.")


async def _qr_cmd(bot: Bot, _args: Namespace) -> None:
    """get bot's verification QR"""
    qrdata, _ = await bot.account.get_qr_code()
    try:
        import qrcode

        qr = qrcode.QRCode()
        qr.add_data(qrdata)
        qr.print_ascii(invert=True)
    except ModuleNotFoundError:
        print("QR data:")
    print(qrdata)
