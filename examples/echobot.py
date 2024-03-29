#!/usr/bin/env python3
"""Minimal echo-bot example."""

from deltachat2 import MsgData

from deltabot_cli import BotCli, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(bot, accid, event):
    bot.logger.debug(f"[acc={accid}] {event}")


@cli.on(events.NewMessage)
def echo(bot, accid, event):
    msg = event.msg
    bot.logger.info(f"received message: {msg.text!r}")
    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=msg.text))


if __name__ == "__main__":
    cli.start()
