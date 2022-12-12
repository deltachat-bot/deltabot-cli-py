#!/usr/bin/env python3
"""Advanced echo bot example."""
import asyncio
import logging

from simplebot_aio import BotCli, EventType, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
async def log_event(event):
    if event.type == EventType.INFO:
        logging.info(event.msg)
    elif event.type == EventType.WARNING:
        logging.warning(event.msg)


@cli.on(events.RawEvent(EventType.ERROR))
async def log_error(event):
    logging.error(event.msg)


@cli.on(events.NewMessage(func=lambda e: not e.command))
async def echo(event):
    if event.text or event.file:
        await event.chat.send_message(text=event.text, file=event.file)


@cli.on(events.NewMessage(command="/help"))
async def help_command(event):
    await event.chat.send_text("Send me any message and I will echo it back")


@cli.on_init
async def on_init(bot, args):
    logging.info("Initializing bot with args: %s", args)


@cli.on_start
async def on_start(bot):
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
