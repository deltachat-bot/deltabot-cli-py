#!/usr/bin/env python3
"""Minimal echo-bot example."""

from deltabot_cli import BotCli, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(bot, _accid, event):
    bot.logger.info(event)


@cli.on(events.NewMessage)
def echo(bot, accid, event):
    msg = event.msg
    bot.rpc.misc_send_text_message(accid, msg.chat_id, msg.text)


if __name__ == "__main__":
    cli.start()
