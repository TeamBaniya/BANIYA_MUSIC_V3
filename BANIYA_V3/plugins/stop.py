# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from BANIYA_V3 import anon, app, db, lang
from BANIYA_V3.helpers import can_manage_vc


@app.on_message(filters.command(["end", "stop"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _stop(_, m: types.Message):
    if len(m.command) > 1:
        return

    call = await db.get_call(m.chat.id)
    await anon.stop(m.chat.id)
    if not call:
        return await m.reply_text(m.lang["not_playing"])

    await m.reply_text(m.lang["play_stopped"].format(m.from_user.mention))
