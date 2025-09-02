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

        # Construct the streamrip command
        # Note: streamrip uses a config file for tidal, but we can try with tokens.
        # This might need adjustment based on streamrip's exact CLI for Tidal.
        # For now, we assume a config file is the most reliable way.
        # Let's create a temporary config for streamrip.

        rip_config = f"""
[tidal]
access_token = "{self.token}"
        """
        config_path = os.path.join(user_dir, "rip.toml")
        with open(config_path, "w") as f:
            f.write(rip_config)

        cmd = [
            "rip",
            "url",
            url,
            "--output-directory", user_dir,
            "--config-path", config_path
        ]

        LOGGER.info(f"Running Streamrip for Tidal: {' '.join(cmd)}")

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
            LOGGER.error(f"Streamrip (Tidal) failed: {error}")
            return {'success': False, 'error': error}

        # Placeholder for file discovery and metadata extraction
        return {
            'success': True,
            'type': 'album', # Placeholder
            'items': [], # Placeholder
            'folderpath': user_dir,
            'title': 'Tidal Download', # Placeholder
            'artist': 'Various Artists' # Placeholder
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

        await edit_message(user['bot_msg'], "✅ Tidal download completed! Uploading will be handled next.")

    except asyncio.CancelledError:
        await edit_message(user['bot_msg'], "⏹️ Task cancelled.")
        raise
    except Exception as e:
        logger.error(f"Tidal error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ An unexpected error occurred: {str(e)}")
    finally:
        await cleanup(user)
