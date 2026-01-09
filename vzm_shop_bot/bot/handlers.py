from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

from .config import Config
from . import db
from .keyboards import (
    main_menu,
    boost_mode_kb,
    boost_type_kb,
    ranks_page,
    div_kb,
    coaching_kb,
    coaching_pack_kb,
    replay_kb,
    play_format_kb,
    play_pack_kb,
    admin_status_kb,
    order_confirm_kb,
)
from .boost import Mode, BoostType, Position, calc_boost_price

router = Router()

SESSION: dict[int, dict] = {}


def s(user_id: int) -> dict:
    return SESSION.setdefault(user_id, {})


@router.message(CommandStart())
async def start(m: Message, config: Config):
    await m.answer(
        "👋 Добро пожаловать в *VZM SHOP*\n\n"
        "Выберите услугу ниже. Оплата и все детали — через оператора.",
        reply_markup=main_menu(config.support_username),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "menu")
async def menu(c: CallbackQuery, config: Config):
    await c.message.edit_text(
        "🏪 *VZM SHOP* — каталог услуг:",
        reply_markup=main_menu(config.support_username),
        parse_mode="Markdown",
    )
    await c.answer()


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
    st = s(c.from_user.id)
    st.update({"boost_type": bt, "start_rank_page": 0})
    await c.message.edit_text(
        "Выберите *СТАРТОВЫЙ* ранг:",
        reply_markup=ranks_page("boost:start_rank", page=0, allow_ssl=False),
        parse_mode="Markdown",
    )
    await c.answer()


@router.callback_query(F.data.startswith("boost:start_rank:page:"))
async def start_rank_page(c: CallbackQuery):
    try:
        page = int(c.data.split(":")[-1])
        s(c.from_user.id)["start_rank_page"] = page
        await c.message.edit_text(
            "Выберите *СТАРТОВЫЙ* ранг:",
            reply_markup=ranks_page("boost:start_rank", page=page, allow_ssl=False),
            parse_mode="Markdown",
        )
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("boost:start_rank:"))
async def start_rank_pick(c: CallbackQuery):
    try:
        rank = c.data.split(":", 2)[2]
        s(c.from_user.id)["start_rank"] = rank
        await c.message.edit_text(
            f"Стартовый ранг: *{rank}*\nВыберите дивизион:",
            reply_markup=div_kb("boost:start_div", rank),
            parse_mode="Markdown",
        )
    except TelegramBadRequest:
        await c.message.answer("⚠️ Ошибка Telegram. Попробуйте ещё раз.")
    finally:
        await c.answer()


@router.callback_query(F.data == "boost:start_div:back_rank")
async def start_div_back(c: CallbackQuery):
    try:
        page = s(c.from_user.id).get("start_rank_page", 0)
        await c.message.edit_text(
            "Выберите *СТАРТОВЫЙ* ранг:",
            reply_markup=ranks_page("boost:start_rank", page=page, allow_ssl=False),
            parse_mode="Markdown",
        )
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("boost:start_div:"))
async def start_div_pick(c: CallbackQuery):
    try:
        _, _, rest = c.data.split(":", 2)
        rank, div = rest.rsplit(":", 1)
        div_n = int(div)

        st = s(c.from_user.id)
        st["start_pos"] = Position(rank, div_n)
        st["end_rank_page"] = 0

        await c.message.edit_text(
            "Выберите *ЦЕЛЕВОЙ* ранг:",
            reply_markup=ranks_page("boost:end_rank", page=0, allow_ssl=True),
            parse_mode="Markdown",
        )
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("boost:end_rank:page:"))
async def end_rank_page(c: CallbackQuery):
    try:
        page = int(c.data.split(":")[-1])
        s(c.from_user.id)["end_rank_page"] = page
        await c.message.edit_text(
            "Выберите *ЦЕЛЕВОЙ* ранг:",
            reply_markup=ranks_page("boost:end_rank", page=page, allow_ssl=True),
            parse_mode="Markdown",
        )
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("boost:end_rank:"))
async def end_rank_pick(c: CallbackQuery):
    try:
        rank = c.data.split(":", 2)[2]
        s(c.from_user.id)["end_rank"] = rank
        await c.message.edit_text(
            f"Целевой ранг: *{rank}*\nВыберите дивизион:",
            reply_markup=div_kb("boost:end_div", rank),
            parse_mode="Markdown",
        )
    except TelegramBadRequest:
        await c.message.answer("⚠️ Ошибка Telegram. Попробуйте ещё раз.")
    finally:
        await c.answer()


@router.callback_query(F.data == "boost:end_div:back_rank")
async def end_div_back(c: CallbackQuery):
    try:
        page = s(c.from_user.id).get("end_rank_page", 0)
        await c.message.edit_text(
            "Выберите *ЦЕЛЕВОЙ* ранг:",
            reply_markup=ranks_page("boost:end_rank", page=page, allow_ssl=True),
            parse_mode="Markdown",
        )
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("boost:end_div:"))
async def end_div_pick(c: CallbackQuery):
    try:
        _, _, rest = c.data.split(":", 2)
        rank, div = rest.rsplit(":", 1)

        if div == "ssl":
            end_pos = Position(rank, None)
        else:
            end_pos = Position(rank, int(div))

        st = s(c.from_user.id)
        start_pos: Position = st.get("start_pos")
        mode: Mode = st.get("boost_mode")
        bt: BoostType = st.get("boost_type")

        if not start_pos or not mode or not bt:
            await c.answer("Сессия устарела. Начните заново.", show_alert=True)
            return

        price = calc_boost_price(start_pos, end_pos, mode, bt)

        route = f"{start_pos.rank} Div {start_pos.div} → {end_pos.rank}" + ("" if end_pos.div is None else f" Div {end_pos.div}")
        details = f"{mode.value} | {bt.value} | {route}"

        st["pending_order"] = {
            "service_key": "boost",
            "service": "Буст ранга",
            "details": details,
            "price": int(price),
        }

        text = (
            f"✅ *Расчёт буста*\n"
            f"Режим: *{mode.value}*\n"
            f"Тип: *{'Пати ×2' if bt == BoostType.PARTY else 'Буст аккаунта'}*\n"
            f"Маршрут: *{route}*\n"
            f"Цена: *{price} ₽*\n\n"
            f"Нажмите «Оформить заявку», и оператор свяжется с вами."
        )

        await c.message.edit_text(
            text,
            reply_markup=order_confirm_kb("boost"),
            parse_mode="Markdown",
        )
    except TelegramBadRequest:
        await c.message.answer("⚠️ Ошибка Telegram. Попробуйте ещё раз.")
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")
    finally:
        await c.answer()


@router.callback_query(F.data == "svc:coaching")
async def svc_coaching(c: CallbackQuery):
    await c.message.edit_text("🎓 Коучинг\nВыберите формат:", reply_markup=coaching_kb())
    await c.answer()


@router.callback_query(F.data.startswith("coach:who:"))
async def coach_who(c: CallbackQuery):
    try:
        who = c.data.split(":")[-1]
        await c.message.edit_text("🎓 Коучинг\nВыберите пакет:", reply_markup=coaching_pack_kb(who))
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("coach:pack:"))
async def coach_pack(c: CallbackQuery):
    try:
        _, _, who, val = c.data.split(":", 3)
        pack, price = val.split(":")
        price_i = int(price)

        service = "Коучинг SSL" if who == "ssl" else "Коучинг VZM"
        details = f"{service} | {pack}"

        s(c.from_user.id)["pending_order"] = {
            "service_key": "coaching",
            "service": "Коучинг",
            "details": details,
            "price": price_i,
        }

        await c.message.edit_text(
            f"✅ *{service}*\n"
            f"Пакет: *{pack}*\n"
            f"Цена: *{price_i} ₽*\n\n"
            f"Нажмите «Оформить заявку», и оператор свяжется с вами.",
            reply_markup=order_confirm_kb("coaching"),
            parse_mode="Markdown",
        )
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")
    finally:
        await c.answer()


@router.callback_query(F.data == "svc:replay")
async def svc_replay(c: CallbackQuery):
    await c.message.edit_text(
        "🎥 Разбор реплея (SSL)\n"
        "Видео ~10 минут, срок до 48 часов.\n"
        "Выберите пакет:",
        reply_markup=replay_kb(),
    )
    await c.answer()


@router.callback_query(F.data.startswith("replay:pack:"))
async def replay_pack(c: CallbackQuery):
    try:
        _, _, n, price = c.data.split(":")
        n_i, price_i = int(n), int(price)

        details = f"Разбор реплея SSL | {n_i} реплей(ев) | до 48 часов"
        s(c.from_user.id)["pending_order"] = {
            "service_key": "replay",
            "service": "Разбор реплея",
            "details": details,
            "price": price_i,
        }

        await c.message.edit_text(
            f"✅ *Разбор реплея (SSL)*\n"
            f"Пакет: *{n_i}*\n"
            f"Цена: *{price_i} ₽*\n"
            f"Срок: *до 48 часов*\n\n"
            f"Нажмите «Оформить заявку», и оператор свяжется с вами (и попросит файл/ник).",
            reply_markup=order_confirm_kb("replay"),
            parse_mode="Markdown",
        )
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")
    finally:
        await c.answer()


@router.callback_query(F.data == "svc:play")
async def svc_play(c: CallbackQuery):
    await c.message.edit_text("🎮 Игра с VZM\nВыберите формат:", reply_markup=play_format_kb())
    await c.answer()


@router.callback_query(F.data.startswith("play:fmt:"))
async def play_fmt(c: CallbackQuery):
    try:
        fmt = c.data.split(":")[-1]
        await c.message.edit_text("🎮 Игра с VZM\nВыберите пакет:", reply_markup=play_pack_kb(fmt))
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("play:pack:"))
async def play_pack(c: CallbackQuery):
    try:
        _, _, fmt, val = c.data.split(":", 3)
        n, price = val.split(":")
        n_i, price_i = int(n), int(price)

        fmt_name = "1x1" if fmt == "1v1" else "2x2 (пати)"
        details = f"Игра с VZM | {fmt_name} | {n_i} игр"

        s(c.from_user.id)["pending_order"] = {
            "service_key": "play",
            "service": "Игра с VZM",
            "details": details,
            "price": price_i,
        }

        await c.message.edit_text(
            f"✅ *Игра с VZM*\n"
            f"Формат: *{fmt_name}*\n"
            f"Пакет: *{n_i} игр*\n"
            f"Цена: *{price_i} ₽*\n\n"
            f"Нажмите «Оформить заявку», и оператор свяжется с вами для времени/деталей.",
            reply_markup=order_confirm_kb("play"),
            parse_mode="Markdown",
        )
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("order:"))
async def create_order(c: CallbackQuery, config: Config):
    try:
        service_key = c.data.split(":")[1]

        st = s(c.from_user.id)
        po = st.get("pending_order")

        if not po or po.get("service_key") != service_key:
            await c.answer("Заявка устарела. Оформите заново.", show_alert=True)
            return

        details = po["details"]
        price = int(po["price"])
        service_name = po["service"]

        order_id = await db.create_order(
            user_id=c.from_user.id,
            username=c.from_user.username,
            service=service_name,
            details=details,
            price_rub=price,
            status="NEW",
        )

        user_link = f"@{c.from_user.username}" if c.from_user.username else f"id:{c.from_user.id}"
        text = (
            f"📦 *Новая заявка*\n"
            f"*ORDER #{order_id}*\n"
            f"Услуга: *{service_name}*\n"
            f"Детали: `{details}`\n"
            f"Цена: *{price} ₽*\n"
            f"Клиент: {user_link}"
        )

        await c.bot.send_message(
            chat_id=config.admin_chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=admin_status_kb(order_id),
        )

        st.pop("pending_order", None)

        await c.message.edit_text(
            "✅ *Заявка отправлена!*\n\n"
            "Оператор скоро свяжется с вами в личных сообщениях.\n"
            "Спасибо!",
            parse_mode="Markdown",
            reply_markup=main_menu(config.support_username),
        )
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка оформления: {e}")
    finally:
        await c.answer()


@router.callback_query(F.data.startswith("adm:st:"))
async def admin_set_status(c: CallbackQuery, config: Config):
    try:
        if c.message.chat.id != config.admin_chat_id:
            await c.answer("Недостаточно прав.", show_alert=True)
            return

        _, _, order_id, status = c.data.split(":", 3)
        order_id_i = int(order_id)

        await db.update_status(order_id_i, status)
        order = await db.get_order(order_id_i)

        if not order:
            await c.answer("Заказ не найден.", show_alert=True)
            return

        user_line = f"@{order.username}" if order.username else f"id:{order.user_id}"
        text = (
            f"📦 *Заявка*\n"
            f"*ORDER #{order.id}*\n"
            f"Услуга: *{order.service}*\n"
            f"Детали: `{order.details}`\n"
            f"Цена: *{order.price_rub} ₽*\n"
            f"Клиент: {user_line}\n\n"
            f"Статус: *{status}* (обновил @{c.from_user.username or c.from_user.id})"
        )

        await c.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_status_kb(order.id),
        )

        await c.answer("Статус обновлён ✅")
    except TelegramBadRequest:
        await c.answer("Ошибка Telegram.", show_alert=True)
    except Exception as e:
        await c.answer(f"Ошибка: {e}", show_alert=True)


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
    by_status = ", ".join([f"{k}:{v}" for k, v in st["by_status"].items()]) or "нет"

    await m.answer(
        f"*Статистика:*\n"
        f"Всего заказов: *{st['total_count']}*\n"
        f"Сумма: *{st['total_sum']} ₽*\n"
        f"По статусам: {by_status}",
        parse_mode="Markdown",
    )
