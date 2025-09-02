import bot.helpers.translations as lang

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config

from ..settings import bot_set
from ..helpers.buttons.settings import *
from ..helpers.database.pg_impl import set_db

from ..helpers.message import edit_message, check_user


@Client.on_callback_query(filters.regex(pattern=r"^providerPanel"))
async def provider_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            lang.s.PROVIDERS_PANEL,
            providers_button()
        )


#----------------
# APPLE MUSIC
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^appleP"))
async def apple_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        formats = {
            'alac': 'ALAC',
            'atmos': 'Dolby Atmos'
        }
        current = Config.APPLE_DEFAULT_FORMAT
        formats[current] += ' ✅'
        
        await edit_message(
            cb.message,
            "🍎 **Apple Music Settings**\n\n"
            "Use the buttons below to configure formats, quality, and manage the Wrapper service.\n\n"
            "**Available Formats:**\n"
            "- ALAC: Apple Lossless Audio Codec\n"
            "- Dolby Atmos: Spatial audio experience\n\n"
            "**Current Default Format:**",
            apple_button(formats)
        )


@Client.on_callback_query(filters.regex(pattern=r"^appleF"))
async def apple_format_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        format_type = cb.data.split('_')[1]
        # Update configuration
        set_db.set_variable('APPLE_DEFAULT_FORMAT', format_type)
        Config.APPLE_DEFAULT_FORMAT = format_type
        await apple_cb(c, cb)


@Client.on_callback_query(filters.regex(pattern=r"^appleQ"))
async def apple_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        qualities = {
            'alac': ['192000', '256000', '320000'],
            'atmos': ['2768', '3072', '3456']
        }
        current_format = Config.APPLE_DEFAULT_FORMAT
        current_quality = getattr(Config, f'APPLE_{current_format.upper()}_QUALITY')
        
        # Create quality buttons
        buttons = []
        for quality in qualities[current_format]:
            label = f"{quality} kbps"
            if quality == current_quality:
                label += " ✅"
            buttons.append([InlineKeyboardButton(label, callback_data=f"appleSQ_{current_format}_{quality}")])
        
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="appleP")])
        
        await edit_message(
            cb.message,
            f"⚙️ **{current_format.upper()} Quality Settings**\n\n"
            "Select the maximum quality for downloads:",
            InlineKeyboardMarkup(buttons)
        )


@Client.on_callback_query(filters.regex(pattern=r"^appleSQ"))
async def apple_set_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        _, format_type, quality = cb.data.split('_')
        # Update configuration
        set_db.set_variable(f'APPLE_{format_type.upper()}_QUALITY', quality)
        setattr(Config, f'APPLE_{format_type.upper()}_QUALITY', quality)
        await apple_quality_cb(c, cb)


# Apple Wrapper: Stop with confirmation
@Client.on_callback_query(filters.regex(pattern=r"^appleStop$"))
async def apple_wrapper_stop_cb(c: Client, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        # Ask for confirmation
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm Stop", callback_data="appleStopConfirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="appleP")]
        ])
        await edit_message(cb.message, "Are you sure you want to stop the Wrapper?", buttons)


@Client.on_callback_query(filters.regex(pattern=r"^appleStopConfirm$"))
async def apple_wrapper_stop_confirm_cb(c: Client, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        from config import Config as Cfg
        import asyncio
        await c.answer_callback_query(cb.id, "Stopping wrapper...", show_alert=False)
        try:
            proc = await asyncio.create_subprocess_exec(
                "/bin/bash", Cfg.APPLE_WRAPPER_STOP_PATH,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            out = stdout.decode(errors='ignore')
            err = stderr.decode(errors='ignore')
            text = "⏹️ Wrapper stop result:\n\n" + (out.strip() or err.strip() or "Done.")
        except Exception as e:
            text = f"❌ Failed to stop wrapper: {e}"
        await edit_message(cb.message, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="appleP")]]))


# Apple Wrapper: Setup flow entry (asks for username then password)
@Client.on_callback_query(filters.regex(pattern=r"^appleSetup$"))
async def apple_wrapper_setup_cb(c: Client, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        # Explain flow
        await edit_message(cb.message, "We'll set up the Wrapper. Please send your Apple ID username.\n\nYou can cancel anytime by sending /cancel.", InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="appleP")]]))
        # Mark state for this user
        from ..helpers.state import conversation_state
        # Also clear any other pending flows for safety
        await conversation_state.clear(cb.from_user.id)
        await conversation_state.start(cb.from_user.id, "apple_setup_username", {"chat_id": cb.message.chat.id, "msg_id": cb.message.id})


# Apple-only build: remove Qobuz/Tidal handlers

#----------------
# QOBUZ
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^qobuzP"))
async def qobuz_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        qualities = {
            5: f"MP3 320 {'✅' if bot_set.qobuz.quality == 5 else ''}",
            6: f"FLAC 16-bit {'✅' if bot_set.qobuz.quality == 6 else ''}",
            7: f"FLAC 24-bit/<=96kHz {'✅' if bot_set.qobuz.quality == 7 else ''}",
            27: f"FLAC 24-bit/>96kHz {'✅' if bot_set.qobuz.quality == 27 else ''}"
        }
        await edit_message(
            cb.message,
            lang.s.QOBUZ_QUALITY_PANEL,
            qb_button(qualities)
        )

@Client.on_callback_query(filters.regex(pattern=r"^qbQ_"))
async def qobuz_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        quality_map = {
            "MP3 320": 5,
            "FLAC 16-bit": 6,
            "FLAC 24-bit/<=96kHz": 7,
            "FLAC 24-bit/>96kHz": 27
        }
        quality_str = cb.data.split('_')[1]
        quality_int = quality_map.get(quality_str)

        bot_set.qobuz.quality = quality_int
        set_db.set_variable('QOBUZ_QUALITY', quality_int)
        await qobuz_cb(c, cb)

#----------------
# DEEZER
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^deezerP"))
async def deezer_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
         await edit_message(
            cb.message,
            "Deezer settings are configured via environment variables (DEEZER_ARL). No in-bot settings are available.",
            InlineKeyboardMarkup(main_button + close_button)
        )

#----------------
# TIDAL
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^tidalP"))
async def tidal_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            lang.s.TIDAL_PANEL,
            tidal_buttons()
        )

@Client.on_callback_query(filters.regex(pattern=r"^tidalQuality"))
async def tidal_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        qualities = {
            'LOW': f"LOW {'✅' if bot_set.tidal.quality == 'LOW' else ''}",
            'HIGH': f"HIGH {'✅' if bot_set.tidal.quality == 'HIGH' else ''}",
            'LOSSLESS': f"LOSSLESS {'✅' if bot_set.tidal.quality == 'LOSSLESS' else ''}",
            'HI_RES': f"HI_RES {'✅' if bot_set.tidal.quality == 'HI_RES' else ''}"
        }
        await edit_message(
            cb.message,
            "Select Tidal Quality",
            tidal_quality_button(qualities)
        )

@Client.on_callback_query(filters.regex(pattern=r"^tidalQ_"))
async def tidal_set_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        quality = cb.data.split('_')[1]
        bot_set.tidal.quality = quality
        set_db.set_variable('TIDAL_QUALITY', quality)
        await tidal_quality_cb(c, cb)

@Client.on_callback_query(filters.regex(pattern=r"^tidalAuth"))
async def tidal_auth_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            lang.s.TIDAL_AUTH_PANEL.format(
                'Yes' if bot_set.tidal.check_login() else 'No',
                'Yes' if Config.TIDAL_MOBILE_TOKEN else 'No',
                'Yes' if Config.TIDAL_ATMOS_MOBILE_TOKEN else 'No',
                'Yes' if Config.TIDAL_TV_TOKEN else 'No'
            ),
            tidal_auth_buttons()
        )

@Client.on_callback_query(filters.regex(pattern=r"^tidalLogin"))
async def tidal_login_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        if not Config.TIDAL_TV_TOKEN:
            await c.answer_callback_query(cb.id, lang.s.WARNING_NO_TIDAL_TOKEN, show_alert=True)
            return

        login_url, _ = await bot_set.tidal.login_get_url()
        await edit_message(cb.message, lang.s.TIDAL_AUTH_URL.format(login_url), None)
        # Placeholder for checking login status
        # In a real scenario, you'd poll or have the user confirm.
        await asyncio.sleep(10) # Simulate waiting time
        if await bot_set.tidal.login_check_url():
            await bot_set.save_tidal_login(bot_set.tidal.get_session())
            await c.answer_callback_query(cb.id, lang.s.TIDAL_AUTH_SUCCESSFULL, show_alert=True)
        else:
            await c.answer_callback_query(cb.id, lang.s.ERR_LOGIN_TIDAL_TV_FAILED.format("Timeout"), show_alert=True)
        await tidal_auth_cb(c, cb)


@Client.on_callback_query(filters.regex(pattern=r"^tidalRemove"))
async def tidal_remove_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        if os.path.exists("./tidal_session.json"):
            os.remove("./tidal_session.json")
        await c.answer_callback_query(cb.id, lang.s.TIDAL_REMOVED_SESSION, show_alert=True)
        await tidal_auth_cb(c, cb)

@Client.on_callback_query(filters.regex(pattern=r"^tidalRefresh"))
async def tidal_refresh_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await bot_set.login_tidal()
        await c.answer_callback_query(cb.id, "Tidal session refreshed.", show_alert=True)
        await tidal_auth_cb(c, cb)