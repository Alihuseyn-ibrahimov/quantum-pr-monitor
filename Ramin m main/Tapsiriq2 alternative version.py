# 1. Test etmək üçün verilən 4 mesajı bir siyahıya (List) yığırıq
mesajlar = [
    "salam, masa sifariş etmək istəyirəm",
    "menyu nədir?",
    "qiymətlər necədir?",
    "sabah açıqsınız?"
]

print("=== Restoran Botu Test Başladı ===\n")

# 2. Dövr (Loop) vasitəsilə hər bir mesajı tək-tək analiz edirik
for orijinal_mesaj in mesajlar:

    # Mesajı tamamilə kiçik hərflərə çeviririk (lower).
    # Çünki "Menyu" yazılsa, `in` operatoru kiçik "menyu" sözünü bəzən tapmaya bilər.
    mesaj = orijinal_mesaj.lower()

    # 3. Şərt operatorları (if/elif/else) və "in" məntiqi ilə yoxlama
    if "salam" in mesaj:
        cavab = "Restoranımıza xoş gəldiniz!"

    elif "sifariş" in mesaj or "sifaris" in mesaj:
        # "or" operatoru istifadə etdik ki, istifadəçi "ş" və ya "s" yazsa da bot anlasın
        cavab = "Sifarişiniz qəbul edildi"

    elif "menyu" in mesaj:
        cavab = "Bu gün: plov, kabab, şorba"

    elif "qiymət" in mesaj or "qiymet" in mesaj or "qiymətler" in mesaj:
        cavab = "Orta çek 15 AZN-dir"

    else:
        cavab = "Başa düşmədim, zəhmət olmasa yenidən yazın"

    # 4. f-string vasitəsilə nəticəni ekrana çıxarırıq
    print(f"İstifadəçi: '{orijinal_mesaj}'")
    print(f"Bot: {cavab}")
    print("-" * 40)