# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


__version__ = "3.0.2"

from config import Config

config = Config()
config.check()
tasks = []
boot = time.time()

from BANIYA_V3.core.bot import Bot
app = Bot()

from BANIYA_V3.core.dir import ensure_dirs
ensure_dirs()

from BANIYA_V3.core.userbot import Userbot
userbot = Userbot()

from BANIYA_V3.core.mongo import MongoDB
db = MongoDB()

from BANIYA_V3.core.lang import Language
lang = Language()

from BANIYA_V3.core.telegram import Telegram
from BANIYA_V3.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

from BANIYA_V3.helpers import Queue
queue = Queue()

from BANIYA_V3.core.calls import TgCall
anon = TgCall()


async def stop() -> None:
    logger.info("Stopping...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.exceptions.CancelledError:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()

    logger.info("Stopped.\n")
