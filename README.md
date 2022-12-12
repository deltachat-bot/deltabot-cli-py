# simplebot-aio

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Asynchronous library to help with Delta Chat bot development.

With simplebot-aio you can focus on writing your event processing logic and let simplebot-aio handle
for you the repetitive process of creating the bot CLI.

## Install

```sh
pip install simplebot-aio
```

## Example

Example echo-bot written with simplebot-aio:

```python
import asyncio
import logging
from simplebot_aio import BotCli, events

cli = BotCli("echobot")


@cli.on(events.RawEvent)
async def log_event(event):
    logging.info(event)


@cli.on(events.NewMessage)
async def echo(event):
    await event.chat.send_text(event.text)


if __name__ == "__main__":
    asyncio.run(cli.start())
```

If you run the above script you will have a bot CLI, that allows to configure and run a bot.
A progress bar is displayed while the bot is configuring, and logs are pretty-printed.

For more examples check the [examples](https://github.com/simplebot-org/simplebot-aio/tree/master/examples) folder.

**Note:** simplebot-aio uses [deltachat-rpc-client](https://github.com/deltachat/deltachat-core-rust/tree/master/deltachat-rpc-client) library, check its documentation and examples to better understand how to use simplebot-aio.
