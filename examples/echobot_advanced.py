#!/usr/bin/env python3
"""Advanced echo bot example."""
from deltabot_cli import BotCli, EventType, events, is_not_known_command

cli = BotCli("echobot")


@cli.on(events.RawEvent)
def log_event(bot, _accid, event):
    if event.kind == EventType.INFO:
        bot.logger.info(event.msg)
    elif event.kind == EventType.WARNING:
        bot.logger.warning(event.msg)
    elif event.kind == EventType.ERROR:
        bot.logger.error(event.msg)


@cli.on(events.NewMessage(func=is_not_known_command))
def echo(bot, accid, event):
    msg = event.msg
    bot.rpc.misc_send_text_message(accid, msg.chat_id, msg.text)


@cli.on(events.NewMessage(command="/help"))
def _help(bot, accid, event):
    msg = event.msg
    bot.rpc.send_msg(accid, msg.chat_id, {"text": "I will repeat anything you say to me"})


@cli.on_init
def on_init(bot, args):
    bot.logger.info("Initializing CLI with args: %s", args)
    for accid in bot.rpc.get_all_account_ids():
        if not bot.rpc.get_config(accid, "displayname"):
            bot.rpc.set_config(accid, "displayname", "EchoBot")
            status = "I am a Delta Chat bot, I will repeat anything you say to me"
            bot.rpc.set_config(accid, "selfstatus", status)
            bot.rpc.set_config(accid, "delete_server_after", "1")  # delete immediately from server


@cli.on_start
def on_start(bot, _args):
    bot.logger.info("Running bot...")


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
