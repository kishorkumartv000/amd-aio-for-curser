import os
import re
import asyncio
import logging
import shutil
from bot.helpers.utils import (
    run_apple_downloader,
    extract_apple_metadata,
    send_message,
    edit_message,
    format_string,
    cleanup,
    list_apple_output_files,
    cleanup_apple_global
)
from bot.helpers.uploader import track_upload, album_upload, music_video_upload, artist_upload, playlist_upload
from bot.helpers.database.pg_impl import download_history
from bot.helpers.progress import ProgressReporter
from bot.helpers.status import start_status_updater, stop_status_updater
from config import Config
from bot.logger import LOGGER

logger = logging.getLogger(__name__)

class AppleMusicProvider:
    def __init__(self):
        self.name = "apple"

    def validate_url(self, url: str) -> bool:
        """Check if URL is valid Apple Music content"""
        return bool(re.match(
            r"https://music\.apple\.com/.+/(album|song|playlist|music-video)/.+",
            url
        ))

    def extract_content_id(self, url: str) -> str:
        """Extract Apple Music content ID from URL"""
        match = re.search(r'/(album|song|playlist|music-video|artist)/[^/]+/(\d+)', url)
        return match.group(2) if match else "unknown"

    async def process(self, url: str, user: dict, options: dict = None) -> dict:
        """Process Apple Music URL with options"""
        user_dir = os.path.join(Config.LOCAL_STORAGE, str(user['user_id']), "Apple Music")
        await asyncio.to_thread(os.makedirs, user_dir, exist_ok=True)
        LOGGER.info(f"Created temporary working directory for Apple Music task: {user_dir}")
        
        cmd_options = self.build_options(options)
        reporter = user.get('progress')
        
        result = await run_apple_downloader(
            url, user_dir, cmd_options, user, reporter, user.get('task_id'), user.get('cancel_event')
        )
        if not result.get('success'):
            return result
        
        files = await asyncio.to_thread(list_apple_output_files)
        if not files:
            return {'success': False, 'error': "No files downloaded"}
        
        LOGGER.info(f"Found {len(files)} files in global Apple output folders")
        
        items = []
        for file_path in files:
            try:
                metadata = await extract_apple_metadata(file_path)
                metadata['filepath'] = file_path
                metadata['provider'] = self.name
                items.append(metadata)
            except Exception as e:
                LOGGER.error(f"Metadata extraction failed for {file_path}: {e}")
        
        if not items:
            return {'success': False, 'error': "Metadata extraction failed"}
        
        if reporter:
            reporter.set_total_tracks(len(items))
            reporter.update_download(tracks_done=len(items))
        
        has_video = any(f.endswith(('.mp4', '.m4v', '.mov')) for f in files)
        folder_path = await asyncio.to_thread(os.path.dirname, os.path.commonpath([i['filepath'] for i in items]))
        
        content_type = 'album'
        if len(items) == 1:
            content_type = 'video' if has_video else 'track'
        elif has_video:
            content_type = 'playlist'
            LOGGER.error(f"Mixed video/audio content detected. Treating as playlist: {folder_path}")

        album_title = items[0].get('album', items[0]['title'])
        download_history.record_download(
            user_id=user['user_id'], provider=self.name, content_type=content_type,
            content_id=self.extract_content_id(url), title=album_title, artist=items[0]['artist'],
            quality=str(options.get('quality', 'Standard'))
        )
        
        return {
            'success': True, 'type': content_type, 'items': items, 'folderpath': folder_path,
            'title': album_title, 'artist': items[0]['artist'], 'poster_msg': user['bot_msg']
        }
    
    def build_options(self, options: dict) -> list:
        """Convert options dictionary to command-line flags"""
        if not options: return []
        cmd_options = []
        # Simplified for brevity, assuming a map exists
        option_map = { 'aac': '--aac', 'alac-max': '--alac-max', 'atmos': '--atmos', 'song': '--song' }
        for key, value in options.items():
            if key in option_map:
                cmd_options.append(option_map[key])
                if value is not True: cmd_options.append(str(value))
        return cmd_options

async def start_apple(link: str, user: dict, options: dict = None):
    """Handle Apple Music download request with options"""
    task_id = user.get('task_id', 'unknown')
    # This is the correct way to instantiate the reporter now.
    reporter = ProgressReporter(label=f"Apple Music • {task_id[:5]}")
    user['progress'] = reporter
    # Start the periodic status updater
    await start_status_updater(task_id, reporter, user['bot_msg'])

    try:
        provider = AppleMusicProvider()
        if not provider.validate_url(link):
            await edit_message(user['bot_msg'], "❌ Invalid Apple Music URL")
            return
        
        reporter.set_stage("Preparing")
        result = await provider.process(link, user, options)

        if not result.get('success'):
            await edit_message(user['bot_msg'], f"❌ Error: {result.get('error', 'Unknown error')}")
            return
        
        upload_map = {
            'track': (track_upload, result['items'][0]),
            'video': (music_video_upload, result['items'][0]),
            'album': (album_upload, result),
            'playlist': (playlist_upload, result)
        }

        if result['type'] in upload_map:
            upload_func, upload_data = upload_map[result['type']]
            if result['type'] == 'video':
                reporter.label = f"🎬 Apple Music • {task_id[:5]}"
            await upload_func(upload_data, user)
        else:
            await edit_message(user['bot_msg'], f"❌ Unsupported content type: {result['type']}")
            return
        
        reporter.set_stage("Done")
        
    except asyncio.CancelledError:
        if user.get('progress'):
            user['progress'].set_stage("Cancelled")
        await asyncio.sleep(1)
        raise

    except Exception as e:
        logger.error(f"Apple Music error: {str(e)}", exc_info=True)
        if user.get('progress'):
            user['progress'].set_stage("Error")
        await edit_message(user['bot_msg'], f"❌ Error: {str(e)}")

    finally:
        # Crucially, stop the status updater to prevent it from running forever
        await stop_status_updater(task_id)
        # Final cleanup
        await cleanup(user)
        await asyncio.to_thread(cleanup_apple_global)
