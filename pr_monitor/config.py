"""
Konfiqurasiya - bütün parametrlər burada
"""

# ── API Açarları ──────────────────────────────────────────────
GEMINI_API_KEY = "AQ.Ab8RN6KgxvnEZxKZku7eoU40-UjbH_VlYNoeJDoL3howiRTOJg"
TELEGRAM_BOT_TOKEN = "8629640966:AAG6dsokinSmxDynaE1tEZX1KndnhqSFJAw"
TELEGRAM_CHAT_ID = "7622824986"

# ── Açar sözlər ───────────────────────────────────────────────
KEYWORDS = [
    "uşaq pulu",
    "Əmək və Əhalinin Sosial Müdafiəsi Nazirliyi",
    "Dövlət Sosial Müdafiə Fondu",
    "Dövlət Əmək Müffətişliyi Xidməti",
    "Sosial Xidmətlər Agentliyi",
    "DOST Agentliyi",
    "Anar Əliyev",
    "Ünvanlı sosial yardım",
    "Əlillik",
    "İşsizlik",
    "Dövlət Tibbi Sosial Ekpertiza və Reabilitasiya Agentliyi",
    "Minimum əmək haqqı",
]

# ── Sistem parametrləri ───────────────────────────────────────
INTERVAL_MINUTES = 15       # Hər neçə dəqiqədən bir yoxlanılsın
HOURS_BACK       = 24       # Son neçə saatın məlumatı götürülsün
MAX_WORKERS      = 4        # Paralel iş axınlarının sayı
REQUEST_TIMEOUT  = 12       # HTTP timeout (saniyə)
RETRY_COUNT      = 3        # Uğursuz sorğularda təkrar cəhd sayı
RETRY_DELAY      = 3        # Cəhdlər arası gözləmə (saniyə)

# ── Fayllar ───────────────────────────────────────────────────
SEEN_LINKS_FILE = "seen_links.json"

# ── AI Parametrləri ───────────────────────────────────────────
GEMINI_MODEL       = "gemini-2.5-flash"
AI_BATCH_SIZE      = 10     # Hər AI sorğusunda max element sayı
AI_RETRY_WAIT      = 65     # Rate limit-dən sonra gözləmə (saniyə)

# ── Telegram formatı ─────────────────────────────────────────
SENTIMENT_EMOJI = {
    "MƏNFİ":   "🔴",
    "MÜSBƏT":  "🟢",
    "NEYTRAL": "🟡",
    "RİSK":    "🟠",
}

SOURCE_EMOJI = {
    "google_news":  "📰",
    "az_news":      "🇦🇿",
    "facebook":     "👤",
    "instagram":    "📸",
    "twitter":      "🐦",
    "youtube":      "▶️",
    "tiktok":       "🎵",
    "forum":        "💬",
    "gov_az":       "🏛",
    "rss":          "📡",
}