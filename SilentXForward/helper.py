import logging
import os
from SilentXForward import database
from SilentXForward.forward import get_forward_runtime_stats, set_forwarding_paused
from pyrogram import Client, filters, enums
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_owner_id() -> int:
    value = os.environ.get("OWNER_ID", "0")
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid OWNER_ID %r. Falling back to 0.", value)
        return 0


OWNER_ID = _get_owner_id()
user_sessions = {}

START_TEXT = """<b>👋 Hello! I am SilentXForward Bot.</b>

<b>Available Commands:</b>
/start - Start the bot
/help - Show help menu
/commands - Show all commands
/about - Show bot info
/forward - Start forwarding setup wizard
/set &lt;source_id&gt; &lt;target_id&gt; - Add source to target mapping
/remove_target &lt;source_id&gt; &lt;target_id&gt; - Remove one target from source
/remove_source &lt;source_id&gt; - Remove complete source mapping
/list - Show your mappings
/clear - Clear all your mappings
/unequify - Remove duplicate target IDs
/settings - Show your settings summary
/status - Show advanced runtime status
/cancel - Cancel ongoing wizard
/reset - Reset your settings
/donate - Support developers
/resetall - Reset all users settings (owner only)
/broadcast &lt;message&gt; - Broadcast message (owner only)
/restart - Restart bot (owner only)
/pauseforward - Pause forwarding (owner only)
/resumeforward - Resume forwarding (owner only)
/stats - Show forwarding runtime stats (owner only)

<b>Maintained By:</b> <a href="https://t.me/SilentXBotz">SilentXBotz</a>
"""

HELP_TEXT = """<b>ℹ️ Help Menu</b>

I Am An Auto-Forward Bot. I Forward All Message Types From Source Channels To Target Channels.

<b>Commands:</b>
/start - Check if I am alive
/help - Show this help message
/commands - Show all commands
/about - Show information about me
/forward - Start interactive forwarding setup
/set &lt;source_id&gt; &lt;target_id&gt; - Add target to source
/remove_target &lt;source_id&gt; &lt;target_id&gt; - Remove a target from source
/remove_source &lt;source_id&gt; - Remove source mapping
/list - View all mapped channels
/clear - Clear all mappings
/unequify - Remove duplicate target IDs
/settings - Show your current setup
/status - Show advanced runtime status
/cancel - Cancel ongoing forwarding setup
/reset - Reset all your settings
/donate - Support the developer
/resetall - Reset all users (owner only)
/broadcast &lt;message&gt; - Send message to users (owner only)
/restart - Restart bot process (owner only)
/pauseforward - Pause forwarding (owner only)
/resumeforward - Resume forwarding (owner only)
/stats - Show forwarding runtime stats (owner only)

<b>How to use:</b>
1. Add Me To Source Channels And Target Channels As Admin.
2. Use <code>/forward</code> wizard OR <code>/set &lt;source_id&gt; &lt;target_id&gt;</code>.
3. I will automatically forward all incoming channel messages.

<b>Channel:</b> @SilentXBotz
"""

ABOUT_TEXT = """<b>🤖 About SilentXForward</b>

<b>Name:</b> SilentXForward
<b>Version:</b> 2.1
<b>Channel:</b> <a href="https://t.me/SilentXBotz">SilentXBotz</a>
<b>Repository:</b> <a href="https://github.com/NBBotz/Auto-Forward-Bot">GitHub</a>
"""

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/SilentXBotz"),
            InlineKeyboardButton("🐱 GitHub", url="https://github.com/NBBotz/Auto-Forward-Bot")
        ]
    ]
)


def _status_icon(value: bool) -> str:
    return "✅" if value else "❌"


def build_settings_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🤖 Bots", callback_data="settings:bots") , InlineKeyboardButton("🏷 Channels", callback_data="settings:channels")],
            [InlineKeyboardButton("✒️ Caption", callback_data="settings:caption"), InlineKeyboardButton("🗄 MongoDB", callback_data="settings:mongodb")],
            [InlineKeyboardButton("🕵️ Filters", callback_data="settings:filters"), InlineKeyboardButton("🔲 Button", callback_data="settings:button")],
            [InlineKeyboardButton("🧪 Extra Settings", callback_data="settings:extra")],
            [InlineKeyboardButton("≪ Back", callback_data="settings:back")],
        ]
    )


def build_filter_keyboard(settings):
    rows = [
        ("🏷 Forward tag", "forward_tag"),
        ("🖍 Texts", "texts"),
        ("📁 Documents", "documents"),
        ("🎞 Videos", "videos"),
        ("📷 Photos", "photos"),
        ("🎧 Audios", "audios"),
        ("🎙 Voices", "voices"),
        ("🎭 Animations", "animations"),
        ("🃏 Stickers", "stickers"),
        ("▶️ Skip duplicate", "skip_duplicate"),
    ]

    keyboard = []
    for label, key in rows:
        keyboard.append([
            InlineKeyboardButton(label, callback_data="noop"),
            InlineKeyboardButton(_status_icon(settings.get(key, False)), callback_data=f"toggle:{key}"),
        ])

    keyboard.append([InlineKeyboardButton("≪ Back", callback_data="settings:menu")])
    return InlineKeyboardMarkup(keyboard)


def is_owner(user_id: int) -> bool:
    return OWNER_ID and user_id == OWNER_ID


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply(
        text=START_TEXT,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=BUTTONS,
        disable_web_page_preview=True
    )


@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply(
        text=HELP_TEXT,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=BUTTONS,
        disable_web_page_preview=True
    )




@Client.on_message(filters.command("commands") & filters.private)
async def commands_command(client, message):
    await message.reply(
        text=HELP_TEXT,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=BUTTONS,
        disable_web_page_preview=True
    )


@Client.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    await message.reply(
        text=ABOUT_TEXT,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=BUTTONS,
        disable_web_page_preview=True
    )


@Client.on_message(filters.command("forward") & filters.private)
async def forward_command(client, message: Message):
    user_sessions[message.from_user.id] = {"state": "await_source"}
    await message.reply_text(
        "<b>✅ Forward setup started.</b>\n\n"
        "Step 1/2: Send source channel ID or username.\n"
        "Example: <code>-1001234567890</code>\n\n"
        "Use <code>/cancel</code> to stop.",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("unequify") & filters.private)
async def unequify_command(client, message: Message):
    removed = await database.remove_duplicate_targets(message.from_user.id)
    await message.reply_text(
        f"<b>✅ Done:</b> Removed <b>{removed}</b> duplicate target entries.",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("settings") & filters.private)
async def settings_command(client, message: Message):
    runtime = get_forward_runtime_stats()
    text = (
        "<b>⚙️ Change your settings as your wish</b>\n\n"
        f"Forwarding: <b>{'Paused' if runtime['paused'] else 'Active'}</b>"
    )
    await message.reply_text(
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=build_settings_keyboard(),
    )


@Client.on_callback_query(filters.regex(r"^(settings:|toggle:|noop$)"))
async def settings_callbacks(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "noop":
        await callback_query.answer("Use right-side button to toggle.", show_alert=False)
        return

    if data == "settings:menu":
        runtime = get_forward_runtime_stats()
        await callback_query.message.edit_text(
            "<b>⚙️ Change your settings as your wish</b>\n\n"
            f"Forwarding: <b>{'Paused' if runtime['paused'] else 'Active'}</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=build_settings_keyboard(),
        )
        await callback_query.answer()
        return

    if data == "settings:filters":
        settings = await database.get_user_settings(user_id)
        await callback_query.message.edit_text(
            "<b>💠 CUSTOM FILTERS 💠</b>\n\n"
            "Configure the type of messages which you want forward.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=build_filter_keyboard(settings),
        )
        await callback_query.answer()
        return

    if data.startswith("toggle:"):
        key = data.split(":", 1)[1]
        settings = await database.toggle_user_setting(user_id, key)
        await callback_query.message.edit_reply_markup(reply_markup=build_filter_keyboard(settings))
        await callback_query.answer(f"{key.replace('_', ' ').title()} updated")
        return

    if data in {"settings:bots", "settings:channels", "settings:caption", "settings:mongodb", "settings:button", "settings:extra"}:
        await callback_query.answer("Feature section placeholder. Filter settings are active now.", show_alert=False)
        return

    if data == "settings:back":
        await callback_query.message.delete()
        await callback_query.answer()
        return


@Client.on_message(filters.command("status") & filters.private)
async def status_command(client, message: Message):
    mappings = await database.get_user_mappings(message.from_user.id)
    total_targets = sum(len(item.get("target_ids", [])) for item in mappings)
    runtime = get_forward_runtime_stats()
    wizard_active = "Yes" if message.from_user.id in user_sessions else "No"

    await message.reply_text(
        f"<b>📈 Advanced Status</b>\n\n"
        f"• Sources: <b>{len(mappings)}</b>\n"
        f"• Targets: <b>{total_targets}</b>\n"
        f"• Wizard active: <b>{wizard_active}</b>\n"
        f"• Forward paused: <b>{'Yes' if runtime['paused'] else 'No'}</b>\n"
        f"• Queue size: <b>{runtime['queue_size']}</b>\n"
        f"• Album buffers: <b>{runtime['active_album_buffers']}</b>\n"
        f"• Buffered messages: <b>{runtime['buffered_messages']}</b>",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_command(client, message: Message):
    user_sessions.pop(message.from_user.id, None)
    await message.reply_text(
        "<b>✅ Cancelled.</b>\nAny ongoing interaction is cancelled. Scheduled mapping remains unchanged.",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("reset") & filters.private)
async def reset_command(client, message: Message):
    user_sessions.pop(message.from_user.id, None)
    deleted = await database.clear_all_mappings(message.from_user.id)
    await message.reply_text(
        f"<b>♻️ Reset complete.</b> Removed <b>{deleted}</b> source mapping(s).",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("donate") & filters.private)
async def donate_command(client, message: Message):
    await message.reply_text(
        "<b>❤️ Thank you for supporting the developers!</b>\n"
        "Donate/contact: <a href='https://t.me/SilentXBotz'>@SilentXBotz</a>",
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )


@Client.on_message(filters.command("resetall") & filters.private)
async def resetall_command(client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply_text("<b>❌ Owner only command.</b>", parse_mode=enums.ParseMode.HTML)
        return

    deleted = await database.clear_everything()
    await message.reply_text(
        f"<b>✅ Global reset complete.</b> Removed <b>{deleted}</b> mapping document(s).",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply_text("<b>❌ Owner only command.</b>", parse_mode=enums.ParseMode.HTML)
        return

    if len(message.command) < 2:
        await message.reply_text("<b>Usage:</b> <code>/broadcast your message</code>", parse_mode=enums.ParseMode.HTML)
        return

    text = message.text.split(maxsplit=1)[1]
    user_ids = await database.get_all_user_ids()
    sent = 0
    for user_id in user_ids:
        try:
            await client.send_message(user_id, text)
            sent += 1
        except Exception as e:
            logger.warning("Broadcast failed for %s: %s", user_id, e)

    await message.reply_text(
        f"<b>📣 Broadcast complete.</b> Sent to <b>{sent}</b>/<b>{len(user_ids)}</b> users.",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("pauseforward") & filters.private)
async def pause_forward_command(client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply_text("<b>❌ Owner only command.</b>", parse_mode=enums.ParseMode.HTML)
        return

    set_forwarding_paused(True)
    await message.reply_text("<b>⏸️ Forwarding paused.</b>", parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command("resumeforward") & filters.private)
async def resume_forward_command(client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply_text("<b>❌ Owner only command.</b>", parse_mode=enums.ParseMode.HTML)
        return

    set_forwarding_paused(False)
    await message.reply_text("<b>▶️ Forwarding resumed.</b>", parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply_text("<b>❌ Owner only command.</b>", parse_mode=enums.ParseMode.HTML)
        return

    runtime = get_forward_runtime_stats()
    await message.reply_text(
        f"<b>🧠 Runtime Stats</b>\n\n"
        f"• Forward paused: <b>{'Yes' if runtime['paused'] else 'No'}</b>\n"
        f"• Queue size: <b>{runtime['queue_size']}</b>\n"
        f"• Active album buffers: <b>{runtime['active_album_buffers']}</b>\n"
        f"• Buffered messages: <b>{runtime['buffered_messages']}</b>",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("restart") & filters.private)
async def restart_command(client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply_text("<b>❌ Owner only command.</b>", parse_mode=enums.ParseMode.HTML)
        return

    await message.reply_text("<b>♻️ Restarting bot...</b>", parse_mode=enums.ParseMode.HTML)
    os._exit(0)


@Client.on_message(filters.command("set") & filters.private)
async def set_channels(client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 3:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/set &lt;source_id&gt; &lt;target_id&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/set -1001234567890 -1009876543210</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    source = message.command[1]
    target = message.command[2]

    try:
        source_chat = await client.get_chat(source)
        target_chat = await client.get_chat(target)

        source_id = source_chat.id
        target_id = target_chat.id

        result = await database.add_target_to_source(
            user_id,
            source_id,
            target_id,
            source_chat.title,
            target_chat.title
        )

        if result == "created":
            await message.reply_text(
                f"<b>✅ New Source Created:</b>\n\n"
                f"<b>📥 Source:</b> {source_chat.title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"<b>📤 Target:</b> {target_chat.title}\n"
                f"   <code>{target_id}</code>\n\n"
                f"🎉 Messages Will Be Forwarded!",
                parse_mode=enums.ParseMode.HTML
            )
        elif result == "added":
            await message.reply_text(
                f"<b>✅ Target Added:</b>\n\n"
                f"<b>📥 Source:</b> {source_chat.title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"<b>📤 New Target:</b> {target_chat.title}\n"
                f"   <code>{target_id}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<b>⚠️ Already Exists:</b>\n\n"
                f"This Target Is Already Set For This Source!",
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error:</b> {e}\n\n"
            "Make sure:\n"
            "• Bot is admin in both channels\n"
            "• Channel IDs are correct",
            parse_mode=enums.ParseMode.HTML
        )


@Client.on_message(filters.private & filters.text & ~filters.command([
    "start", "help", "commands", "about", "forward", "unequify", "settings", "status", "cancel", "reset", "donate",
    "resetall", "broadcast", "pauseforward", "resumeforward", "stats", "restart", "set", "remove_target", "remove_source", "list", "clear"
]))
async def forward_wizard_input(client, message: Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)
    if not session:
        return

    text = message.text.strip()

    if session.get("state") == "await_source":
        session["source"] = text
        session["state"] = "await_target"
        await message.reply_text(
            "<b>Step 2/2:</b> Now send target channel ID or username.",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    if session.get("state") == "await_target":
        source = session.get("source")
        target = text
        user_sessions.pop(user_id, None)

        try:
            source_chat = await client.get_chat(source)
            target_chat = await client.get_chat(target)
            result = await database.add_target_to_source(
                user_id,
                source_chat.id,
                target_chat.id,
                source_chat.title,
                target_chat.title,
            )

            if result in ("created", "added"):
                await message.reply_text(
                    f"<b>✅ Forward mapping saved.</b>\n\n"
                    f"<b>Source:</b> {source_chat.title} (<code>{source_chat.id}</code>)\n"
                    f"<b>Target:</b> {target_chat.title} (<code>{target_chat.id}</code>)",
                    parse_mode=enums.ParseMode.HTML,
                )
            else:
                await message.reply_text(
                    "<b>⚠️ This mapping already exists.</b>",
                    parse_mode=enums.ParseMode.HTML,
                )
        except Exception as e:
            await message.reply_text(
                f"<b>❌ Could not save mapping:</b> {e}",
                parse_mode=enums.ParseMode.HTML,
            )


@Client.on_message(filters.command("remove_target") & filters.private)
async def remove_target_channel(client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 3:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/remove_target &lt;source_id&gt; &lt;target_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    source_input = message.command[1]
    target_input = message.command[2]

    try:
        source_chat = await client.get_chat(source_input)
        source_id = source_chat.id
        source_title = source_chat.title

        target_chat = await client.get_chat(target_input)
        target_id = target_chat.id
        target_title = target_chat.title

        result = await database.remove_target_from_source(user_id, source_id, target_id)

        if result == "removed":
            await message.reply_text(
                f"<b>✅ Target Removed Successfully!</b>\n\n"
                f"<b>📥 Source:</b> {source_title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"<b>🗑️ Target:</b> {target_title}\n"
                f"   <code>{target_id}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<b>⚠️ Not Found:</b>\nNo Mapping Exists For This Source-target Pair.",
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error:</b> {e}",
            parse_mode=enums.ParseMode.HTML
        )


@Client.on_message(filters.command("remove_source") & filters.private)
async def remove_channel(client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/remove_source &lt;source_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    source = message.command[1]

    try:
        chat = await client.get_chat(source)
        source_id = chat.id

        removed = await database.remove_source(user_id, source_id)

        if removed:
            await message.reply_text(
                f"<b>✅ Removed:</b>\n\n"
                f"<b>📥 Source:</b> {chat.title}\n"
                f"   <code>{source_id}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<b>⚠️ Not Found:</b>\nNo Targets Exists For <b>{chat.title}</b>",
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error:</b> {e}",
            parse_mode=enums.ParseMode.HTML
        )


@Client.on_message(filters.command("list") & filters.private)
async def list_mappings(client, message: Message):
    user_id = message.from_user.id

    mappings = await database.get_user_mappings(user_id)

    if not mappings:
        await message.reply_text(
            "<b>❌ No mappings found!</b>\n\n"
            "Use <code>/set &lt;source_id&gt; &lt;target_id&gt;</code> to create one.",
            parse_mode=enums.ParseMode.HTML
        )
        return

    text = "<b>📊 Your Channel Mappings:</b>\n\n"

    for idx, mapping in enumerate(mappings, 1):
        source_id = mapping['source_id']
        target_ids = mapping.get('target_ids', [])

        try:
            source_chat = await client.get_chat(source_id)
            text += f"<b>{idx}. 📥 {source_chat.title}</b>\n"
            text += f"   <code>{source_id}</code>\n"
            text += f"   ⤵️ <b>Targets ({len(target_ids)}):</b>\n"

            for target_id in target_ids:
                try:
                    target_chat = await client.get_chat(target_id)
                    text += f"   • {target_chat.title} (<code>{target_id}</code>)\n"
                except Exception:
                    text += f"   • <code>{target_id}</code> (Unable to fetch)\n"

            text += "\n"
        except Exception:
            text += f"<b>{idx}.</b> <code>{source_id}</code> (Unable to fetch)\n"
            text += f"   Targets: {len(target_ids)}\n\n"

    text += f"<b>Total Sources:</b> {len(mappings)}"

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command("clear") & filters.private)
async def clear_all(client, message: Message):
    user_id = message.from_user.id

    count = await database.clear_all_mappings(user_id)

    if count > 0:
        await message.reply_text(
            f"<b>✅ Cleared {count} source(s)!</b>\n\n"
            f"All Your Mappings Have Been Removed.",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            "<b>❌ You Don't Have Any Mappings To Clear!</b>",
            parse_mode=enums.ParseMode.HTML
        )
