# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import time
from BANIYA_V3 import app, lang


vc_start_times = {}


async def send_vc_started(chat_id: int) -> None:
    """VC start hone par message bhejta hai"""
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


async def send_vc_ended(chat_id: int) -> None:
    """VC end hone par duration ke saath message bhejta hai"""
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

    vc_start_times.pop(chat_id, None)
