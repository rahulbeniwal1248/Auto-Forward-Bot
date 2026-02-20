import asyncio
import logging
from collections import defaultdict, deque

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError

from SilentXForward import database
from config import BUFFER_DELAY, FORWARD_DELAY_SECONDS, MAX_QUEUE_RETRIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

message_queue: asyncio.Queue = asyncio.Queue()
message_buffer = defaultdict(list)
buffer_tasks = {}
forward_runtime_state = {"paused": False}
recent_signatures = defaultdict(lambda: deque(maxlen=2000))


def set_forwarding_paused(paused: bool):
    forward_runtime_state["paused"] = bool(paused)


def is_forwarding_paused() -> bool:
    return forward_runtime_state.get("paused", False)


def get_forward_runtime_stats() -> dict:
    buffered_messages = sum(len(items) for items in message_buffer.values())
    return {
        "paused": is_forwarding_paused(),
        "queue_size": message_queue.qsize(),
        "active_album_buffers": len(buffer_tasks),
        "buffered_messages": buffered_messages,
    }


def _message_type(message):
    if message.text:
        return "texts"
    if message.document:
        return "documents"
    if message.video:
        return "videos"
    if message.photo:
        return "photos"
    if message.audio:
        return "audios"
    if message.voice:
        return "voices"
    if message.animation:
        return "animations"
    if message.sticker:
        return "stickers"
    return "texts"


def _message_signature(message):
    if message.document:
        return f"doc:{message.document.file_unique_id}"
    if message.video:
        return f"vid:{message.video.file_unique_id}"
    if message.photo:
        return f"pho:{message.photo.file_unique_id}"
    if message.audio:
        return f"aud:{message.audio.file_unique_id}"
    if message.voice:
        return f"voc:{message.voice.file_unique_id}"
    if message.animation:
        return f"ani:{message.animation.file_unique_id}"
    if message.sticker:
        return f"stk:{message.sticker.file_unique_id}"
    if message.text:
        return f"txt:{message.text.strip()}"
    return f"msg:{message.chat.id}:{message.id}"


def _allowed_by_settings(message, settings):
    return settings.get(_message_type(message), True)


def _is_duplicate(user_id, message, settings):
    if not settings.get("skip_duplicate", False):
        return False

    sig = _message_signature(message)
    history = recent_signatures[user_id]
    if sig in history:
        return True
    history.append(sig)
    return False


async def handle_flood(func, **kwargs):
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            return await func(**kwargs)
        except FloodWait as e:
            logger.warning("FloodWait detected. Sleeping for %ss.", e.value)
            await asyncio.sleep(e.value + 1)
        except RPCError as e:
            retry_count += 1
            logger.error("RPCError (attempt %s/%s): %s", retry_count, max_retries, e)
            if retry_count >= max_retries:
                raise
            await asyncio.sleep(2**retry_count)
        except Exception as e:
            retry_count += 1
            logger.error("Unexpected error (attempt %s/%s): %s", retry_count, max_retries, e)
            if retry_count >= max_retries:
                raise
            await asyncio.sleep(2**retry_count)

    raise RuntimeError(f"Failed after {max_retries} retries")


async def forward_single_message(client, message, chat_id, user_id, settings):
    try:
        if _is_duplicate(user_id, message, settings):
            logger.info("Skipping duplicate for user %s, message %s", user_id, message.id)
            return True

        if settings.get("forward_tag", False):
            await handle_flood(
                client.forward_messages,
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_ids=message.id,
            )
        else:
            await handle_flood(
                client.copy_message,
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=message.id,
            )

        logger.info("Forwarded message %s from %s to %s", message.id, message.chat.id, chat_id)
        return True
    except Exception as e:
        logger.error("Error forwarding message %s to %s: %s", message.id, chat_id, e)
        return False


async def forward_buffered_messages(client, messages, chat_id, user_id, settings):
    try:
        sorted_messages = sorted(messages, key=lambda m: m.id)
        success_count = 0

        for msg in sorted_messages:
            if await forward_single_message(client, msg, chat_id, user_id, settings):
                success_count += 1
                await asyncio.sleep(FORWARD_DELAY_SECONDS)

        logger.info("Forwarded %s/%s buffered messages to %s", success_count, len(messages), chat_id)
        return success_count == len(messages)

    except Exception as e:
        logger.error("Error forwarding buffered messages to %s: %s", chat_id, e)
        return False


async def process_queue(client):
    while True:
        payload = None
        try:
            payload = await message_queue.get()
            if not payload:
                continue

            messages, target_ids, retry_count, user_id = payload
            settings = await database.get_user_settings(user_id)
            failed_targets = []

            for chat_id in target_ids:
                try:
                    success = await forward_buffered_messages(client, messages, chat_id, user_id, settings)
                    if not success:
                        failed_targets.append(chat_id)
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    logger.warning("FloodWait for chat %s. Waiting %ss", chat_id, e.value)
                    await asyncio.sleep(e.value + 1)
                    failed_targets.append(chat_id)
                except Exception as e:
                    logger.error("Error forwarding to %s: %s", chat_id, e)
                    failed_targets.append(chat_id)

            if failed_targets:
                if retry_count < MAX_QUEUE_RETRIES:
                    await message_queue.put((messages, failed_targets, retry_count + 1, user_id))
                else:
                    logger.error("Dropping %s target(s) after max retry (%s)", len(failed_targets), MAX_QUEUE_RETRIES)

        except Exception as e:
            logger.error("Queue processing error: %s", e)
            await asyncio.sleep(1)
        finally:
            if payload is not None:
                message_queue.task_done()


async def start_processor(client):
    task = asyncio.create_task(process_queue(client))
    logger.info("Message processor started")
    return {"main_processor": task}


async def process_buffered_messages(buffer_key):
    await asyncio.sleep(BUFFER_DELAY)

    messages = message_buffer.pop(buffer_key, [])
    buffer_tasks.pop(buffer_key, None)
    if not messages:
        return

    source_chat_id = messages[0].chat.id

    try:
        mappings = await database.get_all_targets_for_source(source_chat_id)
        if not mappings:
            return

        for mapping in mappings:
            user_id = mapping.get("user_id")
            target_ids = mapping.get("target_ids", [])
            if not user_id or not target_ids:
                continue

            settings = await database.get_user_settings(user_id)
            filtered_messages = [m for m in messages if _allowed_by_settings(m, settings)]
            if filtered_messages:
                await message_queue.put((filtered_messages, target_ids, 0, user_id))

    except Exception as e:
        logger.error("Error processing buffered messages: %s", e)


def _is_bot_origin(message):
    return bool((getattr(message, "from_user", None) and message.from_user.is_bot) or getattr(message, "via_bot", None))


@Client.on_message((filters.channel & filters.incoming) | (filters.channel & filters.outgoing))
async def forward_content(client, message):
    try:
        source_chat_id = message.chat.id

        if is_forwarding_paused():
            return

        if _is_bot_origin(message):
            logger.info("Detected bot-originated channel message %s in %s", message.id, source_chat_id)

        if message.media_group_id:
            buffer_key = (source_chat_id, message.media_group_id)
            message_buffer[buffer_key].append(message)

            if buffer_key in buffer_tasks:
                buffer_tasks[buffer_key].cancel()
            buffer_tasks[buffer_key] = asyncio.create_task(process_buffered_messages(buffer_key))
            return

        mappings = await database.get_all_targets_for_source(source_chat_id)
        if not mappings:
            return

        for mapping in mappings:
            user_id = mapping.get("user_id")
            target_ids = mapping.get("target_ids", [])
            if not user_id or not target_ids:
                continue

            settings = await database.get_user_settings(user_id)
            if _allowed_by_settings(message, settings):
                await message_queue.put(([message], target_ids, 0, user_id))

    except Exception as e:
        logger.error("Error in forward_content handler: %s", e, exc_info=True)
