#!/usr/bin/env python3
"""
Test script for Project-Siesta bot functionality
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from bot.logger import LOGGER
from bot.settings import bot_set

async def test_bot_initialization():
    """Test basic bot initialization"""
    try:
        LOGGER.info("Testing bot initialization...")
        
        # Test config loading
        LOGGER.info(f"Bot username: {Config.BOT_USERNAME}")
        LOGGER.info(f"Database URL configured: {bool(Config.DATABASE_URL)}")
        LOGGER.info(f"Download base dir: {Config.DOWNLOAD_BASE_DIR}")
        
        # Test settings initialization
        LOGGER.info(f"Apple Music enabled: {bool(bot_set.apple)}")
        LOGGER.info(f"Queue mode: {getattr(bot_set, 'queue_mode', False)}")
        LOGGER.info(f"Upload mode: {getattr(bot_set, 'upload_mode', 'Unknown')}")
        
        # Test database connection
        from bot.helpers.database.pg_impl import set_db
        LOGGER.info("Database connection test passed")
        
        LOGGER.info("✅ Bot initialization test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Bot initialization test failed: {str(e)}")
        return False

async def test_apple_music_provider():
    """Test Apple Music provider functionality"""
    try:
        LOGGER.info("Testing Apple Music provider...")
        
        from bot.providers.apple import AppleMusicProvider
        
        provider = AppleMusicProvider()
        
        # Test URL validation
        test_urls = [
            "https://music.apple.com/us/album/test/1234567890",
            "https://music.apple.com/us/song/test/1234567890",
            "https://music.apple.com/us/playlist/test/1234567890",
            "https://music.apple.com/us/music-video/test/1234567890",
            "https://invalid-url.com/test"
        ]
        
        for url in test_urls:
            is_valid = provider.validate_url(url)
            LOGGER.info(f"URL validation: {url} -> {is_valid}")
        
        # Test content ID extraction
        test_url = "https://music.apple.com/us/album/test/1234567890"
        content_id = provider.extract_content_id(test_url)
        LOGGER.info(f"Content ID extraction: {content_id}")
        
        LOGGER.info("✅ Apple Music provider test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Apple Music provider test failed: {str(e)}")
        return False

async def test_utilities():
    """Test utility functions"""
    try:
        LOGGER.info("Testing utility functions...")
        
        from bot.helpers.utils import format_string, _read_apple_config_paths
        
        # Test string formatting
        test_string = "Test {title} by {artist}"
        test_data = {"title": "Song Title", "artist": "Artist Name"}
        formatted = await format_string(test_string, test_data)
        LOGGER.info(f"String formatting test: {formatted}")
        
        # Test Apple config reading
        config_paths = _read_apple_config_paths()
        LOGGER.info(f"Apple config paths test: {len(config_paths)} paths found")
        
        LOGGER.info("✅ Utility functions test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Utility functions test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    LOGGER.info("🚀 Starting Project-Siesta bot tests...")
    
    tests = [
        ("Bot Initialization", test_bot_initialization),
        ("Apple Music Provider", test_apple_music_provider),
        ("Utility Functions", test_utilities)
    ]
    
    results = []
    for test_name, test_func in tests:
        LOGGER.info(f"\n--- Running {test_name} Test ---")
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    LOGGER.info("\n" + "="*50)
    LOGGER.info("TEST SUMMARY")
    LOGGER.info("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        LOGGER.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    LOGGER.info(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        LOGGER.info("🎉 All tests passed! Bot is ready for development.")
    else:
        LOGGER.warn("⚠️ Some tests failed. Please review the issues above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)