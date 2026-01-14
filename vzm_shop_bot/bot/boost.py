from dataclasses import dataclass
from enum import Enum

class Mode(str, Enum):
    DOUBLES_2V2 = "2v2"


class BoostType(str, Enum):
    ACCOUNT = "account"
    PARTY = "party"


RANKS = [
    "Bronze I",
    "Bronze II",
    "Bronze III",
    "Silver I",
    "Silver II",
    "Silver III",
    "Gold I",
    "Gold II",
    "Gold III",
    "Platinum I",
    "Platinum II",
    "Platinum III",
    "Diamond I",
    "Diamond II",
    "Diamond III",
    "Champion I",
    "Champion II",
    "Champion III",
    "Grand Champion I",
    "Grand Champion II",
    "Grand Champion III",
    "Supersonic Legend",
]


# Новые цены за 1 дивизион (логика как раньше)
PRICE_PER_DIVISION = {
    "Bronze": 80,
    "Silver": 100,
    "Gold": 110,
    "Platinum": 130,
    "Diamond": 185,
    "Champion": 360,
    "Grand Champion": 800,
    # Особое правило: начиная с GC3 (все дивы GC3) и переход в SSL — 1500
    "GC3_SPECIAL": 1500,
}


def group_for_rank(rank: str) -> str:
    if rank.startswith("Bronze"):
        return "Bronze"
    if rank.startswith("Silver"):
        return "Silver"
    if rank.startswith("Gold"):
        return "Gold"
    if rank.startswith("Platinum"):
        return "Platinum"
    if rank.startswith("Diamond"):
        return "Diamond"
    if rank.startswith("Champion"):
        return "Champion"
    if rank.startswith("Grand Champion"):
        return "Grand Champion"
    if rank.startswith("Supersonic Legend"):
        return "SSL"
    return "Unknown"


@dataclass
class Position:
    rank: str
    div: int | None  # None для SSL


def pos_index(pos: Position) -> int:
    """
    Индекс позиции по шкале "шагов".
    Один шаг = +1 дивизион.
    SSL = отдельная конечная точка.
    """
    rank_i = RANKS.index(pos.rank)

    if pos.rank == "Supersonic Legend":
        return rank_i * 4  # div игнорируем

    # div 1..4 → шаги 0..3
    return rank_i * 4 + (pos.div - 1)


def step_price_for_rank(rank: str) -> int:
    """
    Цена одного шага (одного дивизиона) по 'текущему рангу' (логика Вариант A).
    Спец правило: все шаги в GC3 стоят GC3_SPECIAL.
    """
    if rank == "Grand Champion III":
        return PRICE_PER_DIVISION["GC3_SPECIAL"]

    group = group_for_rank(rank)
    if group == "SSL":
        # Шаги внутри SSL не считаются, SSL - конечная цель
        return PRICE_PER_DIVISION["GC3_SPECIAL"]

    return PRICE_PER_DIVISION[group]


def calc_boost_price(start: Position, end: Position, mode: Mode, boost_type: BoostType) -> int:
    """
    Считает цену буста по шагам.
    - 1 шаг = 1 дивизион
    - Div4 -> следующий ранг Div1 = цена текущего ранга (закрываем текущий)
    - GC3 дивы и GC3->SSL считаются по 1500
    - PARTY = х2
    """

    s_i = pos_index(start)
    e_i = pos_index(end)

    if e_i <= s_i:
        raise ValueError("Целевой ранг должен быть выше стартового.")

    total = 0

    current = start
    cur_i = s_i

    while cur_i < e_i:
        # шаг считается по цене текущего ранга (который закрываем)
        price_step = step_price_for_rank(current.rank)
        total += price_step

        # двигаемся на 1 шаг вперёд
        cur_i += 1

        # пересчитываем current позицию из индекса
        next_rank_i = cur_i // 4
        next_div_offset = cur_i % 4  # 0..3

        next_rank = RANKS[next_rank_i]

        if next_rank == "Supersonic Legend":
            current = Position(next_rank, None)
        else:
            current = Position(next_rank, next_div_offset + 1)

    # PARTY x2
    if boost_type == BoostType.PARTY:
        total *= 2

    return total
