# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, List, Union

from py_yt import Playlist, VideosSearch
from youtubesearchpython import VideosSearch as NewVideosSearch

from BANIYA_V3 import config, logger
from BANIYA_V3.helpers import Track, utils

# ============ API CONFIGURATION ============
# Primary API - Fast download with API key
API_URL = "https://shrutibots.site"
SHRUTI_API_KEY = getattr(config, "SHRUTI_API_KEY", None) or os.getenv("SHRUTI_API_KEY", "ShrutiBotsz11gSvi8c6u1vOVskrxS")

# Legacy/Fallback API - Token based (no key needed)
FALLBACK_API_URL = os.getenv("FALLBACK_API_URL", "http://40.192.71.152:1000")

DOWNLOAD_DIR = "downloads"

# Create download directory if not exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "BANIYA_V3/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def get_cookies(self) -> Optional[str]:
        """Get random cookie file path"""
        if not self.checked:
            if os.path.exists(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        return random.choice(self.cookies) if self.cookies else None

    async def save_cookies(self, urls: List[str]) -> None:
        """Save cookies from URLs"""
        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)

        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    name = url.split("/")[-1]
                    link = "https://batbin.me/raw/" + name
                    async with session.get(link) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            cookie_path = f"{self.cookie_dir}/{name}.txt"
                            with open(cookie_path, "wb") as fw:
                                fw.write(content)
                            logger.info(f"Cookie saved: {cookie_path}")
                except Exception as e:
                    logger.error(f"Cookie Save Error for {url}: {e}")

        logger.info(f"Cookies updated in {self.cookie_dir}.")

    # ============ API 1: PRIMARY SHRUTI API (WITH API KEY) ============
    async def download_from_api(self, video_id: str, video: bool) -> Optional[str]:
        """
        Primary API download with API key.
        Endpoint: /download?url={video_id}&type=audio&api_key={KEY}
        """
        mode = "video" if video else "audio"
        ext = "mp4" if video else "mp3"
        file_path = f"{DOWNLOAD_DIR}/{video_id}.{ext}"

        # Check if already downloaded
        if Path(file_path).exists() and Path(file_path).stat().st_size > 0:
            return file_path

        # Agar API key nahi hai to skip karo
        if not SHRUTI_API_KEY:
            logger.warning("SHRUTI_API_KEY not set - skipping primary API")
            return None

        try:
            logger.info(f"🔄 Trying Primary API (Direct) for {video_id}...")

            async with aiohttp.ClientSession() as session:
                params = {
                    "url": video_id,
                    "type": mode,
                    "api_key": SHRUTI_API_KEY,
                }

                async with session.get(
                    f"{API_URL}/download",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=180),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠️ Primary API status {resp.status}")
                        return None

                    with open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            f.write(chunk)

                    if Path(file_path).exists() and Path(file_path).stat().st_size > 0:
                        logger.info(f"✅ Downloaded via Primary API: {file_path}")
                        return file_path

        except Exception as e:
            logger.error(f"❌ Primary API error for {video_id}: {e}")

        return None

    # ============ API 2: FALLBACK TOKEN-BASED API ============
    async def download_from_fallback_api(self, video_id: str, video: bool) -> Optional[str]:
        """
        Fallback API download (token based, no key needed).
        Step 1: GET /download?url={id}&type={mode} -> returns download_token
        Step 2: GET /stream/{id}?type={mode}&token={token} -> file
        """
        mode = "video" if video else "audio"
        ext = "mp4" if video else "mp3"
        file_path = f"{DOWNLOAD_DIR}/{video_id}.{ext}"

        if Path(file_path).exists() and Path(file_path).stat().st_size > 0:
            return file_path

        try:
            logger.info(f"🔄 Trying Fallback API (Token) for {video_id}...")

            async with aiohttp.ClientSession() as session:
                # Step 1: Get download token
                async with session.get(
                    f"{FALLBACK_API_URL}/download",
                    params={"url": video_id, "type": mode},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠️ Fallback API status {resp.status}")
                        return None

                    data = await resp.json()
                    token = data.get("token") or data.get("download_token")

                    if not token:
                        logger.warning(f"⚠️ No token from Fallback API: {data}")
                        return None

                # Step 2: Download with token
                stream_url = f"{FALLBACK_API_URL}/stream/{video_id}?type={mode}&token={token}"

                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=600),
                ) as fresp:
                    if fresp.status not in (200, 302):
                        logger.warning(f"⚠️ Fallback stream status {fresp.status}")
                        return None

                    # Handle redirect
                    if fresp.status == 302:
                        redirect_url = fresp.headers.get("Location")
                        if not redirect_url:
                            return None
                        async with session.get(redirect_url) as redir_resp:
                            if redir_resp.status != 200:
                                return None
                            with open(file_path, "wb") as f:
                                async for chunk in redir_resp.content.iter_chunked(16384):
                                    f.write(chunk)
                    else:
                        with open(file_path, "wb") as f:
                            async for chunk in fresp.content.iter_chunked(16384):
                                f.write(chunk)

                    if Path(file_path).exists() and Path(file_path).stat().st_size > 0:
                        logger.info(f"✅ Downloaded via Fallback API: {file_path}")
                        return file_path

        except Exception as e:
            logger.error(f"❌ Fallback API error for {video_id}: {e}")

        return None

    # ============ YT-DLP (WITH COOKIES FALLBACK) ============
    async def download_with_ytdlp(self, video_id: str, video: bool = False) -> Optional[str]:
        """Download using yt-dlp with Android spoofing"""
        url = self.base + video_id
        ext = "mp4" if video else "mp3"
        filename = f"{DOWNLOAD_DIR}/{video_id}.{ext}"

        # Check if already exists
        if Path(filename).exists() and Path(filename).stat().st_size > 0:
            return filename

        cookie = self.get_cookies()

        ydl_opts = {
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            # Android Spoofing - Important for bypassing blocks
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "player_skip": ["webpage", "configs"],
                    "skip": ["dash", "hls"],
                }
            },
        }

        # Cookies sirf tab use karo jab available ho
        if cookie:
            ydl_opts["cookiefile"] = cookie

        if video:
            ydl_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
            ydl_opts["merge_output_format"] = "mp4"
        else:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        def _download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                    if video:
                        final_file = f"{DOWNLOAD_DIR}/{video_id}.mp4"
                    else:
                        final_file = f"{DOWNLOAD_DIR}/{video_id}.mp3"

                    if Path(final_file).exists() and Path(final_file).stat().st_size > 0:
                        return final_file
                    return None
            except Exception as e:
                logger.error(f"yt-dlp download failed for {video_id}: {e}")
                return None

        return await asyncio.to_thread(_download)

    # ============ MAIN DOWNLOAD (API1 -> API2 -> yt-dlp) ============
    async def download(self, video_id: str, video: bool = False) -> Optional[str]:
        """
        Download video/audio from YouTube with multiple fallback methods.

        Order:
          1. Primary API (with API key)
          2. Fallback API (token based)
          3. yt-dlp (last resort, with cookies if available)

        Args:
            video_id: YouTube video ID
            video: True for video download, False for audio only

        Returns:
            Path to downloaded file or None if failed
        """
        # Method 1: Primary API (with API key)
        api_file = await self.download_from_api(video_id, video)
        if api_file:
            return api_file

        # Method 2: Fallback API (token based)
        fallback_file = await self.download_from_fallback_api(video_id, video)
        if fallback_file:
            return fallback_file

        # Method 3: yt-dlp with Android spoofing
        ytdlp_file = await self.download_with_ytdlp(video_id, video)
        if ytdlp_file:
            return ytdlp_file

        logger.error(f"❌ All download methods failed for {video_id}")
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Optional[Track]:
        """Search for a single video/audio"""
        try:
            try:
                search = NewVideosSearch(query, limit=1)
                results = await search.next()
            except:
                search = VideosSearch(query, limit=1)
                results = await search.next()

            if results and results.get("result"):
                data = results["result"][0]

                thumbnails = data.get("thumbnails", [])
                thumbnail = thumbnails[-1].get("url", "").split("?")[0] if thumbnails else ""

                view_count = data.get("viewCount", {})
                if isinstance(view_count, dict):
                    view_count = view_count.get("short", "")

                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                    message_id=m_id,
                    title=data.get("title", "Unknown")[:50],
                    thumbnail=thumbnail,
                    url=data.get("link", ""),
                    view_count=str(view_count),
                    video=video,
                )
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")

        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> List[Track]:
        """Get tracks from a YouTube playlist"""
        tracks = []

        try:
            if "&" in url:
                url = url.split("&")[0]

            plist = await Playlist.get(url)
            videos = plist.get("videos", [])

            for data in videos[:limit]:
                if not data:
                    continue

                thumbnails = data.get("thumbnails", [])
                thumbnail = thumbnails[-1].get("url", "").split("?")[0] if thumbnails else ""

                video_url = data.get("link", "")
                if "&list=" in video_url:
                    video_url = video_url.split("&list=")[0]

                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                    title=data.get("title", "Unknown")[:50],
                    thumbnail=thumbnail,
                    url=video_url,
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)

        except Exception as e:
            logger.error(f"Playlist error for {url}: {e}")

        return tracks

    async def get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        match = self.regex.search(url)
        if match:
            return match.group(5)
        return None

    async def is_playlist(self, url: str) -> bool:
        """Check if URL is a playlist"""
        match = self.regex.search(url)
        if match and match.group(3) and "playlist" in match.group(3):
            return True
        return False


# Create global instance
youtube = YouTube()
