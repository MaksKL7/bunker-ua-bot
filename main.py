import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАЛАШТУВАННЯ ---
TOKEN = "8596556076:AAEP6KQGbxk2hb80y9vo_Jx5JAiO1zav-NU"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВЕЛИКА БАЗА ДАНИХ ---
PROFESSIONS = ["Аніматор", "Архітектор", "Агроном", "Актор", "Блогер", "Бармен", "Будівельник", "Біолог", "Безробітній", "Ветеринар", "Вчений", "Вчитель", "Дизайнер", "Економіст", "Електрик", "Журналіст", "Інфоциган", "Інженер", "Кухар", "Лікар", "Логіст", "Механік", "Маркетолог", "Поліцай", "Пожежник", "Програміст", "Психолог", "Суддя", "Сантехнік", "Фармацевт", "Ядерний фізик"]
HEALTH = ["Зір -10", "Хронічний нежить", "Сколіоз", "Рак", "ВІЛ", "Поганий слух", "Туберкульоз", "Здоровий(а)", "Проблеми з серцем", "Деменція", "Шизофренія", "Геморой"]
ITEMS = ["Пістолет", "Ніж", "Їжа", "М'яч", "Олівці", "Камера", "Телефон", "Аптечка", "Пиво", "Мотузка", "Одяг", "Зарядка", "Металолом", "Настільні ігри", "Гітара"]
CHARACTERS = ["Нарцис", "Аб'юзер", "Біполярка", "Головний герой", "Депресія", "Імпульсивний", "Маніпулятор", "ОКР", "Параноїк", "Роздвоєння особистості", "Закритість"]
FACTS = ["Вбив людину", "Не вміє читати", "Пише фанфіки", "Анімешник", "Гомосексуал", "Їсть соплі", "Пісяє в ліжко", "Дивиться А4", "Путає ліво і право"]
PHOBIAS = ["Арахнофобія", "Кінофобія", "Гідрофобія", "Гемофобія", "Клаустрофобія", "Ніктофобія", "Соціофобія"]

CATASTROPHES = [
    "🧟 Зомбі-вірус: 90 відсотків населення перетворилися на ходячих мерців.",
    "🌊 Всесвітній потоп: рівень океану піднявся на 500 метрів.",
    "☢️ Ядерна війна: поверхня Землі випалена радіацією.",
    "☄️ Падіння метеорита: пил закрив сонце, почався льодовиковий період.",
    "👽 Вторгнення прибульців: людство загнане в підпілля.",
    "🔥 Світова пожежа: 80% лісів згоріло, атмосфера отруєна.",
    "🧊 Глобальне похолодання: середня температура впала на 10 градусів.",
    "🦠 Супербактерія: невиліковна хвороба вбила половину населення.",
    "⚡ Електромагнітна буря: всі електронні пристрої знищені, світ повернувся в кам'яний вік.",
    "🌪 Суперураган: урагани 5 категорії зруйнували міста по всьому світу.",
    "🧙‍♂️ Магічний апокаліпсис: магія вийшла з-під контролю, змінивши реальність.",
    "🧬 Генетична катастрофа: експеримент в лабораторії призвів до мутації людей і тварин."
]

SPECIAL_CARDS_LIST = [
    {"name": "➕ Додаткове місце", "effect": "add_seat", "desc": "Збільшує кількість місць у бункері на 1."},
    {"name": "🛡 Імунітет", "effect": "immunity", "desc": "Вас неможливо вигнати на поточному голосуванні."},
    {"name": "💀 Прокляття", "effect": "minus_seat", "desc": "Забирає одне місце у бункері."}
]

game = {
    "active": False, "players": {}, "order": [], "current_turn_index": 0,
    "chat_id": None, "round": 1, "seats": 0, "waiting_for_uid": None, "timer_task": None, "votes_data": {}, "scenario": ""
}

def generate_full_card():
    return {
        "Вік": random.randint(18, 75), "Стать": random.choice(["Чоловік", "Жінка"]),
        "Професія": random.choice(PROFESSIONS), "Здоров'я": random.choice(HEALTH),
        "Предмет": random.choice(ITEMS), "Характер": random.choice(CHARACTERS),
        "Факт": random.choice(FACTS), "Фобія": random.choice(PHOBIAS),
        "Спец_карта": random.choice(SPECIAL_CARDS_LIST),
        "card_used": False, "has_immunity": False
    }

# --- ЛОГІКА ГРИ ---
async def start_player_turn():
    if not game["active"]: return
    active_uids = [uid for uid in game["order"] if game["players"][uid]["alive"]]
    
    if len(active_uids) <= game["seats"]:
        await finish_game(active_uids)
        return

    if game["current_turn_index"] >= len(active_uids):
        if game["round"] % 3 == 0:
            await bot.send_message(game["chat_id"], "🗳 ЧАС ВИРІШУВАТИ!\nВсі висловились. Оберіть того, хто НЕ потрапить до бункера.", parse_mode="HTML")
            await start_voting()
        else:
            game["round"] += 1
            game["current_turn_index"] = 0
            builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🚀 Наступний раунд", callback_data="next_round_go"))
            await bot.send_message(game["chat_id"], f"🏁 Раунд завершено!\nГотові відкрити наступну карту?", reply_markup=builder.as_markup(), parse_mode="HTML")
        return

    uid = active_uids[game["current_turn_index"]]
    player = game["players"][uid]
    game["waiting_for_uid"] = uid

    f_map = {1: "ВІК І СТАТЬ", 2: "ПРОФЕСІЯ", 3: "ЗДОРОВ'Я", 4: "ПРЕДМЕТ", 5: "ХАРАКТЕР", 6: "ФАКТ", 7: "ФОБІЮ"}
    f_name = f_map.get(game["round"], "ХАРАКТЕРИСТИКУ")

    await bot.send_message(game["chat_id"], 
        f"🎤 ЗАРАЗ ВИСТУПАЄ: {player['name']}\n"
        f"📋 ТЕМА: {f_name}\n⏳ ЧАС: 1:30 хв.", parse_mode="HTML")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Завершити виступ", callback_data="force_end_turn"))
    if not player["card"]["card_used"]:
        builder.row(types.InlineKeyboardButton(text="✨ СПЕЦ-КАРТА", callback_data="use_special_ability"))

    await bot.send_message(uid, f"🔔 Твій хід! Розкажи про свою карту ({f_name}).\nЗакінчив — тисни кнопку:", reply_markup=builder.as_markup(), parse_mode="HTML")

    if game["timer_task"]: game["timer_task"].cancel()
    game["timer_task"] = asyncio.create_task(turn_timeout(uid))

async def turn_timeout(uid):
    await asyncio.sleep(90)
    if game["active"] and game["waiting_for_uid"] == uid:
        await bot.send_message(game["chat_id"], f"⏰ Час {game['players'][uid]['name']} вийшов!")
        game["current_turn_index"] += 1
        await start_player_turn()

# --- ОБРОБКА КНОПОК ---
@dp.callback_query(F.data == "force_end_turn")
async def end_turn(callback: types.CallbackQuery):
    if not game["active"] or game["waiting_for_uid"] != callback.from_user.id: return
    if game["timer_task"]: game["timer_task"].cancel()
    await callback.message.edit_text("✅ Ви завершили промову.")
    await bot.send_message(game["chat_id"], f"⏹ {game['players'][callback.from_user.id]['name']} закінчив.")
    game["current_turn_index"] += 1
    await start_player_turn()

@dp.callback_query(F.data == "use_special_ability")
async def special_card(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if not game["active"] or game["waiting_for_uid"] != uid: return
    player = game["players"][uid]
    card = player["card"]["Спец_карта"]
    player["card"]["card_used"] = True
    
    if card["effect"] == "add_seat": game["seats"] += 1
    elif card["effect"] == "minus_seat": game["seats"] = max(1, game["seats"] - 1)
    elif card["effect"] == "immunity": player["has_immunity"] = True
    
    await bot.send_message(game["chat_id"], f"🔥 СПЕЦ-КАРТА!\n{player['name']} використав: {card['name']}", parse_mode="HTML")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="✅ Завершити виступ", callback_data="force_end_turn"))
    await callback.message.edit_text(f"Карта активована. Тепер заверши хід:", reply_markup=builder.as_markup())

# --- КОМАНДИ СТАРТУ ---
@dp.message(Command("start_game"))
async def lobby(message: types.Message):
    game.update({"active": True, "players": {}, "chat_id": message.chat.id, "round": 1, "scenario": random.choice(CATASTROPHES)})
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🙋‍♂️ ЗАЙТИ", url=f"https://t.me/{(await bot.get_me()).username}?start=join"))
    await message.answer(f"🏚 НАБІР У БУНКЕР! /go — почати гру, /stop_game — зупинити гру\n\n🌍 СЦЕНАРІЙ: {game['scenario']}\n\nТисніть кнопку, щоб отримати роль.", reply_markup=b.as_markup(), parse_mode="HTML")

@dp.message(Command("go"))
async def go(message: types.Message):
    if not game["active"]: return
    if len(game["players"]) < 2: return await message.answer("Мало людей!")
    game["order"] = list(game["players"].keys())
    game["seats"] = max(1, len(game["order"]) // 2)
    await message.answer(f"🚀 ПОЧАЛИ!\nМісць у бункері: {game['seats']}\nРаунд 1: Професії.")
    await start_player_turn()

@dp.message(Command("stop_game"))
async def stop_game(message: types.Message):
    if not game["active"]:
        return await message.answer("Гра і так не запущена.")
    
    game["active"] = False
    if game["timer_task"]:
        game["timer_task"].cancel()
    
    game["players"] = {}
    await message.answer("🛑 Гра була примусово зупинена. Всі дані скинуті.")

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if "join" in message.text and game["active"]:
        b = InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="✅ ПРИЙНЯТИ", callback_data="acc"),
            types.InlineKeyboardButton(text="❌ ВІДХИЛИТИ", callback_data="dec")
        )
        await message.answer("Бажаєте приєднатися до гри?", reply_markup=b.as_markup())

@dp.callback_query(F.data == "dec")
async def decline(c: types.CallbackQuery):
    await c.message.edit_text("Ви відхилили запрошення.")

@dp.callback_query(F.data == "acc")
async def acc(c: types.CallbackQuery):
    if game["active"] and c.from_user.id not in game["players"]:
        card = generate_full_card()
        game["players"][c.from_user.id] = {"name": c.from_user.full_name, "card": card, "alive": True}
        await bot.send_message(game["chat_id"], f"✅ {c.from_user.first_name} у грі!")
        await c.message.edit_text("Твоя карта (нікому не кажи):")
        await bot.send_message(c.from_user.id, f"📦 ТВОЯ КАРТА:\n\n👤 {card['Стать']}, {card['Вік']}р\n🛠 {card['Професія']}\n🩺 {card['Здоров\'я']}\n🎒 {card['Предмет']}\n🎭 {card['Характер']}\n🤐 {card['Факт']}\n😱 {card['Фобія']}\n✨ Спец-карта: {card['Спец_карта']['name']}", parse_mode="HTML")

# --- ГОЛОСУВАННЯ ТА ФІНАЛ ---
async def start_voting():
    if not game["active"]: return
    game["votes_data"] = {}
    builder = InlineKeyboardBuilder()
    active = [u for u in game["players"] if game["players"][u]["alive"]]
    for uid in active:
        if not (game["players"][uid].get("has_immunity") and len(active) > 2):
            builder.row(types.InlineKeyboardButton(text=game["players"][uid]["name"], callback_data=f"v_{uid}"))
    await bot.send_message(game["chat_id"], "🗳 Оберіть того, хто залишиться зовні:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("v_"))
async def vote(c: types.CallbackQuery):
    if not game["active"]: return
    tid = int(c.data.split("_")[1])
    if c.from_user.id == tid: return await c.answer("Не можна проти себе!")
    if c.from_user.id in game["votes_data"]: return
    game["votes_data"][c.from_user.id] = tid
    await c.answer("Голос прийнято!")
    if len(game["votes_data"]) >= len([u for u in game["players"] if game["players"][u]["alive"]]):
        res = {}
        for t in game["votes_data"].values(): res[t] = res.get(t, 0) + 1
        ousted = max(res, key=res.get)
        game["players"][ousted]["alive"] = False
        for p in game["players"].values(): p["has_immunity"] = False
        await bot.send_message(game["chat_id"], f"💀 {game['players'][ousted]['name']} вигнаний!")
        game["current_turn_index"] = 0
        await start_player_turn()

async def finish_game(winners):
    game["active"] = False
    msg = f"🏆 ГРУ ЗАВЕРШЕНО!\n\n👤 Вижили: {', '.join([game['players'][u]['name'] for u in winners])}\n\n📂 ПОВНІ КАРТКИ ВСІХ ГРАВЦІВ:\n"
    for uid, data in game["players"].items():
        c = data["card"]
        msg += f"\n{'✅' if data['alive'] else '❌'} {data['name']}:\n├ {c['Стать']}, {c['Вік']}р\n├ Проф: {c['Професія']}\n├ Здор: {c['Здоров\'я']}\n├ Предмет: {c['Предмет']}\n├ Характер: {c['Характер']}\n├ Факт: {c['Факт']}\n└ Фобія: {c['Фобія']}\n"
    await bot.send_message(game["chat_id"], msg, parse_mode="HTML")

@dp.callback_query(F.data == "next_round_go")
async def next_r(callback: types.CallbackQuery):
    if not game["active"]: return
    await callback.message.delete()
    await start_player_turn()

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
