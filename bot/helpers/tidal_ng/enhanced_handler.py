"""
Enhanced Tidal NG Handler - Version 2
Advanced features for Tidal NG integration with better error handling,
progress reporting, and user experience improvements.
"""
import os
import json
import asyncio
import shutil
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from config import Config
from ..message import edit_message, send_message
from bot.logger import LOGGER
from ..database.pg_impl import download_history
from bot.helpers.utils import (
    extract_audio_metadata,
    extract_video_metadata,
)
from bot.helpers.uploader import track_upload, album_upload, playlist_upload, music_video_upload
from bot.helpers.tidal_ng.utils import get_tidal_ng_download_base_path
from ..progress import ProgressReporter

# Define the path to the tidal-dl-ng CLI script
TIDAL_DL_NG_CLI_PATH = "/usr/src/app/tidal-dl-ng/tidal_dl_ng/cli.py"
# Define the path to the settings.json for the CLI tool
TIDAL_DL_NG_SETTINGS_PATH = "/root/.config/tidal_dl_ng/settings.json"

class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TidalNGDownloadResult:
    """Result of a Tidal NG download operation"""
    success: bool
    files: List[str]
    content_type: str
    metadata: List[Dict]
    error: Optional[str] = None
    download_path: Optional[str] = None
    status: DownloadStatus = DownloadStatus.PENDING
    quality: str = "LOSSLESS"
    duration: float = 0.0

class TidalNGDownloader:
    """Enhanced Tidal NG downloader with advanced features"""
    
    def __init__(self):
        self.original_settings = None
        self.temp_download_path = None
        self.start_time = None
        self.cancel_event = None
        
    async def __aenter__(self):
        """Context manager entry"""
        await self._backup_settings()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - restore settings"""
        await self._restore_settings()
        
    async def _backup_settings(self):
        """Backup original settings.json"""
        try:
            with open(TIDAL_DL_NG_SETTINGS_PATH, "r") as f:
                self.original_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.original_settings = {}
            LOGGER.warn("No existing Tidal NG settings found, using defaults")
            
    async def _restore_settings(self):
        """Restore original settings.json"""
        if self.original_settings is not None:
            try:
                with open(TIDAL_DL_NG_SETTINGS_PATH, "w") as f:
                    json.dump(self.original_settings, f, indent=4)
                LOGGER.info("Tidal NG settings restored successfully")
            except Exception as e:
                LOGGER.error(f"Failed to restore Tidal NG settings: {e}")
                
    def _create_temp_download_path(self, user_id: int) -> Path:
        """Create a temporary download path for this user"""
        timestamp = int(time.time())
        temp_path = Path(Config.DOWNLOAD_BASE_DIR) / str(user_id) / f"tidal_ng_{timestamp}"
        temp_path.mkdir(parents=True, exist_ok=True)
        self.temp_download_path = temp_path
        return temp_path
        
    async def _apply_download_settings(self, user_id: int, options: Dict = None) -> Path:
        """Apply temporary settings for download with smart defaults"""
        download_path = self._create_temp_download_path(user_id)
        
        # Create new settings with smart defaults
        new_settings = self.original_settings.copy() if self.original_settings else {}
        new_settings.update({
            "download_base_path": str(download_path),
            "path_binary_ffmpeg": "/usr/bin/ffmpeg",
            "downloads_concurrent_max": 3,  # Limit concurrent downloads
            "downloads_simultaneous_per_track_max": 1,
            "skip_existing": True,
            "lyrics_embed": True,
            "metadata_cover_embed": True,
            "extract_flac": True,
            "playlist_create": True,
            "video_download": True,
            "video_convert_mp4": True,
        })
        
        # Apply user options if provided
        if options:
            new_settings.update(self._parse_options(options))
            
        # Write new settings
        with open(TIDAL_DL_NG_SETTINGS_PATH, "w") as f:
            json.dump(new_settings, f, indent=4)
            
        LOGGER.info(f"Applied Tidal NG settings: {new_settings}")
        return download_path
        
    def _parse_options(self, options: Dict) -> Dict:
        """Parse user options into Tidal NG settings with validation"""
        option_mapping = {
            'quality': 'quality_audio',
            'video_quality': 'quality_video',
            'lyrics': 'lyrics_embed',
            'cover': 'metadata_cover_embed',
            'playlist': 'playlist_create',
            'concurrent': 'downloads_concurrent_max',
            'flac': 'extract_flac',
            'video': 'video_download',
            'convert': 'video_convert_mp4',
            'skip': 'skip_existing',
        }
        
        parsed = {}
        for key, value in options.items():
            if key in option_mapping:
                setting_key = option_mapping[key]
                if key in ['lyrics', 'cover', 'playlist', 'flac', 'video', 'convert', 'skip']:
                    parsed[setting_key] = bool(value)
                elif key in ['concurrent']:
                    parsed[setting_key] = max(1, min(10, int(value)))  # Limit between 1-10
                else:
                    parsed[setting_key] = value
                    
        return parsed
        
    async def _execute_download(self, url: str, progress_reporter: ProgressReporter) -> bool:
        """Execute the actual download command with enhanced monitoring"""
        cmd = ["python", TIDAL_DL_NG_CLI_PATH, "dl", url]
        
        LOGGER.info(f"Executing Tidal NG command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Start progress monitoring tasks
        tasks = [
            self._monitor_stdout(process.stdout, progress_reporter),
            self._monitor_stderr(process.stderr, progress_reporter),
            self._monitor_process(process, progress_reporter),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            LOGGER.error(f"Error monitoring download process: {e}")
            
        await process.wait()
        return process.returncode == 0
        
    async def _monitor_stdout(self, stream, progress_reporter: ProgressReporter):
        """Monitor stdout for progress updates with enhanced parsing"""
        while True:
            line = await stream.readline()
            if not line:
                break
                
            output = line.decode("utf-8").strip()
            if output:
                LOGGER.info(f"[TidalNG-STDOUT] {output}")
                await self._parse_progress(output, progress_reporter)
                
    async def _monitor_stderr(self, stream, progress_reporter: ProgressReporter):
        """Monitor stderr for error messages and warnings"""
        while True:
            line = await stream.readline()
            if not line:
                break
                
            output = line.decode("utf-8").strip()
            if output:
                LOGGER.warn(f"[TidalNG-STDERR] {output}")
                await progress_reporter.set_stage(f"Warning: {output[:50]}...")
                
    async def _monitor_process(self, process, progress_reporter: ProgressReporter):
        """Monitor process status and handle cancellation"""
        while process.returncode is None:
            if self.cancel_event and self.cancel_event.is_set():
                LOGGER.info("Download cancelled by user")
                process.terminate()
                await progress_reporter.set_stage("Download cancelled")
                break
            await asyncio.sleep(1)
                
    async def _parse_progress(self, output: str, progress_reporter: ProgressReporter):
        """Parse progress from Tidal NG output with enhanced pattern matching"""
        # Look for common progress patterns
        if "Downloading" in output or "Download" in output:
            await progress_reporter.set_stage("Downloading...")
        elif "Processing" in output or "Process" in output:
            await progress_reporter.set_stage("Processing...")
        elif "Converting" in output or "Convert" in output:
            await progress_reporter.set_stage("Converting...")
        elif "Extracting" in output or "Extract" in output:
            await progress_reporter.set_stage("Extracting...")
        elif "Complete" in output or "Finished" in output or "Success" in output:
            await progress_reporter.set_stage("Download complete!")
        elif "Error" in output or "Failed" in output:
            await progress_reporter.set_stage(f"Error: {output[:50]}...")
            
        # Try to extract percentage if available
        import re
        percent_match = re.search(r'(\d+)%', output)
        if percent_match:
            try:
                percent = int(percent_match.group(1))
                await progress_reporter.update_download(percent=percent)
            except Exception:
                pass
                
        # Try to extract file information
        file_match = re.search(r'(\d+)/(\d+)', output)
        if file_match:
            try:
                current = int(file_match.group(1))
                total = int(file_match.group(2))
                await progress_reporter.update_download(tracks_done=current, total_tracks=total)
            except Exception:
                pass
                
    def _collect_downloaded_files(self, download_path: Path) -> List[str]:
        """Collect all downloaded files with filtering"""
        files = []
        for root, _, filenames in os.walk(download_path):
            for filename in filenames:
                # Skip hidden files and temporary files
                if filename.startswith('.') or filename.endswith('.tmp'):
                    continue
                file_path = os.path.join(root, filename)
                files.append(file_path)
        return files
        
    async def _extract_metadata(self, files: List[str]) -> List[Dict]:
        """Extract metadata from downloaded files with error handling"""
        items = []
        for file_path in files:
            try:
                if file_path.lower().endswith((".mp4", ".m4v")):
                    metadata = await extract_video_metadata(file_path)
                else:
                    metadata = await extract_audio_metadata(file_path)
                    
                metadata["filepath"] = file_path
                metadata["provider"] = "Tidal NG"
                items.append(metadata)
                
            except Exception as e:
                LOGGER.error(f"Metadata extraction failed for {file_path}: {str(e)}")
                
        return items
        
    def _determine_content_type(self, items: List[Dict], files: List[str]) -> str:
        """Determine the type of content downloaded with enhanced logic"""
        if not items:
            return "unknown"
            
        # Check for video files
        has_video = any(f.lower().endswith((".mp4", ".m4v")) for f in files)
        if has_video and len(items) == 1:
            return "video"
            
        # Check for album (multiple tracks with same album)
        if len(items) > 1:
            albums = set(item.get("album", "") for item in items)
            if len(albums) == 1 and albums.pop():
                return "album"
            else:
                return "playlist"
                
        return "track"
        
    def _calculate_duration(self) -> float:
        """Calculate download duration"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
        
    async def download(self, url: str, user: Dict, options: Dict = None) -> TidalNGDownloadResult:
        """Main download method with enhanced features"""
        self.start_time = time.time()
        self.cancel_event = user.get('cancel_event')
        
        try:
            # Setup progress reporter
            progress_reporter = ProgressReporter(
                user.get('bot_msg'), 
                label=f"Tidal NG • ID: {user.get('task_id', '?')}"
            )
            user['progress'] = progress_reporter
            
            # Apply settings and get download path
            download_path = await self._apply_download_settings(user['user_id'], options)
            await progress_reporter.set_stage("Starting download...")
            
            # Execute download
            success = await self._execute_download(url, progress_reporter)
            if not success:
                return TidalNGDownloadResult(
                    success=False,
                    files=[],
                    content_type="unknown",
                    metadata=[],
                    error="Download process failed",
                    status=DownloadStatus.FAILED,
                    duration=self._calculate_duration()
                )
                
            # Collect files
            await progress_reporter.set_stage("Processing files...")
            files = self._collect_downloaded_files(download_path)
            if not files:
                return TidalNGDownloadResult(
                    success=False,
                    files=[],
                    content_type="unknown",
                    metadata=[],
                    error="No files were downloaded",
                    status=DownloadStatus.FAILED,
                    duration=self._calculate_duration()
                )
                
            # Extract metadata
            metadata = await self._extract_metadata(files)
            if not metadata:
                return TidalNGDownloadResult(
                    success=False,
                    files=files,
                    content_type="unknown",
                    metadata=[],
                    error="Metadata extraction failed",
                    status=DownloadStatus.FAILED,
                    duration=self._calculate_duration()
                )
                
            # Determine content type
            content_type = self._determine_content_type(metadata, files)
            
            # Get quality from settings
            quality = "LOSSLESS"
            if self.original_settings:
                quality = self.original_settings.get("quality_audio", "LOSSLESS")
            
            await progress_reporter.set_stage("Download complete!")
            
            return TidalNGDownloadResult(
                success=True,
                files=files,
                content_type=content_type,
                metadata=metadata,
                download_path=str(download_path),
                status=DownloadStatus.COMPLETED,
                quality=quality,
                duration=self._calculate_duration()
            )
            
        except asyncio.CancelledError:
            return TidalNGDownloadResult(
                success=False,
                files=[],
                content_type="unknown",
                metadata=[],
                error="Download cancelled",
                status=DownloadStatus.CANCELLED,
                duration=self._calculate_duration()
            )
        except Exception as e:
            LOGGER.error(f"Tidal NG download error: {e}", exc_info=True)
            return TidalNGDownloadResult(
                success=False,
                files=[],
                content_type="unknown",
                metadata=[],
                error=str(e),
                status=DownloadStatus.FAILED,
                duration=self._calculate_duration()
            )

def get_content_id_from_url(url: str) -> str:
    """Extract content ID from Tidal URL with enhanced pattern matching"""
    patterns = [
        r"/(track|album|playlist|video)/(\d+)",
        r"/(artist)/(\d+)",
        r"tidal\.com/([^/]+)/([^/]+)/(\d+)",
        r"listen\.tidal\.com/([^/]+)/(\d+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            groups = match.groups()
            if groups:
                return groups[-1]  # Get the last group (ID)
            
    return "unknown"

async def start_tidal_ng_enhanced(link: str, user: dict, options: dict = None):
    """
    Enhanced Tidal NG download handler with advanced features
    """
    bot_msg = user.get("bot_msg")
    
    try:
        # Validate URL
        if not link or not any(domain in link for domain in ["tidal.com", "listen.tidal.com"]):
            await edit_message(bot_msg, "❌ Invalid Tidal URL")
            return
            
        # Use enhanced downloader
        async with TidalNGDownloader() as downloader:
            result = await downloader.download(link, user, options)
            
            if not result.success:
                error_msg = f"❌ Download failed: {result.error}"
                if result.status == DownloadStatus.CANCELLED:
                    error_msg = "⏹️ Download cancelled"
                await edit_message(bot_msg, error_msg)
                return
                
            # Record download history
            content_id = get_content_id_from_url(link)
            download_history.record_download(
                user_id=user.get("user_id"),
                provider="Tidal NG",
                content_type=result.content_type,
                content_id=content_id,
                title=result.metadata[0].get("album") if result.content_type == "album" else result.metadata[0].get("title"),
                artist=result.metadata[0].get("artist"),
                quality=result.quality,
            )
            
            # Prepare upload metadata
            upload_meta = {
                "success": True,
                "type": result.content_type,
                "items": result.metadata,
                "folderpath": result.download_path,
                "provider": "Tidal NG",
                "title": result.metadata[0].get("album") if result.content_type == "album" else result.metadata[0].get("title"),
                "artist": result.metadata[0].get("artist"),
                "poster_msg": bot_msg,
            }
            
            # Upload based on content type
            if result.content_type == "track":
                await track_upload(result.metadata[0], user)
            elif result.content_type == "video":
                await music_video_upload(result.metadata[0], user)
            elif result.content_type == "album":
                await album_upload(upload_meta, user)
            elif result.content_type == "playlist":
                await playlist_upload(upload_meta, user)
            else:
                await edit_message(bot_msg, f"❌ Unknown content type: {result.content_type}")
                
    except asyncio.CancelledError:
        await edit_message(bot_msg, "⏹️ Download cancelled")
        raise
    except Exception as e:
        LOGGER.error(f"Tidal NG handler error: {e}", exc_info=True)
        await edit_message(bot_msg, f"❌ Error: {str(e)}")