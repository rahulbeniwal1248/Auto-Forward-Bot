import config
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient(config.MONGO_URI)
db = mongo_client[config.DB_NAME]

channel_mappings = db['channel_mappings']
user_settings = db['user_settings']

async def get_user_mappings(user_id):
    cursor = channel_mappings.find({"user_id": user_id})
    return await cursor.to_list(length=None)

async def get_mapping_by_source(user_id, source_id):
    return await channel_mappings.find_one({
        "user_id": user_id,
        "source_id": source_id
    })

async def add_target_to_source(user_id, source_id, target_id, source_title, target_title):
    existing = await channel_mappings.find_one({
        "user_id": user_id,
        "source_id": source_id
    })
    
    if existing:
        if target_id not in existing.get('target_ids', []):
            await channel_mappings.update_one(
                {"user_id": user_id, "source_id": source_id},
                {
                    "$push": {"target_ids": target_id},
                    "$set": {"source_title": source_title}
                }
            )
            return "added"
        return "exists"
    else:
        await channel_mappings.insert_one({
            "user_id": user_id,
            "source_id": source_id,
            "target_ids": [target_id],
            "source_title": source_title
        })
        return "created"

async def remove_target_from_source(user_id, source_id, target_id):
    result = await channel_mappings.update_one(
        {"user_id": user_id, "source_id": source_id, "target_ids": {"$exists": True}},
        {"$pull": {"target_ids": target_id}}
    )
    
    if result.modified_count > 0:
        mapping = await channel_mappings.find_one({"user_id": user_id, "source_id": source_id})
        if not mapping or not mapping.get('target_ids') or len(mapping.get('target_ids', [])) == 0:
            await channel_mappings.delete_one({"user_id": user_id, "source_id": source_id})
        return "removed"
    return "not_found"
    

async def remove_source(user_id, source_id):
    result = await channel_mappings.delete_one({
        "user_id": user_id,
        "source_id": source_id
    })
    return result.deleted_count > 0

async def get_all_targets_for_source(source_id):
    cursor = channel_mappings.find({"source_id": source_id})
    mappings = await cursor.to_list(length=None)
    
    result = []
    for mapping in mappings:
        result.append({
            "user_id": mapping['user_id'],
            "target_ids": mapping.get('target_ids', [])
        })
    return result

async def clear_all_mappings(user_id):
    result = await channel_mappings.delete_many({"user_id": user_id})
    return result.deleted_count


async def remove_duplicate_targets(user_id):
    mappings = await get_user_mappings(user_id)
    removed_count = 0

    for mapping in mappings:
        targets = mapping.get("target_ids", [])
        unique_targets = list(dict.fromkeys(targets))
        duplicates = len(targets) - len(unique_targets)
        if duplicates > 0:
            await channel_mappings.update_one(
                {"_id": mapping["_id"]},
                {"$set": {"target_ids": unique_targets}}
            )
            removed_count += duplicates

    return removed_count


async def clear_everything():
    result = await channel_mappings.delete_many({})
    return result.deleted_count


async def get_all_user_ids():
    return await channel_mappings.distinct("user_id")


DEFAULT_USER_SETTINGS = {
    "forward_tag": False,
    "texts": True,
    "documents": True,
    "videos": True,
    "photos": True,
    "audios": True,
    "voices": True,
    "animations": True,
    "stickers": True,
    "skip_duplicate": False,
}


async def get_user_settings(user_id):
    settings = await user_settings.find_one({"user_id": user_id})
    if not settings:
        return DEFAULT_USER_SETTINGS.copy()

    merged = DEFAULT_USER_SETTINGS.copy()
    merged.update(settings.get("settings", {}))
    return merged


async def toggle_user_setting(user_id, key):
    if key not in DEFAULT_USER_SETTINGS:
        return await get_user_settings(user_id)

    current = await get_user_settings(user_id)
    current[key] = not current[key]

    await user_settings.update_one(
        {"user_id": user_id},
        {"$set": {"settings": current}},
        upsert=True,
    )
    return current
