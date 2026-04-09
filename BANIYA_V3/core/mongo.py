from random import randint
from time import time

from pymongo import AsyncMongoClient

from BANIYA_V3 import config, logger, userbot


class MongoDB:
    def __init__(self):
        # Primary DB
        self.mongo = AsyncMongoClient(config.MONGO_URL, serverSelectionTimeoutMS=12500)
        self.db = self.mongo[config.DB_NAME]

        # Secondary Media DB
        self.media_mongo = AsyncMongoClient(config.DB_URI, serverSelectionTimeoutMS=12500)
        self.mediadb = self.media_mongo["arcapi"]["medias"]

        # Cache & collections
        self.cache = self.db.cache
        self.usersdb = self.db.users
        self.chatsdb = self.db.chats
        self.authdb = self.db.auth
        self.assistantdb = self.db.assistant
        self.langdb = self.db.lang

        # Runtime cache
        self.users = []
        self.chats = []
        self.auth = {}
        self.assistant = {}
        self.lang = {}
        self.admin_list = {}
        self.active_calls = {}
        self.loop = {}
        self.blacklisted = []
        self.cmd_delete = []
        self.admin_play = []
        self.logger = False

    async def connect(self):
        try:
            start = time()
            await self.mongo.admin.command("ping")
            logger.info(f"Primary DB connected ({time() - start:.2f}s)")

            start = time()
            await self.media_mongo.admin.command("ping")
            logger.info(f"Media DB connected ({time() - start:.2f}s)")

            await self.load_cache()

        except Exception as e:
            raise SystemExit(f"Database connection failed: {e}")

    async def close(self):
        await self.mongo.close()
        await self.media_mongo.close()
        logger.info("Database closed")

       # ------------------ LANGUAGE METHODS ------------------

    async def get_lang(self, chat_id: int) -> str:
        if chat_id not in self.lang:
            doc = await self.langdb.find_one({"_id": chat_id})
            self.lang[chat_id] = doc["lang"] if doc else config.LANG_CODE
        return self.lang[chat_id]

    async def set_lang(self, chat_id: int, lang_code: str):
        await self.langdb.update_one(
            {"_id": chat_id},
            {"$set": {"lang": lang_code}},
            upsert=True,
        )
        self.lang[chat_id] = lang_code
        
    # ------------------ MIGRATION FIXED ------------------

    async def migrate_coll(self):
        logger.info("Migrating users and chats...")

        seen_users, seen_chats = set(), set()
        musers, mchats = [], []

        # USERS
        users = []
        users.extend([u async for u in self.usersdb.find()])
        users.extend([u async for u in self.db.tgusersdb.find()])

        for u in users:
            try:
                uid = int(u.get("_id") or u.get("user_id"))
                if uid not in seen_users:
                    seen_users.add(uid)
                    musers.append({"_id": uid})
            except:
                continue

        # Safe replace users
        await self.usersdb.delete_many({})
        if musers:
            await self.usersdb.insert_many(musers, ordered=False)

        # CHATS
        async for c in self.chatsdb.find():
            try:
                cid = int(c.get("_id") or c.get("chat_id"))
                if cid not in seen_chats:
                    seen_chats.add(cid)
                    mchats.append({"_id": cid})
            except:
                continue

        await self.chatsdb.delete_many({})
        if mchats:
            await self.chatsdb.insert_many(mchats, ordered=False)

        # ✅ SAFE FLAG (NO DUPLICATE ERROR)
        await self.cache.update_one(
            {"_id": "migrated"},
            {"$set": {"done": True}},
            upsert=True
        )

        logger.info("Migration completed ✅")

    async def load_cache(self):
        doc = await self.cache.find_one({"_id": "migrated"})
        if not doc:
            await self.migrate_coll()

        self.chats.extend([c["_id"] async for c in self.chatsdb.find()])
        self.users.extend([u["_id"] async for u in self.usersdb.find()])

        logger.info("Cache loaded ✅")

    # ------------------ BASIC METHODS ------------------

    async def add_user(self, user_id: int):
        if user_id not in self.users:
            self.users.append(user_id)
            try:
                await self.usersdb.insert_one({"_id": user_id})
            except:
                pass

    async def add_chat(self, chat_id: int):
        if chat_id not in self.chats:
            self.chats.append(chat_id)
            try:
                await self.chatsdb.insert_one({"_id": chat_id})
            except:
                pass

    async def get_users(self):
        return self.users

    async def get_chats(self):
        return self.chats

           # ------------------ BLACKLIST METHODS ------------------

    async def get_blacklisted(self, chat: bool = False) -> list[int]:
        if chat:
            doc = await self.cache.find_one({"_id": "bl_chats"})
            return doc.get("chat_ids", []) if doc else []
        
        doc = await self.cache.find_one({"_id": "bl_users"})
        return doc.get("user_ids", []) if doc else []

    async def add_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            await self.cache.update_one(
                {"_id": "bl_chats"},
                {"$addToSet": {"chat_ids": chat_id}},
                upsert=True
            )
        else:
            await self.cache.update_one(
                {"_id": "bl_users"},
                {"$addToSet": {"user_ids": chat_id}},
                upsert=True
            )

    async def del_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            await self.cache.update_one(
                {"_id": "bl_chats"},
                {"$pull": {"chat_ids": chat_id}}
            )
        else:
            await self.cache.update_one(
                {"_id": "bl_users"},
                {"$pull": {"user_ids": chat_id}}
            )
            
    # ------------------ SUDO METHODS ------------------

    async def get_sudoers(self) -> list[int]:
        doc = await self.cache.find_one({"_id": "sudoers"})
        return doc.get("user_ids", []) if doc else []

    async def add_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True
        )

    async def del_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"},
            {"$pull": {"user_ids": user_id}}
        )
        
    # ------------------ AUTH ------------------

    async def add_auth(self, chat_id, user_id):
        await self.authdb.update_one(
            {"_id": chat_id},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True
        )

    async def is_auth(self, chat_id, user_id):
        doc = await self.authdb.find_one({"_id": chat_id})
        return user_id in (doc.get("user_ids", []) if doc else [])

    # ------------------ ASSISTANT ------------------

    async def set_assistant(self, chat_id):
        num = randint(1, len(userbot.clients))
        await self.assistantdb.update_one(
            {"_id": chat_id},
            {"$set": {"num": num}},
            upsert=True
        )
        self.assistant[chat_id] = num
        return num

    async def get_assistant(self, chat_id):
        if chat_id not in self.assistant:
            doc = await self.assistantdb.find_one({"_id": chat_id})
            self.assistant[chat_id] = doc["num"] if doc else await self.set_assistant(chat_id)
        return self.assistant[chat_id]

    # ------------------ LOGGER ------------------

    async def get_logger(self):
        doc = await self.cache.find_one({"_id": "logger"})
        return doc.get("status", False) if doc else False

    async def set_logger(self, status: bool):
        await self.cache.update_one(
            {"_id": "logger"},
            {"$set": {"status": status}},
            upsert=True
        )
