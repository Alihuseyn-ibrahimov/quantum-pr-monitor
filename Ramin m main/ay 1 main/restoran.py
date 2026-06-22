import streamlit as st

# 1. Veb-saytın Başlığı və Dizayn Tənzimləmələri
st.set_page_config(page_title="Əlihüseynin restoranı", page_icon="🍽️", layout="centered")
st.title("Əlihüseynin restoranı")
st.write("Restoranımızın ağıllı köməkçisi xidmətinizdədir. Sualınızı yazın:")


# 2. Sizin nümunədəki Funksiya (Məntiq və Mətnlər Eynilə Saxlanılıb)
def cavab_ver(mesaj):
    m = mesaj.lower()

    if "sifariş" in m:
        return "Sifarişiniz qəbul edildi"
    elif "menyu" in m:
        return "Hörmətli müştəri, bu günkü lunch menyumuzda plov, kabab və şorba vardır"
    elif "qiymət" in m or "qiymet" in m:
        return "Lunch-ın ortalama qiyməti 15 AZN-dir."
    elif "salam" in m or "slm" in m:
        return "Hörmətli müştərilər, restoranımıza xoş gəlmisiniz. Sizə necə kömək edə bilərik?"
    elif "açıq" in m or "aciq" in m:
        return "Hörmətli müştəri, restoranımızın iş saatları hər gün 10:00-dan 00:00-a qədərdir."
    else:
        return "Sualınız tam aydın deyil, daha ətraflı qeyd etməyinizi xahiş edirik."


# 3. Çat tarixçəsini brauzer yaddaşında (Session State) saxlamaq
if "mesaj_tarixcesi" not in st.session_state:
    st.session_state.mesaj_tarixcesi = []

# 4. Əvvəl yazışılan mesajları ekranda göstərmək
for sohbet in st.session_state.mesaj_tarixcesi:
    with st.chat_message(sohbet["rol"]):
        st.write(sohbet["metn"])

# 5. Real vaxtda istifadəçidən mesajın alınması və funksiyanın tetiklenmesi
if istifadeci_mesaji := st.chat_input("Mesajınızı yazın... (Məsələn: salam, menyu nədir?)"):
    # İstifadəçinin yazdığını ekrana və yaddaşa əlavə edirik
    with st.chat_message("user"):
        st.write(istifadeci_mesaji)
    st.session_state.mesaj_tarixcesi.append({"rol": "user", "metn": istifadeci_mesaji})

    # Sizin funksiyanı çağırıb botun cavabını alırıq
    botun_cavabi = cavab_ver(istifadeci_mesaji)

    # Botun cavabını ekrana və yaddaşa əlavə edirik
    with st.chat_message("assistant"):
        st.write(botun_cavabi)
    st.session_state.mesaj_tarixcesi.append({"rol": "assistant", "metn": botun_cavabi})
    