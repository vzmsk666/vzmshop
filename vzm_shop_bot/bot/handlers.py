from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from .config import Config
from . import db
from .keyboards import (
    main_menu, boost_mode_kb, boost_type_kb, ranks_page, div_kb,
    coaching_kb, coaching_pack_kb, replay_kb, play_format_kb, play_pack_kb,
    admin_status_kb
)
from .boost import Mode, BoostType, Position, calc_boost_price

router = Router()

# Simple in-memory state per user (good enough for MVP)
SESSION: dict[int, dict] = {}

def s(user_id: int) -> dict:
    return SESSION.setdefault(user_id, {})

@router.message(CommandStart())
async def start(m: Message, config: Config):
    await m.answer(
        "👋 Добро пожаловать в *VZM SHOP*\n\n"
        "Выберите услугу ниже. Оплата и все детали — через оператора.",
        reply_markup=main_menu(config.support_username),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "menu")
async def menu(c: CallbackQuery, config: Config):
    await c.message.edit_text(
        "🏪 *VZM SHOP* — каталог услуг:",
        reply_markup=main_menu(config.support_username),
        parse_mode="Markdown"
    )
    await c.answer()

# --- Services entrypoints ---
@router.callback_query(F.data == "svc:boost")
async def svc_boost(c: CallbackQuery):
    await c.message.edit_text("🚀 Буст ранга\nВыберите режим:", reply_markup=boost_mode_kb())
    await c.answer()

@router.callback_query(F.data.startswith("boost:mode:"))
async def boost_mode(c: CallbackQuery):
    mode = c.data.split(":")[-1]
    if mode != "2v2":
        await c.answer("Этот режим пока в разработке.", show_alert=True)
        return
    s(c.from_user.id).update({"boost_mode": Mode.DOUBLES_2V2})
    await c.message.edit_text("🚀 Буст ранга (2v2)\nВыберите тип:", reply_markup=boost_type_kb())
    await c.answer()

@router.callback_query(F.data == "boost:type")
async def boost_type_back(c: CallbackQuery):
    await c.message.edit_text("🚀 Буст ранга (2v2)\nВыберите тип:", reply_markup=boost_type_kb())
    await c.answer()

@router.callback_query(F.data.startswith("boost:type:"))
async def boost_type(c: CallbackQuery):
    typ = c.data.split(":")[-1]
    bt = BoostType.ACCOUNT if typ == "account" else BoostType.PARTY
    s(c.from_user.id).update({"boost_type": bt, "start_rank_page": 0})
    await c.message.edit_text("Выберите *СТАРТОВЫЙ* ранг:", reply_markup=ranks_page("boost:start_rank", page=0, allow_ssl=False), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("boost:start_rank:page:"))
async def start_rank_page(c: CallbackQuery):
    page = int(c.data.split(":")[-1])
    s(c.from_user.id)["start_rank_page"] = page
    await c.message.edit_text("Выберите *СТАРТОВЫЙ* ранг:", reply_markup=ranks_page("boost:start_rank", page=page, allow_ssl=False), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("boost:start_rank:"))
async def start_rank_pick(c: CallbackQuery):
    parts = c.data.split(":", 2)
    rank = parts[2]
    s(c.from_user.id)["start_rank"] = rank
    await c.message.edit_text(f"Стартовый ранг: *{rank}*\nВыберите дивизион:", reply_markup=div_kb("boost:start_div", rank), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data == "boost:start_div:back_rank")
async def start_div_back(c: CallbackQuery):
    page = s(c.from_user.id).get("start_rank_page", 0)
    await c.message.edit_text("Выберите *СТАРТОВЫЙ* ранг:", reply_markup=ranks_page("boost:start_rank", page=page, allow_ssl=False), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("boost:start_div:"))
async def start_div_pick(c: CallbackQuery):
    _, _, rest = c.data.split(":",2)
    rank, div = rest.rsplit(":",1)
    div_n = int(div)
    s(c.from_user.id)["start_pos"] = Position(rank, div_n)
    s(c.from_user.id)["end_rank_page"] = 0
    await c.message.edit_text("Выберите *ЦЕЛЕВОЙ* ранг:", reply_markup=ranks_page("boost:end_rank", page=0, allow_ssl=True), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("boost:end_rank:page:"))
async def end_rank_page(c: CallbackQuery):
    page = int(c.data.split(":")[-1])
    s(c.from_user.id)["end_rank_page"] = page
    await c.message.edit_text("Выберите *ЦЕЛЕВОЙ* ранг:", reply_markup=ranks_page("boost:end_rank", page=page, allow_ssl=True), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("boost:end_rank:"))
async def end_rank_pick(c: CallbackQuery):
    rank = c.data.split(":",2)[2]
    s(c.from_user.id)["end_rank"] = rank
    await c.message.edit_text(f"Целевой ранг: *{rank}*\nВыберите дивизион:", reply_markup=div_kb("boost:end_div", rank), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data == "boost:end_div:back_rank")
async def end_div_back(c: CallbackQuery):
    page = s(c.from_user.id).get("end_rank_page", 0)
    await c.message.edit_text("Выберите *ЦЕЛЕВОЙ* ранг:", reply_markup=ranks_page("boost:end_rank", page=page, allow_ssl=True), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("boost:end_div:"))
async def end_div_pick(c: CallbackQuery):
    _, _, rest = c.data.split(":",2)
    rank, div = rest.rsplit(":",1)
    if div == "ssl":
        end_pos = Position(rank, None)
    else:
        end_pos = Position(rank, int(div))
    st = s(c.from_user.id)
    start_pos: Position = st["start_pos"]
    mode: Mode = st["boost_mode"]
    bt: BoostType = st["boost_type"]

    try:
        price = calc_boost_price(start_pos, end_pos, mode, bt)
    except Exception as e:
        await c.answer(str(e), show_alert=True)
        return

    st["boost_end_pos"] = end_pos
    st["boost_price"] = price
    details = f"{mode.value} | {bt.value} | {start_pos.rank} Div {start_pos.div} → {end_pos.rank} " + ("" if end_pos.div is None else f"Div {end_pos.div}")
    payload = details.replace("|", "~")  # keep callback small

    text = (
        f"✅ *Расчёт буста*\n"
        f"Режим: *{mode.value}*\n"
        f"Тип: *{'Пати ×2' if bt==BoostType.PARTY else 'Буст аккаунта'}*\n"
        f"Маршрут: *{start_pos.rank} Div {start_pos.div} → {end_pos.rank}{'' if end_pos.div is None else f' Div {end_pos.div}'}*\n"
        f"Цена: *{price} ₽*\n\n"
        f"Нажмите «Оформить заявку», и оператор свяжется с вами."
    )
    from .keyboards import order_confirm_kb
    await c.message.edit_text(text, reply_markup=order_confirm_kb("boost", payload), parse_mode="Markdown")
    await c.answer()

# --- Coaching ---
@router.callback_query(F.data == "svc:coaching")
async def svc_coaching(c: CallbackQuery):
    await c.message.edit_text("🎓 Коучинг\nВыберите формат:", reply_markup=coaching_kb())
    await c.answer()

@router.callback_query(F.data.startswith("coach:who:"))
async def coach_who(c: CallbackQuery):
    who = c.data.split(":")[-1]
    await c.message.edit_text("🎓 Коучинг\nВыберите пакет:", reply_markup=coaching_pack_kb(who))
    await c.answer()

@router.callback_query(F.data.startswith("coach:pack:"))
async def coach_pack(c: CallbackQuery):
    _, _, who, val = c.data.split(":",3)
    pack, price = val.split(":")
    price_i = int(price)
    service = "Коучинг SSL" if who=="ssl" else "Коучинг VZM"
    details = f"{service} | {pack}"
    payload = details.replace("|","~")
    from .keyboards import order_confirm_kb
    await c.message.edit_text(
        f"✅ *{service}*\nПакет: *{pack}*\nЦена: *{price_i} ₽*\n\n"
        "Нажмите «Оформить заявку», и оператор свяжется с вами.",
        reply_markup=order_confirm_kb("coaching", payload),
        parse_mode="Markdown"
    )
    await c.answer()

# --- Replay review ---
@router.callback_query(F.data == "svc:replay")
async def svc_replay(c: CallbackQuery):
    await c.message.edit_text("🎥 Разбор реплея (SSL)\nВидео ~10 минут, срок до 48 часов.\nВыберите пакет:", reply_markup=replay_kb())
    await c.answer()

@router.callback_query(F.data.startswith("replay:pack:"))
async def replay_pack(c: CallbackQuery):
    _, _, n, price = c.data.split(":")
    n_i, price_i = int(n), int(price)
    details = f"Разбор реплея SSL | {n_i} реплей(ев) | до 48 часов"
    payload = details.replace("|","~")
    from .keyboards import order_confirm_kb
    await c.message.edit_text(
        f"✅ *Разбор реплея (SSL)*\nПакет: *{n_i}*\nЦена: *{price_i} ₽*\nСрок: *до 48 часов*\n\n"
        "Нажмите «Оформить заявку», и оператор свяжется с вами (и попросит файл/ник).",
        reply_markup=order_confirm_kb("replay", payload),
        parse_mode="Markdown"
    )
    await c.answer()

# --- Play with VZM ---
@router.callback_query(F.data == "svc:play")
async def svc_play(c: CallbackQuery):
    await c.message.edit_text("🎮 Игра с VZM\nВыберите формат:", reply_markup=play_format_kb())
    await c.answer()

@router.callback_query(F.data.startswith("play:fmt:"))
async def play_fmt(c: CallbackQuery):
    fmt = c.data.split(":")[-1]
    await c.message.edit_text("🎮 Игра с VZM\nВыберите пакет:", reply_markup=play_pack_kb(fmt))
    await c.answer()

@router.callback_query(F.data.startswith("play:pack:"))
async def play_pack(c: CallbackQuery):
    _, _, fmt, val = c.data.split(":",3)
    n, price = val.split(":")
    n_i, price_i = int(n), int(price)
    fmt_name = "1x1" if fmt=="1v1" else "2x2 (пати)"
    details = f"Игра с VZM | {fmt_name} | {n_i} игр"
    payload = details.replace("|","~")
    from .keyboards import order_confirm_kb
    await c.message.edit_text(
        f"✅ *Игра с VZM*\nФормат: *{fmt_name}*\nПакет: *{n_i} игр*\nЦена: *{price_i} ₽*\n\n"
        "Нажмите «Оформить заявку», и оператор свяжется с вами для времени/деталей.",
        reply_markup=order_confirm_kb("play", payload),
        parse_mode="Markdown"
    )
    await c.answer()

# --- Order creation & admin posting ---
SERVICE_LABEL = {
    "boost": "Буст ранга",
    "coaching": "Коучинг",
    "replay": "Разбор реплея",
    "play": "Игра с VZM",
}

@router.callback_query(F.data.startswith("order:"))
async def create_order(c: CallbackQuery, config: Config):
    _, service_key, payload = c.data.split(":",2)
    details = payload.replace("~","|")
    price = 0

    # parse price from message (reliable enough for MVP)
    # We'll store price as last seen in session for boost; for others it's inside message text
    st = s(c.from_user.id)
    if service_key == "boost":
        price = int(st.get("boost_price", 0))
    else:
        # attempt to parse from message text "Цена: *123 ₽*"
        txt = c.message.text or ""
        import re
        m = re.search(r"Цена:\s*\*?(\d+)\s*₽", txt)
        if m:
            price = int(m.group(1))
        else:
            # fallback: 0
            price = 0

    order_id = await db.create_order(
        user_id=c.from_user.id,
        username=c.from_user.username,
        service=SERVICE_LABEL.get(service_key, service_key),
        details=details,
        price_rub=price,
        status="NEW",
    )

    # Send to admin chat
    user_link = f"@{c.from_user.username}" if c.from_user.username else f"id:{c.from_user.id}"
    text = (
        f"📦 *Новая заявка* \n"
        f"*ORDER #{order_id}*\n"
        f"Услуга: *{SERVICE_LABEL.get(service_key, service_key)}*\n"
        f"Детали: `{details}`\n"
        f"Цена: *{price} ₽*\n"
        f"Клиент: {user_link}"
    )
    try:
        await c.bot.send_message(
            chat_id=config.admin_chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=admin_status_kb(order_id),
        )
    except TelegramBadRequest:
        # if markdown fails due to special chars
        await c.bot.send_message(
            chat_id=config.admin_chat_id,
            text=text.replace("`",""),
            reply_markup=admin_status_kb(order_id),
        )

    await c.message.edit_text(
        "✅ *Заявка отправлена!*\n\n"
        "Оператор скоро свяжется с вами в личных сообщениях.\n"
        "Спасибо!",
        parse_mode="Markdown",
        reply_markup=main_menu(config.support_username),
    )
    await c.answer()

# --- Admin callbacks ---
@router.callback_query(F.data.startswith("adm:st:"))
async def admin_set_status(c: CallbackQuery, config: Config):
    # Only allow actions in admin chat
    if c.message.chat.id != config.admin_chat_id:
        await c.answer("Недостаточно прав.", show_alert=True)
        return
    _, _, order_id, status = c.data.split(":",3)
    order_id_i = int(order_id)
    await db.update_status(order_id_i, status)
    order = await db.get_order(order_id_i)
    if not order:
        await c.answer("Заказ не найден.", show_alert=True)
        return
    # Update message header line
    header = f"📦 *Заявка* \n*ORDER #{order.id}*\n"
    body = f"Услуга: *{order.service}*\nДетали: `{order.details}`\nЦена: *{order.price_rub} ₽*\nКлиент: @{order.username}" if order.username else f"Услуга: *{order.service}*\nДетали: `{order.details}`\nЦена: *{order.price_rub} ₽*\nКлиент: id:{order.user_id}"
    status_line = f"\n\nСтатус: *{status}* (обновил @{c.from_user.username or c.from_user.id})"
    await c.message.edit_text(header + body + status_line, parse_mode="Markdown", reply_markup=admin_status_kb(order.id))
    await c.answer("Статус обновлён ✅")

@router.message(Command("orders"))
async def cmd_orders(m: Message, config: Config):
    if m.chat.id != config.admin_chat_id:
        return
    orders = await db.list_recent_orders(20)
    if not orders:
        await m.answer("Пока нет заказов.")
        return
    lines = []
    for o in orders:
        user = f"@{o.username}" if o.username else f"id:{o.user_id}"
        lines.append(f"#{o.id} | {o.status} | {o.service} | {o.price_rub}₽ | {user}")
    await m.answer("*Последние заказы:*\n" + "\n".join(lines), parse_mode="Markdown")

@router.message(Command("stats"))
async def cmd_stats(m: Message, config: Config):
    if m.chat.id != config.admin_chat_id:
        return
    st = await db.stats()
    by_status = ", ".join([f"{k}:{v}" for k,v in st["by_status"].items()]) or "нет"
    await m.answer(
        f"*Статистика:*\n"
        f"Всего заказов: *{st['total_count']}*\n"
        f"Сумма: *{st['total_sum']} ₽*\n"
        f"По статусам: {by_status}",
        parse_mode="Markdown"
    )
