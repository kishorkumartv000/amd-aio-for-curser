import bot.helpers.translations as lang

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config

from ..settings import bot_set
from ..helpers.buttons.settings import *
from ..helpers.database.pg_impl import set_db
from ..helpers.tidal.tidal_api import tidalapi

from ..helpers.message import edit_message, check_user


@Client.on_callback_query(filters.regex(pattern=r"^providerPanel"))
async def provider_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        buttons = []
        # Always show Apple Music button
        buttons.append([
            InlineKeyboardButton("🍎 Apple Music", callback_data="appleP")
        ])

        # Conditionally show other providers
        if bot_set.qobuz:
            buttons.append([
                InlineKeyboardButton(lang.s.QOBUZ, callback_data="qbP")
            ])
        if bot_set.deezer:
            buttons.append([
                InlineKeyboardButton(lang.s.DEEZER, callback_data="dzP")
            ])
        if bot_set.can_enable_tidal:
            buttons.append([
                InlineKeyboardButton(lang.s.TIDAL, callback_data="tdP")
            ])

        buttons += [
            [InlineKeyboardButton(lang.s.MAIN_MENU_BUTTON, callback_data="main_menu")],
            [InlineKeyboardButton(lang.s.CLOSE_BUTTON, callback_data="close")]
        ]
        
        await edit_message(
            cb.message,
            lang.s.PROVIDERS_PANEL,
            InlineKeyboardMarkup(buttons)
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


#----------------
# QOBUZ
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^qbP"))
async def qobuz_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        quality = {5: 'MP3 320', 6: 'Lossless', 7: '24B<=96KHZ', 27: '24B>96KHZ'}
        current = bot_set.qobuz.quality
        quality[current] = quality[current] + '✅'
        try:
            await edit_message(
                cb.message,
                lang.s.QOBUZ_QUALITY_PANEL,
                markup=qb_button(quality)
            )
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^qbQ"))
async def qobuz_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        qobuz = {5: 'MP3 320', 6: 'Lossless', 7: '24B<=96KHZ', 27: '24B>96KHZ'}
        to_set = cb.data.split('_')[1]
        bot_set.qobuz.quality = list(filter(lambda x: qobuz[x] == to_set, qobuz))[0]
        set_db.set_variable('QOBUZ_QUALITY', bot_set.qobuz.quality)
        await qobuz_cb(c, cb)


#----------------
# TIDAL
#----------------
@Client.on_callback_query(filters.regex(pattern=r"^tdP"))
async def tidal_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            lang.s.TIDAL_PANEL,
            tidal_buttons()  # auth and quality button (quality button only if auth already done)
        )


@Client.on_callback_query(filters.regex(pattern=r"^tdQ"))
async def tidal_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        qualities = {
            'LOW': 'LOW',
            'HIGH': 'HIGH',
            'LOSSLESS': 'LOSSLESS'
        }
        if tidalapi.mobile_hires:
            qualities['HI_RES'] = 'MAX'
        qualities[tidalapi.quality] += '✅'

        await edit_message(
            cb.message,
            lang.s.TIDAL_PANEL,
            tidal_quality_button(qualities)
        )


@Client.on_callback_query(filters.regex(pattern=r"^tdSQ"))
async def tidal_set_quality_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        to_set = cb.data.split('_')[1]

        if to_set == 'spatial':
            # options = ['OFF', 'ATMOS AC3 JOC', 'ATMOS AC4', 'Sony 360RA']
            # assuming atleast tv session is added
            options = ['OFF', 'ATMOS AC3 JOC']
            if tidalapi.mobile_atmos:
                options.append('ATMOS AC4')
            if tidalapi.mobile_atmos or tidalapi.mobile_hires:
                options.append('Sony 360RA')

            try:
                current = options.index(tidalapi.spatial)
            except:
                current = 0

            nexti = (current + 1) % 4
            tidalapi.spatial = options[nexti]
            set_db.set_variable('TIDAL_SPATIAL', options[nexti])
        else:
            qualities = {'LOW': 'LOW', 'HIGH': 'HIGH', 'LOSSLESS': 'LOSSLESS', 'HI_RES': 'MAX'}
            to_set = list(filter(lambda x: qualities[x] == to_set, qualities))[0]
            tidalapi.quality = to_set
            set_db.set_variable('TIDAL_QUALITY', to_set)

        await tidal_quality_cb(c, cb)


# show login button if not logged in
# show refresh button in case logged in exist (both tv and mobile)
@Client.on_callback_query(filters.regex(pattern=r"^tdAuth"))
async def tidal_auth_cb(c, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        sub = tidalapi.sub_type
        hires = True if tidalapi.mobile_hires else False
        atmos = True if tidalapi.mobile_atmos else False
        tv = True if tidalapi.tv_session else False

        await edit_message(
            cb.message,
            lang.s.TIDAL_AUTH_PANEL.format(sub, hires, atmos, tv),
            tidal_auth_buttons()
        )


@Client.on_callback_query(filters.regex(pattern=r"^tdLogin"))
async def tidal_login_cb(c: Client, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        auth_url, err = await tidalapi.get_tv_login_url()
        if err:
            return await c.answer_callback_query(
                cb.id,
                err,
                True
            )

        await edit_message(
            cb.message,
            lang.s.TIDAL_AUTH_URL.format(auth_url),
            tidal_auth_buttons()
        )

        sub, err = await tidalapi.login_tv()
        if err:
            return await edit_message(
                cb.message,
                lang.s.ERR_LOGIN_TIDAL_TV_FAILED.format(err),
                tidal_auth_buttons()
            )
        if sub:
            bot_set.tidal = tidalapi
            bot_set.clients.append(tidalapi)

            await bot_set.save_tidal_login(tidalapi.tv_session)

            hires = True if tidalapi.mobile_hires else False
            atmos = True if tidalapi.mobile_atmos else False
            tv = True if tidalapi.tv_session else False
            await edit_message(
                cb.message,
                lang.s.TIDAL_AUTH_PANEL.format(sub, hires, atmos, tv) + '\n' + lang.s.TIDAL_AUTH_SUCCESSFULL,
                tidal_auth_buttons()
            )


@Client.on_callback_query(filters.regex(pattern=r"^tdRemove"))
async def tidal_remove_login_cb(c: Client, cb: CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        set_db.set_variable("TIDAL_AUTH_DATA", 0, True, None)

        tidalapi.tv_session = None
        tidalapi.mobile_atmos = None
        tidalapi.mobile_hires = None
        tidalapi.sub_type = None
        tidalapi.saved = []

        await tidalapi.session.close()
        bot_set.tidal = None

        await c.answer_callback_query(
            cb.id,
            lang.s.TIDAL_REMOVED_SESSION,
            True
        )

        await tidal_auth_cb(c, cb)