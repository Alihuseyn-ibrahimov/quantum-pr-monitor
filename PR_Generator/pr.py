import os

# ====================================================================
# --- AVTOMATİK LİMİT ARTIRICI SİSTEM ---
# ====================================================================
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")

with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write("[server]\nmaxUploadSize = 2000\n")

import streamlit as st
import google.generativeai as genai
import urllib.parse
import requests
import base64
from bs4 import BeautifulSoup
from PIL import Image
import tempfile
import time
import datetime
import json
import pandas as pd
import plotly.express as px

# ====================================================================
# results.json yolu — lokal və Streamlit Cloud üçün
# ====================================================================
def _find_results_file():
    # 1. Repo kökündə (GitHub-dan gəlir)
    repo_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results.json")
    if os.path.exists(repo_root):
        return repo_root
    # 2. Eyni qovluqda
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
    if os.path.exists(local):
        return local
    return repo_root  # default (yoxdursa belə göstərir)

AGENT_RESULTS_FILE = _find_results_file()

# ====================================================================
# 1. AI MODELİNİN VƏ SƏHİFƏNİN AYARLANMASI
# ====================================================================
st.set_page_config(
    page_title="PR Monitorinq Dashboard",
    page_icon="📊",
    layout="wide"
)

model = None
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    pass


# ====================================================================
# 2. KÖMƏKÇİ FUNKSİYALAR
# ====================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def get_image_base64(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'image/png')
            encoded = base64.b64encode(response.content).decode()
            return f"data:{content_type};base64,{encoded}"
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_article_text(article_url):
    if not article_url:
        return ""
    try:
        resp = requests.get(article_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            paragraphs = soup.find_all('p')
            return " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 20])[:3000]
    except Exception:
        pass
    return ""


def _render_cards(df_sub, border_color, bg_color, text_color, show_date=True):
    if df_sub.empty:
        st.info("Bu kateqoriyada xəbər yoxdur.")
        return
    sort_col = "_dt" if "_dt" in df_sub.columns else None
    rows = df_sub.sort_values(sort_col, ascending=False).iterrows() if sort_col else df_sub.iterrows()
    for _, row in rows:
        saved = ""
        if show_date and "_dt" in row and pd.notna(row.get("_dt")):
            saved = row["_dt"].strftime("%d.%m.%Y %H:%M")
        elif show_date and "saved_at" in row and row.get("saved_at"):
            try:
                saved = datetime.datetime.fromisoformat(str(row["saved_at"])).strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass
        kw = row.get("keyword") or row.get("Açar Söz") or ""
        title = row.get("title") or row.get("Mövzu") or ""
        summary = row.get("summary") or row.get("Xülasə (AI)") or ""
        link = row.get("link") or row.get("Link") or "#"
        source = row.get("source") or ""
        st.markdown(
            f'''
            <div style="padding:12px; background-color:{bg_color};
                        border-left:5px solid {border_color};
                        border-radius:4px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;
                            align-items:center; margin-bottom:4px;">
                    <span style="font-size:11px; background-color:{border_color};
                                 color:white; padding:2px 6px; border-radius:3px;">
                        🔑 {kw}</span>
                    <span style="font-size:11px; color:#6b7280;">{saved}</span>
                </div>
                <h5 style="margin:6px 0 4px 0; color:{text_color};">{title}</h5>
                <p style="margin:0 0 6px 0; font-size:13px; color:#4b5563;">
                    <b>AI Xülasə:</b> {summary}</p>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <a href="{link}" target="_blank"
                       style="font-size:12px; color:{border_color};
                              font-weight:bold; text-decoration:none;">
                        🔗 Mənbəyə get →</a>
                    <span style="font-size:11px; color:#9ca3af;">{source}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True
        )


# ====================================================================
# BAŞLIQ
# ====================================================================
gerb_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Emblem_of_Azerbaijan.svg/500px-Emblem_of_Azerbaijan.svg.png"
hero_logo_src = get_image_base64(gerb_url) or "https://flagcdn.com/w160/az.png"

st.markdown(
    f'''
    <div style="text-align: center; padding: 25px; background-color: #f8f9fa;
                border-radius: 12px; margin-bottom: 25px; border-bottom: 5px solid #1f2937;">
        <img src="{hero_logo_src}" width="75" style="margin-bottom: 12px;">
        <h1 style="color: #1f2937; font-size: 28px; margin-bottom: 6px; font-weight: bold;">
            Operativ PR Monitorinq və Reputasiya Dashboard-u</h1>
        <p style="color: #4b5563; font-size: 16px;">
            Süni İntellekt Dəstəkli Fasiləsiz Böhran Nəzarəti Sistemi</p>
    </div>
    ''',
    unsafe_allow_html=True
)

# ====================================================================
# YAN MENYU
# ====================================================================
st.sidebar.markdown("## 🛠️ İş Rejimi")
rejim = st.sidebar.radio(
    "Zəhmət olmasa bölməni seçin:",
    ["📊 Monitorinq Dashboard", "📝 Press-Reliz Yarat", "📱 Sosial Media Postu Yarat"]
)

if "pr_response" not in st.session_state:
    st.session_state.pr_response = None

COLOR_MAP = {"MÜSBƏT": "#10b981", "NEYTRAL": "#f59e0b", "MƏNFİ": "#ef4444"}

# ====================================================================
# REJİM 1: BİRLƏŞDİRİLMİŞ MONİTORİNQ DASHBOARD
# ====================================================================
if rejim == "📊 Monitorinq Dashboard":
    st.markdown("### 📊 PR Monitorinq — Agent Nəticələri və Canlı Axtarış")

    # ── Filtr paneli ──────────────────────────────────────────────
    col_period, col_sent, col_btn = st.columns([2, 2, 1])

    PERIOD_MAP = {
        "Son 24 saat": 1,
        "Son 1 həftə": 7,
        "Son 1 ay":    30,
        "Son 1 rüb":   91,
        "Son 1 il":    365,
    }
    with col_period:
        selected_period = st.selectbox("📅 Zaman aralığı:", list(PERIOD_MAP.keys()))
        days_back = PERIOD_MAP[selected_period]
        period_cutoff = datetime.datetime.now() - datetime.timedelta(days=days_back)

    with col_sent:
        selected_sent = st.selectbox("🎯 Sentiment:", ["Hamısı", "MƏNFİ", "NEYTRAL", "MÜSBƏT"])

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Yenilə", use_container_width=True):
            st.rerun()

    # ── Agent nəticələri (results.json) ───────────────────────────
    df_agent = pd.DataFrame()
    if os.path.exists(AGENT_RESULTS_FILE):
        try:
            with open(AGENT_RESULTS_FILE, encoding="utf-8") as _f:
                raw = json.load(_f)
            if raw:
                df_agent = pd.DataFrame(raw)
                def _pdt(s):
                    try:
                        return datetime.datetime.fromisoformat(str(s))
                    except Exception:
                        return None
                df_agent["_dt"] = df_agent["saved_at"].apply(_pdt)
                df_agent = df_agent[df_agent["_dt"] >= period_cutoff]
                if selected_sent != "Hamısı":
                    df_agent = df_agent[df_agent["sentiment"] == selected_sent]
        except Exception as e:
            st.warning(f"Agent faylı oxunmadı: {e}")

    # ── Canlı Google News axtarışı ─────────────────────────────────
    default_keywords = (
        "Əmək və Əhalinin Sosial Müdafiəsi Nazirliyi\n"
        "Dövlət Sosial Müdafiə Fondu\n"
        "Dövlət Əmək Müffətişliyi Xidməti\n"
        "Sosial Xidmətlər Agentliyi\n"
        "DOST Agentliyi\n"
        "Anar Əliyev\n"
        "Ünvanlı sosial yardım\n"
        "Əlillik\n"
        "İşsizlik\n"
        "Dövlət Tibbi Sosial Ekpertiza və Reabilitasiya Agentliyi\n"
        "Minimum əmək haqqı"
    )

    with st.expander("🔍 Canlı Google News Axtarışı (əlavə mənbə)", expanded=False):
        time_map = {"Son 24 saat": "1d", "Son 1 həftə": "7d", "Son 1 ay": "30d",
                    "Son 1 rüb": "90d", "Son 1 il": "365d"}
        time_token = time_map.get(selected_period, "1d")
        acar_sozler_input = st.text_area(
            "Açar sözlər (hər sətirə bir dənə):",
            value=default_keywords, height=120
        )
        search_btn = st.button("🚀 Google News-da Axtar", type="primary", use_container_width=True)

    df_live = pd.DataFrame()
    if search_btn:
        keywords = [k.strip() for k in acar_sozler_input.split('\n') if k.strip()]
        all_fetched = []
        seen_links_local = set()
        headers = {"User-Agent": "Mozilla/5.0"}

        with st.spinner("⏳ Google News sorğulanır..."):
            prog = st.progress(0)
            for idx, kw in enumerate(keywords):
                gn_query = f'"{kw}" when:{time_token}'
                rss_url = (f"https://news.google.com/rss/search?"
                           f"q={urllib.parse.quote(gn_query)}&hl=az&gl=AZ&ceid=AZ:az")
                try:
                    resp = requests.get(rss_url, headers=headers, timeout=8)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.content, 'xml')
                        for item in soup.find_all('item')[:5]:
                            title = item.title.text if item.title else ""
                            link = item.link.text if item.link else ""
                            desc = item.description.text if item.description else ""
                            if link and link not in seen_links_local:
                                seen_links_local.add(link)
                                all_fetched.append({
                                    "title": title, "link": link,
                                    "desc": desc, "keyword": kw
                                })
                except Exception:
                    pass
                prog.progress((idx + 1) / len(keywords))

        if all_fetched and model:
            sentiment_prompt = f"""
Sən dövlət PR analitikisən. Aşağıdakı xəbərləri analiz et.
Spam, iş elanları, kənar xəbərləri "is_relevant": false et.
Qalan hər biri üçün sentiment: MƏNFİ/MÜSBƏT/NEYTRAL və 1 cümlə summary ver.
YALNIZ JSON massivi:
[{{"link":"...","sentiment":"...","summary":"...","is_relevant":true}}]

{json.dumps(all_fetched, ensure_ascii=False)}
"""
            try:
                ai_resp = model.generate_content(sentiment_prompt).text
                clean_json = ai_resp.replace('```json', '').replace('```', '').strip()
                ai_data = json.loads(clean_json)
                valid_dict = {r.get("link"): r for r in ai_data if r.get("is_relevant", True)}
                live_rows = []
                for n in all_fetched:
                    if n["link"] in valid_dict:
                        r = valid_dict[n["link"]]
                        sentiment = r.get("sentiment", "NEYTRAL")
                        if selected_sent != "Hamısı" and sentiment != selected_sent:
                            continue
                        live_rows.append({
                            "title": n["title"], "link": n["link"],
                            "summary": r.get("summary", ""),
                            "sentiment": sentiment,
                            "keyword": n["keyword"],
                            "source": "Google News",
                            "saved_at": datetime.datetime.now().isoformat(),
                        })
                df_live = pd.DataFrame(live_rows)
            except Exception as e:
                st.error(f"AI analiz xətası: {e}")
        elif all_fetched:
            st.warning("AI açarı tapılmadı — nəticələr sentimentsiz göstərilir.")
            df_live = pd.DataFrame([{
                "title": n["title"], "link": n["link"], "summary": "",
                "sentiment": "NEYTRAL", "keyword": n["keyword"], "source": "Google News"
            } for n in all_fetched])

    # ── Hər iki mənbəni birləşdir ─────────────────────────────────
    frames = [f for f in [df_agent, df_live] if not f.empty]
    df_all = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if df_all.empty:
        st.info("📭 Seçilmiş dövr üçün xəbər tapılmadı. Agent işə salın və ya Google News axtarışını istifadə edin.")
        st.stop()

    # ── Metriklər ─────────────────────────────────────────────────
    n_agent = len(df_agent)
    n_live  = len(df_live)
    n_menfi  = len(df_all[df_all["sentiment"] == "MƏNFİ"])
    n_neytral= len(df_all[df_all["sentiment"] == "NEYTRAL"])
    n_musbet = len(df_all[df_all["sentiment"] == "MÜSBƏT"])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📰 Ümumi", len(df_all))
    m2.metric("🤖 Agent", n_agent)
    m3.metric("🔴 Mənfi", n_menfi)
    m4.metric("🟡 Neytral", n_neytral)
    m5.metric("🟢 Müsbət", n_musbet)

    st.markdown("---")

    # ── Qrafiklər ─────────────────────────────────────────────────
    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.markdown("#### 🥧 Sentiment bölgüsü")
        counts = df_all["sentiment"].value_counts().reset_index()
        counts.columns = ["Sentiment", "Say"]
        fig_pie = px.pie(counts, values="Say", names="Sentiment",
                         color="Sentiment", color_discrete_map=COLOR_MAP, hole=0.4)
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        if "_dt" in df_all.columns and df_all["_dt"].notna().any():
            st.markdown("#### 📊 Günlük xəbər axını")
            df_all["_date"] = pd.to_datetime(df_all["_dt"]).dt.date
            daily = df_all.groupby(["_date", "sentiment"]).size().reset_index(name="say")
            fig_bar = px.bar(daily, x="_date", y="say", color="sentiment",
                             color_discrete_map=COLOR_MAP, barmode="stack",
                             labels={"_date": "Tarix", "say": "Say", "sentiment": "Sentiment"})
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.markdown("#### 🔑 Açar söz üzrə bölgü")
            kw_c = df_all.groupby(["keyword", "sentiment"]).size().reset_index(name="say")
            fig_kw = px.bar(kw_c, x="keyword", y="say", color="sentiment",
                            color_discrete_map=COLOR_MAP, barmode="stack")
            fig_kw.update_layout(xaxis_tickangle=-30, margin=dict(t=10, b=80))
            st.plotly_chart(fig_kw, use_container_width=True)

    # ── Açar söz bölgüsü ──────────────────────────────────────────
    if "keyword" in df_all.columns:
        st.markdown("#### 🔑 Açar söz üzrə bölgü")
        kw_c = df_all.groupby(["keyword", "sentiment"]).size().reset_index(name="say")
        fig_kw = px.bar(kw_c, x="keyword", y="say", color="sentiment",
                        color_discrete_map=COLOR_MAP, barmode="stack",
                        labels={"keyword": "", "say": "Say", "sentiment": "Sentiment"})
        fig_kw.update_layout(xaxis_tickangle=-30, margin=dict(t=10, b=100, l=10, r=10))
        st.plotly_chart(fig_kw, use_container_width=True)

    # ── Xəbər kartları ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"#### 📋 {selected_period} — {len(df_all)} xəbər")

    tab_m, tab_n, tab_p = st.tabs([
        f"🔴 Mənfi ({n_menfi})",
        f"🟡 Neytral ({n_neytral})",
        f"🟢 Müsbət ({n_musbet})",
    ])
    with tab_m:
        _render_cards(df_all[df_all["sentiment"] == "MƏNFİ"],
                      "#ef4444", "#fef2f2", "#991b1b")
    with tab_n:
        _render_cards(df_all[df_all["sentiment"] == "NEYTRAL"],
                      "#f59e0b", "#fffbeb", "#92400e")
    with tab_p:
        _render_cards(df_all[df_all["sentiment"] == "MÜSBƏT"],
                      "#10b981", "#f0fdf4", "#065f46")

    if os.path.exists(AGENT_RESULTS_FILE):
        try:
            with open(AGENT_RESULTS_FILE, encoding="utf-8") as _f:
                all_data = json.load(_f)
            last_ts = max((r.get("saved_at","") for r in all_data), default="")
            if last_ts:
                last_dt = datetime.datetime.fromisoformat(last_ts)
                st.caption(f"🕐 Son agent yeniləməsi: {last_dt.strftime('%d.%m.%Y %H:%M')} "
                           f"| Arxivdə cəmi: {len(all_data)} xəbər")
        except Exception:
            pass

# ====================================================================
# REJİM 2: PRESS-RELİZ YARAT
# ====================================================================
elif rejim == "📝 Press-Reliz Yarat":
    with st.form("pr_form"):
        st.markdown('### 🏢 Dövlət / Korporativ Üslubda Press-Reliz')
        sirket_adi = st.text_input("Qurum və ya Şirkət Adı",
                                   placeholder="Məs: Əmək və Əhalinin Sosial Müdafiəsi Nazirliyi...")
        movzu = st.text_area("Xəbərin/Tədbirin Əsas Məzmunu", height=100)
        menbe_url = st.text_input("İstinad üçün Xəbər Linki (İstəyə bağlı)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("Hədəf Kütlə",
                         ["Geniş İctimaiyyət", "Rəsmi Nümayəndələr", "İxtisaslaşmış Media"])
        with col2:
            ton = st.selectbox("Səs Tonu",
                               ["Rəsmi / Dövlət üslubu", "İnformasiya xarakterli", "Analitik"])
        with col3:
            dil = st.selectbox("Dil", ["Azərbaycanca", "English", "Русский"])

        submitted = st.form_submit_button("Sənədi Formalaşdır")

    if submitted and movzu:
        if not model:
            st.error("API açarı tapılmadı!")
        else:
            with st.spinner("⏳ Press-reliz hazırlanır..."):
                uslub = fetch_article_text(menbe_url) if menbe_url else ""
                prompt = (f"Sən {sirket_adi} qurumunun Mətbuat Katibisən. "
                          f"Mövzu: {movzu}. Dil: {dil}. Ton: {ton}. "
                          f"Üslub nümunəsi: {uslub}. Dolğun rəsmi press-reliz sənədi yaz.")
                try:
                    st.session_state.pr_response = model.generate_content(prompt).text
                    st.success("Sənəd uğurla formalaşdırıldı!")
                except Exception as e:
                    st.error(f"Xəta: {e}")

    if st.session_state.pr_response:
        st.markdown("---")
        st.markdown(st.session_state.pr_response)
        st.download_button("📥 Mətni Saxla (.txt)",
                           st.session_state.pr_response, "press_reliz.txt")

# ====================================================================
# REJİM 3: SOSİAL MEDİA POSTU
# ====================================================================
elif rejim == "📱 Sosial Media Postu Yarat":
    st.markdown('### 📱 Sosial Şəbəkə Paylaşımı Hazırlanması')
    sm_text = st.text_area("Xəbərin Mətni",
                           value=st.session_state.pr_response or "", height=150)
    uploaded_file = st.file_uploader("Poster və ya Video Yüklə (2GB-a qədər)",
                                     type=['jpg', 'jpeg', 'png', 'mp4'])

    if st.button("Sosial Media Postunu Hazırla"):
        if not model:
            st.error("API açarı tapılmadı!")
        else:
            with st.spinner("⏳ Post hazırlanır..."):
                prompt = (f"Aşağıdakı məlumata əsasən rəsmi qurumun sosial media hesabı üçün "
                          f"maraqlı, emojili post başlığı (caption) yaz:\n{sm_text}")
                try:
                    if uploaded_file:
                        if uploaded_file.type in ['image/jpeg', 'image/png', 'image/jpg']:
                            response = model.generate_content([prompt, Image.open(uploaded_file)])
                        elif uploaded_file.type == 'video/mp4':
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                                tmp.write(uploaded_file.read())
                                tmp_path = tmp.name
                            vid = genai.upload_file(path=tmp_path)
                            while vid.state.name == "PROCESSING":
                                time.sleep(2)
                                vid = genai.get_file(vid.name)
                            response = model.generate_content([prompt, vid])
                            os.unlink(tmp_path)
                    else:
                        response = model.generate_content(prompt)
                    st.markdown("### 📝 Hazırlanan Post:")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Xəta: {e}")

st.markdown(
    "<br><hr><center><p style='color: gray;'>"
    "PR Monitorinq Dashboard | Operativ Analitika Modulu 🤖"
    "</p></center>",
    unsafe_allow_html=True
)
