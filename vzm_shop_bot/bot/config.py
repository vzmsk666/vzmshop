import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_chat_id: int
    support_username: str | None

def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_chat_id = os.getenv("ADMIN_CHAT_ID", "").strip()
    support = os.getenv("SUPPORT_USERNAME", "").strip()

    if not token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not admin_chat_id:
        raise RuntimeError("ADMIN_CHAT_ID is not set")

    try:
        admin_chat_id_int = int(admin_chat_id)
    except ValueError:
        raise RuntimeError("ADMIN_CHAT_ID must be integer (e.g. -100...)")

    support_username = support if support else None
    if support_username and not support_username.startswith("@"):
        support_username = "@" + support_username

    return Config(
        bot_token=token,
        admin_chat_id=admin_chat_id_int,
        support_username=support_username,
    )
