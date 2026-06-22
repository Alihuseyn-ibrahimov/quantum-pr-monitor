"""
Telegram Göndərici Modulu
Zəngin formatlaşdırma, flood qoruması, xəta idarəetməsi
"""

import logging
import requests
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    SENTIMENT_EMOJI, SOURCE_EMOJI
)

log = logging.getLogger(__name__)
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _escape_md(text: str) -> str:
    """MarkdownV2 üçün xüsusi simvolları escape edir."""
    special = r"\_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


def _build_message(item: dict) -> str:
    """Bildiriş mətni qurur."""
    sentiment    = item.get("sentiment", "NEYTRAL")
    source_type  = item.get("source_type", "rss")
    pr_risk      = item.get("pr_risk", 0)
    action       = item.get("action_needed", False)

    s_emoji = SENTIMENT_EMOJI.get(sentiment, "🟡")
    src_emoji = SOURCE_EMOJI.get(source_type, "📡")

    # Risk çubuğu
    risk_bar = "▓" * pr_risk + "░" * (10 - pr_risk)

    lines = [
        f"{s_emoji} *PR XƏBƏRDARLİĞI*",
        "",
        f"🔑 `{item.get('keyword', '')}` ",
        f"{src_emoji} *Mənbə:* {source_type.replace('_', ' ').title()}",
        "",
        f"📌 *{item.get('title', 'Başlıqsız')[:200]}*",
        "",
        f"🧠 _{item.get('summary', '—')}_",
        "",
        f"📊 Risk: `{risk_bar}` {pr_risk}/10",
    ]

    if action:
        lines.append("⚠️ *Müdaxilə tövsiyə edilir\\!*")

    lines.append("")
    lines.append(f"🔗 [Mənbəyə keç]({item.get('link', '#')})")

    return "\n".join(lines)


def send_telegram_alert(item: dict) -> bool:
    """Bir bildiriş göndərir. Uğurlu olduqda True qaytarır."""
    try:
        message = _build_message(item)
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       message,
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": False,
            },
            timeout=12,
        )
        if resp.status_code == 200:
            log.info(f"  ✅ Göndərildi: {item.get('title', '')[:50]}...")
            return True
        else:
            # MarkdownV2 parse xətası olduqda sadə mətn ilə yenidən cəhd
            if resp.status_code == 400:
                return _send_plain(item)
            log.warning(f"  ⚠️ Telegram {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        log.error(f"  ❌ Telegram göndərmə xətası: {e}")
        return False


def _send_plain(item: dict) -> bool:
    """Formatlaşdırma xətası üçün sadə mətn variantı."""
    sentiment = item.get("sentiment", "NEYTRAL")
    s_emoji = SENTIMENT_EMOJI.get(sentiment, "🟡")
    pr_risk = item.get("pr_risk", 0)

    text = (
        f"{s_emoji} PR XƏBƏRDARLİĞI\n\n"
        f"🔑 {item.get('keyword', '')}\n"
        f"📌 {item.get('title', '')[:200]}\n\n"
        f"🧠 {item.get('summary', '—')}\n\n"
        f"📊 Risk: {pr_risk}/10\n"
        f"🔗 {item.get('link', '#')}"
    )
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=12,
        )
        return resp.status_code == 200
    except Exception:
        return False


def send_summary_report(stats: dict):
    """Monitorinq dövrünün yekun hesabatını göndərir."""
    text = (
        f"📊 *MONİTORİNQ HESABATI*\n\n"
        f"🔍 Yoxlanan açar sözlər: {stats.get('keywords', 0)}\n"
        f"📰 Tapılan yeni elementlər: {stats.get('total', 0)}\n"
        f"📨 Göndərilən bildirilər: {stats.get('sent', 0)}\n"
        f"🔴 Yüksək risk: {stats.get('high_risk', 0)}\n"
        f"⏱ Müddət: {stats.get('elapsed', 0)}s"
    )
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       text,
                "parse_mode": "Markdown",
            },
            timeout=12,
        )
    except Exception as e:
        log.warning(f"Hesabat göndərilmədi: {e}")