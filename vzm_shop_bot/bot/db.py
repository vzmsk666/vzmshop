import aiosqlite
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

DB_PATH = "data.sqlite3"

@dataclass
class Order:
    id: int
    created_at: str
    user_id: int
    username: str | None
    service: str
    details: str
    price_rub: int
    status: str

CREATE_SQL = '''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT,
    service TEXT NOT NULL,
    details TEXT NOT NULL,
    price_rub INTEGER NOT NULL,
    status TEXT NOT NULL
);
'''

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_SQL)
        await db.commit()

async def create_order(user_id: int, username: Optional[str], service: str, details: str, price_rub: int, status: str="NEW") -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (created_at, user_id, username, service, details, price_rub, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (created_at, user_id, username, service, details, price_rub, status),
        )
        await db.commit()
        return cur.lastrowid

async def update_status(order_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        await db.commit()

async def get_order(order_id: int) -> Optional[Order]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        row = await cur.fetchone()
        if not row:
            return None
        return Order(**dict(row))

async def list_recent_orders(limit: int=20) -> list[Order]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
        return [Order(**dict(r)) for r in rows]

async def stats() -> dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*), COALESCE(SUM(price_rub),0) FROM orders")
        total_count, total_sum = await cur.fetchone()
        cur = await db.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        by_status = {status: count for status, count in await cur.fetchall()}
        return {"total_count": total_count, "total_sum": total_sum, "by_status": by_status}
