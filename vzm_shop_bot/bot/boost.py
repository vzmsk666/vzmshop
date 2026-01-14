from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Mode(str, Enum):
    DUEL_1V1 = "1v1"
    DOUBLES_2V2 = "2v2"
    STANDARD_3V3 = "3v3"

class BoostType(str, Enum):
    ACCOUNT = "account"
    PARTY = "party"  # x2

RANKS_ORDER = [
    "Bronze I","Bronze II","Bronze III",
    "Silver I","Silver II","Silver III",
    "Gold I","Gold II","Gold III",
    "Platinum I","Platinum II","Platinum III",
    "Diamond I","Diamond II","Diamond III",
    "Champion I","Champion II","Champion III",
    "Grand Champion I","Grand Champion II","Grand Champion III",
    "Supersonic Legend"
]

# Price per division step for 2v2 mode (active)
PRICE_PER_DIV_2V2 = {
    "Bronze": 40,
    "Silver": 50,
    "Gold": 60,
    "Platinum": 70,
    "Diamond": 90,
    "Champion": 150,
    "Grand Champion I": 300,
    "Grand Champion II": 300,
    "Grand Champion III": 1500,  # special
}

def rank_group(rank: str) -> str:
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
    if rank.startswith("Grand Champion I"):
        return "Grand Champion I"
    if rank.startswith("Grand Champion II"):
        return "Grand Champion II"
    if rank.startswith("Grand Champion III"):
        return "Grand Champion III"
    if rank == "Supersonic Legend":
        return "Supersonic Legend"
    raise ValueError(f"Unknown rank: {rank}")

@dataclass(frozen=True)
class Position:
    rank: str
    div: Optional[int]  # None for SSL

    def is_ssl(self) -> bool:
        return self.rank == "Supersonic Legend"

def pos_to_index(pos: Position) -> int:
    # Linear scale: each non-SSL rank has div1-4 (4 steps)
    # SSL is last point after GC3 div4
    if pos.is_ssl():
        return len(RANKS_ORDER[:-1])*4  # after all divs
    rank_idx = RANKS_ORDER.index(pos.rank)
    if pos.div is None or not (1 <= pos.div <= 4):
        raise ValueError("div must be 1..4 for non-SSL")
    return rank_idx*4 + (pos.div-1)

def index_to_pos(idx: int) -> Position:
    ssl_index = len(RANKS_ORDER[:-1])*4
    if idx == ssl_index:
        return Position("Supersonic Legend", None)
    rank_idx = idx // 4
    div = (idx % 4) + 1
    return Position(RANKS_ORDER[rank_idx], div)

def price_for_step(current_pos: Position, mode: Mode) -> int:
    # Option A: boundary step is priced by CURRENT rank (the one being closed)
    if mode != Mode.DOUBLES_2V2:
        raise ValueError("Mode not enabled yet")
    if current_pos.is_ssl():
        return 0
    grp = rank_group(current_pos.rank)
    if grp in PRICE_PER_DIV_2V2:
        return PRICE_PER_DIV_2V2[grp]
    # Grand Champion I/II/III are exact matches above; others grouped.
    raise ValueError(f"No price for rank group {grp}")

def calc_boost_price(start: Position, end: Position, mode: Mode, boost_type: BoostType) -> int:
    s = pos_to_index(start)
    e = pos_to_index(end)
    if e <= s:
        raise ValueError("End must be выше старта")
    total = 0
    for idx in range(s, e):
        cur = index_to_pos(idx)
        total += price_for_step(cur, mode)
    if boost_type == BoostType.PARTY:
        total *= 2
    return int(total)
