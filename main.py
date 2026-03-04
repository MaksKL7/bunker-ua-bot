import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8596556076:AAEP6KQGbxk2hb80y9vo_Jx5JAiO1zav-NU"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ПОВНА БАЗА ДАНИХ ---
PROFESSIONS = ["Аніматор", "Архітектор", "Агроном", "Актор", "Блогер", "Фермер", "Тракторист", "Бармен", "Будівельник", "Біолог", "Безробітній", "Ветеринар", "Вчений", "Вчитель", "Дизайнер", "Дворнік", "Економіст", "Електрик", "Журналіст", "Інфоциган", "Інженер", "Касир", "Кухар", "Лікар", "Логіст", "Механік", "Маркетолог", "Поліцай", "Проститутка", "Пожежник", "Програміст", "Психолог", "Суддя", "Сантехнік", "Фармацевт", "Ядерний фізик"]
HEALTH = ["Зір -10", "Хронічний нежить", "Сколіоз", "Рак", "ВІЛ", "Поганий слух", "Туберкульоз","Чума", "Здоровий(а)", "Проблеми з серцем", "Деменція", "Шизофренія", "Геморой"]
ITEMS = ["Пістолет", "Ніж", "Їжа", "М'яч", "Олівці", "Камера", "Телефон", "Аптечка", "Пиво", "Мотузка", "Одяг", "Зарядка", "Металолом", "Настільні ігри", "Гітара"]
CHARACTERS = ["Нарцис", "Аб'юзер", "Біполярка", "Головний герой", "Депресія", "Імпульсивний", "Маніпулятор", "ОКР", "Параноїк", "Роздвоєння особистості", "Закритість"]
FACTS = ["Вбив людину", "Не вміє читати","Любить горох", "Лесбіянка","Гей", "Любить по молодше","Тупий","Срає де попало", "Пише фанфіки", "Анімешник", "Гомосексуал", "Їсть соплі", "Пісяє в ліжко", "Дивиться А4", "Путає ліво і право"]
PHOBIAS = ["Арахнофобія", "Кінофобія", "Гідрофобія", "Гемофобія", "Клаустрофобія", "Ніктофобія", "Соціофобія"]
HABITUS = ["Високий атлет", "Низький з зайвою вагою", "Спортивна статура", "Тендітна зовнішність", "Дуже татуйований", "Альбінос"]
SKILLS = ["Керування літаком", "Злам замків", "Перша допомога", "Риболовля", "Знання їстівних грибів", "Стрільба з лука"]

CATASTROPHES = ["🧟 Зомбі-вірус", "🌊 Всесвітній потоп", "☢️ Ядерна війна", "☄️ Метеорит", "👽 Прибульці", "Назар став бєтменом"]

RANDOM_EVENTS = [
    "⚡️ АВАРІЯ: Зламався генератор! У наступному раунді обов'язково розкажіть, як ваша навичка допоможе з цим.",
    "🍄 ЗНАЙДЕНО ЗАПАСИ: Ресурсів стало більше. Наступне голосування може бути пропущено без втрат!",
    "📻 РАДІОСИГНАЛ: Ви почули, що десь є інший бункер. Всі відчули приплив надії.",
    "☣️ ВИТІК ТОКСИНІВ: Хтось випадково розбив колбу. У наступному раунді обговоріть стан здоров'я ретельніше.",
    "🔒 ЗАКЛИНЕ ДВЕРІ:Бункер закриється раніше! Наступний виступ має бути вдвічі коротшим."
]

game = {
    "active": False, "host_id": None, "players": {}, "order": [], 
    "current_turn_index": 0, "chat_id": None, "round": 1, 
    "seats": 2, "waiting_for_uid": None, "timer_task": None, "votes_data": {}, "scenario": ""
}

def generate_full_card():
    h = random.randint(20, 300)
    w = random.randint(1, 300)
    return {
        "Вік": random.randint(1, 130), "Стать": random.choice(["Чоловік", "Жінка", "Тарансгендер", "Робот", "Скотина"]),
        "Професія": random.choice(PROFESSIONS), 
        "Параметри": f"{h} см / {w} кг",
        "Здоров'я": random.choice(HEALTH),
        "Предмет": random.choice(ITEMS), "Характер": random.choice(CHARACTERS),
        "Факт": random.choice(FACTS), "Фобія": random.choice(PHOBIAS),
        "Хабітус": random.choice(HABITUS), "Навичка": random.choice(SKILLS)
    }

async def start_player_turn():
    if not game["active"]: return
    active_uids = [uid for uid in game["order"] if game["players"][uid]["alive"]]
    
    if len(active_uids) <= game["seats"]:
        await finish_game(active_uids)
        return

    if game["current_turn_index"] >= len(active_uids):
        await bot.send_message(game["chat_id"], f"🗳 Всі висловились! Починаємо голосування за раунд {game['round']}.")
        await start_voting()
        return

    uid = active_uids[game["current_turn_index"]]
    player = game["players"][uid]
    game["waiting_for_uid"] = uid

    # ДОДАНО ВАГУ ТА ЗРІСТ В СПИСОК РАУНДІВ
    f_map = {1: "ПРОФЕСІЮ", 2: "ВІК ТА СТАТЬ", 3: "ВАГУ ТА ЗРІСТ", 4: "ЗДОРОВ'Я", 5: "ХАРАКТЕР", 6: "ПРЕДМЕТ", 7: "ФАКТ", 8: "ФОБІЮ", 9: "ХАБІТУС", 10: "НАВИЧКУ"}
    f_name = f_map.get(game["round"], "ХАРАКТЕРИСТИКУ")

    await bot.send_message(game["chat_id"], 
        f"📢 РАУНД {game['round']}\n🎤 Виступає: {player['name']}\n📋 Тема: {f_name}", parse_mode="HTML")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Завершити виступ", callback_data="force_end_turn"))
    await bot.send_message(uid, f"🔔 Твій хід! Тема: {f_name}.\nНатисни кнопку, коли закінчиш:", reply_markup=builder.as_markup())

    if game["timer_task"]: game["timer_task"].cancel()
    game["timer_task"] = asyncio.create_task(turn_timeout(uid))

async def turn_timeout(uid):
    await asyncio.sleep(90)
    if game["active"] and game["waiting_for_uid"] == uid:
        game["current_turn_index"] += 1
        await start_player_turn()

@dp.callback_query(F.data == "force_end_turn")
async def end_turn(callback: types.CallbackQuery):
    if game["waiting_for_uid"] != callback.from_user.id: return
    if game["timer_task"]: game["timer_task"].cancel()
    await callback.message.edit_text("✅ Ви закінчили виступ.")
    game["current_turn_index"] += 1
    await start_player_turn()

async def start_voting():
    game["votes_data"] = {}
    builder = InlineKeyboardBuilder()
    active_alive = [uid for uid in game["players"] if game["players"][uid]["alive"]]
    for uid in active_alive:
        builder.row(types.InlineKeyboardButton(text=f"❌ {game['players'][uid]['name']}", callback_data=f"v_{uid}"))
    builder.row(types.InlineKeyboardButton(text="⏭ ПРОПУСТИТИ (Ведучий)", callback_data="skip_vote_act"))
    await bot.send_message(game["chat_id"], "🗳 ЧАС ВИРІШУВАТИ!\nОберіть того, хто НЕ потрапить до бункера.", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "skip_vote_act")
async def skip_vote(c: types.CallbackQuery):
    if c.from_user.id != game["host_id"]: return await c.answer("Тільки ведучий!")
    
    # ВИДАЛЯЄМО КНОПКИ ПІСЛЯ НАТИСКАННЯ, ЩОБ НЕ БУЛО БАГУ
    await c.message.edit_reply_markup(reply_markup=None)
    
    event = random.choice(RANDOM_EVENTS)
    await bot.send_message(game["chat_id"], f"⏭ Ведучий вирішив нікого не виганяти.\n\n🔔 ПОДІЯ:\n{event}", parse_mode="HTML")
    game["round"] += 1
    game["current_turn_index"] = 0
    await start_player_turn()

@dp.callback_query(F.data.startswith("v_"))
async def vote_act(c: types.CallbackQuery):
    tid = int(c.data.split("_")[1])
    if c.from_user.id in game["votes_data"]: return await c.answer("Ви вже голосували!")
    game["votes_data"][c.from_user.id] = tid
    await c.answer("Голос прийнято!")
    active_count = len([u for u in game["players"] if game["players"][u]["alive"]])
    if len(game["votes_data"]) >= active_count:
        res = {}
        for t in game["votes_data"].values(): res[t] = res.get(t, 0) + 1
        ousted = max(res, key=res.get)
        game["players"][ousted]["alive"] = False
        
        # ВИДАЛЯЄМО КНОПКИ ПІСЛЯ ГОЛОСУВАННЯ
        await c.message.edit_reply_markup(reply_markup=None)
        
        event = random.choice(RANDOM_EVENTS)
        await bot.send_message(game["chat_id"], f"💀 Гравця {game['players'][ousted]['name']} вигнано!\n\n🔔 ПОДІЯ:\n{event}", parse_mode="HTML")
        game["round"] += 1
        game["current_turn_index"] = 0
        await start_player_turn()

@dp.message(Command("stop_game"))
async def stop_game_cmd(message: types.Message):
    if message.from_user.id == game["host_id"]:
        game["active"] = False
        if game["timer_task"]: game["timer_task"].cancel()
        await message.answer("🛑 ГРУ ПРИМУСОВО ЗУПИНЕНО ВЕДУЧИМ.", parse_mode="HTML")

@dp.message(Command("start_game"))
async def lobby(message: types.Message):
    game.update({"active": True, "host_id": message.from_user.id, "players": {}, "round": 1, "chat_id": message.chat.id, "scenario": random.choice(CATASTROPHES)})
    rules = (
        "📖 ПРАВИЛА ГРИ «БУНКЕР»\n\n1. Кожен отримує карту з 11 характеристиками.\n2. Раунди йдуть по черзі.\n3. Після голосування — випадкова подія!\n4. В бункері всього 2 місця.\n\n🕹 КОМАНДИ: /go, /stop_game\n\n🌍 КАТАСТРОФА: " + game["scenario"]
    )
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🙋‍♂️ ЗАЙТИ В ГРУ", url=f"https://t.me/{(await bot.get_me()).username}?start=join"))
    await message.answer(rules, reply_markup=b.as_markup(), parse_mode="HTML")

@dp.message(Command("go"))
async def go(message: types.Message):
    if message.from_user.id != game["host_id"]: return
    if len(game["players"]) < 3: return await message.answer("Мало людей!")
    game["order"] = list(game["players"].keys())
    random.shuffle(game["order"])
    await message.answer(f"🚀 ПОЧАЛИ! Раунд 1: ПРОФЕСІЇ.")
    await start_player_turn()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if "join" in message.text and game["active"]:
        b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="✅ ПРИЙНЯТИ", callback_data="acc"), types.InlineKeyboardButton(text="❌ ВІДХИЛИТИ", callback_data="dec"))
        await message.answer("Запрошення до гри. Приймаєте?", reply_markup=b.as_markup())

@dp.callback_query(F.data == "acc")
async def acc(c: types.CallbackQuery):
    if c.from_user.id not in game["players"]:
        card = generate_full_card()
        game["players"][c.from_user.id] = {"name": c.from_user.full_name, "card": card, "alive": True}
        await bot.send_message(game["chat_id"], f"✅ {c.from_user.first_name} приєднався!")
        card_text = (
            f"📦 ТВОЯ КАРТА:\n\n👤 {card['Стать']}, {card['Вік']}р\n🛠 Професія: {card['Професія']}\n⚖️ Вага/Зріст: {card['Параметри']}\n🩺 Здоров'я: {card['Здоров\'я']}\n🎒 Предмет: {card['Предмет']}\n🎭 Характер: {card['Характер']}\n🤐 Факт: {card['Факт']}\n😱 Фобія: {card['Фобія']}\n🏃 Хабітус: {card['Хабітус']}\n💡 Навичка: {card['Навичка']}"
        )
        await bot.send_message(c.from_user.id, card_text, parse_mode="HTML")
        await c.message.edit_text("Ви у грі!")

@dp.callback_query(F.data == "dec")
async def dec(c: types.CallbackQuery):
    await c.message.edit_text("Ви відхилили запрошення.")

async def finish_game(winners):
    game["active"] = False
    msg = f"🏆 ГРУ ЗАВЕРШЕНО!\n\n👤 Вижили: {', '.join([game['players'][u]['name'] for u in winners])}\n\n📂 ДОСЬЄ ГРАВЦІВ:\n"
    for uid, data in game["players"].items():
        c = data["card"]
        msg += (
            f"\n{'✅' if data['alive'] else '❌'} {data['name']}:\n"
            f"├ Стать/Вік: {c['Стать']}, {c['Вік']}р\n├ Професія: {c['Професія']}\n"
            f"├ Вага/Зріст: {c['Параметри']}\n├ Здоров'я: {c['Здоров\'я']}\n"
            f"├ Предмет: {c['Предмет']}\n├ Характер: {c['Характер']}\n"
            f"├ Факт: {c['Факт']}\n├ Фобія: {c['Фобія']}\n"
            f"├ Хабітус: {c['Хабітус']}\n└ Навичка: {c['Навичка']}\n"
        )
    await bot.send_message(game["chat_id"], msg, parse_mode="HTML")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
