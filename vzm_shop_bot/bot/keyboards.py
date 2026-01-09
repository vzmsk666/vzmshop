from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from .boost import Mode, BoostType, RANKS_ORDER

def main_menu(support_username: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Буст ранга", callback_data="svc:boost")
    kb.button(text="🎓 Коучинг", callback_data="svc:coaching")
    kb.button(text="🎥 Разбор реплея", callback_data="svc:replay")
    kb.button(text="🎮 Игра с VZM", callback_data="svc:play")
    if support_username:
        kb.button(text="🆘 Поддержка", url=f"https://t.me/{support_username.lstrip('@')}")
    kb.adjust(2,2)
    return kb.as_markup()

def back_to_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu")
    return kb.as_markup()

def boost_mode_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="1v1 (В РАЗРАБОТКЕ)", callback_data="boost:mode:1v1")
    kb.button(text="2v2 ✅", callback_data="boost:mode:2v2")
    kb.button(text="3v3 (В РАЗРАБОТКЕ)", callback_data="boost:mode:3v3")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1,1,1,1)
    return kb.as_markup()

def boost_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 Буст аккаунта", callback_data="boost:type:account")
    kb.button(text="👥 Пати с бустером (×2)", callback_data="boost:type:party")
    kb.button(text="⬅️ Назад", callback_data="svc:boost")
    kb.adjust(1,1,1)
    return kb.as_markup()

def ranks_page(prefix: str, page: int=0, page_size: int=10, allow_ssl: bool=True) -> InlineKeyboardMarkup:
    ranks = RANKS_ORDER if allow_ssl else [r for r in RANKS_ORDER if r != "Supersonic Legend"]
    start = page*page_size
    chunk = ranks[start:start+page_size]
    kb = InlineKeyboardBuilder()
    for r in chunk:
        kb.button(text=r, callback_data=f"{prefix}:{r}")
    nav = InlineKeyboardBuilder()
    if page > 0:
        nav.button(text="⬅️", callback_data=f"{prefix}:page:{page-1}")
    if start+page_size < len(ranks):
        nav.button(text="➡️", callback_data=f"{prefix}:page:{page+1}")
    if nav.buttons:
        kb.row(*nav.buttons)
    kb.button(text="⬅️ Назад", callback_data="boost:type")
    kb.adjust(1)
    return kb.as_markup()

def div_kb(prefix: str, rank: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if rank == "Supersonic Legend":
        kb.button(text="✅ SSL (без дивизионов)", callback_data=f"{prefix}:{rank}:ssl")
    else:
        for d in [1,2,3,4]:
            kb.button(text=f"Div {d}", callback_data=f"{prefix}:{rank}:{d}")
    kb.button(text="⬅️ Назад", callback_data=f"{prefix}:back_rank")
    kb.adjust(2,2,1)
    return kb.as_markup()

def order_confirm_kb(service_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Оформить заявку", callback_data=f"order:{service_key}")
    kb.button(text="⬅️ Назад", callback_data=f"svc:{service_key}")
    kb.adjust(1,1)
    return kb.as_markup()
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Оформить заявку", callback_data=f"order:{service_key}:{payload}")
    kb.button(text="⬅️ Назад", callback_data=f"svc:{service_key}")
    kb.adjust(1,1)
    return kb.as_markup()

def coaching_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏆 Коучинг от SSL", callback_data="coach:who:ssl")
    kb.button(text="⭐ Коучинг от VZM (PREMIUM)", callback_data="coach:who:vzm")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1,1,1)
    return kb.as_markup()

def coaching_pack_kb(who: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if who == "ssl":
        packs = [("1 час — 1500₽","1h:1500"),("1+1 — 2700₽ (-10%)","2h:2700"),("5 тренировок — 6375₽ (-15%)","5:6375"),("10 тренировок — 12000₽ (-20%)","10:12000")]
    else:
        packs = [("1 час — 2400₽","1h:2400"),("1+1 — 4320₽ (-10%)","2h:4320"),("5 тренировок — 10200₽ (-15%)","5:10200"),("10 тренировок — 19200₽ (-20%)","10:19200")]
    for text, val in packs:
        kb.button(text=text, callback_data=f"coach:pack:{who}:{val}")
    kb.button(text="⬅️ Назад", callback_data="svc:coaching")
    kb.adjust(1)
    return kb.as_markup()

def replay_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="1 реплей — 700₽", callback_data="replay:pack:1:700")
    kb.button(text="3 реплея — 1890₽ (-10%)", callback_data="replay:pack:3:1890")
    kb.button(text="5 реплеев — 2800₽ (-20%)", callback_data="replay:pack:5:2800")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1,1,1,1)
    return kb.as_markup()

def play_format_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="1x1", callback_data="play:fmt:1v1")
    kb.button(text="2x2 (пати)", callback_data="play:fmt:2v2")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1,1,1)
    return kb.as_markup()

def play_pack_kb(fmt: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if fmt == "1v1":
        packs = [("1 игра — 500₽","1:500"),("3 игры — 1350₽ (-10%)","3:1350"),("5 игр — 2125₽ (-15%)","5:2125"),("10 игр — 4000₽ (-20%)","10:4000")]
    else:
        packs = [("1 игра — 750₽","1:750"),("3 игры — 2025₽ (-10%)","3:2025"),("5 игр — 3190₽ (до -15%)","5:3190"),("10 игр — 6000₽ (-20%)","10:6000")]
    for text, val in packs:
        kb.button(text=text, callback_data=f"play:pack:{fmt}:{val}")
    kb.button(text="⬅️ Назад", callback_data="svc:play")
    kb.adjust(1)
    return kb.as_markup()

def admin_status_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🆕 Новый", callback_data=f"adm:st:{order_id}:NEW")
    kb.button(text="💬 Связались", callback_data=f"adm:st:{order_id}:CONTACTED")
    kb.button(text="💰 Оплата", callback_data=f"adm:st:{order_id}:PAID")
    kb.button(text="🎮 В работе", callback_data=f"adm:st:{order_id}:IN_PROGRESS")
    kb.button(text="✅ Готово", callback_data=f"adm:st:{order_id}:DONE")
    kb.button(text="❌ Отмена", callback_data=f"adm:st:{order_id}:CANCELLED")
    kb.adjust(2,2,2)
    return kb.as_markup()
