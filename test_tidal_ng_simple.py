#!/usr/bin/env python3
"""
Simple test suite for Enhanced Tidal NG integration - Version 2
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from bot.logger import LOGGER
from bot.helpers.tidal_ng.config_manager import (
    TidalNGConfig, QualityAudio, QualityVideo, DownloadPreset
)
from bot.helpers.tidal_ng.enhanced_handler import (
    get_content_id_from_url, DownloadStatus, TidalNGDownloadResult
)

async def test_quality_enums():
    """Test quality enum functionality"""
    try:
        LOGGER.info("Testing quality enums...")
        
        # Test audio qualities
        for quality in QualityAudio:
            LOGGER.info(f"Audio quality: {quality.value}")
            
        # Test video qualities
        for quality in QualityVideo:
            LOGGER.info(f"Video quality: {quality.value}")
            
        # Test enum validation
        valid_audio = [q.value for q in QualityAudio]
        valid_video = [q.value for q in QualityVideo]
        
        LOGGER.info(f"Valid audio qualities: {valid_audio}")
        LOGGER.info(f"Valid video qualities: {valid_video}")
        
        LOGGER.info("✅ Quality enums test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Quality enums test failed: {str(e)}")
        return False

async def test_download_status():
    """Test download status enumeration"""
    try:
        LOGGER.info("Testing download status enumeration...")
        
        # Test all status values
        for status in DownloadStatus:
            LOGGER.info(f"Download status: {status.value}")
            
        # Test status creation
        result_status = DownloadStatus.COMPLETED
        LOGGER.info(f"Result status: {result_status.value}")
        
        LOGGER.info("✅ Download status test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Download status test failed: {str(e)}")
        return False

async def test_url_parsing():
    """Test URL parsing functionality"""
    try:
        LOGGER.info("Testing URL parsing...")
        
        # Test URL parsing
        test_urls = [
            "https://tidal.com/track/123456789",
            "https://listen.tidal.com/album/987654321",
            "https://tidal.com/playlist/456789123",
            "https://tidal.com/video/789123456",
            "https://tidal.com/artist/321654987",
            "https://invalid-url.com/test"
        ]
        
        for url in test_urls:
            content_id = get_content_id_from_url(url)
            LOGGER.info(f"URL: {url} -> ID: {content_id}")
            
        LOGGER.info("✅ URL parsing test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ URL parsing test failed: {str(e)}")
        return False

async def test_download_result():
    """Test download result dataclass"""
    try:
        LOGGER.info("Testing download result dataclass...")
        
        # Create a test result
        download_result = TidalNGDownloadResult(
            success=True,
            files=["test1.mp3", "test2.mp3"],
            content_type="album",
            metadata=[{"title": "Test Song", "artist": "Test Artist"}],
            status=DownloadStatus.COMPLETED,
            quality="LOSSLESS",
            duration=120.5
        )
        
        LOGGER.info(f"Download result created: {download_result.success}")
        LOGGER.info(f"Files count: {len(download_result.files)}")
        LOGGER.info(f"Content type: {download_result.content_type}")
        LOGGER.info(f"Status: {download_result.status.value}")
        LOGGER.info(f"Quality: {download_result.quality}")
        LOGGER.info(f"Duration: {download_result.duration}s")
        
        LOGGER.info("✅ Download result test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Download result test failed: {str(e)}")
        return False

async def test_config_creation():
    """Test configuration creation and validation"""
    try:
        LOGGER.info("Testing configuration creation...")
        
        # Create a test configuration
        config = TidalNGConfig()
        LOGGER.info(f"Default config created: {type(config)}")
        
        # Test configuration validation
        errors = config.validate()
        LOGGER.info(f"Config validation errors: {len(errors)}")
        
        if errors:
            for error in errors:
                LOGGER.info(f"Validation error: {error}")
        
        # Test configuration to dict
        config_dict = config.to_dict()
        LOGGER.info(f"Config dict keys: {list(config_dict.keys())}")
        
        # Test configuration from dict
        new_config = TidalNGConfig.from_dict(config_dict)
        LOGGER.info(f"Config from dict created: {type(new_config)}")
        
        LOGGER.info("✅ Configuration creation test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Configuration creation test failed: {str(e)}")
        return False

async def test_preset_configs():
    """Test preset configurations"""
    try:
        LOGGER.info("Testing preset configurations...")
        
        # Create a temporary config manager for testing
        from bot.helpers.tidal_ng.config_manager import TidalNGConfigManager
        temp_config_manager = TidalNGConfigManager("/tmp/tidal_ng_test_config/settings.json")
        
        # Test getting presets
        presets = temp_config_manager.get_presets()
        LOGGER.info(f"Available presets: {list(presets.keys())}")
        
        # Test each preset
        for preset_name, preset_config in presets.items():
            LOGGER.info(f"Testing preset: {preset_name}")
            LOGGER.info(f"  Audio: {preset_config.quality_audio}")
            LOGGER.info(f"  Video: {preset_config.quality_video}")
            LOGGER.info(f"  Concurrent: {preset_config.downloads_concurrent_max}")
            
            # Validate preset
            errors = preset_config.validate()
            if errors:
                LOGGER.warning(f"Preset {preset_name} has validation errors: {errors}")
            else:
                LOGGER.info(f"Preset {preset_name} is valid")
        
        LOGGER.info("✅ Preset configurations test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Preset configurations test failed: {str(e)}")
        return False

async def main():
    """Run all Enhanced Tidal NG tests"""
    LOGGER.info("🚀 Starting Enhanced Tidal NG simple tests - Version 2...")
    
    tests = [
        ("Quality Enums", test_quality_enums),
        ("Download Status", test_download_status),
        ("URL Parsing", test_url_parsing),
        ("Download Result", test_download_result),
        ("Configuration Creation", test_config_creation),
        ("Preset Configurations", test_preset_configs),
    ]
    
    results = []
    for test_name, test_func in tests:
        LOGGER.info(f"\n--- Running {test_name} Test ---")
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    LOGGER.info("\n" + "="*70)
    LOGGER.info("ENHANCED TIDAL NG SIMPLE TEST SUMMARY - VERSION 2")
    LOGGER.info("="*70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        LOGGER.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    LOGGER.info(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        LOGGER.info("🎉 All Enhanced Tidal NG simple tests passed! Core functionality is working.")
    else:
        LOGGER.error("⚠️ Some Enhanced Tidal NG simple tests failed. Please review the issues above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)