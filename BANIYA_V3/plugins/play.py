# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pathlib import Path

from pyrogram import filters, types

from BANIYA_V3 import anon, app, config, db, lang, queue, tg, yt
from BANIYA_V3.helpers import buttons, utils
from BANIYA_V3.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


# ========== AUDIO PLAY COMMANDS ==========
@app.on_message(
    filters.command(["play", "playforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    sent = await m.reply_text(m.lang["play_searching"])
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    if not file:
        return await sent.edit_text(m.lang["play_usage"])

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if position != 0 or await db.get_call(m.chat.id):
            await sent.edit_text(
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    m.chat.id, file.id, m.lang["play_now"]
                ),
            )
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await yt.download(file.id, video=video)

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )


# ========== VIDEO PLAY COMMANDS ==========
@app.on_message(
    filters.command(["vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def vplay_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = True,  # Changed to True for video
    url: str = None,
) -> None:
    """Handle video playback in voice chat"""
    
    # Check if video is enabled in config
    if not hasattr(config, 'VIDEO_ALLOWED') or config.VIDEO_ALLOWED:
        pass
    else:
        await m.reply_text("❌ **Video playback is disabled!**\nUse `/play` for audio only.")
        return
    
    sent = await m.reply_text("🎬 **Searching video...**")
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    # Check if command is force version
    if m.command[0].endswith("force"):
        force = True

    # Handle media from reply
    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    # Handle m3u8 streams
    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video=True)

    # Handle URL or playlist
    elif url:
        if "playlist" in url:
            await sent.edit_text("📋 **Fetching playlist...**")
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video=True
            )

            if not tracks:
                return await sent.edit_text("❌ Failed to fetch playlist!")

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=True)

        if not file:
            return await sent.edit_text(
                "❌ **Video not found!**\n\n"
                f"Try checking the link or join @{config.SUPPORT_CHAT} for help."
            )

    # Handle search query
    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        
        # Show searching status
        await sent.edit_text(f"🔍 **Searching:** `{query[:50]}`")
        
        file = await yt.search(query, sent.id, video=True)
        
        if not file:
            return await sent.edit_text(
                "❌ **No videos found!**\n\n"
                f"Try different keywords or join @{config.SUPPORT_CHAT} for help."
            )

    if not file:
        return await sent.edit_text(
            "📝 **Usage:**\n"
            "• `/vplay <video name>`\n"
            "• `/vplay <youtube link>`\n"
            "• `/vplayforce <video name>` (force play)\n\n"
            "**Example:** `/vplay Dil Chahiye`"
        )

    # Check duration limit
    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            f"⏰ **Duration Limit Exceeded!**\n\n"
            f"Video length: `{file.duration}`\n"
            f"Maximum allowed: `{config.DURATION_LIMIT // 60} minutes`\n\n"
            f"Try a shorter video."
        )

    # Log to logger group if enabled
    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration, video=True)

    # Set user mention
    file.user = mention
    
    # Add to queue
    if force:
        queue.force_add(m.chat.id, file)
        await sent.edit_text(
            f"⚡ **Force Playing Video!**\n\n"
            f"🎬 **Title:** [{file.title[:50]}]({file.url})\n"
            f"⏱️ **Duration:** `{file.duration}`\n"
            f"👤 **Requested by:** {m.from_user.mention}",
            disable_web_page_preview=True
        )
    else:
        position = queue.add(m.chat.id, file)

        # If position != 0 or call is active, add to queue
        if position != 0 or await db.get_call(m.chat.id):
            await sent.edit_text(
                f"📌 **Queued at position:** `#{position}`\n\n"
                f"🎬 **Title:** [{file.title[:50]}]({file.url})\n"
                f"⏱️ **Duration:** `{file.duration}`\n"
                f"👤 **Requested by:** {m.from_user.mention}\n\n"
                f"_Use /playnow to skip to this video_",
                reply_markup=buttons.play_queued(
                    m.chat.id, file.id, "Play Now"
                ),
                disable_web_page_preview=True
            )
            
            # Add playlist tracks to queue
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=f"📋 **Playlist added:** `{len(tracks)}` videos\n\n" + added,
                    disable_web_page_preview=True
                )
            return

    # Download video if not already downloaded
    if not file.file_path:
        fname = f"downloads/{file.id}.mp4"
        if Path(fname).exists() and Path(fname).stat().st_size > 0:
            file.file_path = fname
        else:
            await sent.edit_text(f"📥 **Downloading video:** `{file.title[:40]}`...")
            file.file_path = await yt.download(file.id, video=True)
            
            # Check if download failed
            if not file.file_path:
                await sent.edit_text(
                    "❌ **Download Failed!**\n\n"
                    "The video might be too large or blocked.\n"
                    "Try another video or use `/play` for audio only."
                )
                return

    # Play the video
    await sent.edit_text(
        f"🎬 **Now Playing Video!**\n\n"
        f"**Title:** [{file.title[:50]}]({file.url})\n"
        f"**Duration:** `{file.duration}`\n"
        f"**Requested by:** {m.from_user.mention}\n\n"
        f"_Use /stop to stop playback_",
        disable_web_page_preview=True
    )
    
    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    
    # Add playlist tracks to queue after current video
    if not tracks:
        return
    
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=f"📋 **Playlist queued:** `{len(tracks)}` videos\n\n" + added,
        disable_web_page_preview=True
    )


# ========== HELP COMMAND UPDATE ==========
@app.on_message(filters.command("vhelp") & filters.group & ~app.bl_users)
@lang.language()
async def vhelp_handler(_, m: types.Message):
    """Help command for video playback"""
    await m.reply_text(
        "🎬 **Video Playback Commands**\n\n"
        "**Play Video:**\n"
        "• `/vplay <video name>` - Search and play video\n"
        "• `/vplay <youtube link>` - Play video from link\n"
        "• `/vplayforce` - Force play (skips queue)\n\n"
        "**Control:**\n"
        "• `/vstop` - Stop video playback\n"
        "• `/vpause` - Pause video\n"
        "• `/vresume` - Resume video\n"
        "• `/vskip` - Skip current video\n\n"
        "**Queue:**\n"
        "• `/vqueue` - Show video queue\n"
        "• `/vclear` - Clear queue\n\n"
        f"**Support:** @{config.SUPPORT_CHAT}\n"
        f"**Channel:** @{config.CHANNEL}",
        disable_web_page_preview=True
    )
