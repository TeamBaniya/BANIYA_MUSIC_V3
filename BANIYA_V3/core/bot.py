# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import pyrogram
from pyrogram import Client, filters, enums, types

from BANIYA_V3 import config, logger


class Bot(pyrogram.Client):
    def __init__(self):
        # Check pyrogram version for compatibility
        self.pyro_version = tuple(map(int, pyrogram.__version__.split('.')))
        
        # Base kwargs for all versions
        kwargs = {
            "name": "BANIYA_V3",
            "api_id": config.API_ID,
            "api_hash": config.API_HASH,
            "bot_token": config.BOT_TOKEN,
            "parse_mode": enums.ParseMode.HTML,
            "max_concurrent_transmissions": 7,
        }
        
        # Add link_preview_options for newer versions (>= 2.0.0)
        if self.pyro_version >= (2, 0, 0):
            kwargs["link_preview_options"] = types.LinkPreviewOptions(is_disabled=True)
        else:
            # Fallback for older versions
            kwargs["disable_web_page_preview"] = True
        
        super().__init__(**kwargs)
        
        self.owner = config.OWNER_ID
        self.logger = config.LOGGER_ID
        
        # Initialize filters
        self.bl_users = filters.user()
        self.sudoers = filters.user(self.owner)
        
        # Bot info (will be set in boot)
        self.id = None
        self.name = None
        self.username = None
        self.mention = None

    async def boot(self):
        """
        Starts the bot and performs initial setup.

        Raises:
            SystemExit: If the bot fails to access the log group or is not an administrator in the logger group.
        """
        await super().start()
        
        # Set bot info
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            # Try to send message to log group
            await self.send_message(self.logger, "✅ **Bot Started Successfully!**")
            
            # Check bot's permissions in log group
            get = await self.get_chat_member(self.logger, self.id)
            
        except Exception as ex:
            raise SystemExit(
                f"❌ **Bot Failed to Access Log Group!**\n\n"
                f"**Log Group ID:** `{self.logger}`\n"
                f"**Reason:** `{ex}`\n\n"
                f"**Solutions:**\n"
                f"1. Make sure the bot is admin in the log group\n"
                f"2. Check if LOGGER_ID in config is correct\n"
                f"3. Add bot to the group first"
            )

        # Check if bot is admin
        if get.status != enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit(
                f"❌ **Bot is Not Admin in Logger Group!**\n\n"
                f"Please promote @{self.username} as an administrator in the log group.\n"
                f"Required permissions:\n"
                f"• Send Messages\n"
                f"• Delete Messages\n"
                f"• Ban Users\n"
                f"• Invite Users"
            )
        
        logger.info(f"✅ Bot started successfully as @{self.username}")
        logger.info(f"📊 Pyrogram Version: {pyrogram.__version__}")
        logger.info(f"👤 Bot ID: {self.id}")
        logger.info(f"📝 Log Group: {self.logger}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        try:
            await self.send_message(self.logger, "🛑 **Bot Stopped!**")
        except:
            pass
        
        await super().stop()
        logger.info("✅ Bot stopped successfully.")


# Alternative simpler version without version checking (if above doesn't work)
class BotSimple(Client):
    def __init__(self):
        try:
            # Try with new LinkPreviewOptions (Pyrogram v2.0.0+)
            super().__init__(
                name="BANIYA_V3",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                bot_token=config.BOT_TOKEN,
                parse_mode=enums.ParseMode.HTML,
                max_concurrent_transmissions=7,
                link_preview_options=types.LinkPreviewOptions(is_disabled=True),
            )
        except AttributeError:
            # Fallback for older versions
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

    async def boot(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(self.logger, "✅ Bot Started")
            get = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(f"Bot failed to access log group: {self.logger}\nReason: {ex}")

        if get.status != enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit("Please promote the bot as an admin in logger group.")
        
        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        await super().stop()
        logger.info("Bot stopped.")
