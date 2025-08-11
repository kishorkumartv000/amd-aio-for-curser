import os
import json
import base64
import requests
import subprocess

import bot.helpers.translations as lang

from config import Config
from bot.logger import LOGGER

from .helpers.database.pg_impl import set_db, download_history

from .helpers.translations import lang_available


# Helper functions
def __getvalue__(var):
    value, _ = set_db.get_variable(var)
    return value if value else False

def __encrypt_string__(string):
    s = bytes(string, 'utf-8')
    s = base64.b64encode(s)
    return s

def __decrypt_string__(string):
    try:
        s = base64.b64decode(string)
        s = s.decode()
        return s
    except:
        return string

class BotSettings:
    def __init__(self):
        # Apple-only build: remove other providers
        self.deezer = False
        self.qobuz = False
        self.can_enable_tidal = False
        self.admins = Config.ADMINS
        self.apple = None  # Apple Music settings placeholder
        self.bot_username = (Config.BOT_USERNAME or "").lstrip("@")

        self.set_language()

        db_users, _ = set_db.get_variable('AUTH_USERS')
        self.auth_users = json.loads(db_users) if db_users else []
        db_chats, _ = set_db.get_variable('AUTH_CHATS')
        self.auth_chats = json.loads(db_chats) if db_chats else []

        self.rclone = False
        self.check_upload_mode()
        self.initialize_apple()

        spam, _ = set_db.get_variable('ANTI_SPAM')
        self.anti_spam = spam if spam else 'OFF'

        self.bot_public = __getvalue__('BOT_PUBLIC')
        self.art_poster = __getvalue__('ART_POSTER')
        self.playlist_sort = __getvalue__('PLAYLIST_SORT')
        self.disable_sort_link = __getvalue__('PLAYLIST_LINK_DISABLE')
        self.artist_batch = __getvalue__('ARTIST_BATCH_UPLOAD')
        self.playlist_conc = __getvalue__('PLAYLIST_CONCURRENT')
        
        link_option, _ = set_db.get_variable('RCLONE_LINK_OPTIONS')
        self.link_options = link_option if self.rclone and link_option else 'False'

        self.album_zip = __getvalue__('ALBUM_ZIP')
        self.playlist_zip = __getvalue__('PLAYLIST_ZIP')
        self.artist_zip = __getvalue__('ARTIST_ZIP')

        self.clients = []
        self.download_history = download_history

    def check_upload_mode(self):
        """Determine upload mode based on configuration"""
        if os.path.exists('rclone.conf'):
            self.rclone = True
        elif Config.RCLONE_CONFIG:
            if Config.RCLONE_CONFIG.startswith('http'):
                try:
                    rclone = requests.get(Config.RCLONE_CONFIG, allow_redirects=True)
                    if rclone.status_code == 200:
                        with open('rclone.conf', 'wb') as f:
                            f.write(rclone.content)
                        self.rclone = True
                    else:
                        LOGGER.error(f"Rclone config download failed: HTTP {rclone.status_code}")
                except Exception as e:
                    LOGGER.error(f"Rclone config download error: {str(e)}")
            else:
                if os.path.exists(Config.RCLONE_CONFIG):
                    self.rclone = True
        
        db_upload, _ = set_db.get_variable('UPLOAD_MODE')
        if self.rclone and db_upload == 'RCLONE':
            self.upload_mode = 'RCLONE'
        elif db_upload == 'Telegram' or db_upload == 'Local':
            self.upload_mode = db_upload
        else:
            self.upload_mode = 'Local'

    def initialize_apple(self):
        """Initialize Apple Music settings"""
        self.apple = {
            'downloader_path': Config.DOWNLOADER_PATH,
            'installer_path': Config.INSTALLER_PATH,
            'format': __getvalue__('APPLE_DEFAULT_FORMAT') or Config.APPLE_DEFAULT_FORMAT,
            'alac_quality': int(__getvalue__('APPLE_ALAC_QUALITY') or Config.APPLE_ALAC_QUALITY),
            'atmos_quality': int(__getvalue__('APPLE_ATMOS_QUALITY') or Config.APPLE_ATMOS_QUALITY)
        }
        
        # Ensure downloader is installed
        if not os.path.exists(Config.DOWNLOADER_PATH):
            LOGGER.warning("Apple Music downloader not found! Attempting installation...")
            try:
                subprocess.run([Config.INSTALLER_PATH], check=True)
                LOGGER.info("Apple Music downloader installed successfully")
            except Exception as e:
                LOGGER.error(f"Apple Music installer failed: {str(e)}")

    # Apple-only build: remove other providers' login flows
    async def login_qobuz(self):
        return

    async def login_deezer(self):
        return

    async def login_tidal(self):
        return

    async def save_tidal_login(self, session):
        return

    def set_language(self):
        """Set bot language"""
        db_lang, _ = set_db.get_variable('BOT_LANGUAGE')
        self.bot_lang = db_lang if db_lang else 'en'

        for item in lang_available:
            if item.__language__ == self.bot_lang:
                lang.s = item
                break

bot_set = BotSettings()
