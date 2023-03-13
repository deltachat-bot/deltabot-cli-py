#!/usr/bin/env python3
"""Minimal echo-bot example."""

import asyncio
import logging

from deltabot_cli import BotCli, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
async def log_event(event):
    logging.info(event)


@cli.on(events.NewMessage)
async def echo(event):
    await event.chat.send_text(event.message_snapshot.text)


if __name__ == "__main__":
    asyncio.run(cli.start())
