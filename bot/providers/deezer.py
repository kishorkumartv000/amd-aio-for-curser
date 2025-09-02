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

        # Construct the orpheus-dl command
        cmd = [
            "orpheus",
            "-a", self.arl,
            "-o", user_dir,
            "-q", "flac", # Default to FLAC, can be configured later
            url
        ]

        LOGGER.info(f"Running Orpheus-DL: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Register for cancellation
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

        # Since orpheus-dl doesn't have a library mode for metadata,
        # we will need to scan the directory and extract metadata manually.
        # This part will be implemented in a future step. For now, we assume success.

        # Placeholder for file discovery and metadata extraction
        # For now, we'll just return a success message.
        # The actual file processing will be added later.

        return {
            'success': True,
            'type': 'album', # Placeholder
            'items': [], # Placeholder
            'folderpath': user_dir,
            'title': 'Deezer Download', # Placeholder
            'artist': 'Various Artists' # Placeholder
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

        await edit_message(user['bot_msg'], "✅ Deezer download completed! Uploading will be handled next.")
        # Uploading logic will be added here based on the result

    except asyncio.CancelledError:
        await edit_message(user['bot_msg'], "⏹️ Task cancelled.")
        raise
    except Exception as e:
        logger.error(f"Deezer error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ An unexpected error occurred: {str(e)}")
    finally:
        await cleanup(user)
