# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import time
from pyrogram import filters, enums
from pyrogram.types import Message
from pyrogram.enums import ChatType
from pyrogram.errors import (ChatSendPlainForbidden, ChatWriteForbidden,
                             Forbidden, ChannelPrivate)

from BANIYA_V3 import app, lang


vc_start_times = {}


async def _safe_send(chat_id: int, text: str):
    """Message bhejne ka safe tarika"""
    try:
        await app.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=enums.ParseMode.HTML,
        )
    except (ChatSendPlainForbidden, ChatWriteForbidden, Forbidden, ChannelPrivate):
        pass
    except Exception as e:
        print(f"[VC Notify] Send error: {e}")


@app.on_message(filters.video_chat_started & filters.group)
async def on_voice_chat_started(_, message: Message):
    """Jab VC start ho — TURANT trigger hota hai"""
    chat_id = message.chat.id
    vc_start_times[chat_id] = time.time()

    try:
        _lang = await lang.get_lang(chat_id)
        await _safe_send(chat_id, _lang["vc_started"])
    except Exception as e:
        print(f"[VC Notify] Start error: {e}")


@app.on_message(filters.video_chat_ended & filters.group)
async def on_voice_chat_ended(_, message: Message):
    """Jab VC end ho — TURANT trigger hota hai"""
    chat_id = message.chat.id

    # Duration calculate karo
    if chat_id in vc_start_times:
        duration = int(time.time() - vc_start_times.pop(chat_id))
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        duration_str = f"{hours}h:{minutes}m:{seconds}s"
    else:
        duration_str = "0h:0m:0s"

    try:
        _lang = await lang.get_lang(chat_id)
        await _safe_send(
            chat_id,
            _lang["vc_ended"].format(duration=duration_str),
        )
    except Exception as e:
        print(f"[VC Notify] End error: {e}")


# --- Optional: Neeche wale functions ab zaroorat nahi, par rakh sakte ho ---
# Agar aapko `/play` ke baad wala old behavior bhi chahiye toh rakho,
# warna inhe delete kar sakte ho.

async def send_vc_started(chat_id: int) -> None:
    if chat_id in vc_start_times:
        return
    vc_start_times[chat_id] = time.time()
    try:
        _lang = await lang.get_lang(chat_id)
        await _safe_send(chat_id, _lang["vc_started"])
    except Exception as e:
        print(f"[VC Notify] Start error: {e}")


async def send_vc_ended(chat_id: int) -> None:
    if chat_id not in vc_start_times:
        return
    duration = int(time.time() - vc_start_times.pop(chat_id))
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    duration_str = f"{hours}h:{minutes}m:{seconds}s"
    try:
        _lang = await lang.get_lang(chat_id)
        await _safe_send(
            chat_id,
            _lang["vc_ended"].format(duration=duration_str),
        )
    except Exception as e:
        print(f"[VC Notify] End error: {e}")
