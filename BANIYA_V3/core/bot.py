# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pyrogram import Client, filters, enums
from BANIYA_V3 import config, logger


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="BANIYA_V3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            disable_web_page_preview=True,
        )
        self.owner = config.OWNER_ID
        self.logger = config.LOGGER_ID
        self.bl_users = filters.user()
        self.sudoers = filters.user(self.owner)
        self.id = None
        self.name = None
        self.username = None
        self.mention = None

    async def boot(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(self.logger, "✅ Bot Started Successfully!")
            get = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(f"❌ Bot failed to access log group: {self.logger}\nReason: {ex}")

        if get.status != enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit("❌ Please promote bot as admin in logger group!")
        
        logger.info(f"✅ Bot started as @{self.username}")

    async def exit(self):
        await super().stop()
        logger.info("✅ Bot stopped.")
