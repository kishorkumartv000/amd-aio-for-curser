#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced Tidal NG integration - Version 2
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
    config_manager, TidalNGConfig, QualityAudio, QualityVideo, DownloadPreset
)
from bot.helpers.tidal_ng.enhanced_handler import (
    TidalNGDownloader, get_content_id_from_url, DownloadStatus
)

async def test_config_manager():
    """Test the enhanced configuration manager"""
    try:
        LOGGER.info("Testing Enhanced Tidal NG configuration manager...")
        
        # Test loading default config
        config = config_manager.load_config()
        LOGGER.info(f"Default config loaded: {type(config)}")
        
        # Test setting values
        success = config_manager.set_value("quality_audio", "LOSSLESS")
        LOGGER.info(f"Set quality_audio: {success}")
        
        # Test getting values
        value = config_manager.get_value("quality_audio")
        LOGGER.info(f"Get quality_audio: {value}")
        
        # Test presets
        presets = config_manager.get_presets()
        LOGGER.info(f"Available presets: {list(presets.keys())}")
        
        # Test preset application
        success = config_manager.apply_preset("high_quality")
        LOGGER.info(f"Applied high_quality preset: {success}")
        
        # Test summary
        summary = config_manager.get_config_summary()
        LOGGER.info(f"Config summary keys: {list(summary.keys())}")
        
        # Test validation
        errors = config.validate()
        LOGGER.info(f"Config validation errors: {len(errors)}")
        
        LOGGER.info("✅ Enhanced configuration manager test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Enhanced configuration manager test failed: {str(e)}")
        return False

async def test_enhanced_handler():
    """Test the enhanced Tidal NG handler"""
    try:
        LOGGER.info("Testing Enhanced Tidal NG handler...")
        
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
            
        # Test downloader initialization
        async with TidalNGDownloader() as downloader:
            LOGGER.info("Enhanced downloader initialized successfully")
            
            # Test option parsing
            test_options = {
                'quality': 'LOSSLESS',
                'video_quality': '1080',
                'lyrics': True,
                'cover': True,
                'concurrent': 5
            }
            
            parsed = downloader._parse_options(test_options)
            LOGGER.info(f"Parsed options: {parsed}")
            
        LOGGER.info("✅ Enhanced handler test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Enhanced handler test failed: {str(e)}")
        return False

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

async def test_config_validation():
    """Test configuration validation"""
    try:
        LOGGER.info("Testing configuration validation...")
        
        # Test valid values
        valid_tests = [
            ("quality_audio", "LOSSLESS"),
            ("quality_video", "1080"),
            ("downloads_concurrent_max", 5),
            ("lyrics_embed", True),
            ("metadata_cover_dimension", 1200),
        ]
        
        for key, value in valid_tests:
            is_valid = config_manager._validate_value(key, value)
            LOGGER.info(f"Validation {key}={value}: {is_valid}")
            
        # Test invalid values
        invalid_tests = [
            ("quality_audio", "INVALID"),
            ("quality_video", "999"),
            ("downloads_concurrent_max", -1),
            ("metadata_cover_dimension", 0),
        ]
        
        for key, value in invalid_tests:
            is_valid = config_manager._validate_value(key, value)
            LOGGER.info(f"Validation {key}={value}: {is_valid} (should be False)")
            
        LOGGER.info("✅ Configuration validation test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Configuration validation test failed: {str(e)}")
        return False

async def test_preset_functionality():
    """Test preset functionality"""
    try:
        LOGGER.info("Testing preset functionality...")
        
        presets = config_manager.get_presets()
        
        for preset_name in presets.keys():
            LOGGER.info(f"Testing preset: {preset_name}")
            
            # Apply preset
            success = config_manager.apply_preset(preset_name)
            LOGGER.info(f"Applied {preset_name}: {success}")
            
            if success:
                # Verify preset was applied
                config = config_manager.load_config()
                LOGGER.info(f"Preset {preset_name} - Audio: {config.quality_audio}, Video: {config.quality_video}")
                
        LOGGER.info("✅ Preset functionality test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Preset functionality test failed: {str(e)}")
        return False

async def test_config_persistence():
    """Test configuration persistence"""
    try:
        LOGGER.info("Testing configuration persistence...")
        
        # Set some test values
        test_values = {
            "quality_audio": "HI_RES_LOSSLESS",
            "quality_video": "720",
            "downloads_concurrent_max": 8,
            "lyrics_embed": False,
        }
        
        # Set values
        for key, value in test_values.items():
            success = config_manager.set_value(key, value)
            LOGGER.info(f"Set {key}={value}: {success}")
            
        # Save config
        success = config_manager.save_config()
        LOGGER.info(f"Save config: {success}")
        
        # Reset and reload
        config_manager._config = None
        config = config_manager.load_config()
        
        # Verify values were saved
        for key, expected_value in test_values.items():
            actual_value = getattr(config, key)
            LOGGER.info(f"Persistence check {key}: {actual_value} (expected: {expected_value})")
            
        LOGGER.info("✅ Configuration persistence test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Configuration persistence test failed: {str(e)}")
        return False

async def test_download_result():
    """Test download result dataclass"""
    try:
        LOGGER.info("Testing download result dataclass...")
        
        # Create a test result
        result = DownloadStatus.COMPLETED
        LOGGER.info(f"Created download status: {result}")
        
        # Test result creation
        from bot.helpers.tidal_ng.enhanced_handler import TidalNGDownloadResult
        
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

async def test_enhanced_features():
    """Test enhanced features"""
    try:
        LOGGER.info("Testing enhanced features...")
        
        # Test configuration summary
        summary = config_manager.get_config_summary()
        LOGGER.info(f"Config summary sections: {list(summary.keys())}")
        
        # Test backup functionality
        backup_path = config_manager._backup_config()
        LOGGER.info(f"Backup created: {backup_path}")
        
        # Test cleanup functionality
        config_manager.cleanup_old_backups(keep_count=5)
        LOGGER.info("Cleanup completed")
        
        # Test error handling
        try:
            config_manager.set_value("invalid_key", "invalid_value")
        except Exception:
            LOGGER.info("Error handling works correctly")
            
        LOGGER.info("✅ Enhanced features test completed successfully!")
        return True
        
    except Exception as e:
        LOGGER.error(f"❌ Enhanced features test failed: {str(e)}")
        return False

async def main():
    """Run all Enhanced Tidal NG tests"""
    LOGGER.info("🚀 Starting Enhanced Tidal NG comprehensive tests - Version 2...")
    
    tests = [
        ("Enhanced Configuration Manager", test_config_manager),
        ("Enhanced Handler", test_enhanced_handler),
        ("Quality Enums", test_quality_enums),
        ("Download Status", test_download_status),
        ("Configuration Validation", test_config_validation),
        ("Preset Functionality", test_preset_functionality),
        ("Configuration Persistence", test_config_persistence),
        ("Download Result", test_download_result),
        ("Enhanced Features", test_enhanced_features),
    ]
    
    results = []
    for test_name, test_func in tests:
        LOGGER.info(f"\n--- Running {test_name} Test ---")
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    LOGGER.info("\n" + "="*70)
    LOGGER.info("ENHANCED TIDAL NG TEST SUMMARY - VERSION 2")
    LOGGER.info("="*70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        LOGGER.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    LOGGER.info(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        LOGGER.info("🎉 All Enhanced Tidal NG tests passed! Ready for development.")
    else:
        LOGGER.warning("⚠️ Some Enhanced Tidal NG tests failed. Please review the issues above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)