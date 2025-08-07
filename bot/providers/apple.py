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
    format_string
)
from bot.helpers.uploader import track_upload, album_upload
from bot.helpers.database.pg_impl import download_history
from config import Config
from bot.logger import LOGGER

logger = logging.getLogger(__name__)

class AppleMusicProvider:
    def __init__(self):
        self.name = "apple"
    
    def validate_url(self, url: str) -> bool:
        return bool(re.match(r"https://music\.apple\.com/.+/(album|song|playlist)/.+", url))
    
    def extract_content_id(self, url: str) -> str:
        """Extract Apple Music content ID from URL"""
        match = re.search(r'/(album|song|playlist|artist)/[^/]+/(\d+)', url)
        return match.group(2) if match else "unknown"
    
    async def process(self, url: str, user: dict, options: dict = None) -> dict:
        """Process Apple Music URL with options"""
        # Create user-specific directory in bot's structure
        user_dir = os.path.join(Config.LOCAL_STORAGE, "Apple Music", str(user['user_id']))
        os.makedirs(user_dir, exist_ok=True)
        
        # Process options
        cmd_options = self.build_options(options)
        
        # Add Apple-specific path options
        alac_dir = os.path.join(user_dir, 'alac')
        atmos_dir = os.path.join(user_dir, 'atmos')
        os.makedirs(alac_dir, exist_ok=True)
        os.makedirs(atmos_dir, exist_ok=True)
        
        cmd_options.extend(["--alac-save-folder", alac_dir])
        cmd_options.extend(["--atmos-save-folder", atmos_dir])
        
        # Update user message
        await edit_message(user['bot_msg'], "⏳ Starting Apple Music download...")
        
        # Download content
        result = await run_apple_downloader(url, user_dir, cmd_options, user)
        if not result['success']:
            return result
        
        # Find downloaded files
        files = []
        for root, _, filenames in os.walk(user_dir):
            for file in filenames:
                if file.endswith(('.m4a', '.flac', '.alac')):
                    files.append(os.path.join(root, file))
        
        if not files:
            return {'success': False, 'error': "No files downloaded"}
        
        # Extract metadata
        tracks = []
        for file_path in files:
            metadata = await extract_apple_metadata(file_path)
            metadata['filepath'] = file_path
            metadata['provider'] = self.name
            tracks.append(metadata)
        
        # Determine content type
        if len(tracks) == 1:
            content_type = 'track'
            folder_path = os.path.dirname(tracks[0]['filepath'])
        else:
            content_type = 'album'
            # Find common parent directory
            folder_path = os.path.commonpath([os.path.dirname(t['filepath']) for t in tracks])
        
        # Record download in history
        content_id = self.extract_content_id(url)
        quality = options.get('alac-max', Config.APPLE_ALAC_QUALITY) if 'alac' in options else \
                  options.get('atmos-max', Config.APPLE_ATMOS_QUALITY)
        
        download_history.record_download(
            user_id=user['user_id'],
            provider=self.name,
            content_type=content_type,
            content_id=content_id,
            title=tracks[0]['title'] if content_type == 'track' else tracks[0]['album'],
            artist=tracks[0]['artist'],
            quality=quality
        )
        
        return {
            'success': True,
            'type': content_type,
            'tracks': tracks,
            'folderpath': folder_path,
            'title': tracks[0]['title'] if content_type == 'track' else tracks[0]['album'],
            'artist': tracks[0]['artist'],
            'album': tracks[0]['album'] if content_type == 'album' else None
        }
    
    def build_options(self, options: dict) -> list:
        """Convert options dictionary to command-line flags"""
        if not options:
            return []
        
        cmd_options = []
        option_map = {
            'aac': '--aac',
            'aac-type': '--aac-type',
            'alac-max': '--alac-max',
            'all-album': '--all-album',
            'atmos': '--atmos',
            'atmos-max': '--atmos-max',
            'debug': '--debug',
            'mv-audio-type': '--mv-audio-type',
            'mv-max': '--mv-max',
            'select': '--select',
            'song': '--song'
        }
        
        for key, value in options.items():
            if key in option_map:
                if value is True:  # Flag option
                    cmd_options.append(option_map[key])
                else:  # Value option
                    cmd_options.extend([option_map[key], str(value)])
        
        return cmd_options

async def start_apple(link: str, user: dict, options: dict = None):
    """Handle Apple Music download request with options"""
    try:
        provider = AppleMusicProvider()
        if not provider.validate_url(link):
            await edit_message(user['bot_msg'], "❌ Invalid Apple Music URL")
            return
        
        # Process content with options
        result = await provider.process(link, user, options)
        if not result['success']:
            await edit_message(user['bot_msg'], f"❌ Error: {result['error']}")
            return
        
        # Set poster message for albums
        if result['type'] != 'track':
            result['poster_msg'] = user['bot_msg']
        
        # Process and upload content
        if result['type'] == 'track':
            await track_upload(result['tracks'][0], user)
        else:
            await album_upload(result, user)
        
        await edit_message(user['bot_msg'], "✅ Apple Music download completed!")
        
    except Exception as e:
        logger.error(f"Apple Music error: {str(e)}", exc_info=True)
        await edit_message(user['bot_msg'], f"❌ Error: {str(e)}")
    finally:
        # Cleanup temporary files
        try:
            if 'folderpath' in result:
                shutil.rmtree(result['folderpath'], ignore_errors=True)
        except:
            pass
