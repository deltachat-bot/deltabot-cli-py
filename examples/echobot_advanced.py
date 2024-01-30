#!/usr/bin/env python3
"""Advanced echo bot example."""
import logging

from deltabot_cli import BotCli, EventType, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(bot, accid, event):
    if event.kind == EventType.INFO:
        logging.info(event.msg)
    elif event.kind == EventType.WARNING:
        logging.warning(event.msg)
    elif event.kind == EventType.ERROR:
        logging.error(event.msg)


@cli.on(events.NewMessage)
def echo(bot, accid, event):
    msg = event.msg
    bot.rpc.misc_send_text_message(accid, msg.chat_id, msg.text)


@cli.on_init
def on_init(_bot, args):
    logging.info("Initializing bot with args: %s", args)


@cli.on_start
def on_start(_bot, _args):
    logging.info("Running bot...")


def test(_cli, _bot, args):
    """just some example subcommand"""
    logging.info("Hello %s, this is an example subcommand!", args.name)


if __name__ == "__main__":
    subcmd = cli.add_subcommand(test)
    subcmd.add_argument("name", help="the new name to set")

    try:
        cli.start()
    except KeyboardInterrupt:
        pass
