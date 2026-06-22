import requests

# BURA ÖZ MƏLUMATLARINIZI YAZIN
TELEGRAM_BOT_TOKEN = "8629640966:AAG6dsokinSmxDynaE1tEZX1KndnhqSFJAw"
TELEGRAM_CHAT_ID = "7622824986"


def test_mesaji_gonder():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "✅ Salam! Mən sizin PR Botunuzam. Əlaqə uğurla quruldu! 🚀"
    }

    print("Mesaj göndərilir...")
    cavab = requests.post(url, json=payload)

    if cavab.status_code == 200:
        print("Əla! Mesaj Telegram-a çatdı. Telefonunuzu yoxlayın.")
    else:
        print(f"Xəta baş verdi! Telegram-ın cavabı: {cavab.text}")


test_mesaji_gonder()