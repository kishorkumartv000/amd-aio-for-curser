"""
Tidal provider for Project-Siesta.
This file handles downloading from Tidal using the streamrip library.
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

# We will use streamrip ('rip') as a command-line tool.

logger = logging.getLogger(__name__)

class TidalProvider:
    def __init__(self):
        self.name = "tidal"
        self.token = Config.TIDAL_TV_TOKEN # Assuming TV token is the primary one for ripping

    def validate_url(self, url: str) -> bool:
        """Check if URL is a valid Tidal URL."""
        return bool(re.match(r"https?://(www\.)?tidal\.com/.+/(track|album|playlist|artist)/.+", url))

    async def process(self, url: str, user: dict, options: dict = None) -> dict:
        """Process a Tidal URL."""
        if not self.token:
            return {'success': False, 'error': "Tidal Token is not configured."}

        user_dir = os.path.join(Config.LOCAL_STORAGE, str(user['user_id']), "Tidal")
        os.makedirs(user_dir, exist_ok=True)
        LOGGER.info(f"Created Tidal directory: {user_dir}")

        from bot.helpers.progress import ProgressReporter
        label = f"Tidal • ID: {user.get('task_id','?')}"
        reporter = ProgressReporter(user['bot_msg'], label=label)
        user['progress'] = reporter
        await reporter.set_stage("Preparing")

        config_path = os.path.join(user_dir, "rip.toml")
        rip_config = f'[tidal]\naccess_token = "{self.token}"\n'
        with open(config_path, "w") as f:
            f.write(rip_config)

        cmd = [
            "rip", "url", url,
            "--folder", user_dir,
            "--config-path", config_path
        ]

        LOGGER.info(f"Running Streamrip for Tidal: {' '.join(cmd)}")
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

        os.remove(config_path)

        if process.returncode != 0:
            error = stderr.decode().strip() or stdout.decode().strip()
            LOGGER.error(f"Streamrip (Tidal) failed: {error}")
            return {'success': False, 'error': error}

        from bot.helpers.utils import extract_audio_metadata

        items = []
        downloaded_files = []
        for root, _, files in os.walk(user_dir):
            for file in files:
                if file.lower().endswith(('.flac', '.mp3', '.m4a')):
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
            'title': items[0].get('album') or items[0].get('title', 'Tidal Download'),
            'artist': items[0].get('artist', 'Various Artists'),
            'poster_msg': user['bot_msg']
        }


async def start_tidal(link: str, user: dict, options: dict = None):
    """Handle Tidal download request."""
    if not Config.ENABLE_TIDAL or Config.ENABLE_TIDAL.lower() != 'true':
        await edit_message(user['bot_msg'], "Tidal support is not enabled in the configuration.")
        return

    try:
        provider = TidalProvider()
        if not provider.validate_url(link):
            await edit_message(user['bot_msg'], "❌ Invalid Tidal URL")
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

        await edit_message(user['bot_msg'], "✅ Tidal download and upload complete!")

    except asyncio.CancelledError:
        await edit_message(user['bot_msg'], "⏹️ Task cancelled.")
        raise
    except Exception as e:
        logger.error(f"Tidal error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ An unexpected error occurred: {str(e)}")
    finally:
        await cleanup(user)
