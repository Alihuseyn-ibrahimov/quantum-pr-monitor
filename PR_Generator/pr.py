alk import os

# ====================================================================
# --- AVTOMATİK LİMİT ARTIRICI SİSTEM ---
# ====================================================================
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")

with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write("[server]\nmaxUploadSize = 2000\n")

# agent.py ilə ortaq nəticə faylı (bir qovluq yuxarıda)
AGENT_RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results.json")

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
# 1. AI MODELİNİN VƏ SƏHİFƏNİN AYARLANMASI
# ====================================================================
st.set_page_config(
    page_title="Universal PR və Reputasiya Dashboard-u",
    page_icon="📊",
    layout="wide"
)

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("API açarı tapılmadı! Lütfən .streamlit/secrets.toml faylını yoxlayın.")


# ====================================================================
# 2. KÖMƏKÇİ FUNKSİYALAR (Veb Scraper və Şəkil Kodlaşdırıcı)
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
    except:
        pass
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_article_text(article_url):
    if not article_url: return ""
    try:
        resp = requests.get(article_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            paragraphs = soup.find_all('p')
            return " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 20])[:3000]
    except:
        pass
    return ""


# ====================================================================
# HERO LOGO VƏ BAŞLIQ BÖLMƏSİ (UNIVERSAL RƏSMİ ÜSLUB)
# ====================================================================
gerb_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Emblem_of_Azerbaijan.svg/500px-Emblem_of_Azerbaijan.svg.png"
hero_logo_src = get_image_base64(gerb_url) or "https://flagcdn.com/w160/az.png"

st.markdown(
    f'''
    <div style="text-align: center; padding: 25px; background-color: #f8f9fa; border-radius: 12px; margin-bottom: 25px; border-bottom: 5px solid #1f2937;">
        <img src="{hero_logo_src}" width="75" style="margin-bottom: 12px;">
        <h1 style="color: #1f2937; font-size: 28px; margin-bottom: 6px; font-weight: bold;">Operativ PR Monitorinq və Reputasiya Dashboard-u</h1>
        <p style="color: #4b5563; font-size: 16px;">Süni İntellekt Dəstəkli Fasiləsiz Böhran Nəzarəti Sistemi</p>
    </div>
    ''',
    unsafe_allow_html=True
)

# ====================================================================
# YAN MENYU (SİDEBAR) - MOD SEÇİMİ
# ====================================================================
st.sidebar.markdown("## 🛠️ İş Rejimi")
rejim = st.sidebar.radio(
    "Zəhmət olmasa bölməni seçin:",
    ["📡 Agent Xəbər Arxivi", "📊 Canlı Operativ Dashboard", "📝 Press-Reliz Yarat", "📱 Sosial Media Postu Yarat"]
)

if "pr_response" not in st.session_state: st.session_state.pr_response = None

# ====================================================================
# REJİM 0: AGENT XƏBƏRLƏRİ ARXİVİ (agent.py nəticələri)
# ====================================================================
if rejim == "📡 Agent Xəbər Arxivi":
    st.markdown("### 📡 Avtomatik Agent tərəfindən tapılmış xəbərlər")

    # ── Fayl oxuma ────────────────────────────────────────────────
    if not os.path.exists(AGENT_RESULTS_FILE):
        st.info("📭 Hələ heç bir nəticə yoxdur. Əvvəlcə `agent.py`-ni işə salın.")
        st.stop()
    try:
        with open(AGENT_RESULTS_FILE, encoding="utf-8") as _f:
            raw_results = json.load(_f)
    except Exception as _e:
        st.error(f"Fayl oxunmadı: {_e}")
        st.stop()
    if not raw_results:
        st.success("🟢 Arxivdə hələ heç bir xəbər yoxdur.")
        st.stop()

    df_agent = pd.DataFrame(raw_results)

    # saved_at → datetime sütunu
    def _parse_dt(s):
        try:
            return datetime.datetime.fromisoformat(str(s))
        except Exception:
            return None

    df_agent["_dt"] = df_agent["saved_at"].apply(_parse_dt)

    # ── Üst filtr paneli ──────────────────────────────────────────
    col_t, col_kw, col_sent, col_btn = st.columns([2, 2, 2, 1])

    with col_t:
        PERIOD_MAP = {
            "Son 1 həftə":  7,
            "Son 1 ay":    30,
            "Son 1 rüb":   91,
            "Son 1 il":   365,
        }
        selected_period = st.selectbox("📅 Zaman aralığı:", list(PERIOD_MAP.keys()))
        days_back = PERIOD_MAP[selected_period]
        period_cutoff = datetime.datetime.now() - datetime.timedelta(days=days_back)

    with col_kw:
        kw_list = ["Hamısı"] + sorted(df_agent["keyword"].dropna().unique().tolist())
        selected_kw = st.selectbox("🔑 Açar söz:", kw_list)

    with col_sent:
        sent_list = ["Hamısı", "MƏNFİ", "NEYTRAL", "MÜSBƏT"]
        selected_sent = st.selectbox("🎯 Sentiment:", sent_list)

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Yenilə", use_container_width=True):
            st.rerun()

    # ── Filtrasiya ────────────────────────────────────────────────
    filtered = df_agent[df_agent["_dt"] >= period_cutoff].copy()
    if selected_kw != "Hamısı":
        filtered = filtered[filtered["keyword"] == selected_kw]
    if selected_sent != "Hamısı":
        filtered = filtered[filtered["sentiment"] == selected_sent]

    n_total   = len(filtered)
    n_musbet  = len(filtered[filtered["sentiment"] == "MÜSBƏT"])
    n_neytral = len(filtered[filtered["sentiment"] == "NEYTRAL"])
    n_menfi   = len(filtered[filtered["sentiment"] == "MƏNFİ"])

    # ── Metriklər ─────────────────────────────────────────────────
    # Müqayisə üçün əvvəlki eyni müddət
    prev_cutoff = period_cutoff - datetime.timedelta(days=days_back)
    prev = df_agent[(df_agent["_dt"] >= prev_cutoff) & (df_agent["_dt"] < period_cutoff)]
    if selected_kw != "Hamısı":
        prev = prev[prev["keyword"] == selected_kw]
    if selected_sent != "Hamısı":
        prev = prev[prev["sentiment"] == selected_sent]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📰 Ümumi xəbər",    n_total,   delta=n_total - len(prev))
    m2.metric("🟢 Müsbət",         n_musbet,  delta=n_musbet  - len(prev[prev["sentiment"]=="MÜSBƏT"]))
    m3.metric("🟡 Neytral",        n_neytral, delta=n_neytral - len(prev[prev["sentiment"]=="NEYTRAL"]))
    m4.metric("🔴 Mənfi / Şikayət",n_menfi,   delta=n_menfi   - len(prev[prev["sentiment"]=="MƏNFİ"]),
              delta_color="inverse")

    if filtered.empty:
        st.info(f"Bu dövr üçün ({selected_period}) seçilmiş filtrlərlə xəbər tapılmadı.")
        st.stop()

    st.markdown("---")

    # ── Qrafiklər ─────────────────────────────────────────────────
    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.markdown("#### 🥧 Sentiment bölgüsü")
        counts = filtered["sentiment"].value_counts().reset_index()
        counts.columns = ["Sentiment", "Say"]
        color_map = {"MÜSBƏT": "#10b981", "NEYTRAL": "#f59e0b", "MƏNFİ": "#ef4444"}
        fig_pie = px.pie(counts, values="Say", names="Sentiment",
                         color="Sentiment", color_discrete_map=color_map, hole=0.4)
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.markdown("#### 📊 Günlük xəbər axını")
        if filtered["_dt"].notna().any():
            filtered["_date"] = filtered["_dt"].dt.date
            daily = (filtered.groupby(["_date", "sentiment"])
                     .size().reset_index(name="say"))
            fig_bar = px.bar(daily, x="_date", y="say", color="sentiment",
                             color_discrete_map=color_map,
                             labels={"_date": "Tarix", "say": "Xəbər sayı", "sentiment": "Sentiment"},
                             barmode="stack")
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                                  xaxis_title="", yaxis_title="Xəbər sayı")
            st.plotly_chart(fig_bar, use_container_width=True)

    # ── Açar söz üzrə bölgü (yalnız "Hamısı" seçiləndə) ──────────
    if selected_kw == "Hamısı" and "keyword" in filtered.columns:
        st.markdown("#### 🔑 Açar söz üzrə xəbər sayı")
        kw_counts = (filtered.groupby(["keyword", "sentiment"])
                     .size().reset_index(name="say"))
        fig_kw = px.bar(kw_counts, x="keyword", y="say", color="sentiment",
                        color_discrete_map=color_map, barmode="stack",
                        labels={"keyword": "Açar söz", "say": "Say", "sentiment": "Sentiment"})
        fig_kw.update_layout(xaxis_tickangle=-30, margin=dict(t=10, b=80, l=10, r=10))
        st.plotly_chart(fig_kw, use_container_width=True)

    # ── Xəbər kartları ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"#### 📋 {selected_period} — {n_total} xəbər")

    tab_m, tab_n, tab_p = st.tabs([
        f"🔴 Mənfi ({n_menfi})",
        f"🟡 Neytral ({n_neytral})",
        f"🟢 Müsbət ({n_musbet})",
    ])

    def _render_cards(df_sub, border_color, bg_color, text_color):
        if df_sub.empty:
            st.info("Bu kateqoriyada xəbər yoxdur.")
            return
        for _, row in df_sub.sort_values("_dt", ascending=False).iterrows():
            saved = ""
            if pd.notna(row.get("_dt")):
                saved = row["_dt"].strftime("%d.%m.%Y %H:%M")
            st.markdown(
                f'''
                <div style="padding:12px; background-color:{bg_color};
                            border-left:5px solid {border_color};
                            border-radius:4px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between;
                                align-items:center; margin-bottom:4px;">
                        <span style="font-size:11px; background-color:{border_color};
                                     color:white; padding:2px 6px; border-radius:3px;">
                            🔑 {row.get("keyword","")}</span>
                        <span style="font-size:11px; color:#6b7280;">{saved}</span>
                    </div>
                    <h5 style="margin:6px 0 4px 0; color:{text_color};">{row.get("title","")}</h5>
                    <p style="margin:0 0 6px 0; font-size:13px; color:#4b5563;">
                        <b>AI Xülasə:</b> {row.get("summary","")}</p>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <a href="{row.get("link","#")}" target="_blank"
                           style="font-size:12px; color:{border_color};
                                  font-weight:bold; text-decoration:none;">
                            🔗 Mənbəyə get →</a>
                        <span style="font-size:11px; color:#9ca3af;">{row.get("source","")}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True
            )

    with tab_m:
        _render_cards(filtered[filtered["sentiment"] == "MƏNFİ"],
                      "#ef4444", "#fef2f2", "#991b1b")
    with tab_n:
        _render_cards(filtered[filtered["sentiment"] == "NEYTRAL"],
                      "#f59e0b", "#fffbeb", "#92400e")
    with tab_p:
        _render_cards(filtered[filtered["sentiment"] == "MÜSBƏT"],
                      "#10b981", "#f0fdf4", "#065f46")

    # ── Son yenilənmə vaxtı ───────────────────────────────────────
    if "saved_at" in df_agent.columns:
        last_ts = df_agent["saved_at"].max()
        try:
            last_dt = datetime.datetime.fromisoformat(last_ts)
            st.caption(f"🕐 Arxivin son yenilənməsi: {last_dt.strftime('%d.%m.%Y %H:%M')} "
                       f"| Cəmi arxivdə: {len(df_agent)} xəbər")
        except Exception:
            pass

# ====================================================================
# REJİM 1: CANLI OPERATİV MONITORINQ VƏ DASHBOARD (YENİ MEXANİZM)
# ====================================================================
elif rejim == "📊 Canlı Operativ Dashboard":
    st.markdown('### ⏱️ Real-Vaxt Yüksək Tezlikli Media Analizi')

    # 11 Rəsmi Default Açar Sözlər
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

    # İnterfeys Filtrləri Paneli
    col_time, col_btn_space = st.columns([1, 2])
    with col_time:
        saat_araligi = st.selectbox(
            "⏰ Operativ Zaman Aralığı Seçin:",
            ["Son 1 Saat", "Son 3 Saat", "Son 6 Saat", "Son 12 Saat", "Son 24 Saat (1 Gün)"]
        )

        # Seçilən saatı Google News RSS sorğu formatına çeviririk
        time_map = {"Son 1 Saat": "1h", "Son 3 Saat": "3h", "Son 6 Saat": "6h", "Son 12 Saat": "12h",
                    "Son 24 Saat (1 Gün)": "1d"}
        time_token = time_map[saat_araligi]

    st.markdown("#### 🔑 İzlənilən Strateji Açar Sözlər")
    acar_sozler_input = st.text_area("İzləmə siyahısını buradan tənzimləyə bilərsiniz (Hər sətrə bir dənə):",
                                     value=default_keywords, height=140)

    if st.button("🚀 Canlı Operativ Monitorinqi Başlat", type="primary", use_container_width=True):
        keywords = [k.strip() for k in acar_sozler_input.split('\n') if k.strip()]

        if not keywords:
            st.warning("⚠️ Lütfən ən azı bir açar söz daxil edin.")
        else:
            with st.spinner(
                    f"⏳ Google News RSS üzərindən {saat_araligi} üçün məlumatlar toplanır və toplu analiz edilir..."):
                all_fetched_news = []
                seen_links_local = set()
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

                # Məlumat Toplama Prosesi
                progress_bar = st.progress(0)
                for index, kw in enumerate(keywords):
                    gn_query = f'"{kw}" when:{time_token}'
                    rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(gn_query)}&hl=az&gl=AZ&ceid=AZ:az"

                    try:
                        resp = requests.get(rss_url, headers=headers, timeout=8)
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.content, 'xml')
                            items = soup.find_all('item')[:5]  # Hər açar söz üçün max 5 son tapıntı

                            for item in items:
                                title = item.title.text if item.title else ""
                                link = item.link.text if item.link else ""
                                desc = item.description.text if item.description else ""

                                if link not in seen_links_local:
                                    seen_links_local.add(link)
                                    all_fetched_news.append({
                                        "title": title,
                                        "link": link,
                                        "desc": desc,
                                        "keyword": kw
                                    })
                    except:
                        pass
                    progress_bar.progress((index + 1) / len(keywords))

                # Tapılan xəbərləri AI-yə Göndərmə və 3 Kateqoriyaya Bölmə
                if not all_fetched_news:
                    st.success(
                        f"🟢 Mükəmməl! {saat_araligi} ərzində izlənilən mövzular üzrə heç bir yeni xəbər və ya şikayət qeydə alınmadı.")
                else:
                    st.markdown(f"### 📊 Tapılan Ümumi Resurs Sayı: {len(all_fetched_news)}. AI Toplu Analiz Aparır...")

                    # Gemini üçün toplu sorğu formatı
                    sentiment_prompt = f"""
                    Sən dövlət orqanı üçün çalışan peşəkar PR və Reputasiya Analitikisən. 
                    Aşağıdakı siyahı rəsmi mövzular üzrə son saatlar ərzində toplanmış media tapıntılarıdır.

                    SƏNİN QƏTİ ƏMRLƏRİN:
                    1. İş elanları, kommersiya satış/reklam elanları, kazino/mərc oyunları kimi spamları dərhal "is_relevant": false edərək təmizlə.
                    2. DİL VƏ TƏKRAR FİLTRİ: Əgər eyni mövzu həm Azərbaycanca, həm də Rusca/İngiliscə çıxıbsa, YALNIZ Azərbaycanca linki saxla, digər dillərdəki eyni məzmunlu linkləri sil!
                    3. SENTİMENT BÖLGÜSÜ: Qalan bütün real xəbərləri 3 kateqoriyaya böl:
                       - Vətəndaş şikayəti, tənqid, problem və ya krizis ehtimalı varsa: "MƏNFİ"
                       - Dövlətin uğurları, islahatlar, təriflər və ya müsbət rəylər varsa: "MÜSBƏT"
                       - Neytral məlumat, rəsmi elan, adi xəbər axınıdırsa: "NEYTRAL"

                    Gələn Məlumatlar:
                    {json.dumps(all_fetched_news, ensure_ascii=False)}

                    Cavabı YALNIZ aşağıdakı JSON formatında (siyahı daxilində obyektlər) qaytar, kənarda heç bir şərh yazma:
                    [
                        {{
                            "link": "xəbərin tam orijinal linki",
                            "sentiment": "MƏNFİ" / "MÜSBƏT" / "NEYTRAL",
                            "summary": "Mətnin mahiyyətini izah edən rəsmi və dolğun 1 cümləlik Azərbaycan dilində xülasə"
                        }}
                    ]
                    """

                    try:
                        ai_resp = model.generate_content(sentiment_prompt).text
                        clean_json = ai_resp.replace('```json', '').replace('```', '').strip()
                        ai_data = json.loads(clean_json)

                        # AI nəticələrini ilkin datamızla xəritələyirik (Map edirik)
                        valid_dict = {res.get("link"): res for res in ai_data if res.get("is_relevant", True)}

                        final_monitored_list = []
                        for news in all_fetched_news:
                            link = news["link"]
                            if link in valid_dict:
                                final_monitored_list.append({
                                    "Mövzu": news["title"],
                                    "Açar Söz": news["keyword"],
                                    "Xülasə (AI)": valid_dict[link].get("summary"),
                                    "Sentiment": valid_dict[link].get("sentiment"),
                                    "Link": link
                                })

                        if not final_monitored_list:
                            st.success(f"🟢 Filtri keçən əlaqəli və təmiz PR məlumatı tapılmadı.")
                        else:
                            df = pd.DataFrame(final_monitored_list)

                            # 1. METRİKLƏR PANERLİ (ÜST HİSSƏ)
                            m_musbet = len(df[df['Sentiment'] == 'MÜSBƏT'])
                            m_neytral = len(df[df['Sentiment'] == 'NEYTRAL'])
                            m_menfi = len(df[df['Sentiment'] == 'MƏNFİ'])

                            c1, c2, c3 = st.columns(3)
                            c1.metric("🟢 Müsbət Tərif / Yenilik", m_musbet)
                            c2.metric("🟡 Neytral İnformativ Xəbər", m_neytral)
                            c3.metric("🔴 Mənfi Xəbər / Şikayət", m_menfi)

                            # 2. VİZUAL QRAFİK PANERLİ (SOL TƏRƏF)
                            st.markdown("---")
                            col_graph, col_lists = st.columns([1, 2])

                            with col_graph:
                                st.markdown("#### 📈 Reputasiya İndeksi (Faizlə)")
                                counts = df['Sentiment'].value_counts().reset_index()
                                counts.columns = ['Sentiment', 'Say']
                                color_map = {'MÜSBƏT': '#10b981', 'NEYTRAL': '#f59e0b', 'MƏNFİ': '#ef4444'}
                                fig = px.pie(counts, values='Say', names='Sentiment', color='Sentiment',
                                             color_discrete_map=color_map, hole=0.4)
                                st.plotly_chart(fig, use_container_width=True)

                            # 3. KATEQORİYALI SİYAHILAŞDIRMA (SAĞ TƏRƏF)
                            with col_lists:
                                st.markdown(f"#### 📋 {saat_araligi} ərzində Strukturlu Xəbər Siyahısı")

                                tab_menfi, tab_neytral, tab_musbet = st.tabs([
                                    f"🔴 Mənfi / Şikayətlər ({m_menfi})",
                                    f"🟡 Neytral Xəbərlər ({m_neytral})",
                                    f"🟢 Müsbət Xəbərlər ({m_musbet})"
                                ])

                                # MƏNFİ TABI
                                with tab_menfi:
                                    df_menfi = df[df['Sentiment'] == 'MƏNFİ']
                                    if df_menfi.empty:
                                        st.success("Təmizdir! Son saatlarda heç bir mənfi rəy və ya şikayət yoxdur. 🎉")
                                    else:
                                        for _, row in df_menfi.iterrows():
                                            st.markdown(
                                                f'''
                                                <div style="padding: 12px; background-color: #fef2f2; border-left: 5px solid #ef4444; border-radius: 4px; margin-bottom: 10px;">
                                                    <span style="font-size:11px; background-color:#ef4444; color:white; padding:2px 6px; border-radius:3px;">🔑 {row['Açar Söz']}</span>
                                                    <h5 style="margin: 8px 0 4px 0; color:#991b1b;">{row['Mövzu']}</h5>
                                                    <p style="margin:0 0 8px 0; font-size:13px; color:#4b5563;"><b>AI Xülasə:</b> {row['Xülasə (AI)']}</p>
                                                    <a href="{row['Link']}" target="_blank" style="font-size:12px; color:#ef4444; font-weight:bold; text-decoration:none;">🔗 Mənbəyə get →</a>
                                                </div>
                                                ''', unsafe_allow_html=True
                                            )

                                # NEYTRAL TABI
                                with tab_neytral:
                                    df_neytral = df[df['Sentiment'] == 'NEYTRAL']
                                    if df_neytral.empty:
                                        st.info("Bu kateqoriyada xəbər tapılmadı.")
                                    else:
                                        for _, row in df_neytral.iterrows():
                                            st.markdown(
                                                f'''
                                                <div style="padding: 12px; background-color: #fffbeb; border-left: 5px solid #f59e0b; border-radius: 4px; margin-bottom: 10px;">
                                                    <span style="font-size:11px; background-color:#f59e0b; color:white; padding:2px 6px; border-radius:3px;">🔑 {row['Açar Söz']}</span>
                                                    <h5 style="margin: 8px 0 4px 0; color:#92400e;">{row['Mövzu']}</h5>
                                                    <p style="margin:0 0 8px 0; font-size:13px; color:#4b5563;"><b>AI Xülasə:</b> {row['Xülasə (AI)']}</p>
                                                    <a href="{row['Link']}" target="_blank" style="font-size:12px; color:#f59e0b; font-weight:bold; text-decoration:none;">🔗 Mənbəyə get →</a>
                                                </div>
                                                ''', unsafe_allow_html=True
                                            )

                                # MÜSBƏT TABI
                                with tab_musbet:
                                    df_musbet = df[df['Sentiment'] == 'MÜSBƏT']
                                    if df_musbet.empty:
                                        st.info("Bu kateqoriyada xəbər tapılmadı.")
                                    else:
                                        for _, row in df_musbet.iterrows():
                                            st.markdown(
                                                f'''
                                                <div style="padding: 12px; background-color: #f0fdf4; border-left: 5px solid #10b981; border-radius: 4px; margin-bottom: 10px;">
                                                    <span style="font-size:11px; background-color:#10b981; color:white; padding:2px 6px; border-radius:3px;">🔑 {row['Açar Söz']}</span>
                                                    <h5 style="margin: 8px 0 4px 0; color:#065f46;">{row['Mövzu']}</h5>
                                                    <p style="margin:0 0 8px 0; font-size:13px; color:#4b5563;"><b>AI Xülasə:</b> {row['Xülasə (AI)']}</p>
                                                    <a href="{row['Link']}" target="_blank" style="font-size:12px; color:#10b981; font-weight:bold; text-decoration:none;">🔗 Mənbəyə get →</a>
                                                </div>
                                                ''', unsafe_allow_html=True
                                            )
                    except Exception as e:
                        st.error(
                            f"Sistem hesabat formalaşdırarkən xəta baş verdi: {e}. Lütfən 1 dəqiqə gözləyib yenidən yoxlayın.")

# ====================================================================
# REJİM 2: PRESS-RELİZ YARAT (KÖHNE VƏ SABİT FUNKSİYA)
# ====================================================================
elif rejim == "📝 Press-Reliz Yarat":
    with st.form("pr_form"):
        st.markdown('### 🏢 Dövlət / Korporativ Üslubda Press-Reliz')
        sirket_adi = st.text_input("Qurum və ya Şirkət Adı",
                                   placeholder="Məs: Əmək və Əhalinin Sosial Müdafiəsi Nazirliyi...")
        movzu = st.text_area("Xəbərin/Tədbirin Əsas Məzmunu", height=100)
        menbe_url = st.text_input("İstinad və Üslub Analizi üçün Köhnə Xəbər Linki (İstəyə bağlı)")

        col1, col2, col3 = st.columns(3)
        with col1: hedef = st.selectbox("Hədəf Kütlə",
                                        ["Geniş İctimaiyyət", "Rəsmi Nümayəndələr", "İxtisaslaşmış Media"])
        with col2: ton = st.selectbox("Səs Tonu", ["Rəsmi / Dövlət üslubu", "İnformasiya xarakterli", "Analitik"])
        with col3: dil = st.selectbox("Dil", ["Azərbaycanca", "English", "Русский"])

        submitted = st.form_submit_button("Sənədi Formalaşdır")

    if submitted and movzu:
        with st.spinner("⏳ Süni İntellekt rəsmi press-reliz mətnini hazırlayır..."):
            uslub = fetch_article_text(menbe_url) if menbe_url else ""
            prompt = f"Sən {sirket_adi} qurumunun Mətbuat Katibisən. Mövzu: {movzu}. Dil: {dil}. Ton: {ton}. Üslub nümunəsi: {uslub}. Dolğun rəsmi press-reliz sənədi yaz."
            try:
                st.session_state.pr_response = model.generate_content(prompt).text
                st.success("Sənəd uğurla formalaşdırıldı!")
            except Exception as e:
                st.error(f"Xəta: {e}")

    if st.session_state.pr_response:
        st.markdown("---")
        st.markdown(st.session_state.pr_response)
        st.download_button("📥 Mətni Saxla (.txt)", st.session_state.pr_response, "press_reliz.txt")

# ====================================================================
# REJİM 3: SOSİAL MEDİA POSTU (POSTER/VİDEO DƏSTƏKLİ)
# ====================================================================
elif rejim == "📱 Sosial Media Postu Yarat":
    st.markdown('### 📱 Sosial Şəbəkə Paylaşımı Hazırlanması')
    sm_text = st.text_area("Xəbərin Mətni (Boş qoyub yalnız fayl da yükləyə bilərsiniz)",
                           value=st.session_state.pr_response or "", height=150)
    uploaded_file = st.file_uploader("Poster (Şəkil) və ya Video Yüklə (2GB-a qədər)",
                                     type=['jpg', 'jpeg', 'png', 'mp4'])

    if st.button("Sosial Media Postunu Hazırla"):
        with st.spinner("⏳ Süni İntellekt multimedia faylını analiz edir və post hazırlayır..."):
            prompt = f"Aşağıdakı məlumata əsasən rəsmi qurumun sosial media hesabı üçün maraqlı, emojili post başlığı (caption) yaz:\n{sm_text}"
            try:
                if uploaded_file:
                    if uploaded_file.type in ['image/jpeg', 'image/png', 'image/jpg']:
                        response = model.generate_content([prompt, Image.open(uploaded_file)])
                    elif uploaded_file.type == 'video/mp4':
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name
                        vid = genai.upload_file(path=tmp_path)
                        while vid.state.name == "PROCESSING": time.sleep(2); vid = genai.get_file(vid.name)
                        response = model.generate_content([prompt, vid])
                        os.unlink(tmp_path)
                else:
                    response = model.generate_content(prompt)

                st.markdown("### 📝 Sizin üçün hazırlanan Sosial Post:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Xəta baş verdi: {e}")

st.markdown(
    "<br><hr><center><p style='color: gray;'>Universal PR Dashboard Systems | Operativ Analitika Modulu 🤖</p></center>",
    unsafe_allow_html=True)
