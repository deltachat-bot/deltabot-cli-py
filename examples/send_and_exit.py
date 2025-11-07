#!/usr/bin/env python3
from argparse import Namespace

from deltachat2 import Bot, EventType, MsgData, events

from deltabot_cli import BotCli

cli = BotCli("sendbot")


@cli.on(events.RawEvent)
def log_event(bot: Bot, _accid: int, event) -> None:
    if event.kind == EventType.INFO:
        bot.logger.debug(event.msg)
    elif event.kind == EventType.WARNING:
        bot.logger.warning(event.msg)
    elif event.kind == EventType.ERROR:
        bot.logger.error(event.msg)


def send(cli: BotCli, bot: Bot, args: Namespace) -> None:
    """send a message"""
    accid = bot.rpc.get_all_account_ids()[0]

    # first fetch incoming messages to have updated chats state
    bot.logger.info("first syncing chats state...")
    bot.rpc.accounts_background_fetch(60)

    bot.logger.info("sending message...")
    chatid = cli.get_admin_chat(bot.rpc, accid)
    msgid = bot.rpc.send_msg(accid, chatid, MsgData(text=args.text, file=args.file))
    bot.run_until(
        lambda ev: ev.event.kind in (EventType.MSG_DELIVERED, EventType.MSG_FAILED)
        and ev.event.msg_id == msgid
    )
    bot.logger.info("Done, message sent")


if __name__ == "__main__":
    send_subcmd = cli.add_subcommand(send)
    send_subcmd.add_argument("text", help="the message's text")
    send_subcmd.add_argument(
        "file",
        nargs="?",
        help="path to a file to send as attachment",
    )
    cli.start()
