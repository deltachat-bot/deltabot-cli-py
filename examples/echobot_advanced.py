#!/usr/bin/env python3
"""Advanced echo bot example."""
from deltachat2 import MsgData

from deltabot_cli import BotCli, EventType, events

cli = BotCli("echobot")


@cli.on_init
def on_init(bot, args):
    bot.logger.info("Initializing CLI with args: %s", args)
    for accid in bot.rpc.get_all_account_ids():
        if not bot.rpc.get_config(accid, "displayname"):
            bot.rpc.set_config(accid, "displayname", "EchoBot")
            status = "I am a Delta Chat bot, I will repeat anything you say to me"
            bot.rpc.set_config(accid, "selfstatus", status)
            bot.rpc.set_config(accid, "delete_server_after", "1")  # delete immediately from server
            # bot.rpc.set_config(accid, "delete_device_after", "3600")


@cli.on_start
def on_start(bot, _args):
    bot.logger.info(
        "Bot is listening to requests... here connect to databases, start worker threads, etc"
    )


@cli.on(events.RawEvent)
def log_event(bot, accid, event):
    if event.kind == EventType.INFO:
        bot.logger.debug(event.msg)
    elif event.kind == EventType.WARNING:
        bot.logger.warning(event.msg)
    elif event.kind == EventType.ERROR:
        bot.logger.error(event.msg)
    elif event.kind == EventType.SECUREJOIN_INVITER_PROGRESS:
        if event.progress == 1000 and not bot.rpc.get_contact(accid, event.contact_id).is_bot:
            # bot's QR scanned by an user, send introduction message
            chatid = bot.rpc.create_chat_by_contact_id(accid, event.contact_id)
            reply = MsgData(text="Hi, I will repeat anything you say to me")
            bot.rpc.send_msg(accid, chatid, reply)


@cli.on(events.NewMessage(is_info=False))
def echo(bot, accid, event):
    if bot.has_command(event.command):
        return
    msg = event.msg
    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text=msg.text))


@cli.on(events.NewMessage(command="/help"))
def _help(bot, accid, event):
    msg = event.msg
    bot.rpc.send_msg(accid, msg.chat_id, MsgData(text="I will repeat anything you say to me"))


def test(_cli, bot, args):
    """just some example subcommand"""
    bot.logger.info("Hello %s, this is an example subcommand!", args.name)


if __name__ == "__main__":
    subcmd = cli.add_subcommand(test)
    subcmd.add_argument("name", help="your name")

    try:
        cli.start()
    except KeyboardInterrupt:
        pass
