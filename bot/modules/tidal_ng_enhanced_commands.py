"""
Enhanced Tidal NG Command Module - Version 2
Comprehensive command interface for Tidal NG configuration and management
"""
from __future__ import annotations

import json
import os
import shutil
from typing import Dict, Any, List
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from ..helpers.message import send_message, check_user, edit_message
from ..helpers.tidal_ng.config_manager import (
    config_manager, TidalNGConfig, QualityAudio, QualityVideo, DownloadPreset
)
from bot.logger import LOGGER

# Enhanced command handlers for Tidal NG configuration

@Client.on_message(filters.command(["tidal_ng_config", "tncfg"]))
async def tidal_ng_help(c: Client, msg: Message):
    """Show comprehensive help for Tidal NG configuration commands"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    help_text = """
🎵 **Tidal NG Configuration Help - Version 2**

**Basic Commands:**
• `/tidal_ng_get <key>` - Get current value of a setting
• `/tidal_ng_set <key> <value>` - Set a setting value
• `/tidal_ng_toggle <key>` - Toggle a boolean setting
• `/tidal_ng_show [keys...]` - Show current configuration

**Advanced Commands:**
• `/tidal_ng_preset <name>` - Apply a configuration preset
• `/tidal_ng_presets` - List available presets
• `/tidal_ng_reset` - Reset to default configuration
• `/tidal_ng_summary` - Show configuration summary
• `/tidal_ng_validate` - Validate current configuration
• `/tidal_ng_status` - Show system status and health
• `/tidal_ng_backup` - Create configuration backup
• `/tidal_ng_restore <backup>` - Restore from backup

**Available Presets:**
• `high_quality` - Maximum quality settings
• `fast_download` - Optimized for speed
• `minimal` - Minimal settings
• `archive_quality` - Archive-quality with delays
• `balanced` - Balanced quality and speed

**Quality Options:**
• Audio: `LOW`, `HIGH`, `LOSSLESS`, `HI_RES_LOSSLESS`
• Video: `360`, `480`, `720`, `1080`

**Example Usage:**
```
/tidal_ng_set quality_audio LOSSLESS
/tidal_ng_preset high_quality
/tidal_ng_show quality_audio quality_video
/tidal_ng_status
```
    """
    
    await send_message(msg, help_text)

@Client.on_message(filters.command(["tidal_ng_get"]))
async def tidal_ng_get(c: Client, msg: Message):
    """Get a specific configuration value with enhanced error handling"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await send_message(msg, "Usage: `/tidal_ng_get <key>`")
        return
        
    key = parts[1].strip()
    config = config_manager.load_config()
    value = getattr(config, key, None)
    
    if value is None:
        # Show available keys
        available_keys = [field.name for field in config.__dataclass_fields__.values()]
        await send_message(msg, f"❌ Unknown key: `{key}`\n\nAvailable keys: `{', '.join(available_keys[:10])}...`")
        return
        
    await send_message(msg, f"`{key}`: `{value}`")

@Client.on_message(filters.command(["tidal_ng_set"]))
async def tidal_ng_set(c: Client, msg: Message):
    """Set a configuration value with enhanced validation"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await send_message(msg, "Usage: `/tidal_ng_set <key> <value>`")
        return
        
    key = parts[1].strip()
    value_str = parts[2].strip()
    
    # Parse value based on type
    value = value_str
    
    # Try to convert to appropriate type
    if value_str.lower() in ['true', 'false']:
        value = value_str.lower() == 'true'
    elif value_str.isdigit():
        value = int(value_str)
    elif value_str.replace('.', '').isdigit():
        value = float(value_str)
        
    success = config_manager.set_value(key, value)
    
    if success:
        await send_message(msg, f"✅ Set `{key}` to `{value}`")
    else:
        await send_message(msg, f"❌ Failed to set `{key}` to `{value}` (invalid value)")

@Client.on_message(filters.command(["tidal_ng_toggle"]))
async def tidal_ng_toggle(c: Client, msg: Message):
    """Toggle a boolean configuration value"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await send_message(msg, "Usage: `/tidal_ng_toggle <key>`")
        return
        
    key = parts[1].strip()
    config = config_manager.load_config()
    current_value = getattr(config, key, None)
    
    if current_value is None:
        await send_message(msg, f"❌ Unknown key: `{key}`")
        return
        
    if not isinstance(current_value, bool):
        await send_message(msg, f"❌ `{key}` is not a boolean value")
        return
        
    new_value = not current_value
    success = config_manager.set_value(key, new_value)
    
    if success:
        await send_message(msg, f"✅ Toggled `{key}`: `{current_value}` → `{new_value}`")
    else:
        await send_message(msg, f"❌ Failed to toggle `{key}`")

@Client.on_message(filters.command(["tidal_ng_show"]))
async def tidal_ng_show(c: Client, msg: Message):
    """Show current configuration with enhanced formatting"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    config = config_manager.load_config()
    parts = msg.text.split()[1:] if len(msg.text.split()) > 1 else []
    
    if parts:
        # Show specific keys
        data = {key: getattr(config, key, "<not set>") for key in parts}
    else:
        # Show all configuration
        data = config.to_dict()
        
    output = json.dumps(data, indent=2, default=str)
    
    if len(output) > 4000:
        # Split long output
        chunks = [output[i:i+4000] for i in range(0, len(output), 4000)]
        for i, chunk in enumerate(chunks):
            await send_message(msg, f"```json\n{chunk}\n```" + (f" (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else ""))
    else:
        await send_message(msg, f"```json\n{output}\n```")

@Client.on_message(filters.command(["tidal_ng_presets"]))
async def tidal_ng_presets(c: Client, msg: Message):
    """List available configuration presets with detailed descriptions"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    presets = config_manager.get_presets()
    
    text = "🎵 **Available Tidal NG Presets - Version 2:**\n\n"
    
    preset_descriptions = {
        "high_quality": "Maximum quality with slower downloads",
        "fast_download": "Optimized for speed with good quality",
        "minimal": "Minimal settings for basic downloads",
        "archive_quality": "Archive-quality with server-friendly delays",
        "balanced": "Balanced quality and speed (recommended)"
    }
    
    for name, config in presets.items():
        description = preset_descriptions.get(name, "Custom preset")
        text += f"**{name}:** {description}\n"
        text += f"  • Audio: `{config.quality_audio}`\n"
        text += f"  • Video: `{config.quality_video}`\n"
        text += f"  • Concurrent: `{config.downloads_concurrent_max}`\n"
        text += f"  • Lyrics: `{config.lyrics_embed}`\n"
        text += f"  • Cover: `{config.metadata_cover_embed}`\n"
        text += f"  • Retry: `{config.retry_attempts}`\n\n"
        
    text += "Use `/tidal_ng_preset <name>` to apply a preset."
    
    await send_message(msg, text)

@Client.on_message(filters.command(["tidal_ng_preset"]))
async def tidal_ng_preset(c: Client, msg: Message):
    """Apply a configuration preset with confirmation"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await send_message(msg, "Usage: `/tidal_ng_preset <name>`\nUse `/tidal_ng_presets` to see available presets.")
        return
        
    preset_name = parts[1].strip()
    success = config_manager.apply_preset(preset_name)
    
    if success:
        # Show what was applied
        config = config_manager.load_config()
        await send_message(msg, f"✅ Applied preset: `{preset_name}`\n\n"
                               f"Audio: `{config.quality_audio}`\n"
                               f"Video: `{config.quality_video}`\n"
                               f"Concurrent: `{config.downloads_concurrent_max}`")
    else:
        await send_message(msg, f"❌ Unknown preset: `{preset_name}`")

@Client.on_message(filters.command(["tidal_ng_reset"]))
async def tidal_ng_reset(c: Client, msg: Message):
    """Reset configuration to defaults with confirmation"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    success = config_manager.reset_to_defaults()
    
    if success:
        await send_message(msg, "✅ Configuration reset to defaults")
    else:
        await send_message(msg, "❌ Failed to reset configuration")

@Client.on_message(filters.command(["tidal_ng_summary"]))
async def tidal_ng_summary(c: Client, msg: Message):
    """Show comprehensive configuration summary"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    summary = config_manager.get_config_summary()
    
    text = "🎵 **Tidal NG Configuration Summary - Version 2:**\n\n"
    
    # Quality settings
    text += "**Quality:**\n"
    text += f"  • Audio: `{summary['quality']['audio']}`\n"
    text += f"  • Video: `{summary['quality']['video']}`\n\n"
    
    # Download settings
    text += "**Download:**\n"
    text += f"  • Concurrent Max: `{summary['download']['concurrent_max']}`\n"
    text += f"  • Per Track: `{summary['download']['simultaneous_per_track']}`\n"
    text += f"  • Delay: `{summary['download']['delay']}`\n"
    text += f"  • Retry: `{summary['download']['retry_attempts']}`\n"
    text += f"  • Timeout: `{summary['download']['timeout']}s`\n\n"
    
    # Metadata settings
    text += "**Metadata:**\n"
    text += f"  • Lyrics Embed: `{summary['metadata']['lyrics_embed']}`\n"
    text += f"  • Lyrics File: `{summary['metadata']['lyrics_file']}`\n"
    text += f"  • Cover Embed: `{summary['metadata']['cover_embed']}`\n"
    text += f"  • Cover Size: `{summary['metadata']['cover_dimension']}px`\n"
    text += f"  • Replay Gain: `{summary['metadata']['replay_gain']}`\n\n"
    
    # File settings
    text += "**Files:**\n"
    text += f"  • Skip Existing: `{summary['files']['skip_existing']}`\n"
    text += f"  • Extract FLAC: `{summary['files']['extract_flac']}`\n"
    text += f"  • Video Download: `{summary['files']['video_download']}`\n"
    text += f"  • Convert MP4: `{summary['files']['video_convert_mp4']}`\n\n"
    
    # Playlist settings
    text += "**Playlist:**\n"
    text += f"  • Create: `{summary['playlist']['create']}`\n"
    text += f"  • Track Padding: `{summary['playlist']['track_padding']}`\n\n"
    
    # System settings
    text += "**System:**\n"
    text += f"  • FFmpeg: `{summary['system']['ffmpeg_path']}`\n"
    text += f"  • Download Path: `{summary['system']['download_path']}`\n"
    
    await send_message(msg, text)

@Client.on_message(filters.command(["tidal_ng_validate"]))
async def tidal_ng_validate(c: Client, msg: Message):
    """Validate current configuration with detailed error reporting"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    config = config_manager.load_config()
    errors = config.validate()
    
    if errors:
        text = "❌ **Configuration Issues Found:**\n\n"
        for i, error in enumerate(errors, 1):
            text += f"{i}. {error}\n"
        text += "\nUse `/tidal_ng_reset` to reset to defaults or fix individual settings."
    else:
        text = "✅ **Configuration is valid!**\n\nAll settings are properly configured and within acceptable ranges."
        
    await send_message(msg, text)

@Client.on_message(filters.command(["tidal_ng_status"]))
async def tidal_ng_status(c: Client, msg: Message):
    """Show comprehensive Tidal NG status and system information"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    import psutil
    from pathlib import Path
    
    # Check if tidal-dl-ng is installed
    tidal_ng_path = "/usr/src/app/tidal-dl-ng/tidal_dl_ng/cli.py"
    tidal_ng_installed = os.path.exists(tidal_ng_path)
    
    # Check settings file
    settings_path = "/root/.config/tidal_dl_ng/settings.json"
    settings_exists = os.path.exists(settings_path)
    
    # Check FFmpeg
    ffmpeg_available = shutil.which("ffmpeg") is not None
    
    # System info
    disk_usage = psutil.disk_usage('/')
    memory = psutil.virtual_memory()
    
    # Configuration status
    config = config_manager.load_config()
    config_errors = config.validate()
    
    text = "🎵 **Tidal NG Status - Version 2:**\n\n"
    
    text += "**Installation:**\n"
    text += f"  • Tidal-dl-ng: {'✅ Installed' if tidal_ng_installed else '❌ Not found'}\n"
    text += f"  • Settings file: {'✅ Exists' if settings_exists else '❌ Missing'}\n"
    text += f"  • FFmpeg: {'✅ Available' if ffmpeg_available else '❌ Not found'}\n"
    text += f"  • Config valid: {'✅ Yes' if not config_errors else '❌ No'}\n\n"
    
    text += "**System:**\n"
    text += f"  • Disk free: {disk_usage.free // (1024**3)} GB\n"
    text += f"  • Memory: {memory.percent}% used\n"
    text += f"  • CPU: {psutil.cpu_percent()}% used\n\n"
    
    text += "**Configuration:**\n"
    text += f"  • Audio Quality: `{config.quality_audio}`\n"
    text += f"  • Video Quality: `{config.quality_video}`\n"
    text += f"  • Concurrent Downloads: `{config.downloads_concurrent_max}`\n"
    text += f"  • Retry Attempts: `{config.retry_attempts}`\n\n"
    
    if config_errors:
        text += "**Configuration Issues:**\n"
        for error in config_errors[:3]:  # Show first 3 errors
            text += f"  • {error}\n"
        if len(config_errors) > 3:
            text += f"  • ... and {len(config_errors) - 3} more\n"
        text += "\n"
    
    if not tidal_ng_installed:
        text += "⚠️ **Tidal-dl-ng not found!**\n"
        text += "Please install it first:\n"
        text += "```bash\npip install tidal-dl-ng\n```"
    
    await send_message(msg, text)

@Client.on_message(filters.command(["tidal_ng_backup"]))
async def tidal_ng_backup(c: Client, msg: Message):
    """Create a configuration backup"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    backup_path = config_manager._backup_config()
    
    if backup_path:
        await send_message(msg, f"✅ Configuration backed up to: `{backup_path}`")
    else:
        await send_message(msg, "❌ Failed to create backup")

@Client.on_message(filters.command(["tidal_ng_restore"]))
async def tidal_ng_restore(c: Client, msg: Message):
    """Restore configuration from backup"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        # List available backups
        backup_dir = config_manager._backup_dir
        if backup_dir.exists():
            backups = list(backup_dir.glob("settings.backup.*.json"))
            if backups:
                text = "Available backups:\n"
                for backup in sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    text += f"• `{backup.name}`\n"
                text += "\nUsage: `/tidal_ng_restore <backup_name>`"
            else:
                text = "No backups found"
        else:
            text = "No backups found"
        await send_message(msg, text)
        return
        
    backup_name = parts[1].strip()
    backup_path = config_manager._backup_dir / backup_name
    
    if not backup_path.exists():
        await send_message(msg, f"❌ Backup not found: `{backup_name}`")
        return
        
    try:
        # Restore backup
        shutil.copy2(backup_path, config_manager.settings_path)
        await send_message(msg, f"✅ Configuration restored from: `{backup_name}`")
    except Exception as e:
        await send_message(msg, f"❌ Failed to restore backup: {e}")

@Client.on_message(filters.command(["tidal_ng_cleanup"]))
async def tidal_ng_cleanup(c: Client, msg: Message):
    """Clean up old backups and temporary files"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    try:
        # Clean up old backups
        config_manager.cleanup_old_backups(keep_count=5)
        
        # Clean up temporary files
        temp_dirs = Path(Config.DOWNLOAD_BASE_DIR).glob("*/tidal_ng_*")
        cleaned_count = 0
        for temp_dir in temp_dirs:
            if temp_dir.is_dir():
                shutil.rmtree(temp_dir, ignore_errors=True)
                cleaned_count += 1
                
        await send_message(msg, f"✅ Cleanup completed\n• Old backups cleaned\n• {cleaned_count} temp directories removed")
    except Exception as e:
        await send_message(msg, f"❌ Cleanup failed: {e}")