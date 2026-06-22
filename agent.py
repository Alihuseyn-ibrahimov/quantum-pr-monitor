"""
PR MONİTORİNQ AGENTİ  (v8 — Facebook tam dəstəyi)
====================================================
v8 yenilikləri:
  1. Facebook: rəsmi səhifələr birbaşa scrape (mbasic, login lazım deyil)
  2. Facebook: Selenium ilə giriş + axtarış (FB_EMAIL/FB_PASS varsa)
  3. Facebook: Google vasitəsilə site:facebook.com axtarışı (DuckDuckGo)
  4. FACEBOOK_PAGES — hər açar söz üçün rəsmi FB səhifə siyahısı
  5. Bütün v7 funksionallığı qorunur

Quraşdırma:
    pip install requests schedule google-generativeai beautifulsoup4 lxml
"""

import time, re, json, os, socket, datetime, urllib.parse, logging, warnings
import requests, schedule
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=FutureWarning)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("monitor.log", encoding="utf-8")],
)
log = logging.getLogger(__name__)
socket.setdefaulttimeout(12)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    log.warning("⚠️  google-generativeai yoxdur")


# ======================================================================
# 1. KONFİQURASİYA
# ======================================================================
GEMINI_API_KEY   = "AQ.Ab8RN6KgxvnEZxKZku7eoU40-UjbH_VlYNoeJDoL3howiRTOJg"
TELEGRAM_TOKEN   = "8629640966:AAG6dsokinSmxDynaE1tEZX1KndnhqSFJAw"
TELEGRAM_CHAT_ID = "7622824986"

KEYWORDS = {
    "Əmək və Əhalinin Sosial Müdafiəsi Nazirliyi":
        ["ƏƏSMN", "əəsmn", "Əmək Nazirliyi", "Sosial Nazirlik"],
    "Dövlət Sosial Müdafiə Fondu":
        ["DSMF", "dsmf", "Sosial Müdafiə Fondu", "Sosial Sığorta",
         "üdsy", "Ünvanlı dövlət sosial yardım", "ÜSY", "Zəka Mirzəyev",
         "pensiya", "sosial müavinət", "sosial ödənişlər"],
    "Dövlət Əmək Müfəttişliyi Xidməti":
        ["DƏMX", "dəmx", "Əmək Müfəttişliyi"],
    "Sosial Xidmətlər Agentliyi":
        ["SXA", "günərzi", "ahıllar evi", "uşaqlar evi", "övladlığa götürmə"],
    "DOST Agentliyi":
        ["DOST mərkəzi", "Qarabağ DOST"],
    "Anar Əliyev":
        ["Nazir Anar Əliyev"],
    "Əlillik":
        ["DTSERA", "əlillik kəsildi", "Anar Bayramov", "əlillik müavinəti"],
    "İşsizlik":
        ["işsizlikdən sığorta", "məşğulluq", "özünüməşğulluq"],
    "Dövlət Tibbi Sosial Ekspertiza və Reabilitasiya Agentliyi":
        ["DTSERA", "Tibbi Sosial Ekspertiza", "Reabilitasiya Agentliyi"],
    "Minimum əmək haqqı":
        ["minimum maaş", "əməkhaqqılar artdı"],
}

HOURS_LIMIT          = 24           # son 24 saat
MAX_PER_SOURCE       = 30           # hər mənbə üçün ayrıca limit
MAX_TOTAL_PER_KW     = 100          # bir açar söz üçün cəm limit
SEEN_EXPIRY_DAYS     = 1            # 24 saat ilə uyğun
SEEN_FILE            = "seen_links.json"
RESULTS_FILE         = "results.json"        # dashboard üçün ortaq nəticə faylı
RUN_INTERVAL_MINUTES = 30
ALIAS_SEARCH_MIN_LEN = 6

ENABLE_DUCKDUCKGO    = True
ENABLE_SELENIUM      = True
ENABLE_DIRECT_SCRAPE = True
ENABLE_TG_CHANNELS   = True
ENABLE_FACEBOOK      = True
SEND_STARTUP_PING    = True

# ── Facebook credentials (opsional — varsa Selenium daha dərin axtarır) ──
FB_EMAIL = ""   # məs: "email@gmail.com"
FB_PASS  = ""   # məs: "sifre123"

# ── Hər açar söz üçün rəsmi Facebook səhifə slug-ları ────────────────
# mbasic.facebook.com/{slug} — login olmadan public postlar oxunur
FACEBOOK_PAGES: dict[str, list[str]] = {
    "Əmək və Əhalinin Sosial Müdafiəsi Nazirliyi": [
        "ssn.gov.az",
        "azerbaycanin.emek.nazirliyi",
        "sosialnazirligi",
    ],
    "Dövlət Sosial Müdafiə Fondu": [
        "dsmf.az",
        "dsmfofficial",
        "DSMFAzerbaijan",
    ],
    "Dövlət Əmək Müfəttişliyi Xidməti": [
        "demx.gov.az",
        "demxaz",
    ],
    "Sosial Xidmətlər Agentliyi": [
        "sxa.gov.az",
        "sosialxidmetleragentliyi",
    ],
    "DOST Agentliyi": [
        "dostagentliyi",
        "dost.center.az",
        "DOSTAgentliyiAZ",
    ],
    "Anar Əliyev": [
        "anar.aliyev.minister",
    ],
    "Əlillik": [
        "dtsera.az",
        "DTSERAofficial",
    ],
    "İşsizlik": [
        "azerbaijanjobs",
        "ishalqasi.az",
    ],
    "Dövlət Tibbi Sosial Ekspertiza və Reabilitasiya Agentliyi": [
        "dtsera.az",
        "DTSERAofficial",
    ],
    "Minimum əmək haqqı": [
        "ssn.gov.az",
        "sosialnazirligi",
    ],
}

# ── RSS Feed-lər ──────────────────────────────────────────────────────
AZ_RSS_FEEDS = [
    # Əsas xəbər agentlikləri
    "https://www.azertag.az/rss",
    "https://www.trend.az/rss",
    "https://apa.az/rss",
    "https://turan.az/rss",
    # Xəbər portalları
    "https://www.1news.az/rss",
    "https://www.report.az/rss",
    "https://www.oxu.az/rss",
    "https://www.haqqin.az/rss",
    "https://day.az/rss",
    "https://azvision.az/rss",
    "https://www.musavat.com/rss",
    "https://aztv.az/rss",
    "https://lent.az/rss",
    "https://caliber.az/feed",
    "https://olaylar.az/rss.xml",
    "https://ann.az/rss",
    "https://www.azernews.az/rss",
    "https://modern.az/az/rss",
    "https://press.az/rss",
    "https://contact.az/rss",
    "https://virtualaz.org/feed",
    # Müstəqil / xarici Azərbaycan xəbərləri
    "https://www.meydan.tv/az/feed/",
    "https://www.azadliq.org/api/ztyiit_itoi",   # RFE/RL Azərbaycanca
    "https://www.bbc.com/azeri/index.xml",
    # İqtisadi/sosial fokuslu
    "https://kapital.az/rss",
    "https://banker.az/rss",
    "https://economy.az/rss",
    "https://sia.az/rss",
    # Rəsmi hökumət
    "https://sosial.gov.az/rss",
    "https://president.az/az/feed/news",
    "https://cabmin.gov.az/az/rss",
    # Neqativ mənbələr — RSS mövcud olanlar
    "https://www.meydan.tv/az/feed/",        # Meydan TV (artıq var, təkrar zərərsiz)
    "https://www.azadliq.org/api/ztyiit_itoi",
    "https://www.bizimyol.info/feed/",
    "https://kanal24.az/rss",
    "https://azxeber.com/feed/",
    "https://www.yeniavaz.com/rss",
    "https://afn.az/rss",
    "https://tribunainfo.az/rss",
    "https://sozcu.az/feed/",
    "https://azpolitika.info/feed/",
    "https://reaksiya.az/feed/",
    "https://www.xural.com/feed/",
    "https://araz.az/rss",
    "https://aktualinfo.org/feed/",
    "https://manevr.az/feed/",
    "https://teref.az/rss",
    "https://muxalifet.az/feed/",
    "https://aktor.az/rss",
    "https://paralel.az/az/rss",
    "https://buta.media/feed/",
    "https://reyting.az/rss",
    "https://yenisabah.az/feed/",
    "https://www.millitv.az/rss",
    # Yeni əlavə edilən mənbələr
    "https://qaynarinfo.az/rss",
    "https://qafqazinfo.az/rss",
    "https://teleqraf.az/rss",
    "https://teref.net/rss",
    "https://yenixeber.org/rss",
    "https://yenisoz.az/rss",
    "https://yurd.media/feed/",
    "https://unikal.az/rss",
    "https://ikisahil.az/rss",
    "https://iqtisadiyyat.az/rss",
    "https://olke.az/rss",
    "https://operativmedia.az/rss",
    "https://pravda.az/rss",
    "https://patrulaz.az/rss",
    "https://publika.az/rss",
    "https://azerbaijan-news.az/rss",
    "https://azfakt.com/rss",
    "https://azerbaycan24.com/rss",
    "https://sfera.az/rss",
    "https://demokrat.az/rss",
    "https://fed.az/rss",
    "https://faktor.az/rss",
    "https://gununsesi.info/rss",
    "https://globalinfo.az/rss",
    "https://gundelikxeber.org/rss",
    "https://konkret.az/rss",
    "https://kanal12.az/rss",
    "https://lider-media.az/rss",
    "https://xalqqazeti.az/rss",
    "https://xalq.online/rss",
    "https://xezertv.info/rss",
    "https://xalqcebhesi.az/rss",
    "https://cebheinfo.az/rss",
    "https://cumhuriyyet.az/rss",
    "https://veteninfo.az/rss",
    "https://vetennamine.az/rss",
    "https://bizimmedia.az/rss",
    "https://bayraqdar.info/rss",
    "https://baku.news/rss",
    "https://bakunews.az/rss",
    "https://newscenter.az/rss",
    "https://nuh.az/rss",
    "https://naxcivanxeberleri.az/rss",
    "https://news365.az/rss",
    "https://nocomment.az/rss",
    "https://media.az/rss",
    "https://metbuat.az/rss",
    "https://moderator.az/rss",
    "https://median.az/rss",
    "https://missiya.az/rss",
    "https://manset.az/rss",
    "https://milletinsesi.info/rss",
    "https://www.32gun.az/rss",
    "https://www.525.az/rss",
    "https://editor.az/rss",
    "https://elaz.info/rss",
    "https://e-huquq.az/rss",
    "https://qht.az/rss",
    "https://qaziler.az/rss",
    "https://aia.az/rss",
    "https://azturkxeber.az/rss",
    "https://islam.az/rss",
    "https://operativmm.az/rss",
    "https://nuhcixan.az/rss",
    "https://nk.gov.az/rss",
    "https://www.baku.ws/rss",
]

# ── NEQATİV MƏNBƏ Facebook səhifələri (mbasic scraping) ─────────────
NEGATIVE_FB_PAGES = [
    "Azad.Soz.Az",
    "azadliqradiosu",
    "HamamTimes",
    "MeydanTelevision",
    "azadliqqazeti",
    "Sancaq",
    "AzerbaycanSaati",
    "bizimyolinfo",
    "BBCnewsAzeri",
    "buta.media1",
    "BakuTimes.Tv",
    "KANAL24AZ",
    "azxebercom",
    "reyting.az",
    "arazmediagroup",
    "xeberle",
    "yeniavaz2016",
    "AFNAZNEWS",
    "manevr.az",
    "Birxeber.az",
    "Aktor.Az",
    "tribunainfoaz",
    "aktualinfo.org",
    "azpolitika.info",
    "tvkanal13",
    "hurriyyet.org",
    "TIMETVMEDIAGROUP",
    "ToplumTv",
    "azadmediaLAFTV",
    "oguztv.azerbaijan",
    "TvPressklub",
    "Millitv.azerbaycan",
    "cenubmediatv",
    "tvreaksiya",
    "talktvit",
    # Yeni əlavə edilən FB mənbələri
    "AbzasMedia",
    "ajmedia.az",
    "AzadHaqq",
    "toplumtv",
]

# ── NEQATİV MƏNBƏ saytları (birbaşa scraping) ────────────────────────
NEGATIVE_DIRECT_SITES = [
    ("https://www.meydan.tv/az/",       "meydan.tv"),
    ("https://www.azadliq.org/",        "azadliq.org"),
    ("https://www.bizimyol.info/",      "bizimyol.info"),
    ("https://kanal24.az/",             "kanal24.az"),
    ("https://azxeber.com/",            "azxeber.com"),
    ("https://www.yeniavaz.com/",       "yeniavaz.com"),
    ("https://afn.az/",                 "afn.az"),
    ("https://tribunainfo.az/",         "tribunainfo.az"),
    ("https://sozcu.az/",               "sozcu.az"),
    ("https://azpolitika.info/",        "azpolitika.info"),
    ("https://reaksiya.az/",            "reaksiya.az"),
    ("https://www.xural.com/",          "xural.com"),
    ("https://araz.az/",                "araz.az"),
    ("https://aktualinfo.org/",         "aktualinfo.org"),
    ("https://manevr.az/",              "manevr.az"),
    ("https://teref.az/",               "teref.az"),
    ("https://muxalifet.az/",           "muxalifet.az"),
    ("https://aktor.az/",               "aktor.az"),
    ("https://paralel.az/az/",          "paralel.az"),
    ("https://buta.media/",             "buta.media"),
    ("https://reyting.az/",             "reyting.az"),
    ("https://yenisabah.az/",           "yenisabah.az"),
    ("https://www.millitv.az/",         "millitv.az"),
    ("https://arazmedia.az/",           "arazmedia.az"),
    ("https://www.dia-az.info/",        "dia-az.info"),
    ("https://hurriyyet.az/az/",        "hurriyyet.az"),
    ("https://azadmedia.az/",           "azadmedia.az"),
    ("https://mediatv.az/",             "mediatv.az"),
    ("https://azel.tv/",                "azel.tv"),
    # Yeni əlavə edilən saytlar
    ("https://qaynarinfo.az/",          "qaynarinfo.az"),
    ("https://qafqazinfo.az/",          "qafqazinfo.az"),
    ("https://qht.az/",                 "qht.az"),
    ("https://qaziler.az/",             "qaziler.az"),
    ("https://e-huquq.az/",             "e-huquq.az"),
    ("https://elaz.info/",              "elaz.info"),
    ("https://editor.az/",              "editor.az"),
    ("https://teleqraf.az/",            "teleqraf.az"),
    ("https://teref.net/",              "teref.net"),
    ("https://yenixeber.org/",          "yenixeber.org"),
    ("https://yenisoz.az/",             "yenisoz.az"),
    ("https://yurd.media/",             "yurd.media"),
    ("https://unikal.az/",              "unikal.az"),
    ("https://ikisahil.az/",            "ikisahil.az"),
    ("https://iqtisadiyyat.az/",        "iqtisadiyyat.az"),
    ("https://olke.az/",                "olke.az"),
    ("https://operativmm.az/",          "operativmm.az"),
    ("https://operativmedia.az/",       "operativmedia.az"),
    ("https://pravda.az/",              "pravda.az"),
    ("https://patrulaz.az/",            "patrulaz.az"),
    ("https://publika.az/",             "publika.az"),
    ("https://azerbaijan-news.az/",     "azerbaijan-news.az"),
    ("https://azfakt.com/",             "azfakt.com"),
    ("https://aia.az/",                 "aia.az"),
    ("https://azturkxeber.az/",         "azturkxeber.az"),
    ("https://azerbaycan24.com/",       "azerbaycan24.com"),
    ("https://sfera.az/",               "sfera.az"),
    ("https://demokrat.az/",            "demokrat.az"),
    ("https://fed.az/",                 "fed.az"),
    ("https://faktor.az/",              "faktor.az"),
    ("https://gununsesi.info/",         "gununsesi.info"),
    ("https://globalinfo.az/",          "globalinfo.az"),
    ("https://gundelikxeber.org/",      "gundelikxeber.org"),
    ("https://islam.az/",               "islam.az"),
    ("https://konkret.az/",             "konkret.az"),
    ("https://kanal12.az/",             "kanal12.az"),
    ("https://lider-media.az/",         "lider-media.az"),
    ("https://xalqqazeti.az/",          "xalqqazeti.az"),
    ("https://xalq.online/",            "xalq.online"),
    ("https://xezertv.info/",           "xezertv.info"),
    ("https://xalqcebhesi.az/",         "xalqcebhesi.az"),
    ("https://cebheinfo.az/",           "cebheinfo.az"),
    ("https://cumhuriyyet.az/",         "cumhuriyyet.az"),
    ("https://veteninfo.az/",           "veteninfo.az"),
    ("https://vetennamine.az/",         "vetennamine.az"),
    ("https://bizimmedia.az/",          "bizimmedia.az"),
    ("https://bayraqdar.info/",         "bayraqdar.info"),
    ("https://baku.news/",              "baku.news"),
    ("https://bakunews.az/",            "bakunews.az"),
    ("https://www.baku.ws/",            "baku.ws"),
    ("https://newscenter.az/",          "newscenter.az"),
    ("https://nuh.az/",                 "nuh.az"),
    ("https://naxcivanxeberleri.az/",   "naxcivanxeberleri.az"),
    ("https://nuhcixan.az/",            "nuhcixan.az"),
    ("https://news365.az/",             "news365.az"),
    ("https://nocomment.az/",           "nocomment.az"),
    ("https://media.az/",               "media.az"),
    ("https://metbuat.az/",             "metbuat.az"),
    ("https://moderator.az/",           "moderator.az"),
    ("https://median.az/",              "median.az"),
    ("https://missiya.az/",             "missiya.az"),
    ("https://manset.az/",              "manset.az"),
    ("https://milletinsesi.info/",      "milletinsesi.info"),
    ("https://www.32gun.az/",           "32gun.az"),
    ("https://www.525.az/",             "525.az"),
    ("https://nk.gov.az/",              "nk.gov.az"),
]

# ── Birbaşa scrape ediləcək saytlar (RSS yoxdur/işləmir) ─────────────
DIRECT_SCRAPE_SITES = [
    ("https://www.azertag.az/az/xeber",          "azertag.az"),
    ("https://report.az/az/",                     "report.az"),
    ("https://1news.az/",                         "1news.az"),
    ("https://trend.az/azerbaijan/",              "trend.az"),
    ("https://lent.az/",                          "lent.az"),
    ("https://oxu.az/",                           "oxu.az"),
    ("https://www.haqqin.az/",                    "haqqin.az"),
]

# ── Açıq Telegram kanalları ──────────────────────────────────────────
TG_CHANNELS = [
    # Rəsmi nazirliklər / qurumlar
    "sosialnazirliyiaz",     # Əmək Nazirliyi
    "dsmfaz",                # DSMF
    "dost_agentliyi",        # DOST Agentliyi
    "sxaaz",                 # Sosial Xidmətlər Agentliyi
    # Xəbər kanalları
    "azertag",
    "trend_az",
    "reportaz",
    "1newsaz",
    "lentaz",
    "oxuaz",
    "haqqin_az",
    "apa_az",
    "caliber_az",
    "meydan_tv",
    "turanaz",
]

if GEMINI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    _gemini_model = genai.GenerativeModel("gemini-2.5-flash")
else:
    _gemini_model = None


# ======================================================================
# 2. MATCHING
# ======================================================================
AZ_MAP = {
    "ə":"e","Ə":"e","ı":"i","İ":"i","ö":"o","Ö":"o",
    "ü":"u","Ü":"u","ş":"s","Ş":"s","ç":"c","Ç":"c","ğ":"g","Ğ":"g",
}
STOPWORDS = {"ve","ile","ucun","da","de","the","of","and","uzre","bir","bu","o"}

def normalize(text: str) -> str:
    text = text.lower()
    for a, l in AZ_MAP.items():
        text = text.replace(a, l)
    return text

def _sig_words(phrase_norm: str) -> list:
    return [w for w in phrase_norm.split() if w not in STOPWORDS and len(w) >= 3]

def _word_present(word_norm: str, text_norm: str) -> bool:
    if re.search(r"(?<![a-z])" + re.escape(word_norm) + r"(?![a-z])", text_norm):
        return True
    if len(word_norm) >= 5:
        return bool(re.search(r"(?<![a-z])" + re.escape(word_norm[:5]), text_norm))
    return False

def _phrase_matches(phrase: str, text: str) -> bool:
    pn = normalize(phrase)
    tn = normalize(text)
    sig = _sig_words(pn)
    if not sig:
        return False
    if len(sig) == 1:
        return _word_present(sig[0], tn)
    if len(sig) <= 3:
        pat = r"(?<![a-z])" + re.escape(pn) + r"(?:[a-z]{0,4})?(?![a-z])"
        if re.search(pat, tn):
            return True
        return all(_word_present(w, tn) for w in sig)
    anchor = _word_present(sig[-1], tn)
    present = sum(1 for w in sig if _word_present(w, tn))
    return anchor and present >= (len(sig) - 1)

def keyword_matches(keyword: str, text: str, aliases=None) -> bool:
    if _phrase_matches(keyword, text):
        return True
    for a in (aliases or []):
        is_acronym = a.isupper() and len(a) <= 6 and len(a.split()) == 1
        if is_acronym:
            if re.search(r"(?<![\wƏəĞğŞşÇçÖöÜüİı])" + re.escape(a)
                         + r"(?![\wƏəĞğŞşÇçÖöÜüİı])", text):
                return True
        else:
            if _phrase_matches(a, text):
                return True
    return False

def matches_any(keyword: str, aliases, *texts: str) -> bool:
    return any(keyword_matches(keyword, t, aliases) for t in texts if t)


# ======================================================================
# 3. TARİX FİLTRİ
# ======================================================================
def is_recent(pub_date_str: str, hours: int = HOURS_LIMIT):
    if not pub_date_str:
        return None   # tarix bilinmir → keç (itirmə)
    now    = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=hours)
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pub_date_str) >= cutoff
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(pub_date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt >= cutoff
        except ValueError:
            pass
    return None


# ======================================================================
# 4. GÖRÜLMÜŞ LİNKLƏR
# ======================================================================
def _load_seen() -> dict:
    try:
        with open(SEEN_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):
            today = datetime.date.today().isoformat()
            data  = {lnk: today for lnk in data}
        return data
    except Exception:
        return {}

def _save_seen(links: list):
    data  = _load_seen()
    today = datetime.date.today()
    for lnk in links:
        data.setdefault(lnk, today.isoformat())
    cleaned = {
        lnk: ds for lnk, ds in data.items()
        if (today - datetime.date.fromisoformat(ds)).days <= SEEN_EXPIRY_DAYS
    }
    removed = len(data) - len(cleaned)
    if removed:
        log.info(f"    🧹 {removed} köhnə link silindi")
    with open(SEEN_FILE, "w") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)


def _append_results(items: list):
    """Göndərilən xəbərləri results.json-a əlavə et (son 48 saat saxlanılır)."""
    try:
        existing = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, encoding="utf-8") as f:
                existing = json.load(f)
        cutoff = datetime.datetime.now() - datetime.timedelta(days=366)
        kept = []
        for r in existing:
            try:
                if datetime.datetime.fromisoformat(r.get("saved_at", "")) >= cutoff:
                    kept.append(r)
            except Exception:
                pass
        now_str = datetime.datetime.now().isoformat()
        for it in items:
            kept.append({
                "title":     it.get("title", ""),
                "link":      it.get("link", "#"),
                "summary":   it.get("summary", ""),
                "sentiment": it.get("sentiment", "NEYTRAL"),
                "keyword":   it.get("keyword", ""),
                "source":    it.get("source", ""),
                "saved_at":  now_str,
            })
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(kept, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"results.json yazılmadı: {e}")


# ======================================================================
# 5. HTTP YARDIMÇILARI
# ======================================================================
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
_UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
_HEADERS = {"User-Agent": _UA, "Accept-Language": "az-AZ,az;q=0.9,en;q=0.8"}

def _rss_link(item) -> str:
    """
    RSS <item> elementindən düzgün URL-i al.
    BeautifulSoup bəzən <link> teqini boş qaytarır (lent.az, teleqraf.az və s.).
    Prioritet: <link> → <guid> → <enclosure url> → boş string.
    """
    # 1. Standart <link> — amma bəzi parserlarda boş olur
    raw = (item.link.text or "").strip() if item.link else ""
    if raw.startswith("http"):
        return raw

    # 2. BeautifulSoup <link> teqini bəzən NavigableString kimi saxlayır
    lnk = item.find("link")
    if lnk:
        # next_sibling — lent.az kimi saytlarda link mətni teqin kənarında olur
        ns = getattr(lnk, "next_sibling", None)
        if ns and str(ns).strip().startswith("http"):
            return str(ns).strip()
        if lnk.string and str(lnk.string).strip().startswith("http"):
            return str(lnk.string).strip()

    # 3. <guid> — çox vaxt həqiqi URL saxlayır
    if item.guid:
        g = (item.guid.text or "").strip()
        if g.startswith("http"):
            return g

    # 4. <enclosure> — media RSS-lərdə
    enc = item.find("enclosure")
    if enc and enc.get("url", "").startswith("http"):
        return enc["url"]

    return ""


def _source_from_url(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _article_pub_date(url: str) -> str:
    """
    Məqalə səhifəsindən nəşr tarixini oxu.
    meta[article:published_time], JSON-LD, <time datetime> yoxlanılır.
    Tapılmazsa boş string qaytarır.
    """
    try:
        resp = _get(url, timeout=8)
        if not resp:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        # 1. Meta teqlər
        for sel, attr in [
            ('meta[property="article:published_time"]', "content"),
            ('meta[name="pubdate"]',                    "content"),
            ('meta[name="date"]',                       "content"),
            ('meta[itemprop="datePublished"]',          "content"),
            ('meta[name="DC.date.issued"]',             "content"),
        ]:
            tag = soup.select_one(sel)
            if tag and tag.get(attr):
                return tag[attr]
        # 2. JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        d = item.get("datePublished") or item.get("dateCreated")
                        if d:
                            return d
            except Exception:
                pass
        # 3. <time datetime>
        tag = soup.find("time", attrs={"datetime": True})
        if tag:
            return tag["datetime"]
    except Exception:
        pass
    return ""

def _get(url: str, timeout: int = 10, mobile: bool = False) -> requests.Response | None:
    headers = dict(_HEADERS)
    if mobile:
        headers["User-Agent"] = _UA_MOBILE
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        return r if r.status_code == 200 else None
    except Exception:
        return None


# ======================================================================
# 6. MƏNBƏ 1 — GOOGLE NEWS
# ======================================================================
def _google_news_query(session, query: str, keyword: str, aliases: list,
                       seen: dict, seen_g: set) -> list:
    """Yalnız Azərbaycan dili sorğusu — Rus sorğuları eyni məqalələri qaytarır."""
    items_out = []
    enc = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={enc}&hl=az&gl=AZ&ceid=AZ:az"
    try:
        resp = session.get(url, timeout=12)
        if resp.status_code != 200:
            log.warning(f"    ⚠️ Google [{query[:25]}]: {resp.status_code}")
            return []
        soup  = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        d_old = d_nokw = d_seen = d_seeng = 0
        for it in items:
            title    = (it.title.text   or "").strip()
            link     = _rss_link(it)
            pub_date = (it.pubDate.text or "").strip()
            desc     = (it.description.text or "").strip() if it.description else ""
            if not title or not link:
                continue
            if link in seen_g:
                d_seeng += 1; continue
            seen_g.add(link)
            if link in seen:
                d_seen += 1; continue
            if not is_recent(pub_date):
                d_old += 1; continue
            if not matches_any(keyword, aliases, title, desc):
                d_nokw += 1; continue
            items_out.append({"title": title, "link": link, "pub_date": pub_date,
                              "source": _source_from_url(link), "desc": desc})
            if len(items_out) >= MAX_PER_SOURCE:
                break
        log.info(f"    [Google/{query[:25]}] {len(items)} tapıldı → "
                 f"✅{len(items_out)} yeni "
                 f"(köhnə:{d_old} uyğunsuz:{d_nokw} "
                 f"seen:{d_seen} run-daxili-təkrar:{d_seeng})")
    except Exception as e:
        log.error(f"    ❌ Google [{query[:25]}]: {e}")
    return items_out


def _google_news(keyword: str, aliases: list) -> list:
    log.info("  📡 [GOOGLE NEWS]")
    seen   = _load_seen()
    seen_g : set = set()
    result : list = []

    session = requests.Session()
    session.headers.update({**_HEADERS, "Accept": "application/xml"})
    try:
        session.get("https://www.google.com", timeout=8); time.sleep(0.5)
    except Exception:
        pass

    result.extend(_google_news_query(session, keyword, keyword, aliases, seen, seen_g))

    # Uzun alias-lar da ayrıca axtarılır
    seen_queries = {keyword}
    for alias in aliases:
        if (len(alias) >= ALIAS_SEARCH_MIN_LEN and not alias.isupper()
                and alias not in seen_queries and len(result) < MAX_TOTAL_PER_KW):
            seen_queries.add(alias)
            new = _google_news_query(session, alias, keyword, aliases, seen, seen_g)
            existing = {i["link"] for i in result}
            result.extend(i for i in new if i["link"] not in existing)
            time.sleep(1)

    log.info(f"    ✅ Google News cəmi: {len(result)}")
    return result


# ======================================================================
# 7. MƏNBƏ 2 — AZ RSS FEED-LƏRİ
# ======================================================================
def _az_rss(keyword: str, aliases: list) -> list:
    log.info("  📡 [AZ RSS FEED-LƏRİ]")
    seen = _load_seen()
    all_items : list = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; RSSReader)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })

    for feed_url in AZ_RSS_FEEDS:
        try:
            resp = session.get(feed_url, timeout=8)
            if not resp or resp.status_code != 200:
                continue
            soup  = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")
            matched = 0
            for it in items:
                title    = (it.title.text   or "").strip()
                link     = _rss_link(it)
                desc     = (it.description.text or "").strip() if it.description else ""
                pub_date = (it.pubDate.text or "").strip()     if it.pubDate else ""
                if not title or not link or link in seen:
                    continue
                if not is_recent(pub_date):
                    continue
                if not matches_any(keyword, aliases, title, desc):
                    continue
                all_items.append({"title": title, "link": link, "pub_date": pub_date,
                                  "source": _source_from_url(link) or feed_url, "desc": desc})
                matched += 1
                if matched >= MAX_PER_SOURCE:
                    break
            if matched:
                log.info(f"    → {_source_from_url(feed_url)}: {matched}")
        except Exception:
            pass
        time.sleep(0.15)

    log.info(f"    ✅ RSS cəmi: {len(all_items)}")
    return all_items


# ======================================================================
# 8. MƏNBƏ 3 — BİRBAŞA SAYT SCRAPING
# ======================================================================
def _direct_scrape(keyword: str, aliases: list) -> list:
    if not ENABLE_DIRECT_SCRAPE:
        return []
    log.info("  📡 [BİRBAŞA SAYT SCRAPING]")
    seen = _load_seen()
    result : list = []

    for base_url, domain in DIRECT_SCRAPE_SITES:
        try:
            resp = _get(base_url, timeout=10)
            if not resp:
                continue
            soup  = BeautifulSoup(resp.text, "html.parser")
            found = 0
            # Xəbər linklərini tap (ən çox istifadə edilən strukturlar)
            for a in soup.find_all("a", href=True):
                href  = a["href"].strip()
                title = a.get_text(strip=True)
                if len(title) < 10:
                    continue
                # Nisbi URL-ləri tam et
                if href.startswith("/"):
                    parsed = urllib.parse.urlparse(base_url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                if not href.startswith("http"):
                    continue
                if href in seen:
                    continue
                if not matches_any(keyword, aliases, title):
                    continue
                # Saytdan nəşr tarixini oxu və 24 saat filtrini tətbiq et
                pub_date = _article_pub_date(href)
                if not is_recent(pub_date):
                    log.debug(f"      ✂️ köhnə/tarixin yoxdur: {title[:40]}")
                    continue
                result.append({"title": title, "link": href, "pub_date": pub_date,
                               "source": domain, "desc": ""})
                found += 1
                if found >= 15:
                    break
            if found:
                log.info(f"    → {domain}: {found}")
        except Exception as e:
            log.debug(f"    ⚠️ {domain}: {e}")
        time.sleep(0.3)

    log.info(f"    ✅ Birbaşa scraping cəmi: {len(result)}")
    return result


# ======================================================================
# 9. MƏNBƏ 4 — AÇIQ TELEGRAM KANALLARI (t.me/s/)
# ======================================================================
def _telegram_channels(keyword: str, aliases: list) -> list:
    if not ENABLE_TG_CHANNELS:
        return []
    log.info("  📡 [TELEGRAM KANALLARI]")
    seen   = _load_seen()
    result : list = []

    for ch in TG_CHANNELS:
        url = f"https://t.me/s/{ch}"
        try:
            resp = _get(url, timeout=10)
            if not resp:
                continue
            soup  = BeautifulSoup(resp.text, "html.parser")
            found = 0
            for msg in soup.find_all("div", class_="tgme_widget_message_text"):
                text = msg.get_text(separator=" ", strip=True)
                if len(text) < 15 or not matches_any(keyword, aliases, text):
                    continue
                # Postun linki
                wrap = msg.find_parent("div", class_="tgme_widget_message_wrap")
                post_link = ""
                if wrap:
                    time_tag = wrap.find("a", class_="tgme_widget_message_date")
                    post_link = time_tag["href"] if time_tag and time_tag.get("href") else ""
                if not post_link or post_link in seen:
                    continue
                # Başlıq — ilk 100 simvol
                title = text[:100].rstrip() + ("…" if len(text) > 100 else "")
                result.append({"title": f"[TG/{ch}] {title}", "link": post_link,
                               "pub_date": "", "source": f"t.me/{ch}", "desc": text[:400]})
                found += 1
                if found >= 10:
                    break
            if found:
                log.info(f"    → t.me/{ch}: {found}")
        except Exception as e:
            log.debug(f"    ⚠️ t.me/{ch}: {e}")
        time.sleep(0.5)

    log.info(f"    ✅ Telegram kanalları cəmi: {len(result)}")
    return result


# ======================================================================
# 10. MƏNBƏ 5 — FACEBOOK (3 yanaşma)
# ======================================================================

def _fb_scrape_page(slug: str, keyword: str, aliases: list, seen: dict) -> list:
    """mbasic vasitəsilə bir rəsmi Facebook səhifəsini oxu (login lazım deyil)."""
    result = []
    for base in [f"https://mbasic.facebook.com/{slug}",
                 f"https://mbasic.facebook.com/pg/{slug}/posts"]:
        try:
            resp = _get(base, mobile=True, timeout=12)
            if not resp or len(resp.text) < 500:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            post_blocks = (soup.find_all("div", attrs={"data-ft": True}) or
                           soup.find_all("article") or
                           soup.find_all("div", class_=re.compile(r"story_body|userContent")))
            if not post_blocks:
                body = soup.find("div", id="root") or soup.body
                if body:
                    post_blocks = [body]

            for block in post_blocks[:40]:
                text = block.get_text(separator=" ", strip=True)
                if len(text) < 20 or not matches_any(keyword, aliases, text):
                    continue
                link = ""
                for pat in [r"/permalink/", r"/posts/", r"story_fbid", r"fbid="]:
                    a = block.find("a", href=re.compile(pat))
                    if a:
                        link = a.get("href", "")
                        break
                if not link:
                    link = f"https://www.facebook.com/{slug}"
                if link.startswith("/"):
                    link = "https://www.facebook.com" + link
                link = link.split("?")[0]
                if link in seen:
                    continue
                title = text[:120].rstrip() + ("..." if len(text) > 120 else "")
                result.append({"title": f"[FB/{slug}] {title}",
                               "link": link, "pub_date": "",
                               "source": "facebook.com", "desc": text[:500]})
                if len(result) >= 10:
                    break
            if result:
                break
        except Exception as e:
            log.debug(f"      mbasic/{slug}: {e}")
    return result


def _fb_selenium_search(keyword: str, aliases: list, seen: dict) -> list:
    """Selenium ile Facebook axtarisi. FB_EMAIL/FB_PASS varsa login edir."""
    if not (ENABLE_SELENIUM and SELENIUM_AVAILABLE):
        return []
    result = []
    opts = Options()
    for arg in ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1280,900"]:
        opts.add_argument(arg)
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"user-agent={_UA}")
    try:
        driver = webdriver.Chrome(options=opts)
        driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    except Exception as e:
        log.debug(f"    Selenium Chrome acilmadi: {e}")
        return []

    try:
        if FB_EMAIL and FB_PASS:
            try:
                driver.get("https://www.facebook.com/login")
                time.sleep(3)
                driver.find_element(By.ID, "email").send_keys(FB_EMAIL)
                driver.find_element(By.ID, "pass").send_keys(FB_PASS)
                driver.find_element(By.NAME, "login").click()
                time.sleep(5)
                log.info("    Facebook login edildi")
            except Exception as e:
                log.warning(f"    Facebook login ugursuz: {e}")

        search_terms = [keyword] + [a for a in aliases
                                    if 4 <= len(a) <= 30 and not a.isupper()][:2]
        for term in search_terms:
            enc = urllib.parse.quote(term)
            url = (f"https://www.facebook.com/search/posts/?q={enc}"
                   if FB_EMAIL else
                   f"https://mbasic.facebook.com/search/posts/?q={enc}")
            try:
                driver.get(url)
                time.sleep(4)
                for _ in range(3):
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.5)
                seen_hrefs: set = set()
                for a in driver.find_elements(By.TAG_NAME, "a")[:150]:
                    try:
                        href = a.get_attribute("href") or ""
                        text = a.text.strip()
                        if (len(text) < 15
                                or "facebook.com" not in href
                                or not matches_any(keyword, aliases, text)):
                            continue
                        if href in seen or href in seen_hrefs:
                            continue
                        if not re.search(
                                r"/posts/|/permalink/|story_fbid|/videos/|/photos/",
                                href):
                            continue
                        seen_hrefs.add(href)
                        link = href.split("?")[0]
                        title = text[:120].rstrip() + ("..." if len(text) > 120 else "")
                        result.append({"title": f"[FB/search] {title}",
                                       "link": link, "pub_date": "",
                                       "source": "facebook.com", "desc": text[:500]})
                        if len(result) >= 20:
                            break
                    except Exception:
                        continue
                if result:
                    log.info(f"    Selenium FB '{term[:25]}': {len(result)}")
            except Exception as e:
                log.debug(f"    Selenium FB search: {e}")
            time.sleep(2)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return result


def _facebook(keyword: str, aliases: list) -> list:
    """
    Facebook ucun 3 yenasma:
      1. Resmi sehifeler birbasx mbasic - login lazim deyil
      2. Selenium ile axtaris (FB_EMAIL/FB_PASS varsa login edir)
      3. DuckDuckGo modulunda site:facebook.com artiq var
    """
    if not ENABLE_FACEBOOK:
        return []
    log.info("  📡 [FACEBOOK]")
    seen       = _load_seen()
    result     : list = []
    seen_links : set  = set()

    # 1. Resmi sehifeler (mbasic)
    for slug in FACEBOOK_PAGES.get(keyword, []):
        items = _fb_scrape_page(slug, keyword, aliases, seen)
        for it in items:
            if it["link"] not in seen_links:
                result.append(it)
                seen_links.add(it["link"])
        if items:
            log.info(f"    mbasic/{slug}: {len(items)}")
        time.sleep(0.8)

    # 2. Selenium axtarisi
    for it in _fb_selenium_search(keyword, aliases, seen):
        if it["link"] not in seen_links:
            result.append(it)
            seen_links.add(it["link"])

    log.info(f"    Facebook cemi: {len(result)}")
    return result


# ======================================================================
# NEQATİV MƏNBƏ SKANER — Facebook + saytlar
# ======================================================================
def _negative_sources(keyword: str, aliases: list) -> list:
    """
    Siyahıdakı 57 neqativ media mənbəsini skan edir.
    Tapılan xəbərlər avtomatik MƏNFİ sentiment alır.
    """
    log.info("  📡 [NEQATİV MƏNBƏLƏR]")
    seen       = _load_seen()
    result     : list = []
    seen_links : set  = set()

    def _add(item: dict):
        lnk = item.get("link", "")
        if lnk and lnk not in seen_links and lnk not in seen:
            item["_force_negative"] = True   # Gemini-dən asılı olmayaraq MƏNFİ
            result.append(item)
            seen_links.add(lnk)

    # 1. Facebook səhifələri (mbasic)
    fb_found = 0
    for slug in NEGATIVE_FB_PAGES:
        items = _fb_scrape_page(slug, keyword, aliases, seen)
        for it in items:
            it["source"] = f"[NEQ] {it.get('source', slug)}"
            _add(it)
            fb_found += 1
        time.sleep(0.5)
    if fb_found:
        log.info(f"    → Neqativ FB: {fb_found}")

    # 2. Saytlar birbaşa scraping
    site_found = 0
    for base_url, domain in NEGATIVE_DIRECT_SITES:
        try:
            resp = _get(base_url, timeout=8)
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href  = a["href"].strip()
                title = a.get_text(strip=True)
                if len(title) < 10:
                    continue
                if href.startswith("/"):
                    parsed = urllib.parse.urlparse(base_url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                if not href.startswith("http"):
                    continue
                if not matches_any(keyword, aliases, title):
                    continue
                clean_href = href.split("?")[0]
                pub_date = _article_pub_date(clean_href)
                if not is_recent(pub_date):
                    continue
                _add({"title": title, "link": clean_href,
                      "pub_date": pub_date, "source": f"[NEQ] {domain}", "desc": ""})
                site_found += 1
                if site_found >= MAX_PER_SOURCE:
                    break
        except Exception:
            pass
        time.sleep(0.2)
    if site_found:
        log.info(f"    → Neqativ saytlar: {site_found}")

    log.info(f"    ✅ Neqativ mənbələr cəmi: {len(result)}")
    return result


# ======================================================================
# 11. MƏNBƏ 6 — DUCKDUCKGO (sosial + ümumi AZ xəbər)
# ======================================================================
def _duckduckgo(keyword: str, aliases: list) -> list:
    if not ENABLE_DUCKDUCKGO:
        return []
    log.info("  📡 [DUCKDUCKGO]")
    seen = _load_seen()
    result : list = []

    session = requests.Session()
    session.headers.update({
        "User-Agent": _UA,
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://duckduckgo.com/",
        "Origin": "https://duckduckgo.com",
    })
    try:
        r = session.get("https://duckduckgo.com", timeout=5)
        if r.status_code != 200:
            log.warning("    ⚠️ DuckDuckGo əlçatmaz — atlanır")
            return []
        time.sleep(1)
    except Exception:
        log.warning("    ⚠️ DuckDuckGo bağlantı yoxdur — atlanır")
        return []

    # AZ xəbər saytları + sosial media
    az_news_domains = (
        "site:azertag.az OR site:trend.az OR site:1news.az OR site:report.az "
        "OR site:oxu.az OR site:lent.az OR site:haqqin.az OR site:caliber.az "
        "OR site:day.az OR site:apa.az OR site:olaylar.az"
    )
    queries = [
        (f'"{keyword}" {az_news_domains}',              "AZ Xəbərlər"),
        (f'"{keyword}" site:facebook.com',              "Facebook"),
        (f'"{keyword}" site:x.com OR site:twitter.com', "X/Twitter"),
        (f'"{keyword}" site:t.me',                      "Telegram"),
        (f'"{keyword}" site:instagram.com',             "Instagram"),
    ]
    seen_links : set = set()

    for query, pname in queries:
        try:
            resp = session.post("https://html.duckduckgo.com/html/",
                                data={"q": query, "df": "d"}, timeout=10)
            if not resp or resp.status_code != 200:
                continue
            soup  = BeautifulSoup(resp.text, "html.parser")
            found = 0
            for div in soup.find_all("div", class_="result"):
                t_tag = div.find("h2", class_="result__title")
                s_tag = div.find("a",  class_="result__snippet")
                d_tag = div.find("span", class_="result__timestamp")
                if not t_tag:
                    continue
                title   = t_tag.get_text(strip=True)
                snippet = s_tag.get_text(strip=True) if s_tag else ""
                d_text  = d_tag.get_text(strip=True) if d_tag else ""

                a_tag = t_tag.find("a", class_="result__a") or t_tag.find("a")
                if not a_tag:
                    continue
                raw  = a_tag.get("href", "")
                link = raw
                if "uddg=" in raw:
                    try:
                        link = urllib.parse.unquote(
                            urllib.parse.parse_qs(
                                urllib.parse.urlparse(raw).query
                            ).get("uddg", [raw])[0]
                        )
                    except Exception:
                        pass
                elif raw.startswith("//duckduckgo.com/l/"):
                    try:
                        link = urllib.parse.unquote(
                            urllib.parse.parse_qs(
                                urllib.parse.urlparse("https:" + raw).query
                            ).get("uddg", [raw])[0]
                        )
                    except Exception:
                        pass

                if not link.startswith("http") or len(title) < 5:
                    continue
                if link in seen or link in seen_links:
                    continue

                if d_text:
                    dl = d_text.lower()
                    m  = re.search(r"(\d+)\s*day", dl)
                    if (m and int(m.group(1)) > 1) or re.search(r"week|month|year", dl):
                        continue

                if not matches_any(keyword, aliases, title, snippet):
                    continue

                seen_links.add(link)
                result.append({"title": f"[{pname}] {title}", "link": link,
                               "pub_date": d_text, "source": pname, "snippet": snippet})
                found += 1
                if found >= MAX_PER_SOURCE:
                    break

            if found:
                log.info(f"    → {pname}: {found}")

        except requests.exceptions.Timeout:
            log.warning(f"    ⏱️ {pname}: timeout — DuckDuckGo bloklu, atlanır")
            break
        except Exception as e:
            log.error(f"    ❌ {pname}: {e}")
        time.sleep(2)

    log.info(f"    ✅ DuckDuckGo cəmi: {len(result)}")
    return result


# ======================================================================
# 12. MƏNBƏ 7 — SELENIUM (Facebook/Instagram — login ilə)
# ======================================================================
def _selenium(keyword: str, aliases: list) -> list:
    if not (ENABLE_SELENIUM and SELENIUM_AVAILABLE):
        return []
    log.info("  📡 [SELENIUM]")
    opts = Options()
    for arg in ["--headless", "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"]:
        opts.add_argument(arg)
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"user-agent={_UA}")
    try:
        driver = webdriver.Chrome(options=opts)
        driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    except Exception as e:
        log.error(f"    ⚠️ Chrome açılmadı: {e}")
        return []

    results : list = []

    def _scrape(url, domain):
        try:
            driver.get(url); time.sleep(4)
            for a in driver.find_elements(By.TAG_NAME, "a")[:80]:
                href = a.get_attribute("href") or ""
                text = a.text.strip()
                if domain in href and len(text) > 8 and keyword_matches(keyword, text, aliases):
                    results.append({"title": f"[{domain}] {text[:100]}", "link": href,
                                    "source": domain, "pub_date": "", "desc": text})
                if len(results) >= 10:
                    break
        except Exception as e:
            log.warning(f"    ⚠️ {domain}: {e}")

    q = urllib.parse.quote(keyword)
    _scrape(f"https://www.facebook.com/search/posts/?q={q}", "facebook.com")
    time.sleep(2)
    _scrape(f"https://www.instagram.com/explore/search/keyword/?q={q}", "instagram.com")
    driver.quit()
    log.info(f"    ✅ Selenium: {len(results)} nəticə")
    return results


# ======================================================================
# 13. TELEGRAM GÖNDƏRMƏ — HTML + retry
# ======================================================================
def _html_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

def _telegram_send(text_html: str) -> bool:
    base    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text_html,
               "parse_mode": "HTML", "disable_web_page_preview": False}
    for attempt in range(3):
        try:
            r = requests.post(base, json=payload, timeout=12)
            if r.status_code == 200:
                return True
            if r.status_code == 429:
                wait = r.json().get("parameters", {}).get("retry_after", 5)
                log.warning(f"    ⏳ Telegram 429 — {wait}s gözlənilir")
                time.sleep(wait + 1)
                continue
            log.error(f"    ❌ Telegram HTTP {r.status_code}: {r.text[:200]}")
            return False
        except Exception as e:
            log.error(f"    ❌ Telegram xətası (cəhd {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    return False

def _telegram_alert(title: str, summary: str, link: str,
                    sentiment: str, keyword: str, source: str = ""):
    emoji    = {"MƏNFİ": "🔴", "MÜSBƏT": "🟢"}.get(sentiment, "🟡")
    src_line = f"📰 {_html_escape(source)}\n" if source else ""
    text = (
        f"{emoji} <b>PR XƏBƏRDARLİĞI</b>\n\n"
        f"🔑 {_html_escape(keyword)}\n"
        f"📌 {_html_escape(title)}\n"
        f"🧠 {_html_escape(summary)}\n"
        f"{src_line}"
        f'🔗 <a href="{link}">Xəbərə bax</a>'
    )
    if _telegram_send(text):
        log.info(f"    ✅ Telegram: {title[:55]}")
    else:
        log.error(f"    ❌ Telegram göndərilmədi: {title[:55]}")


# ======================================================================
# 14. GEMINI ANALİZ — filtrləmə aktiv
# ======================================================================
_gemini_off_until = 0.0

def _raw_items(news_list: list) -> list:
    out = []
    for n in news_list:
        summary = n.get("snippet") or n.get("desc") or "—"
        if len(summary) > 300:
            summary = summary[:300].rsplit(" ", 1)[0] + "…"
        out.append({"title": n["title"], "summary": summary,
                    "link": n["link"], "sentiment": "NEYTRAL",
                    "source": n.get("source", "")})
    return out

def _ai_analyze(news_list: list, keyword: str) -> list:
    global _gemini_off_until
    if not GEMINI_AVAILABLE or not _gemini_model:
        return _raw_items(news_list)
    if time.time() < _gemini_off_until:
        log.info("    ⏸️ Gemini söndürülüb — xam göndərilir")
        return _raw_items(news_list)

    results, chunk = [], 8
    for i in range(0, len(news_list), chunk):
        part = news_list[i:i+chunk]
        prompt = (
            f'Sən Azərbaycan hökumət kommunikasiyası üzrə PR ekspertisən.\n'
            f'Qurum/mövzu: "{keyword}"\n\n'
            f'Hər xəbər üçün:\n'
            f'1. relevant: true/false — bu qurum/mövzu ilə əlaqəlidirmi?\n'
            f'2. summary: Azərbaycanca 1-2 cümlə (yalnız relevant:true üçün)\n'
            f'3. sentiment: MÜSBƏT | MƏNFİ | NEYTRAL\n\n'
            f'Xüsusi diqqət: neqativ xəbərlər (şikayət, problem, tənqid, '
            f'itirilmiş müavinət, işsizlik artımı) mütləq MƏNFİ sentiment almalıdır.\n'
            f'Əlaqəsiz xəbərlərdə relevant:false, summary boş.\n'
            f'YALNIZ JSON massivi:\n'
            f'[{{"title":"...","summary":"...","link":"...",'
            f'"sentiment":"...","source":"...","relevant":true}}]\n\n'
            f'{json.dumps(part, ensure_ascii=False, indent=2)}'
        )
        done = False
        for attempt in range(2):
            try:
                resp   = _gemini_model.generate_content(prompt)
                raw    = re.sub(r"```(?:json)?|```", "", resp.text).strip()
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("massiv deyil")
                by_link  = {p.get("link"): p for p in parsed if isinstance(p, dict)}
                kept     = []
                filtered = 0
                for n in part:
                    g = by_link.get(n["link"])
                    if g:
                        if not g.get("relevant", True):
                            filtered += 1
                            log.info(f"    🤖 Əlaqəsiz filtrlədi: {n['title'][:50]}")
                            continue
                        kept.append({
                            "title":     g.get("title", n["title"]),
                            "summary":   g.get("summary") or n.get("snippet") or n.get("desc") or "—",
                            "link":      n["link"],
                            "sentiment": g.get("sentiment", "NEYTRAL"),
                            "source":    n.get("source", g.get("source", "")),
                        })
                    else:
                        kept.extend(_raw_items([n]))
                if filtered:
                    log.info(f"    🤖 Gemini {filtered} əlaqəsiz xəbər atdı")
                results.extend(kept)
                done = True
                break
            except Exception as e:
                err = str(e).lower()
                if "429" in err or "quota" in err or "rate" in err:
                    if attempt == 0:
                        log.warning("    ⚠️ Gemini limit — 20s gözlənilir")
                        time.sleep(20)
                else:
                    log.error(f"    ❌ Gemini: {e}")
                    break

        if not done:
            log.warning("    ⚠️ Gemini əlçatmaz — xam göndərilir, 10 dəq söndürülür")
            _gemini_off_until = time.time() + 600
            for j in range(i, len(news_list), chunk):
                results.extend(_raw_items(news_list[j:j+chunk]))
            break

        if i + chunk < len(news_list):
            time.sleep(2)

    return results


# ======================================================================
# 15. ANA FUNKSIYA
# ======================================================================
def process_keyword(keyword: str, aliases: list):
    log.info(f"\n{'─'*55}")
    log.info(f"🔍  {keyword}")
    log.info(f"{'─'*55}")

    seen        = _load_seen()
    all_news    : list = []
    seen_in_run : set  = set()

    def merge(items: list):
        for n in items:
            lnk = n.get("link", "")
            if lnk and lnk not in seen_in_run:
                all_news.append(n)
                seen_in_run.add(lnk)

    merge(_google_news(keyword, aliases));          time.sleep(2)
    merge(_az_rss(keyword, aliases));               time.sleep(2)
    merge(_direct_scrape(keyword, aliases));         time.sleep(1)
    merge(_telegram_channels(keyword, aliases));     time.sleep(1)
    merge(_facebook(keyword, aliases));              time.sleep(2)
    merge(_negative_sources(keyword, aliases));      time.sleep(2)
    merge(_duckduckgo(keyword, aliases));            time.sleep(2)
    merge(_selenium(keyword, aliases))

    fresh = [n for n in all_news if n["link"] not in seen]
    log.info(f"\n  📊 Tapılan: {len(all_news)}  |  Yeni: {len(fresh)}")

    if not fresh:
        log.info("  ℹ️  Yeni xəbər yoxdur.")
        return

    link_text = {n["link"]: f"{n.get('title', '')} {n.get('snippet', n.get('desc', ''))}"
                 for n in fresh}

    log.info(f"  🧠 AI analiz ({len(fresh)} xəbər)...")
    analyzed = _ai_analyze(fresh, keyword)

    sent = 0
    sent_links = []
    results_to_save = []
    for item in analyzed:
        if not isinstance(item, dict):
            continue
        link = item.get("link", "#")
        orig = link_text.get(link, "")
        if orig and not keyword_matches(keyword, orig, aliases):
            log.info(f"    🛡️  Son yoxlama rədd: {item.get('title', '')[:50]}")
            continue
        # _force_negative: neqativ mənbə siyahısından gəlirsə həmişə 🔴
        sentiment = ("MƏNFİ" if item.get("_force_negative")
                     else item.get("sentiment", "NEYTRAL"))
        _telegram_alert(item.get("title", "Başlıqsız"),
                        item.get("summary", "Xülasə yoxdur"),
                        link, sentiment,
                        keyword, item.get("source", ""))
        sent += 1
        if link and link != "#":
            sent_links.append(link)
        results_to_save.append({
            "title":     item.get("title", ""),
            "link":      link,
            "summary":   item.get("summary", ""),
            "sentiment": sentiment,
            "keyword":   keyword,
            "source":    item.get("source", ""),
        })
        time.sleep(0.5)

    log.info(f"  📨 {sent} bildiriş göndərildi")
    if sent_links:
        _save_seen(sent_links)
    if results_to_save:
        _append_results(results_to_save)


# ======================================================================
# 16. STARTUP
# ======================================================================
def startup_check():
    log.info("▶️  Agent işə düşdü (v7)")
    log.info(f"   Açar sözlər    : {len(KEYWORDS)}")
    log.info(f"   RSS feed-lər   : {len(AZ_RSS_FEEDS)}")
    log.info(f"   TG kanalları   : {len(TG_CHANNELS)}")
    log.info(f"   İnterval       : {RUN_INTERVAL_MINUTES} dəq | Limit: {HOURS_LIMIT}s")
    log.info(f"   Gemini         : {'✅' if GEMINI_AVAILABLE else '❌'}")
    log.info(f"   Selenium       : {'✅' if (SELENIUM_AVAILABLE and ENABLE_SELENIUM) else '❌'}")
    log.info(f"   DuckDuckGo     : {'✅' if ENABLE_DUCKDUCKGO else '⏸️'}")
    log.info(f"   Birbaşa scrape : {'✅' if ENABLE_DIRECT_SCRAPE else '⏸️'}")
    log.info(f"   TG kanalları   : {'✅' if ENABLE_TG_CHANNELS else '⏸️'}")
    log.info(f"   Facebook       : {'✅' if ENABLE_FACEBOOK else '⏸️'}")
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
        if r.status_code == 200 and r.json().get("ok"):
            bot = r.json()["result"].get("username", "?")
            log.info(f"   Telegram       : ✅ (@{bot})")
            if SEND_STARTUP_PING:
                fb_mode = "login" if FB_EMAIL else "mbasic+selenium"
                _telegram_send(
                    f"🤖 <b>PR monitorinq agenti işə düşdü</b> "
                    f"(v8 — Facebook: {fb_mode})"
                )
        else:
            log.error(f"   Telegram       : ❌ token problemi ({r.status_code})")
    except Exception as e:
        log.error(f"   Telegram       : ❌ bağlantı yoxdur — {e}")


# ======================================================================
# 17. ƏSAS DÖNGÜ
# ======================================================================
def job():
    log.info(f"\n{'='*55}")
    log.info(f"🚀  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"{'='*55}")
    for kw, aliases in KEYWORDS.items():
        try:
            process_keyword(kw, aliases)
        except Exception as e:
            log.error(f"❌ '{kw}': {e}")
        time.sleep(5)
    log.info(f"\n💤  {RUN_INTERVAL_MINUTES} dəqiqə gözlənilir...\n")


if __name__ == "__main__":
    try:
        if os.path.exists(SEEN_FILE):
            with open(SEEN_FILE) as f:
                _existing = json.load(f)
            if isinstance(_existing, (list, dict)) and len(_existing) > 500:
                os.remove(SEEN_FILE)
                log.warning(f"🧹 Şişmiş seen faylı ({len(_existing)} link) sıfırlandı")
    except Exception:
        pass
    if not os.path.exists(SEEN_FILE):
        json.dump({}, open(SEEN_FILE, "w"))

    startup_check()
    job()
    schedule.every(RUN_INTERVAL_MINUTES).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
