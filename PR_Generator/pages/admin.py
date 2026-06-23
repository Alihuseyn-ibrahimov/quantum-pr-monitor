import streamlit as st
import os
import json
import datetime

st.set_page_config(
    page_title="Admin Panel | PR Monitorinq",
    page_icon="⚙️",
    layout="wide"
)

# ── Şifrə yoxlama ────────────────────────────────────────────────────
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    st.markdown(
        """
        <div style="max-width:400px; margin:100px auto 0 auto; text-align:center;">
            <h2 style="color:#1f2937;">⚙️ Admin Paneli</h2>
            <p style="color:#6b7280; font-size:14px;">Bu bölmə yalnız sistem administratoru üçündür</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("admin_login"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("İstifadəçi adı")
            password = st.text_input("Şifrə", type="password")
            submit  = st.form_submit_button("Daxil ol", use_container_width=True)

    if submit:
        try:
            correct_user = st.secrets.get("ADMIN_USERNAME", "admin")
            correct_pass = st.secrets["ADMIN_PASSWORD"]
            if username.strip() == correct_user and password.strip() == correct_pass:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("❌ İstifadəçi adı və ya şifrə yanlışdır!")
        except Exception:
            st.error("❌ Secrets konfiqurasiyası tapılmadı.")
    st.stop()

# ── Admin daxil olub ─────────────────────────────────────────────────
st.markdown("## ⚙️ Admin Panel")
st.markdown("---")

col_logout = st.columns([6, 1])[1]
if col_logout.button("🚪 Çıxış"):
    st.session_state.admin_auth = False
    st.rerun()

# results.json yolu
def _find_results():
    base = os.path.dirname(os.path.abspath(__file__))
    for path in [
        os.path.join(base, "..", "..", "results.json"),
        os.path.join(base, "..", "results.json"),
    ]:
        if os.path.exists(path):
            return os.path.normpath(path)
    return None

results_path = _find_results()

tab1, tab2, tab3 = st.tabs(["📰 Nəticələri İdarə Et", "🔑 Açar Sözlər", "ℹ️ Sistem Məlumatı"])

# ====================================================================
# TAB 1: NƏTİCƏLƏRİ İDARƏ ET
# ====================================================================
with tab1:
    st.markdown("### 📰 Xəbərləri Redaktə Et")

    if not results_path:
        st.warning("results.json tapılmadı.")
    else:
        with open(results_path, encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            st.info("Hələ heç bir xəbər yoxdur.")
        else:
            import pandas as pd
            df = pd.DataFrame(data)
            df["_idx"] = range(len(df))

            # Filtr
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filt_sent = st.selectbox("Sentiment filtri:", ["Hamısı", "MƏNFİ", "NEYTRAL", "MÜSBƏT"])
            with col_f2:
                filt_kw = st.selectbox("Açar söz filtri:", ["Hamısı"] + sorted(df["keyword"].dropna().unique().tolist()))

            df_view = df.copy()
            if filt_sent != "Hamısı":
                df_view = df_view[df_view["sentiment"] == filt_sent]
            if filt_kw != "Hamısı":
                df_view = df_view[df_view["keyword"] == filt_kw]

            st.caption(f"Cəmi {len(df_view)} xəbər göstərilir")

            for _, row in df_view.head(50).iterrows():
                idx = int(row["_idx"])
                with st.expander(f"[{row.get('sentiment','')}] {str(row.get('title',''))[:80]}"):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        new_summary = st.text_area(
                            "Xülasə:",
                            value=str(row.get("summary", "")),
                            key=f"sum_{idx}",
                            height=80,
                        )
                    with col_b:
                        new_sent = st.selectbox(
                            "Sentiment:",
                            ["MƏNFİ", "NEYTRAL", "MÜSBƏT"],
                            index=["MƏNFİ", "NEYTRAL", "MÜSBƏT"].index(
                                row.get("sentiment", "NEYTRAL")
                                if row.get("sentiment") in ["MƏNFİ", "NEYTRAL", "MÜSBƏT"]
                                else "NEYTRAL"
                            ),
                            key=f"sent_{idx}",
                        )
                        st.markdown(f"[🔗 Mənbə]({row.get('link','#')})")

                    col_save, col_del = st.columns(2)
                    with col_save:
                        if st.button("💾 Saxla", key=f"save_{idx}", use_container_width=True):
                            data[idx]["sentiment"] = new_sent
                            data[idx]["summary"]   = new_summary
                            with open(results_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            st.success("Saxlandı!")
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Sil", key=f"del_{idx}", use_container_width=True, type="secondary"):
                            data.pop(idx)
                            with open(results_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            st.success("Silindi!")
                            st.rerun()

# ====================================================================
# TAB 2: AÇAR SÖZLƏR
# ====================================================================
with tab2:
    st.markdown("### 🔑 İzlənilən Açar Sözlər")
    st.info("Bu bölmə növbəti mərhələdə agent.py ilə inteqrasiya ediləcək.")

    # agent.py-dəki keywords-i oxu
    agent_path = None
    for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agent.py"),
    ]:
        if os.path.exists(p):
            agent_path = os.path.normpath(p)
            break

    if agent_path:
        with open(agent_path, encoding="utf-8") as f:
            agent_src = f.read()
        import re
        m = re.search(r'KEYWORDS\s*=\s*\[(.*?)\]', agent_src, re.DOTALL)
        if m:
            kws = re.findall(r'"([^"]+)"', m.group(1))
            st.markdown("**Hal-hazırda izlənilən açar sözlər:**")
            for kw in kws:
                st.markdown(f"- `{kw}`")
        else:
            st.warning("KEYWORDS siyahısı tapılmadı.")
    else:
        st.warning("agent.py tapılmadı.")

# ====================================================================
# TAB 3: SİSTEM MƏLUMATI
# ====================================================================
with tab3:
    st.markdown("### ℹ️ Sistem Məlumatı")
    if results_path and os.path.exists(results_path):
        size_kb = os.path.getsize(results_path) / 1024
        mtime   = datetime.datetime.fromtimestamp(os.path.getmtime(results_path))
        with open(results_path, encoding="utf-8") as f:
            total = len(json.load(f))
        col1, col2, col3 = st.columns(3)
        col1.metric("📰 Ümumi xəbər sayı", total)
        col2.metric("📁 results.json ölçüsü", f"{size_kb:.1f} KB")
        col3.metric("🕐 Son yeniləmə", mtime.strftime("%d.%m.%Y %H:%M"))
    else:
        st.warning("results.json tapılmadı.")
    st.markdown(f"**Fayl yolu:** `{results_path}`")
