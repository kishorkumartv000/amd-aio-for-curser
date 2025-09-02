"""
Qobuz provider for Project-Siesta.
This file handles downloading from Qobuz using the streamrip library.
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

class QobuzProvider:
    def __init__(self):
        self.name = "qobuz"
        self.email = Config.QOBUZ_EMAIL
        self.password = Config.QOBUZ_PASSWORD
        self.token = Config.QOBUZ_TOKEN

    def validate_url(self, url: str) -> bool:
        """Check if URL is a valid Qobuz URL."""
        return bool(re.match(r"https?://(www\.)?qobuz\.com/.+/(album|track|playlist|artist)/.+", url))

    async def process(self, url: str, user: dict, options: dict = None) -> dict:
        """Process a Qobuz URL."""
        if not (self.token or (self.email and self.password)):
            return {'success': False, 'error': "Qobuz credentials (token or email/password) are not configured."}

        user_dir = os.path.join(Config.LOCAL_STORAGE, str(user['user_id']), "Qobuz")
        os.makedirs(user_dir, exist_ok=True)
        LOGGER.info(f"Created Qobuz directory: {user_dir}")

        config_path = os.path.join(user_dir, "rip.toml")
        rip_config = "[qobuz]\n"
        if self.token:
            rip_config += f'token = "{self.token}"\n'
        else:
            rip_config += f'email = "{self.email}"\n'
            rip_config += f'password = "{self.password}"\n'

        with open(config_path, "w") as f:
            f.write(rip_config)

        from bot.helpers.progress import ProgressReporter
        label = f"Qobuz • ID: {user.get('task_id','?')}"
        reporter = ProgressReporter(user['bot_msg'], label=label)
        user['progress'] = reporter
        await reporter.set_stage("Preparing")

        cmd = [
            "rip", "url", url,
            "--folder", user_dir,
            "--config-path", config_path,
            "--codec", "flac"
        ]

        LOGGER.info(f"Running Streamrip for Qobuz: {' '.join(cmd)}")
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
            LOGGER.error(f"Streamrip (Qobuz) failed: {error}")
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
            # Check if all items belong to the same album
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
            'title': items[0].get('album') or items[0].get('title', 'Qobuz Download'),
            'artist': items[0].get('artist', 'Various Artists'),
            'poster_msg': user['bot_msg']
        }


async def start_qobuz(link: str, user: dict, options: dict = None):
    """Handle Qobuz download request."""
    try:
        provider = QobuzProvider()
        if not provider.validate_url(link):
            await edit_message(user['bot_msg'], "❌ Invalid Qobuz URL")
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

        await edit_message(user['bot_msg'], "✅ Qobuz download and upload complete!")

    except asyncio.CancelledError:
        await edit_message(user['bot_msg'], "⏹️ Task cancelled.")
        raise
    except Exception as e:
        logger.error(f"Qobuz error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ An unexpected error occurred: {str(e)}")
    finally:
        await cleanup(user)
