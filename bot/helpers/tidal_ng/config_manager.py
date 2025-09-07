"""
Enhanced Tidal NG Configuration Manager - Version 2
Advanced configuration management with presets, validation, and smart defaults
"""
import os
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from bot.logger import LOGGER

class QualityAudio(Enum):
    """Audio quality options"""
    LOW = "LOW"
    HIGH = "HIGH"
    LOSSLESS = "LOSSLESS"
    HI_RES_LOSSLESS = "HI_RES_LOSSLESS"

class QualityVideo(Enum):
    """Video quality options"""
    P360 = "360"
    P480 = "480"
    P720 = "720"
    P1080 = "1080"

class DownloadPreset(Enum):
    """Download preset options"""
    HIGH_QUALITY = "high_quality"
    FAST_DOWNLOAD = "fast_download"
    MINIMAL = "minimal"
    ARCHIVE_QUALITY = "archive_quality"
    BALANCED = "balanced"

@dataclass
class TidalNGConfig:
    """Tidal NG configuration schema with validation and smart defaults"""
    
    # Download settings
    download_base_path: str = "~/download"
    downloads_concurrent_max: int = 3
    downloads_simultaneous_per_track_max: int = 1
    download_delay: bool = False
    
    # Quality settings
    quality_audio: str = "LOSSLESS"
    quality_video: str = "1080"
    
    # Metadata settings
    lyrics_embed: bool = True
    lyrics_file: bool = True
    metadata_cover_embed: bool = True
    metadata_cover_dimension: int = 1200
    cover_album_file: bool = True
    metadata_replay_gain: bool = True
    
    # File handling
    skip_existing: bool = True
    extract_flac: bool = True
    symlink_to_track: bool = False
    video_download: bool = True
    video_convert_mp4: bool = True
    
    # Playlist settings
    playlist_create: bool = True
    album_track_num_pad_min: int = 2
    
    # System settings
    path_binary_ffmpeg: str = "/usr/bin/ffmpeg"
    
    # Advanced settings
    retry_attempts: int = 3
    timeout_seconds: int = 300
    chunk_size: int = 1024 * 1024  # 1MB chunks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            field.name: getattr(self, field.name) 
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TidalNGConfig':
        """Create instance from dictionary with validation"""
        config = cls()
        for field_name, field_value in data.items():
            if hasattr(config, field_name):
                setattr(config, field_name, field_value)
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate quality settings
        if self.quality_audio not in [q.value for q in QualityAudio]:
            errors.append(f"Invalid audio quality: {self.quality_audio}")
            
        if self.quality_video not in [q.value for q in QualityVideo]:
            errors.append(f"Invalid video quality: {self.quality_video}")
            
        # Validate numeric values
        if self.downloads_concurrent_max <= 0 or self.downloads_concurrent_max > 10:
            errors.append("Concurrent downloads must be between 1 and 10")
            
        if self.metadata_cover_dimension <= 0 or self.metadata_cover_dimension > 5000:
            errors.append("Cover dimension must be between 1 and 5000")
            
        if self.retry_attempts < 0 or self.retry_attempts > 10:
            errors.append("Retry attempts must be between 0 and 10")
            
        if self.timeout_seconds <= 0 or self.timeout_seconds > 3600:
            errors.append("Timeout must be between 1 and 3600 seconds")
            
        # Validate paths
        if not self.download_base_path:
            errors.append("Download base path is empty")
            
        if not self.path_binary_ffmpeg:
            errors.append("FFmpeg path is empty")
            
        return errors

class TidalNGConfigManager:
    """Enhanced configuration manager for Tidal NG with advanced features"""
    
    def __init__(self, settings_path: str = "/root/.config/tidal_dl_ng/settings.json"):
        self.settings_path = Path(settings_path)
        self.config_dir = self.settings_path.parent
        self._config: Optional[TidalNGConfig] = None
        self._backup_dir = self.config_dir / "backups"
        
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
    def _backup_config(self) -> str:
        """Create backup of current configuration"""
        if not self.settings_path.exists():
            return ""
            
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_path = self._backup_dir / f"settings.backup.{timestamp}.json"
        
        try:
            shutil.copy2(self.settings_path, backup_path)
            LOGGER.info(f"Configuration backed up to: {backup_path}")
            return str(backup_path)
        except Exception as e:
            LOGGER.error(f"Failed to backup configuration: {e}")
            return ""
            
    def load_config(self) -> TidalNGConfig:
        """Load configuration from file with error handling"""
        try:
            if not self.settings_path.exists():
                LOGGER.info("No configuration file found, using defaults")
                self._config = TidalNGConfig()
                return self._config
                
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self._config = TidalNGConfig.from_dict(data)
            
            # Validate loaded config
            errors = self._config.validate()
            if errors:
                LOGGER.warn(f"Configuration validation warnings: {errors}")
                
            LOGGER.info("Configuration loaded successfully")
            return self._config
            
        except (json.JSONDecodeError, KeyError) as e:
            LOGGER.error(f"Error loading configuration: {e}")
            self._config = TidalNGConfig()
            return self._config
            
    def save_config(self, config: Optional[TidalNGConfig] = None) -> bool:
        """Save configuration to file with atomic write"""
        try:
            self._ensure_config_dir()
            
            if config is None:
                config = self._config or TidalNGConfig()
                
            # Validate before saving
            errors = config.validate()
            if errors:
                LOGGER.error(f"Configuration validation failed: {errors}")
                return False
                
            # Create backup before saving
            self._backup_config()
            
            # Write to temporary file first
            temp_path = self.settings_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=4)
                
            # Atomic move
            temp_path.replace(self.settings_path)
            
            self._config = config
            LOGGER.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            LOGGER.error(f"Failed to save configuration: {e}")
            return False
            
    def get_value(self, key: str) -> Any:
        """Get a configuration value"""
        if self._config is None:
            self.load_config()
            
        return getattr(self._config, key, None)
        
    def set_value(self, key: str, value: Any) -> bool:
        """Set a configuration value with validation"""
        if self._config is None:
            self.load_config()
            
        # Validate the value
        if not self._validate_value(key, value):
            return False
            
        try:
            setattr(self._config, key, value)
            return self.save_config()
        except Exception as e:
            LOGGER.error(f"Failed to set {key}: {e}")
            return False
            
    def _validate_value(self, key: str, value: Any) -> bool:
        """Validate a configuration value"""
        try:
            if key == "quality_audio":
                return value in [q.value for q in QualityAudio]
            elif key == "quality_video":
                return value in [q.value for q in QualityVideo]
            elif key in ["downloads_concurrent_max", "downloads_simultaneous_per_track_max", 
                        "metadata_cover_dimension", "album_track_num_pad_min", "retry_attempts"]:
                return isinstance(value, int) and value > 0
            elif key == "timeout_seconds":
                return isinstance(value, int) and 1 <= value <= 3600
            elif key in ["lyrics_embed", "lyrics_file", "metadata_cover_embed", 
                        "cover_album_file", "metadata_replay_gain", "skip_existing",
                        "extract_flac", "symlink_to_track", "video_download", 
                        "video_convert_mp4", "playlist_create", "download_delay"]:
                return isinstance(value, bool)
            elif key in ["download_base_path", "path_binary_ffmpeg"]:
                return isinstance(value, str) and len(value) > 0
            else:
                return True
        except Exception:
            return False
            
    def get_presets(self) -> Dict[str, TidalNGConfig]:
        """Get predefined configuration presets"""
        return {
            "high_quality": TidalNGConfig(
                quality_audio="HI_RES_LOSSLESS",
                quality_video="1080",
                metadata_cover_embed=True,
                metadata_cover_dimension=2000,
                lyrics_embed=True,
                lyrics_file=True,
                extract_flac=True,
                downloads_concurrent_max=2,
                retry_attempts=5,
            ),
            "fast_download": TidalNGConfig(
                quality_audio="HIGH",
                quality_video="720",
                downloads_concurrent_max=5,
                downloads_simultaneous_per_track_max=2,
                metadata_cover_embed=False,
                lyrics_embed=False,
                extract_flac=False,
                retry_attempts=2,
                timeout_seconds=180,
            ),
            "minimal": TidalNGConfig(
                quality_audio="HIGH",
                quality_video="480",
                metadata_cover_embed=False,
                lyrics_embed=False,
                lyrics_file=False,
                extract_flac=False,
                playlist_create=False,
                downloads_concurrent_max=1,
            ),
            "archive_quality": TidalNGConfig(
                quality_audio="HI_RES_LOSSLESS",
                quality_video="1080",
                metadata_cover_embed=True,
                metadata_cover_dimension=3000,
                lyrics_embed=True,
                lyrics_file=True,
                extract_flac=True,
                metadata_replay_gain=True,
                download_delay=True,
                downloads_concurrent_max=1,
                retry_attempts=5,
                timeout_seconds=600,
            ),
            "balanced": TidalNGConfig(
                quality_audio="LOSSLESS",
                quality_video="720",
                metadata_cover_embed=True,
                metadata_cover_dimension=1200,
                lyrics_embed=True,
                lyrics_file=False,
                extract_flac=True,
                downloads_concurrent_max=3,
                retry_attempts=3,
            )
        }
        
    def apply_preset(self, preset_name: str) -> bool:
        """Apply a configuration preset"""
        presets = self.get_presets()
        if preset_name not in presets:
            LOGGER.error(f"Unknown preset: {preset_name}")
            return False
            
        preset_config = presets[preset_name]
        return self.save_config(preset_config)
        
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        default_config = TidalNGConfig()
        return self.save_config(default_config)
        
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        if self._config is None:
            self.load_config()
            
        summary = {
            "quality": {
                "audio": self._config.quality_audio,
                "video": self._config.quality_video,
            },
            "download": {
                "concurrent_max": self._config.downloads_concurrent_max,
                "simultaneous_per_track": self._config.downloads_simultaneous_per_track_max,
                "delay": self._config.download_delay,
                "retry_attempts": self._config.retry_attempts,
                "timeout": self._config.timeout_seconds,
            },
            "metadata": {
                "lyrics_embed": self._config.lyrics_embed,
                "lyrics_file": self._config.lyrics_file,
                "cover_embed": self._config.metadata_cover_embed,
                "cover_dimension": self._config.metadata_cover_dimension,
                "replay_gain": self._config.metadata_replay_gain,
            },
            "files": {
                "skip_existing": self._config.skip_existing,
                "extract_flac": self._config.extract_flac,
                "video_download": self._config.video_download,
                "video_convert_mp4": self._config.video_convert_mp4,
            },
            "playlist": {
                "create": self._config.playlist_create,
                "track_padding": self._config.album_track_num_pad_min,
            },
            "system": {
                "ffmpeg_path": self._config.path_binary_ffmpeg,
                "download_path": self._config.download_base_path,
            }
        }
        
        return summary
        
    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            if not self._backup_dir.exists():
                return
                
            backup_files = list(self._backup_dir.glob("settings.backup.*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                LOGGER.info(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            LOGGER.error(f"Failed to cleanup old backups: {e}")

# Global configuration manager instance
config_manager = TidalNGConfigManager()