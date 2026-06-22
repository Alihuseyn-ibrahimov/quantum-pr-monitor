# Restoran Botu

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


test_mesajlari = [
    "salam, masa sifariş etmək istəyirəm",
    "menyu nədir?",
    "qiymətlər necədir?",
    "açıq" ,
    "qiymet" ,
    "unvan haradir" , ]
for mesaj in test_mesajlari:
    print("Siz:", mesaj)
    print("Bot:", cavab_ver(mesaj))
    print()