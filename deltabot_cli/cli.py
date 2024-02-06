"""Command Line Interface application"""

import logging
import os
import time
from argparse import ArgumentParser, Namespace
from threading import Thread
from typing import Callable, Optional, Set, Union

import qrcode
from appdirs import user_config_dir
from rich.logging import RichHandler

from ._utils import AttrDict, ConfigProgressBar, parse_docstring
from .client import Bot
from .const import EventType
from .events import EventFilter, HookCollection, HookDecorator, RawEvent
from .rpc import JsonRpcError, Rpc

CliEventHook = Callable[[Bot, Namespace], None]
CmdCallback = Callable[["BotCli", Bot, Namespace], None]


class BotCli:
    """Class implementing a bot CLI.

    You can register additional CLI arguments and subcommands.
    Register event handlers with `on()`.
    Start running the bot with `start()`.
    """

    def __init__(self, app_name: str, log_level=logging.INFO) -> None:
        self.app_name = app_name
        self.log_level = log_level
        self._parser = ArgumentParser(app_name)
        self._subparsers = self._parser.add_subparsers(title="subcommands")
        self._hooks = HookCollection()
        self._init_hooks: Set[CliEventHook] = set()
        self._start_hooks: Set[CliEventHook] = set()
        self._bot: Bot

    def on(self, event: Union[type, EventFilter]) -> HookDecorator:  # noqa
        """Register decorated function as listener for the given event."""
        return self._hooks.on(event)

    def on_init(self, func: CliEventHook) -> CliEventHook:
        """Register function to be called before the bot starts serving requests.

        The function will receive the bot instance and the CLI arguments received.
        """
        self._init_hooks.add(func)
        return func

    def _on_init(self, bot: Bot, args: Namespace) -> None:
        for func in self._init_hooks:
            func(bot, args)

    def on_start(self, func: CliEventHook) -> CliEventHook:
        """Register function to be called when the bot is about to start serving requests.

        The function will receive the bot instance.
        """
        self._start_hooks.add(func)
        return func

    def _on_start(self, bot: Bot, args: Namespace) -> None:
        for func in self._start_hooks:
            func(bot, args)

    def add_generic_option(self, *flags, **kwargs) -> None:
        """Add a generic argument option to the CLI."""
        if not (flags and flags[0].startswith("-")):
            raise ValueError("can not generically add positional args")
        self._parser.add_argument(*flags, **kwargs)

    def add_subcommand(
        self,
        func: CmdCallback,
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

    def set_custom_config(self, key: str, value: str) -> None:
        """set a custom configuration value.

        This is useful to set custom settings for your application.
        """
        self._bot.account.set_config(f"ui.{self.app_name}.{key}", value)

    def get_custom_config(self, key: str) -> Optional[str]:
        """get custom a configuration value"""
        return self._bot.account.get_config(f"ui.{self.app_name}.{key}")

    def init_parser(self) -> None:
        """Add some default options and subcommands.

        You don't have to call this method manually. Overwrite this method
        if you don't want the default options and subcommand.
        """
        config_dir = user_config_dir(self.app_name)
        self.add_generic_option(
            "--config-dir",
            "-c",
            help="program configuration folder (default: %(default)s)",
            metavar="PATH",
            default=config_dir,
        )
        self.add_generic_option(
            "--account",
            "-a",
            help="operate over this account only when running any subcommand",
            metavar="ADDR",
        )

        init_parser = self.add_subcommand(_init_cmd, name="init")
        init_parser.add_argument("addr", help="the e-mail address to use")
        init_parser.add_argument("password", help="account password")

        config_parser = self.add_subcommand(_config_cmd, name="config")
        config_parser.add_argument("option", help="option name", nargs="?")
        config_parser.add_argument("value", help="option value to set", nargs="?")

        self.add_subcommand(_serve_cmd, name="serve")
        self.add_subcommand(_qr_cmd, name="qr")
        self.add_subcommand(_list_cmd, name="list")
        self.add_subcommand(_remove_cmd, name="remove")

    def get_accounts_dir(self, args: Namespace) -> str:
        """Get bot's account folder."""
        if not os.path.exists(args.config_dir):
            os.makedirs(args.config_dir)
        return os.path.join(args.config_dir, "accounts")

    def get_or_create_account(self, rpc: Rpc, addr: str) -> int:
        """Get account for address, if no account exists create a new one."""
        accid = self.get_account(rpc, addr)
        if not accid:
            accid = rpc.add_account()
            rpc.set_config(accid, "addr", addr)
        return accid

    def get_account(self, rpc: Rpc, addr: str) -> int:
        """Get account id for address.
        If no account exists with the given address, zero is returned.
        """
        try:
            return int(addr)
        except ValueError:
            for accid in rpc.get_all_account_ids():
                if addr == self.get_address(rpc, accid):
                    return accid
        return 0

    def get_address(self, rpc: Rpc, accid: int) -> str:
        if rpc.is_configured(accid):
            return rpc.get_config(accid, "configured_addr")
        return rpc.get_config(accid, "addr")

    def start(self) -> None:
        """Start running the bot and processing incoming messages."""
        self.init_parser()
        args = self._parser.parse_args()
        logging.basicConfig(
            level=self.log_level,
            format="%(message)s",
            handlers=[RichHandler(show_path=False)],
        )
        accounts_dir = self.get_accounts_dir(args)

        with Rpc(accounts_dir=accounts_dir) as rpc:
            self._bot = Bot(rpc, self._hooks)
            self._on_init(self._bot, args)

            core_version = rpc.get_system_info().deltachat_core_version
            self._bot.logger.info("Running deltachat core %s", core_version)
            if "cmd" in args:
                args.cmd(self, self._bot, args)
            else:
                self._parser.parse_args(["-h"])


def _init_cmd(cli: BotCli, bot: Bot, args: Namespace) -> None:
    """initialize the account"""

    def on_progress(event: AttrDict) -> None:
        if event.comment:
            bot.logger.info(event.comment)
        pbar.set_progress(event.progress)

    def configure() -> None:
        try:
            bot.configure(accid, email=args.addr, password=args.password)
        except JsonRpcError as err:
            bot.logger.error(err)

    if args.account:
        accid = cli.get_account(bot.rpc, args.account)
        if not accid:
            bot.logger.error(f"unknown account: {args.account!r}")
            return
    else:
        accid = cli.get_or_create_account(bot.rpc, args.addr)

    bot.logger.info("Starting configuration process...")
    pbar = ConfigProgressBar()
    bot.add_hook(on_progress, RawEvent(EventType.CONFIGURE_PROGRESS))
    task = Thread(target=configure)
    task.start()
    bot.run_until(lambda _: pbar.progress in (-1, pbar.total))
    task.join()
    pbar.close()
    if pbar.progress == -1:
        bot.logger.error("Configuration failed.")
    else:
        bot.logger.info("Account configured successfully.")


def _serve_cmd(cli: BotCli, bot: Bot, args: Namespace) -> None:
    """start processing messages"""
    rpc = bot.rpc
    if args.account:
        accounts = [cli.get_account(rpc, args.account)]
        if not accounts[0]:
            bot.logger.error(f"unknown account: {args.account!r}")
            return
    else:
        accounts = rpc.get_all_account_ids()
    addrs = []
    for accid in accounts:
        if rpc.is_configured(accid):
            addrs.append(rpc.get_config(accid, "configured_addr"))
        else:
            bot.logger.error(f"account {accid} not configured")
    if len(addrs) != 0:
        bot.logger.info(f"Listening at: {', '.join(addrs)}")
        cli._on_start(bot, args)  # noqa
        while True:
            try:
                bot.run_forever(accounts[0] if args.account else 0)
            except KeyboardInterrupt:
                return
            except Exception as ex:  # pylint:disable=W0703
                bot.logger.exception(ex)
                time.sleep(5)
    else:
        bot.logger.error("There are no configured accounts to serve")


def _config_cmd(cli: BotCli, bot: Bot, args: Namespace) -> None:
    """set/get account configuration values"""
    if args.account:
        accounts = [cli.get_account(bot.rpc, args.account)]
        if not accounts[0]:
            bot.logger.error(f"unknown account: {args.account!r}")
            return
    else:
        accounts = bot.rpc.get_all_account_ids()
    for accid in accounts:
        addr = cli.get_address(bot.rpc, accid)
        print(f"Account #{accid} ({addr}):")
        _config_cmd_for_acc(bot, accid, args)
        print("")
    if not accounts:
        bot.logger.error("There are no accounts yet, add a new account using the init subcommand")


def _config_cmd_for_acc(bot: Bot, accid: int, args: Namespace) -> None:
    if args.value:
        bot.rpc.set_config(accid, args.option, args.value)

    if args.option:
        try:
            value = bot.rpc.get_config(accid, args.option)
            print(f"{args.option}={value!r}")
        except JsonRpcError:
            bot.logger.error("Unknown configuration option: %s", args.option)
    else:
        keys = bot.rpc.get_config(accid, "sys.config_keys") or ""
        for key in keys.split():
            value = bot.rpc.get_config(accid, key)
            print(f"{key}={value!r}")


def _qr_cmd(cli: BotCli, bot: Bot, args: Namespace) -> None:
    """get bot's verification QR"""
    if args.account:
        accounts = [cli.get_account(bot.rpc, args.account)]
        if not accounts[0]:
            bot.logger.error(f"unknown account: {args.account!r}")
            return
    else:
        accounts = bot.rpc.get_all_account_ids()
    for accid in accounts:
        addr = cli.get_address(bot.rpc, accid)
        print(f"Account #{accid} ({addr}):")
        _qr_cmd_for_acc(bot, accid)
        print("")
    if not accounts:
        bot.logger.error("There are no accounts yet, add a new account using the init subcommand")


def _qr_cmd_for_acc(bot: Bot, accid: int) -> None:
    """get bot's verification QR"""
    if bot.rpc.is_configured(accid):
        qrdata, _ = bot.rpc.get_chat_securejoin_qr_code_svg(accid, None)
        code = qrcode.QRCode()
        code.add_data(qrdata)
        code.print_ascii(invert=True)
        fragment = qrdata.split(":", maxsplit=1)[1].replace("#", "&", 1)
        print(f"https://i.delta.chat/#{fragment}")
    else:
        bot.logger.error("account not configured")


def _list_cmd(cli: BotCli, bot: Bot, _args: Namespace) -> None:
    """show a list of existing bot accounts"""
    rpc = bot.rpc
    accounts = rpc.get_all_account_ids()
    for accid in accounts:
        addr = cli.get_address(rpc, accid)
        if not rpc.is_configured(accid):
            addr = addr + " (not configured)"
        print(f"#{accid} - {addr}")


def _remove_cmd(cli: BotCli, bot: Bot, args: Namespace) -> None:
    """remove Delta Chat accounts from the bot"""
    if args.account:
        accid = cli.get_account(bot.rpc, args.account)
        if not accid:
            bot.logger.error(f"unknown account: {args.account!r}")
            return
    else:
        accounts = bot.rpc.get_all_account_ids()
        if len(accounts) == 1:
            accid = accounts[0]
        else:
            bot.logger.error(
                "There are more than one account, to remove one of them, pass the account"
                " address with -a/--account option"
            )
            return

    addr = cli.get_address(bot.rpc, accid)
    bot.rpc.remove_account(accid)
    print(f"Account #{accid} ({addr}) removed successfully.")
