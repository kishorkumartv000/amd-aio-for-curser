from bot import CMD
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

import bot.helpers.translations as lang

from ..settings import bot_set
from ..helpers.buttons.settings import *
from ..helpers.database.pg_impl import set_db
from ..helpers.message import send_message, edit_message, check_user, fetch_user_details



@Client.on_message(filters.command(CMD.SETTINGS))
async def settings(c, message):
    if await check_user(message.from_user.id, restricted=True):
        user = await fetch_user_details(message)
        await send_message(user, lang.s.INIT_SETTINGS_PANEL, markup=main_menu())


@Client.on_callback_query(filters.regex(pattern=r"^corePanel"))
async def core_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            lang.s.CORE_PANEL,
            core_buttons()
        )


# New: Rclone settings panel
@Client.on_callback_query(filters.regex(pattern=r"^rclonePanel"))
async def rclone_panel_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        await edit_message(
            cb.message,
            "Rclone Settings",
            rclone_buttons()
        )

# Simple in-memory flag to accept next document as rclone.conf
_import_waiting = set()

@Client.on_callback_query(filters.regex(pattern=r"^rcloneImport"))
async def rclone_import_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        _import_waiting.add(cb.from_user.id)
        await edit_message(cb.message, "Please send your rclone.conf as a document now.")

@Client.on_message(filters.document)
async def handle_rclone_conf_upload(client, message: Message):
    try:
        user_id = message.from_user.id if message.from_user else None
        if user_id not in _import_waiting:
            return
        if not message.document:
            return
        # Only accept a file named rclone.conf or any .conf
        filename = (message.document.file_name or '').lower()
        if 'rclone' not in filename and not filename.endswith('.conf'):
            return
        # Download to a temp path and move to ./rclone.conf
        temp_path = await client.download_media(message, file_name='rclone.conf.tmp')
        import os
        if os.path.exists('rclone.conf'):
            os.remove('rclone.conf')
        os.replace(temp_path, 'rclone.conf')
        _import_waiting.discard(user_id)
        await send_message(message, "✅ rclone.conf imported successfully.")
    except Exception:
        try:
            await send_message(message, "❌ Failed to import rclone.conf.")
        except Exception:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^rcloneDelete"))
async def rclone_delete_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        import os
        try:
            if os.path.exists('rclone.conf'):
                os.remove('rclone.conf')
            # Refresh panel regardless
            await rclone_panel_cb(client, cb)
        except Exception:
            await edit_message(cb.message, "❌ Failed to delete rclone.conf", markup=rclone_buttons())

@Client.on_callback_query(filters.regex(pattern=r"^rcloneListRemotes"))
async def rclone_list_remotes_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        import asyncio
        import os
        if not os.path.exists('rclone.conf'):
            return await edit_message(cb.message, "rclone.conf not found.", markup=rclone_buttons())
        # Run rclone listremotes using our config
        try:
            proc = await asyncio.create_subprocess_shell(
                'rclone listremotes --config ./rclone.conf | cat',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out, err = await proc.communicate()
            if proc.returncode == 0:
                remotes = out.decode().strip() or "(no remotes)"
                await edit_message(cb.message, f"Available remotes:\n<code>{remotes}</code>", markup=rclone_buttons())
            else:
                await edit_message(cb.message, f"Failed to list remotes:\n<code>{err.decode().strip()}</code>", markup=rclone_buttons())
        except Exception as e:
            await edit_message(cb.message, f"Error: {e}", markup=rclone_buttons())

@Client.on_callback_query(filters.regex(pattern=r"^rcloneSend"))
async def rclone_send_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        import os
        if not os.path.exists('rclone.conf'):
            return await edit_message(cb.message, "rclone.conf not found.", markup=rclone_buttons())
        # Send the file as document
        try:
            await send_message(cb, './rclone.conf', 'doc')
        except Exception:
            await edit_message(cb.message, "❌ Failed to send rclone.conf", markup=rclone_buttons())

@Client.on_callback_query(filters.regex(pattern=r"^rcloneSelectRemote"))
async def rclone_select_remote_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        import asyncio, os
        if not os.path.exists('rclone.conf'):
            return await edit_message(cb.message, "rclone.conf not found.", markup=rclone_buttons())
        try:
            proc = await asyncio.create_subprocess_shell(
                'rclone listremotes --config ./rclone.conf | cat',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out, err = await proc.communicate()
            if proc.returncode != 0:
                return await edit_message(cb.message, f"Failed to list remotes:\n<code>{err.decode().strip()}</code>", markup=rclone_buttons())
            remotes = [r.strip(':') for r in out.decode().splitlines() if r.strip()]
            if not remotes:
                return await edit_message(cb.message, "No remotes configured.", markup=rclone_buttons())
            # Build buttons for each remote
            from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
            rows = []
            for r in remotes:
                rows.append([InlineKeyboardButton(r, callback_data=f"rcloneApplyRemote|{r}")])
            rows.append([InlineKeyboardButton("Cancel", callback_data="rclonePanel")])
            return await edit_message(cb.message, "Select remote:", markup=InlineKeyboardMarkup(rows))
        except Exception as e:
            return await edit_message(cb.message, f"Error: {e}", markup=rclone_buttons())

@Client.on_callback_query(filters.regex(pattern=r"^rcloneApplyRemote\|"))
async def rclone_apply_remote_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            remote = cb.data.split('|', 1)[1]
            # Preserve current path
            suffix = getattr(bot_set, 'rclone_dest_path', '')
            bot_set.rclone_remote = remote
            if bot_set.rclone_remote:
                bot_set.rclone_dest = f"{bot_set.rclone_remote}:{suffix}" if suffix else f"{bot_set.rclone_remote}:"
            else:
                bot_set.rclone_dest = ''
            set_db.set_variable('RCLONE_REMOTE', bot_set.rclone_remote)
            set_db.set_variable('RCLONE_DEST', bot_set.rclone_dest)
            await rclone_panel_cb(client, cb)
        except Exception:
            await edit_message(cb.message, "❌ Failed to set remote", markup=rclone_buttons())

# Capture destination path via next text message after tapping the button
_dest_path_waiting = set()

@Client.on_callback_query(filters.regex(pattern=r"^rcloneSetDestPath"))
async def rclone_set_dest_path_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        _dest_path_waiting.add(cb.from_user.id)
        await edit_message(cb.message, "Send destination path suffix (e.g., AppleMusic or AppleMusic/alac). Empty to use remote root.")

@Client.on_message(filters.text)
async def handle_dest_path_text(client, message: Message):
    try:
        user_id = message.from_user.id if message.from_user else None
        if user_id not in _dest_path_waiting:
            return
        text = (message.text or '').strip()
        # Update bot_set and DB
        bot_set.rclone_dest_path = text
        # Build final
        remote = getattr(bot_set, 'rclone_remote', '')
        if remote:
            final = f"{remote}:{text}" if text else f"{remote}:"
        else:
            final = text
        bot_set.rclone_dest = final
        set_db.set_variable('RCLONE_DEST_PATH', text)
        set_db.set_variable('RCLONE_DEST', final)
        _dest_path_waiting.discard(user_id)
        await send_message(message, f"✅ Destination set to: <code>{final or '(unset)'}</code>")
    except Exception:
        try:
            await send_message(message, "❌ Failed to set destination path.")
        except Exception:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^rcloneScope"))
async def rclone_scope_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        # Toggle between FILE and FOLDER
        current = getattr(bot_set, 'rclone_copy_scope', 'FILE').upper()
        next_value = 'FOLDER' if current == 'FILE' else 'FILE'
        bot_set.rclone_copy_scope = next_value
        set_db.set_variable('RCLONE_COPY_SCOPE', next_value)
        try:
            await rclone_panel_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^upload"))
async def upload_mode_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        modes = ['Local', 'Telegram']
        modes_count = 2
        if bot_set.rclone:
            modes.append('RCLONE')
            modes_count+=1

        current = modes.index(bot_set.upload_mode)
        nexti = (current + 1) % modes_count
        bot_set.upload_mode = modes[nexti]
        set_db.set_variable('UPLOAD_MODE', modes[nexti])
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^vidUploadType"))
async def video_upload_type_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            # toggle
            bot_set.video_as_document = not bool(getattr(bot_set, 'video_as_document', False))
            set_db.set_variable('VIDEO_AS_DOCUMENT', bot_set.video_as_document)
        except Exception:
            pass
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^linkOption"))
async def link_option_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        options = ['False', 'Index', 'RCLONE', 'Both']
        current = options.index(bot_set.link_options)
        nexti = (current + 1) % 4
        bot_set.link_options = options[nexti]
        set_db.set_variable('RCLONE_LINK_OPTIONS', options[nexti])
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^albArt"))
async def alb_art_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        art_post = bot_set.art_poster
        art_post = False if art_post else True
        bot_set.art_poster = art_post
        set_db.set_variable('ART_POSTER', art_post)
        try:
            await core_cb(client, cb)
        except:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^playCONC"))
async def playlist_conc_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        play_conc = bot_set.playlist_conc
        play_conc = False if play_conc else True
        bot_set.playlist_conc = play_conc
        set_db.set_variable('PLAYLIST_CONCURRENT', play_conc)
        try:
            await core_cb(client, cb)
        except:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^artBATCH"))
async def artist_conc_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        artist_batch = bot_set.artist_batch
        artist_batch = False if artist_batch else True
        bot_set.artist_batch = artist_batch
        set_db.set_variable('ARTIST_BATCH_UPLOAD', artist_batch)
        try:
            await core_cb(client, cb)
        except:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^sortPlay"))
async def playlist_sort_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        sort = bot_set.playlist_sort
        sort = False if sort else True
        bot_set.playlist_sort = sort
        set_db.set_variable('PLAYLIST_SORT', sort)
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^playZip"))
async def playlist_zip_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        option = bot_set.playlist_zip
        option = False if option else True
        bot_set.playlist_zip = option
        set_db.set_variable('PLAYLIST_ZIP', option)
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^sortLinkPlay"))
async def playlist_disable_zip_link(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        option = bot_set.disable_sort_link
        option = False if option else True
        bot_set.disable_sort_link = option
        set_db.set_variable('PLAYLIST_LINK_DISABLE', option)
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^artZip"))
async def artist_zip_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        option = bot_set.artist_zip
        option = False if option else True
        bot_set.artist_zip = option
        set_db.set_variable('ARTIST_ZIP', option)
        try:
            await core_cb(client, cb)
        except:
            pass


@Client.on_callback_query(filters.regex(pattern=r"^albZip"))
async def album_zip_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        option = bot_set.album_zip
        option = False if option else True
        bot_set.album_zip = option
        set_db.set_variable('ALBUM_ZIP', option)
        try:
            await core_cb(client, cb)
        except:
            pass



#--------------------

# COMMON

#--------------------
@Client.on_callback_query(filters.regex(pattern=r"^main_menu"))
async def main_menu_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            await edit_message(cb.message, lang.s.INIT_SETTINGS_PANEL, markup=main_menu())
        except:
            pass

@Client.on_callback_query(filters.regex(pattern=r"^close"))
async def close_cb(client, cb:CallbackQuery):
    if await check_user(cb.from_user.id, restricted=True):
        try:
            await client.delete_messages(
                chat_id=cb.message.chat.id,
                message_ids=cb.message.id
            )
        except:
            pass

@Client.on_message(filters.command(CMD.BAN))
async def ban(client:Client, msg:Message):
    if await check_user(msg.from_user.id, restricted=True):
        try:
            id = int(msg.text.split(" ", maxsplit=1)[1])
        except:
            await send_message(msg, lang.s.BAN_AUTH_FORMAT)
            return

        user = False if str(id).startswith('-100') else True
        if user:
            if id in bot_set.auth_users:
                bot_set.auth_users.remove(id)
                set_db.set_variable('AUTH_USERS', str(bot_set.auth_users))
            else: await send_message(msg, lang.s.USER_DOEST_EXIST)
        else:
            if id in bot_set.auth_chats:
                bot_set.auth_chats.remove(id)
                set_db.set_variable('AUTH_CHATS', str(bot_set.auth_chats))
            else: await send_message(msg, lang.s.USER_DOEST_EXIST)
        await send_message(msg, lang.s.BAN_ID)
        

@Client.on_message(filters.command(CMD.AUTH))
async def auth(client:Client, msg:Message):
    if await check_user(msg.from_user.id, restricted=True):
        try:
            id = int(msg.text.split(" ", maxsplit=1)[1])
        except:
            await send_message(msg, lang.s.BAN_AUTH_FORMAT)
            return

        user = False if str(id).startswith('-100') else True
        if user:
            if id not in bot_set.auth_users:
                bot_set.auth_users.append(id)
                set_db.set_variable('AUTH_USERS', str(bot_set.auth_users))
            else: await send_message(msg, lang.s.USER_EXIST)
        else:
            if id not in bot_set.auth_chats:
                bot_set.auth_chats.append(id)
                set_db.set_variable('AUTH_CHATS', str(bot_set.auth_chats))
            else: await send_message(msg, lang.s.USER_EXIST)
        await send_message(msg, lang.s.AUTH_ID)


@Client.on_message(filters.command(CMD.LOG))
async def send_log(client:Client, msg:Message):
    if await check_user(msg.from_user.id, restricted=True):
        user = await fetch_user_details(msg)
        await send_message(
            user, 
            './bot/bot_logs.log',
            'doc'
        )
