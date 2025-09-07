# Enhanced Tidal NG Development Guide - Version 2

## Overview

This document provides comprehensive guidance for developing and enhancing the Tidal NG integration in the Project-Siesta AIO Telegram music bot. The enhanced Tidal NG implementation includes advanced features, better error handling, progress reporting, and a comprehensive configuration management system.

## Architecture

### Core Components

1. **Enhanced Handler** (`bot/helpers/tidal_ng/enhanced_handler.py`)
   - Advanced download management with context managers
   - Real-time progress reporting
   - Smart error handling and retry logic
   - Content type detection and metadata extraction

2. **Configuration Manager** (`bot/helpers/tidal_ng/config_manager.py`)
   - Centralized configuration management
   - Preset system for common configurations
   - Validation and error reporting
   - Backup and restore functionality

3. **Enhanced Commands** (`bot/modules/tidal_ng_enhanced_commands.py`)
   - Comprehensive command interface
   - Advanced configuration controls
   - System status and health monitoring
   - Preset management

4. **Test Suite** (`test_tidal_ng_enhanced.py`)
   - Comprehensive testing framework
   - Unit tests for all components
   - Integration testing
   - Performance validation

## Features

### Enhanced Download Handler

#### Key Features
- **Context Manager Support**: Automatic cleanup and resource management
- **Progress Reporting**: Real-time download progress with detailed status updates
- **Smart Error Handling**: Comprehensive error detection and recovery
- **Content Type Detection**: Automatic detection of tracks, albums, playlists, and videos
- **Metadata Extraction**: Enhanced metadata processing with error handling
- **Cancellation Support**: User-initiated download cancellation

#### Usage Example
```python
async with TidalNGDownloader() as downloader:
    result = await downloader.download(url, user, options)
    if result.success:
        # Process successful download
        pass
    else:
        # Handle error
        pass
```

#### Configuration Options
- `quality`: Audio quality (LOW, HIGH, LOSSLESS, HI_RES_LOSSLESS)
- `video_quality`: Video quality (360, 480, 720, 1080)
- `lyrics`: Enable/disable lyrics embedding
- `cover`: Enable/disable cover art embedding
- `concurrent`: Number of concurrent downloads (1-10)
- `flac`: Enable/disable FLAC extraction
- `video`: Enable/disable video downloads

### Configuration Manager

#### Preset System
The configuration manager includes predefined presets for common use cases:

1. **high_quality**: Maximum quality settings
   - Audio: HI_RES_LOSSLESS
   - Video: 1080p
   - Full metadata embedding
   - Conservative concurrent downloads

2. **fast_download**: Speed-optimized settings
   - Audio: HIGH quality
   - Video: 720p
   - Minimal metadata
   - High concurrent downloads

3. **minimal**: Basic settings
   - Audio: HIGH quality
   - Video: 480p
   - No metadata embedding
   - Single concurrent download

4. **archive_quality**: Archive-quality settings
   - Audio: HI_RES_LOSSLESS
   - Video: 1080p
   - Full metadata with delays
   - Single concurrent download

5. **balanced**: Balanced settings (recommended)
   - Audio: LOSSLESS
   - Video: 720p
   - Moderate metadata
   - Moderate concurrent downloads

#### Configuration Validation
- Type checking for all configuration values
- Range validation for numeric values
- Enum validation for quality settings
- Path validation for system settings

### Enhanced Commands

#### Basic Commands
- `/tidal_ng_get <key>`: Get configuration value
- `/tidal_ng_set <key> <value>`: Set configuration value
- `/tidal_ng_toggle <key>`: Toggle boolean settings
- `/tidal_ng_show [keys...]`: Display configuration

#### Advanced Commands
- `/tidal_ng_preset <name>`: Apply configuration preset
- `/tidal_ng_presets`: List available presets
- `/tidal_ng_reset`: Reset to default configuration
- `/tidal_ng_summary`: Show configuration summary
- `/tidal_ng_validate`: Validate current configuration
- `/tidal_ng_status`: Show system status and health
- `/tidal_ng_backup`: Create configuration backup
- `/tidal_ng_restore <backup>`: Restore from backup
- `/tidal_ng_cleanup`: Clean up old files and backups

## Development Guidelines

### Code Structure

#### File Organization
```
bot/helpers/tidal_ng/
├── __init__.py
├── handler.py              # Original handler
├── enhanced_handler.py     # Enhanced handler
├── config_manager.py       # Configuration management
└── utils.py               # Utility functions

bot/modules/
├── tidal_ng_settings.py           # Original settings
└── tidal_ng_enhanced_commands.py  # Enhanced commands
```

#### Naming Conventions
- Classes: PascalCase (e.g., `TidalNGDownloader`)
- Functions: snake_case (e.g., `start_tidal_ng_enhanced`)
- Constants: UPPER_SNAKE_CASE (e.g., `TIDAL_DL_NG_CLI_PATH`)
- Enums: PascalCase (e.g., `DownloadStatus`)

### Error Handling

#### Exception Hierarchy
```python
class TidalNGError(Exception):
    """Base exception for Tidal NG operations"""
    pass

class ConfigurationError(TidalNGError):
    """Configuration-related errors"""
    pass

class DownloadError(TidalNGError):
    """Download-related errors"""
    pass
```

#### Error Recovery
- Automatic retry with exponential backoff
- Graceful degradation for non-critical errors
- User-friendly error messages
- Detailed logging for debugging

### Testing

#### Test Categories
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **Performance Tests**: Load and stress testing
4. **User Acceptance Tests**: End-to-end functionality

#### Running Tests
```bash
# Run all enhanced Tidal NG tests
python test_tidal_ng_enhanced.py

# Run specific test categories
python -m pytest test_tidal_ng_enhanced.py::test_config_manager
```

### Logging

#### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARN`: Warning messages for non-critical issues
- `ERROR`: Error messages for failed operations
- `CRITICAL`: Critical errors that may cause system failure

#### Log Format
```
[LEVEL] [TIMESTAMP] [FILENAME] - MESSAGE
```

### Performance Optimization

#### Download Optimization
- Concurrent download limits
- Smart retry logic
- Progress reporting efficiency
- Memory usage optimization

#### Configuration Optimization
- Lazy loading of configurations
- Caching of frequently accessed values
- Atomic file operations
- Backup management

## Integration Guide

### Adding New Features

1. **Define the Feature**
   - Create feature specification
   - Design API interface
   - Plan error handling

2. **Implement Core Logic**
   - Add to appropriate handler
   - Implement configuration options
   - Add validation logic

3. **Add Commands**
   - Create command handlers
   - Add help documentation
   - Implement user feedback

4. **Write Tests**
   - Unit tests for core logic
   - Integration tests for commands
   - Performance tests if applicable

5. **Update Documentation**
   - Update this guide
   - Add command help text
   - Update README if needed

### Configuration Schema

#### Adding New Settings
1. Add field to `TidalNGConfig` dataclass
2. Add validation in `_validate_value` method
3. Update preset configurations
4. Add command support if needed
5. Update documentation

#### Example
```python
@dataclass
class TidalNGConfig:
    # ... existing fields ...
    new_setting: str = "default_value"
    
def _validate_value(self, key: str, value: Any) -> bool:
    # ... existing validations ...
    elif key == "new_setting":
        return isinstance(value, str) and len(value) > 0
```

### Command Development

#### Command Structure
```python
@Client.on_message(filters.command(["tidal_ng_new_command"]))
async def tidal_ng_new_command(c: Client, msg: Message):
    """Command description"""
    if not await check_user(msg.from_user.id, restricted=True):
        return
        
    try:
        # Command logic here
        await send_message(msg, "Success message")
    except Exception as e:
        LOGGER.error(f"Command error: {e}")
        await send_message(msg, f"Error: {e}")
```

## Troubleshooting

### Common Issues

#### Configuration Issues
- **Invalid settings**: Use `/tidal_ng_validate` to check configuration
- **Missing settings file**: Use `/tidal_ng_reset` to create defaults
- **Corrupted settings**: Use `/tidal_ng_restore` to restore from backup

#### Download Issues
- **Process failures**: Check system status with `/tidal_ng_status`
- **Permission errors**: Verify file system permissions
- **Network issues**: Check internet connectivity and Tidal access

#### Performance Issues
- **Slow downloads**: Adjust concurrent download limits
- **High memory usage**: Reduce concurrent downloads or chunk size
- **Disk space**: Use `/tidal_ng_cleanup` to remove old files

### Debug Mode

Enable debug logging for detailed troubleshooting:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Batch Downloads**: Support for multiple URLs
2. **Quality Optimization**: Automatic quality selection based on content
3. **Smart Retry**: Intelligent retry logic with backoff
4. **Progress Persistence**: Resume interrupted downloads
5. **User Preferences**: Per-user configuration settings
6. **Analytics**: Download statistics and performance metrics

### Extension Points
- Custom download handlers
- Plugin system for additional features
- Webhook support for external integrations
- API endpoints for programmatic access

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for all public methods
- Include error handling for all operations

### Pull Request Process
1. Create feature branch from `tidal-version2`
2. Implement changes with tests
3. Update documentation
4. Submit pull request with detailed description

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass successfully
- [ ] Documentation is updated
- [ ] Error handling is comprehensive
- [ ] Performance impact is considered
- [ ] Backward compatibility is maintained

## Support

For questions or issues related to the Enhanced Tidal NG implementation:

1. Check this documentation
2. Review test suite for examples
3. Check system status with `/tidal_ng_status`
4. Enable debug logging for detailed information
5. Create issue with detailed error information

---

**Version**: 2.0  
**Last Updated**: 2024  
**Maintainer**: Project-Siesta Development Team