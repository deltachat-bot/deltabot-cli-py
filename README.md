<p align="center"><img height="150px" width="auto" src="https://github.com/deltachat-bot/deltabot-cli-py/raw/main/docs/_static/logo.svg"></p>
<h1 align="center">deltabot-cli for Python</h1>

<p align="center">
  <a href="https://pypi.org/project/deltabot-cli">
    <img src="https://img.shields.io/pypi/v/deltabot-cli.svg" alt="Latest Release">
  </a>
  <a href="https://github.com/deltachat-bot/deltabot-cli-py/actions/workflows/python-ci.yml">
    <img src="https://github.com/deltachat-bot/deltabot-cli-py/actions/workflows/python-ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
  </a>
</p>

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
from deltachat2 import MessageData, events
from deltabot_cli import BotCli

cli = BotCli("echobot")

@cli.on(events.RawEvent)
def log_event(bot, accid, event):
    bot.logger.info(event)

@cli.on(events.NewMessage)
def echo(bot, accid, event):
    msg = event.msg
    bot.rpc.send_msg(accid, msg.chat_id, MessageData(text=msg.text))

if __name__ == "__main__":
    cli.start()
```

If you run the above script you will have a bot CLI, that allows to configure and run a bot.
A progress bar is displayed while the bot is configuring, and logs are pretty-printed.

For more examples check the [examples](https://github.com/deltachat-bot/deltabot-cli-py/blob/main/examples) folder.
