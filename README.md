# deltabot-cli for Python

[![Latest Release](https://img.shields.io/pypi/v/deltabot-cli.svg)](https://pypi.org/project/deltabot-cli)
[![CI](https://github.com/deltachat-bot/deltabot-cli-py/actions/workflows/python-ci.yml/badge.svg)](https://github.com/deltachat-bot/deltabot-cli-py/actions/workflows/python-ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Library to speedup Delta Chat bot development.

With this library you can focus on writing your event/message processing logic and let us handle the
repetitive process of creating the bot CLI.

## Install

```sh
pip install deltabot-cli
```

## Usage

Example echo-bot written with deltabot-cli:

```python
import logging
from deltabot_cli import BotCli, events

cli = BotCli("echobot")

@cli.on(events.RawEvent)
def log_event(event):
    logging.info(event)

@cli.on(events.NewMessage)
def echo(event):
    msg = event.msg
    event.rpc.misc_send_text_message(event.accid, msg.chat_id, msg.text)

if __name__ == "__main__":
    cli.start()
```

If you run the above script you will have a bot CLI, that allows to configure and run a bot.
A progress bar is displayed while the bot is configuring, and logs are pretty-printed.

For more examples check the [examples](https://github.com/deltachat-bot/deltabot-cli-py/tree/master/examples) folder.
