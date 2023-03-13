#!/usr/bin/env python3
"""Advanced echo bot example."""
import asyncio
import logging

from deltabot_cli import BotCli, EventType, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
async def log_event(event):
    if event.type == EventType.INFO:
        logging.info(event.msg)
    elif event.type == EventType.WARNING:
        logging.warning(event.msg)
    elif event.type == EventType.ERROR:
        logging.error(event.msg)


@cli.on(events.NewMessage)
async def echo(event):
    await event.chat.send_text(event.message_snapshot.text)


@cli.on_init
async def on_init(_bot, args):
    logging.info("Initializing bot with args: %s", args)


@cli.on_start
async def on_start(_bot, _args):
    logging.info("Running bot...")


async def test(bot, args):
    """set the bot's display name"""
    await bot.account.set_config("displayname", args.name)
    logging.info("Bot display name updated to %s", args.name)


if __name__ == "__main__":
    subcmd = cli.add_subcommand(test)
    subcmd.add_argument("name", help="the new name to set")

    try:
        asyncio.run(cli.start())
    except KeyboardInterrupt:
        pass
