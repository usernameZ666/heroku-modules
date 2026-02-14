# meta developer: @usernameZ666
# meta version: 1.0.0
# meta description: Автоответчик — реагирует на фразу от конкретного пользователя в нужных чатах

from .. import loader, utils
from telethon import events
import json


@loader.tds
class AutoResponderMod(loader.Module):
    """Автоответчик на фразу от конкретного пользователя"""

    strings = {
        "name": "AutoResponder",
        "enabled": "<b>✅ Автоответчик включён</b>",
        "disabled": "<b>❌ Автоответчик выключен</b>",
        "status_on": "🟢 Включён",
        "status_off": "🔴 Выключен",
        "status_msg": (
            "<b>📊 Статус AutoResponder:</b>\n\n"
            "<b>Состояние:</b> {state}\n"
            "<b>Пользователь ID:</b> <code>{user_id}</code>\n"
            "<b>Триггер:</b> <code>{trigger}</code>\n"
            "<b>Ответ:</b> <code>{reply}</code>\n"
            "<b>Режим:</b> <code>{mode}</code>\n"
            "<b>Чаты:</b> <code>{chats}</code>"
        ),
        "saved": "<b>✅ Настройки сохранены</b>",
        "usage_user": "<b>Использование:</b> <code>.aruser [ID]</code>",
        "usage_trigger": "<b>Использование:</b> <code>.artrigger [фраза]</code>",
        "usage_reply": "<b>Использование:</b> <code>.arreply [текст]</code>",
        "usage_chat": "<b>Использование:</b> <code>.archat [ID или 'all' или 'clear']</code>",
        "chats_cleared": "<b>✅ Список чатов очищен — бот слушает все чаты</b>",
        "chat_added": "<b>✅ Чат <code>{chat}</code> добавлен</b>",
        "chat_removed": "<b>✅ Чат <code>{chat}</code> удалён</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("user_id", 0, "ID пользователя за которым следим"),
            loader.ConfigValue("trigger", "", "Фраза-триггер"),
            loader.ConfigValue("reply", "", "Текст ответа"),
            loader.ConfigValue("match_mode", "contains", "Режим: exact или contains"),
            loader.ConfigValue("chat_ids", [], "Список ID чатов (пусто = все чаты)"),
            loader.ConfigValue("enabled", False, "Включён ли автоответчик"),
        )

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    def _is_match(self, text):
        trigger = self.config["trigger"].lower()
        text = text.strip().lower()
        if self.config["match_mode"] == "exact":
            return text == trigger
        return trigger in text

    async def _handler(self, event):
        if not self.config["enabled"]:
            return
        if not self.config["trigger"] or not self.config["reply"]:
            return

        sender = await event.get_sender()
        if not sender:
            return
        if sender.id != int(self.config["user_id"]):
            return

        chat_ids = self.config["chat_ids"]
        if chat_ids and event.chat_id not in [int(c) for c in chat_ids]:
            return

        text = event.message.text or ""
        if self._is_match(text):
            await event.reply(self.config["reply"])

    async def arenable_cmd(self, message):
        """Включить автоответчик"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings["enabled"])

    async def ardisable_cmd(self, message):
        """Выключить автоответчик"""
        self.config["enabled"] = False
        await utils.answer(message, self.strings["disabled"])

    async def arstatus_cmd(self, message):
        """Показать текущие настройки"""
        chat_ids = self.config["chat_ids"]
        await utils.answer(
            message,
            self.strings["status_msg"].format(
                state=self.strings["status_on"] if self.config["enabled"] else self.strings["status_off"],
                user_id=self.config["user_id"] or "не задан",
                trigger=self.config["trigger"] or "не задан",
                reply=self.config["reply"] or "не задан",
                mode=self.config["match_mode"],
                chats=", ".join(str(c) for c in chat_ids) if chat_ids else "все чаты",
            ),
        )

    async def aruser_cmd(self, message):
        """Установить ID пользователя: .aruser [ID]"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["usage_user"])
            return
        self.config["user_id"] = int(args.strip())
        await utils.answer(message, self.strings["saved"])

    async def artrigger_cmd(self, message):
        """Установить фразу-триггер: .artrigger [фраза]"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["usage_trigger"])
            return
        self.config["trigger"] = args.strip()
        await utils.answer(message, self.strings["saved"])

    async def arreply_cmd(self, message):
        """Установить текст ответа: .arreply [текст]"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["usage_reply"])
            return
        self.config["reply"] = args.strip()
        await utils.answer(message, self.strings["saved"])

    async def armode_cmd(self, message):
        """Переключить режим совпадения: exact или contains"""
        current = self.config["match_mode"]
        self.config["match_mode"] = "exact" if current == "contains" else "contains"
        await utils.answer(message, f"<b>Режим переключён на:</b> <code>{self.config['match_mode']}</code>")

    async def archat_cmd(self, message):
        """Управление чатами: .archat [ID] или .archat clear"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["usage_chat"])
            return

        args = args.strip()
        chat_ids = list(self.config["chat_ids"])

        if args == "clear":
            self.config["chat_ids"] = []
            await utils.answer(message, self.strings["chats_cleared"])
            return

        try:
            chat_id = int(args)
        except ValueError:
            await utils.answer(message, self.strings["usage_chat"])
            return

        if chat_id in chat_ids:
            chat_ids.remove(chat_id)
            self.config["chat_ids"] = chat_ids
            await utils.answer(message, self.strings["chat_removed"].format(chat=chat_id))
        else:
            chat_ids.append(chat_id)
            self.config["chat_ids"] = chat_ids
            await utils.answer(message, self.strings["chat_added"].format(chat=chat_id))

    async def watcher(self, message):
        """Отслеживает все входящие сообщения"""
        await self._handler(message)
