# deltabot-cli for Python

[![Latest Release](https://img.shields.io/pypi/v/deltabot-cli.svg)](https://pypi.org/project/deltabot-cli)
[![CI](https://github.com/deltachat-bot/deltabot-cli-py/actions/workflows/python-ci.yml/badge.svg)](https://github.com/deltachat-bot/deltabot-cli-py/actions/workflows/python-ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Library to speedup Delta Chat bot development.

With this library you can focus on writing your event/message processing logic and let us handle the repetitive
process of creating the bot CLI.

## Install

```sh
pip install deltabot-cli-py
```

### Installing deltachat-rpc-server

This package depends on a standalone Delta Chat RPC server `deltachat-rpc-server` program.
To install it check:
https://github.com/deltachat/deltachat-core-rust/tree/master/deltachat-rpc-server

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
    event.chat.send_text(event.text)


if __name__ == "__main__":
    cli.start()
```

If you run the above script you will have a bot CLI, that allows to configure and run a bot.
A progress bar is displayed while the bot is configuring, and logs are pretty-printed.

For more examples check the [examples](https://github.com/deltachat-bot/deltabot-cli-py/tree/master/examples) folder.

**Note:** deltabot-cli uses [deltachat-rpc-client](https://github.com/deltachat/deltachat-core-rust/tree/master/deltachat-rpc-client) library, check its documentation and examples to better understand how to use deltabot-cli.
