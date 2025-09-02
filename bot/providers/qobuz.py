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

        from bot.helpers.progress import ProgressReporter
        label = f"Qobuz • ID: {user.get('task_id','?')}"
        reporter = ProgressReporter(user['bot_msg'], label=label)
        user['progress'] = reporter
        await reporter.set_stage("Preparing")

        # Construct the streamrip command
        cmd = [
            "rip",
            "url",
            url,
            "--output-directory", user_dir,
            "--codec", "flac" # Default to FLAC
        ]

        # Add credentials
        if self.token:
            cmd.extend(["--token", self.token])
        else:
            cmd.extend(["--email", self.email, "--password", self.password])

        LOGGER.info(f"Running Streamrip for Qobuz: {' '.join(cmd)}")

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
            LOGGER.error(f"Streamrip (Qobuz) failed: {error}")
            return {'success': False, 'error': error}

        # Placeholder for file discovery and metadata extraction
        return {
            'success': True,
            'type': 'album', # Placeholder
            'items': [], # Placeholder
            'folderpath': user_dir,
            'title': 'Qobuz Download', # Placeholder
            'artist': 'Various Artists' # Placeholder
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

        await edit_message(user['bot_msg'], "✅ Qobuz download completed! Uploading will be handled next.")

    except asyncio.CancelledError:
        await edit_message(user['bot_msg'], "⏹️ Task cancelled.")
        raise
    except Exception as e:
        logger.error(f"Qobuz error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ An unexpected error occurred: {str(e)}")
    finally:
        await cleanup(user)
