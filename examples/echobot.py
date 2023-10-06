#!/usr/bin/env python3
"""Minimal echo-bot example."""

import logging

from deltabot_cli import BotCli, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(event):
    logging.info(event)


@cli.on(events.NewMessage)
def echo(event):
    msg = event.message_snapshot
    msg.chat.send_text(msg.text)


if __name__ == "__main__":
    cli.start()
