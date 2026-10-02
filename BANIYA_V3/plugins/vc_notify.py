# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import time
from pytgcalls.types import Update

from BANIYA_V3 import app, anon, db, lang


vc_start_times = {}


@anon.calls.on_stream_start()
async def vc_stream_start(client, update: Update):
    """Jab VC start ho toh message bheje"""
    chat_id = update.chat_id
    vc_start_times[chat_id] = time.time()

    try:
        _lang = await lang.get_lang(chat_id)
        await app.send_message(
            chat_id=chat_id,
            text=_lang["vc_started"],
            parse_mode="html",
        )
    except Exception as e:
        print(f"[VC Notify] Start error: {e}")


@anon.calls.on_stream_end()
async def vc_stream_end(client, update: Update):
    """Jab VC end ho toh duration ke saath message bheje"""
    chat_id = update.chat_id

    if chat_id not in vc_start_times:
        return

    duration = int(time.time() - vc_start_times[chat_id])
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    duration_str = f"{hours}h:{minutes}m:{seconds}s"

    try:
        _lang = await lang.get_lang(chat_id)
        await app.send_message(
            chat_id=chat_id,
            text=_lang["vc_ended"].format(duration=duration_str),
            parse_mode="html",
        )
    except Exception as e:
        print(f"[VC Notify] End error: {e}")

    del vc_start_times[chat_id]
