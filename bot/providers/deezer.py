"""
Deezer provider for Project-Siesta.
This file handles downloading from Deezer using the orpheus-dl library.
"""
import os
import re
import asyncio
import logging
from config import Config
from bot.helpers.utils import (
    send_message,
    edit_message,
    cleanup,
)
from bot.helpers.uploader import track_upload, album_upload, playlist_upload
from bot.helpers.database.pg_impl import download_history
from bot.logger import LOGGER

# Orpheus-dl is expected to be used as a command-line tool here,
# similar to the Apple Music downloader, for maximum stability.
# We will construct and run a command.

logger = logging.getLogger(__name__)

class DeezerProvider:
    def __init__(self):
        self.name = "deezer"
        self.arl = Config.DEEZER_ARL

    def validate_url(self, url: str) -> bool:
        """Check if URL is a valid Deezer URL."""
        return bool(re.match(r"https?://(www\.)?deezer\.com/.+/(track|album|playlist|artist)/.+", url))

    async def process(self, url: str, user: dict, options: dict = None) -> dict:
        """Process a Deezer URL."""
        if not self.arl:
            return {'success': False, 'error': "Deezer ARL is not configured in .env file."}

        user_dir = os.path.join(Config.LOCAL_STORAGE, str(user['user_id']), "Deezer")
        os.makedirs(user_dir, exist_ok=True)
        LOGGER.info(f"Created Deezer directory: {user_dir}")

        from bot.helpers.progress import ProgressReporter
        label = f"Deezer • ID: {user.get('task_id','?')}"
        reporter = ProgressReporter(user['bot_msg'], label=label)
        user['progress'] = reporter
        await reporter.set_stage("Preparing")

        cmd = [
            "python3", "/opt/orpheusdl/orpheus.py",
            "-a", self.arl,
            "-o", user_dir,
            "-q", "6", # Corresponds to FLAC in orpheus
            url
        ]

        LOGGER.info(f"Running Orpheus-DL: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            if user.get('task_id'):
                from bot.helpers.tasks import task_manager
                await task_manager.register_subprocess(user['task_id'], process)
        except Exception:
            pass

        await reporter.set_stage("Downloading")
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error = stderr.decode().strip() or stdout.decode().strip()
            LOGGER.error(f"Orpheus-DL failed: {error}")
            return {'success': False, 'error': error}

        from bot.helpers.utils import extract_audio_metadata

        items = []
        downloaded_files = []
        for root, _, files in os.walk(user_dir):
            for file in files:
                if file.lower().endswith(('.flac', '.mp3')): # Orpheus usually downloads as FLAC or MP3
                    downloaded_files.append(os.path.join(root, file))

        if not downloaded_files:
            return {'success': False, 'error': "No media files found after download."}

        for file_path in downloaded_files:
            try:
                metadata = await extract_audio_metadata(file_path)
                metadata['filepath'] = file_path
                metadata['provider'] = self.name
                items.append(metadata)
            except Exception as e:
                LOGGER.error(f"Metadata extraction failed for {file_path}: {str(e)}")

        if not items:
            return {'success': False, 'error': "Failed to extract metadata from any downloaded files."}

        content_type = 'track'
        if len(items) > 1:
            album_name = items[0].get('album')
            if album_name and all(item.get('album') == album_name for item in items):
                content_type = 'album'
            else:
                content_type = 'playlist'

        return {
            'success': True,
            'type': content_type,
            'items': items,
            'folderpath': user_dir,
            'title': items[0].get('album') or items[0].get('title', 'Deezer Download'),
            'artist': items[0].get('artist', 'Various Artists'),
            'poster_msg': user['bot_msg']
        }


async def start_deezer(link: str, user: dict, options: dict = None):
    """Handle Deezer download request."""
    try:
        provider = DeezerProvider()
        if not provider.validate_url(link):
            await edit_message(user['bot_msg'], "❌ Invalid Deezer URL")
            return

        result = await provider.process(link, user, options)
        if not result['success']:
            await edit_message(user['bot_msg'], f"❌ Error: {result['error']}")
            return

        if result['type'] == 'track':
            await track_upload(result['items'][0], user)
        elif result['type'] == 'album':
            await album_upload(result, user)
        elif result['type'] == 'playlist':
            await playlist_upload(result, user)

        await edit_message(user['bot_msg'], "✅ Deezer download and upload complete!")

    except asyncio.CancelledError:
        await edit_message(user['bot_msg'], "⏹️ Task cancelled.")
        raise
    except Exception as e:
        logger.error(f"Deezer error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ An unexpected error occurred: {str(e)}")
    finally:
        await cleanup(user)
