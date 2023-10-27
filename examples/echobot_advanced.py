#!/usr/bin/env python3
"""Advanced echo bot example."""
import logging

from deltabot_cli import BotCli, EventType, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(event):
    if event.kind == EventType.INFO:
        logging.info(event.msg)
    elif event.kind == EventType.WARNING:
        logging.warning(event.msg)
    elif event.kind == EventType.ERROR:
        logging.error(event.msg)


@cli.on(events.NewMessage)
def echo(event):
    msg = event.message_snapshot
    msg.chat.send_text(msg.text)


@cli.on_init
def on_init(_bot, args):
    logging.info("Initializing bot with args: %s", args)


@cli.on_start
def on_start(_bot, _args):
    logging.info("Running bot...")


def test(bot, args):
    """set the bot's display name"""
    bot.account.set_config("displayname", args.name)
    logging.info("Bot display name updated to %s", args.name)


if __name__ == "__main__":
    subcmd = cli.add_subcommand(test)
    subcmd.add_argument("name", help="the new name to set")

    try:
        cli.start()
    except KeyboardInterrupt:
        pass
