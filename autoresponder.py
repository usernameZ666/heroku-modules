# meta developer: @usernameZ666
# meta version: 2.0.0
# meta description: Автоответчик с поддержкой до 5 триггеров

from .. import loader, utils


@loader.tds
class AutoResponderMod(loader.Module):
    """Автоответчик с поддержкой до 5 триггеров"""

    strings = {
        "name": "AutoResponder",
        "enabled": "<b>✅ Автоответчик включён</b>",
        "disabled": "<b>❌ Автоответчик выключен</b>",
        "saved": "<b>✅ Триггер #{num} сохранён</b>",
        "cleared": "<b>🗑 Триггер #{num} удалён</b>",
        "cleared_all": "<b>🗑 Все триггеры удалены</b>",
        "list_empty": "<b>📋 Триггеров нет</b>",
        "list_header": "<b>📋 Список триггеров:</b>\n\n",
        "list_item": (
            "<b>#{num}</b>\n"
            "👤 Пользователь: <code>{user_id}</code>\n"
            "💬 Триггер: <code>{trigger}</code>\n"
            "📨 Ответ: <code>{reply}</code>\n"
            "🎯 Режим: <code>{mode}</code>\n"
            "💭 Чаты: <code>{chats}</code>\n\n"
        ),
        "max_triggers": "<b>❌ Максимум 5 триггеров. Удали один командой .ardel [номер]</b>",
        "usage_add": "<b>Использование:</b> <code>.aradd [user_id] | [триггер] | [ответ]</code>",
        "usage_del": "<b>Использование:</b> <code>.ardel [номер]</code>",
        "usage_chat": "<b>Использование:</b> <code>.archat [номер_триггера] [chat_id или clear]</code>",
        "not_found": "<b>❌ Триггер #{num} не найден</b>",
        "chat_added": "<b>✅ Чат <code>{chat}</code> добавлен в триггер #{num}</b>",
        "chat_cleared": "<b>✅ Чаты триггера #{num} очищены</b>",
        "status_on": "🟢 Включён",
        "status_off": "🔴 Выключен",
        "status": "<b>Состояние:</b> {state}\n<b>Активных триггеров:</b> {count}",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("triggers", [], "Список триггеров"),
            loader.ConfigValue("enabled", False, "Включён ли автоответчик"),
        )

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    def _is_match(self, text, trigger, mode):
        t = trigger.lower()
        text = text.strip().lower()
        if mode == "exact":
            return text == t
        return t in text

    async def _handler(self, event):
        if not self.config["enabled"]:
            return

        triggers = self.config["triggers"]
        if not triggers:
            return

        sender = await event.get_sender()
        if not sender:
            return

        text = event.message.text or ""

        for item in triggers:
            if sender.id != int(item.get("user_id", 0)):
                continue

            chat_ids = item.get("chat_ids", [])
            if chat_ids and event.chat_id not in [int(c) for c in chat_ids]:
                continue

            if self._is_match(text, item.get("trigger", ""), item.get("mode", "contains")):
                await event.reply(item.get("reply", ""))
                break

    async def arenable_cmd(self, message):
        """Включить автоответчик"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings["enabled"])

    async def ardisable_cmd(self, message):
        """Выключить автоответчик"""
        self.config["enabled"] = False
        await utils.answer(message, self.strings["disabled"])

    async def arstatus_cmd(self, message):
        """Статус автоответчика"""
        state = self.strings["status_on"] if self.config["enabled"] else self.strings["status_off"]
        count = len(self.config["triggers"])
        await utils.answer(message, self.strings["status"].format(state=state, count=count))

    async def aradd_cmd(self, message):
        """Добавить триггер: .aradd [user_id] | [триггер] | [ответ]"""
        args = utils.get_args_raw(message)
        if not args or "|" not in args:
            await utils.answer(message, self.strings["usage_add"])
            return

        parts = [p.strip() for p in args.split("|")]
        if len(parts) < 3:
            await utils.answer(message, self.strings["usage_add"])
            return

        triggers = list(self.config["triggers"])
        if len(triggers) >= 5:
            await utils.answer(message, self.strings["max_triggers"])
            return

        try:
            user_id = int(parts[0])
        except ValueError:
            await utils.answer(message, self.strings["usage_add"])
            return

        triggers.append({
            "user_id": user_id,
            "trigger": parts[1],
            "reply": parts[2],
            "mode": "contains",
            "chat_ids": [],
        })
        self.config["triggers"] = triggers
        await utils.answer(message, self.strings["saved"].format(num=len(triggers)))

    async def ardel_cmd(self, message):
        """Удалить триггер: .ardel [номер] или .ardel all"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["usage_del"])
            return

        args = args.strip()

        if args == "all":
            self.config["triggers"] = []
            await utils.answer(message, self.strings["cleared_all"])
            return

        try:
            num = int(args)
        except ValueError:
            await utils.answer(message, self.strings["usage_del"])
            return

        triggers = list(self.config["triggers"])
        if num < 1 or num > len(triggers):
            await utils.answer(message, self.strings["not_found"].format(num=num))
            return

        triggers.pop(num - 1)
        self.config["triggers"] = triggers
        await utils.answer(message, self.strings["cleared"].format(num=num))

    async def arlist_cmd(self, message):
        """Показать все триггеры"""
        triggers = self.config["triggers"]
        if not triggers:
            await utils.answer(message, self.strings["list_empty"])
            return

        text = self.strings["list_header"]
        for i, item in enumerate(triggers, 1):
            chat_ids = item.get("chat_ids", [])
            text += self.strings["list_item"].format(
                num=i,
                user_id=item.get("user_id", "?"),
                trigger=item.get("trigger", "?"),
                reply=item.get("reply", "?"),
                mode=item.get("mode", "contains"),
                chats=", ".join(str(c) for c in chat_ids) if chat_ids else "все чаты",
            )
        await utils.answer(message, text)

    async def armode_cmd(self, message):
        """Переключить режим триггера: .armode [номер]"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>Использование:</b> <code>.armode [номер]</code>")
            return

        try:
            num = int(args.strip())
        except ValueError:
            return

        triggers = list(self.config["triggers"])
        if num < 1 or num > len(triggers):
            await utils.answer(message, self.strings["not_found"].format(num=num))
            return

        current = triggers[num - 1].get("mode", "contains")
        triggers[num - 1]["mode"] = "exact" if current == "contains" else "contains"
        self.config["triggers"] = triggers
        await utils.answer(message, f"<b>Триггер #{num} — режим переключён на:</b> <code>{triggers[num-1]['mode']}</code>")

    async def archat_cmd(self, message):
        """Управление чатами триггера: .archat [номер] [chat_id или clear]"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["usage_chat"])
            return

        parts = args.strip().split()
        if len(parts) < 2:
            await utils.answer(message, self.strings["usage_chat"])
            return

        try:
            num = int(parts[0])
        except ValueError:
            await utils.answer(message, self.strings["usage_chat"])
            return

        triggers = list(self.config["triggers"])
        if num < 1 or num > len(triggers):
            await utils.answer(message, self.strings["not_found"].format(num=num))
            return

        if parts[1] == "clear":
            triggers[num - 1]["chat_ids"] = []
            self.config["triggers"] = triggers
            await utils.answer(message, self.strings["chat_cleared"].format(num=num))
            return

        try:
            chat_id = int(parts[1])
        except ValueError:
            await utils.answer(message, self.strings["usage_chat"])
            return

        chat_ids = list(triggers[num - 1].get("chat_ids", []))
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
        triggers[num - 1]["chat_ids"] = chat_ids
        self.config["triggers"] = triggers
        await utils.answer(message, self.strings["chat_added"].format(chat=chat_id, num=num))

    async def watcher(self, message):
        """Отслеживает все входящие сообщения"""
        await self._handler(message)
