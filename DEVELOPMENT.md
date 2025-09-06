# Project-Siesta Development Guide

## Overview

Project-Siesta is a Telegram bot for downloading music from Apple Music. This guide will help you understand the codebase structure, set up the development environment, and contribute to the project.

## Project Structure

```
/workspace/
├── bot/                          # Main bot code
│   ├── __init__.py              # Bot package initialization
│   ├── __main__.py              # Bot entry point
│   ├── tgclient.py              # Telegram client setup
│   ├── settings.py              # Bot configuration and settings
│   ├── logger.py                # Custom logging implementation
│   ├── helpers/                 # Helper modules
│   │   ├── buttons/             # Inline keyboard buttons
│   │   ├── database/            # Database operations
│   │   ├── deezer/              # Deezer integration (legacy)
│   │   ├── qobuz/               # Qobuz integration (legacy)
│   │   ├── tidal/               # Tidal integration (legacy)
│   │   ├── tidal_ng/            # Tidal NG integration
│   │   ├── translations/        # Multi-language support
│   │   ├── uploader.py          # File upload handling
│   │   ├── utils.py             # Utility functions
│   │   ├── message.py           # Message handling
│   │   ├── progress.py          # Progress reporting
│   │   ├── state.py             # State management
│   │   └── tasks.py             # Task management
│   ├── modules/                 # Bot command modules
│   │   ├── start.py             # /start command
│   │   ├── help.py              # /help command
│   │   ├── download.py          # /download command
│   │   ├── settings.py          # /settings command
│   │   ├── cancel.py            # /cancel command
│   │   ├── history.py           # /history command
│   │   ├── config_yaml.py       # Apple Music config management
│   │   ├── provider_settings.py # Provider-specific settings
│   │   ├── telegram_setting.py  # Telegram-specific settings
│   │   └── tidal_ng_settings.py # Tidal NG settings
│   └── providers/               # Music provider implementations
│       └── apple.py             # Apple Music provider
├── downloader/                  # External downloader scripts
│   ├── am_downloader.sh         # Apple Music downloader
│   ├── install_am_downloader.sh # Installer script
│   ├── setup_wrapper.sh         # Apple Music wrapper setup
│   ├── stop_wrapper.sh          # Stop wrapper script
│   └── rclone_download_upload.sh # Rclone operations
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── sample.env                   # Environment variables template
├── .env                         # Environment variables (created from sample.env)
├── test_bot.py                  # Test suite
└── README.md                    # Project documentation
```

## Development Environment Setup

### Prerequisites

- Python 3.10+ (3.12 recommended)
- PostgreSQL database
- Git
- FFmpeg (for audio processing)
- Rclone (for cloud storage)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd project-siesta
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp sample.env .env
   # Edit .env with your configuration
   ```

5. **Set up database:**
   - Create a PostgreSQL database
   - Update `DATABASE_URL` in `.env`

6. **Make scripts executable:**
   ```bash
   chmod +x downloader/*.sh
   ```

### Configuration

Key environment variables in `.env`:

```bash
# Telegram Configuration
TG_BOT_TOKEN=your_bot_token
APP_ID=your_app_id
API_HASH=your_api_hash
BOT_USERNAME=@your_bot
ADMINS=user_id1,user_id2

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Apple Music
DOWNLOADER_PATH=/workspace/downloader/am_downloader.sh
INSTALLER_PATH=/workspace/downloader/install_am_downloader.sh

# Upload Mode
UPLOAD_MODE=Telegram  # or RCLONE or Local
```

## Running the Bot

### Development Mode

```bash
source venv/bin/activate
python -m bot
```

### Production Mode

```bash
# Using Docker
docker build -t project-siesta .
docker run -d --env-file .env --name siesta project-siesta

# Or using systemd service
sudo systemctl start project-siesta
```

## Testing

Run the test suite:

```bash
source venv/bin/activate
python test_bot.py
```

The test suite covers:
- Bot initialization
- Apple Music provider functionality
- Utility functions
- Database connectivity

## Key Components

### 1. Bot Client (`bot/tgclient.py`)

The main Telegram client that handles:
- Bot initialization
- Provider login
- Task management
- Queue processing

### 2. Settings Management (`bot/settings.py`)

Centralized configuration management:
- Environment variable loading
- Provider settings
- Database configuration
- Upload mode selection

### 3. Apple Music Provider (`bot/providers/apple.py`)

Core Apple Music integration:
- URL validation
- Content type detection
- Download processing
- Metadata extraction

### 4. Task Management (`bot/helpers/tasks.py`)

Handles concurrent operations:
- Task creation and tracking
- Queue management
- Progress reporting
- Cancellation handling

### 5. Upload System (`bot/helpers/uploader.py`)

File upload handling:
- Telegram uploads
- Rclone cloud storage
- Local storage
- Progress tracking

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write descriptive docstrings
- Use meaningful variable names

### Error Handling

- Use specific exception types
- Avoid bare `except:` statements
- Log errors with context
- Provide user-friendly error messages

### Testing

- Write tests for new features
- Test error conditions
- Verify database operations
- Test provider integrations

### Database Operations

- Use the provided database helpers
- Handle connection errors gracefully
- Use transactions for multi-step operations
- Clean up resources properly

## Common Tasks

### Adding a New Provider

1. Create provider class in `bot/providers/`
2. Implement required methods:
   - `validate_url()`
   - `extract_content_id()`
   - `process()`
3. Add provider to download routing in `bot/modules/download.py`
4. Add provider settings to `bot/settings.py`

### Adding a New Command

1. Create command module in `bot/modules/`
2. Use the `@Client.on_message` decorator
3. Implement user authentication checks
4. Add command to help system

### Modifying Upload Behavior

1. Update `bot/helpers/uploader.py`
2. Modify upload mode logic in `bot/settings.py`
3. Test with different upload modes
4. Update configuration options

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` in `.env`
   - Verify PostgreSQL is running
   - Check network connectivity

2. **Apple Music Downloader Not Found**
   - Run the installer script
   - Check file permissions
   - Verify script paths in `.env`

3. **Import Errors**
   - Activate virtual environment
   - Check Python path
   - Verify all dependencies installed

4. **Permission Denied**
   - Make scripts executable: `chmod +x downloader/*.sh`
   - Check file ownership
   - Verify user permissions

### Debug Mode

Enable debug logging by setting log level to DEBUG in `bot/logger.py`:

```python
self.logger.setLevel(logging.DEBUG)
```

### Log Files

- Bot logs: `./bot/bot_logs.log`
- Database logs: Check PostgreSQL logs
- System logs: `/var/log/syslog` (Linux)

## Performance Optimization

### Database

- Use connection pooling
- Optimize queries
- Add indexes for frequently queried columns
- Monitor query performance

### File Operations

- Use async file operations
- Implement proper cleanup
- Monitor disk usage
- Use efficient file formats

### Memory Management

- Clean up large objects
- Use generators for large datasets
- Monitor memory usage
- Implement proper garbage collection

## Security Considerations

- Never commit sensitive data to version control
- Use environment variables for secrets
- Validate user inputs
- Implement rate limiting
- Use secure database connections
- Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Run the test suite
6. Submit a pull request

## Support

- Check the README.md for basic setup
- Review this development guide
- Check existing issues on GitHub
- Create a new issue for bugs or feature requests

## License

This project is licensed under the MIT License. See LICENSE file for details.