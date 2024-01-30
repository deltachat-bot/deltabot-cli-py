#!/usr/bin/env python3
"""Advanced echo bot example."""
from deltabot_cli import BotCli, EventType, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(bot, _accid, event):
    if event.kind == EventType.INFO:
        bot.logger.info(event.msg)
    elif event.kind == EventType.WARNING:
        bot.logger.warning(event.msg)
    elif event.kind == EventType.ERROR:
        bot.logger.error(event.msg)


@cli.on(events.NewMessage)
def echo(bot, accid, event):
    msg = event.msg
    bot.rpc.misc_send_text_message(accid, msg.chat_id, msg.text)


@cli.on_init
def on_init(bot, args):
    bot.logger.info("Initializing bot with args: %s", args)


@cli.on_start
def on_start(bot, _args):
    bot.logger.info("Running bot...")


def test(_cli, bot, args):
    """just some example subcommand"""
    bot.logger.info("Hello %s, this is an example subcommand!", args.name)


if __name__ == "__main__":
    subcmd = cli.add_subcommand(test)
    subcmd.add_argument("name", help="the new name to set")

    try:
        cli.start()
    except KeyboardInterrupt:
        pass
