# sinif_a = [75, 90, 55]
# sinif_b = [80, 45, 95, 60]
# butun_qiymetler=sinif_a +sinif_b
# butun_qiymetler.sort(reverse=True)
# print(butun_qiymetler)
# kecenler = [i for i in butun_qiymetler if i >= 60]
# print("İmtahandan keçənlərin qiymətləri:", kecenler)
# print("Keçənlərin sayı:", len(kecenler))

# task1
# sifarisler=["Kofe", "Pizza", "Su"]
# sifarisler[0] = "Çay"
# sifarisler.append("Şirniyyat")
# sifarisler.remove("Su")
# print(sifarisler)
# print(len(sifarisler))


#task2
# maşın_məlumatı = ("Toyota", 2022, "Gümüşü")
# print(maşın_məlumatı[1])
# for i in maşın_məlumatı:
#     print(i)



#task3
# pleylist = ["Mahnı A", "Mahnı B", "Mahnı C", "Mahnı D", "Mahnı E", "Mahnı F"]
# print(pleylist[:2])
# print(pleylist[-2:])
# print(pleylist[2:4])


 #task4
# idmanlar = ("Futbol", "Basketbol", "Tennis")
# idman_list = list(idmanlar)
# idman_list.append("Voleybol")
# idman_list.insert(0, "Üzgüçülük")
# idman_list.sort()
# idmanlar=tuple(idman_list)
# print(idmanlar)



#task5
# hefte_1 = [15, 45, 8]
# hefte_2 = [60, 12, 35, 90]
# butun_xercler=hefte_1+hefte_2
# butun_xercler.sort(reverse=True)
# böyük_xərclər = [xerc for xerc in butun_xercler if xerc > 30]
# print("30 AZN-dən çox olan xərclər:", böyük_xərclər)
# print("Sayı:", len(böyük_xərclər))


#task6
# istifadeciler = ["admin", "user01", "shadow", "guest"]
# ad=input("ad daxil edin")
# if ad.lower() in istifadeciler:
#     print("Giriş uğurludur!")
# else:
#     print("İstifadəçi tapılmadı!")


#task7
# teatr = [
#     ["Boş", "Dolu", "Boş"],  # 1-ci sıra (Sıra 0)
#     ["Dolu", "Dolu", "Boş"], # 2-ci sıra (Sıra 1)
#     ["Boş", "Boş", "Dolu"]   # 3-cü sıra (Sıra 2)
# ]
# print(teatr[1][0])
# print(teatr[2][2])
# for sira in teatr:
#     for oturacaq in sira:
#         print(oturacaq, end=" ")
#     print()

#task8
# numuneler = [12, 7, 19, 24, 5, 10, 33, 50]
# cutler=[i for i in numuneler if  i % 2 == 0]
# cutler.sort()
# print(cutler)


#task9
# sahmat = [
#     ["A1", "B1"],
#     ["A2", "B2"]
# ]
# sahmat[1][1] = "Şah"
# print("--- Şahmat Taxtasının Son Vəziyyəti ---")
# for setir in sahmat:
#     for koordinat in setir:
#         print(koordinat, end=" ")
#     print()


#task10
# cumle = "python proqramlaşdırma dillərin ən populyarı hesab olunur"
# sozler = cumle.split()
# qisa_sozler = []
# for soz in sozler:
#     uzunluq = len(soz)
#     print(f"{soz} — {uzunluq} hərf")
#     if uzunluq < 3:
#         qisa_sozler.append(soz)
# print("\nUzunluğu 3-dən az olan sözlər:", qisa_sozler)

#bonustask
# inventar = ["qılınc", "qalxan", "iksir"]
#
# while True:
#     emr = input("\nNə etmək istəyirsən? (bax / at / götür / çıx): ").lower()
#
#     if emr == "çıx":
#         print("Macəra bitdi!")
#         break
#     elif emr == "bax":
#         print(f" Çantanızdakı əşyalar: {inventar}")
#         print(f" Toplam əşya sayı: {len(inventar)}")
#
#     elif emr == "götür":
#         yeni_esya = input("Yerdən nə götürdün? ").lower()
#         inventar.append(yeni_esya)
#         print(f"✅ '{yeni_esya}' çantaya əlavə olundu!")
#
#     elif emr == "at":
#         silinen_esya = input("Hansı əşyanı çantanızdan atmaq istəyirsiniz? ").lower()
#
#         # in operatoru ilə əşyanın çantada olub-olmadığını yoxlayırıq
#         if silinen_esya in inventar:
#             inventar.remove(silinen_esya)
#             print(f" '{silinen_esya}' çantadan atıldı.")
#         else:
#             print(f"❌ Xəta: Çantanızda '{silinen_esya}' adında bir əşya yoxdur!")
#
#     else:
#         print("⚠️ Yanlış əmr! Zəhmət olmasa 'bax', 'at', 'götür' və ya 'çıx' yazın.")

#task1anagram
# soz1 = input("Birinci sözü daxil edin: ")
# soz2 = input("İkinci sözü daxil edin: ")
#
# sirali_soz1 = sorted(soz1.replace(" ", "").lower())
# sirali_soz2 = sorted(soz2.replace(" ", "").lower())
#
# if sirali_soz1 == sirali_soz2:
#     print(f"Əla! '{soz1}' və '{soz2}' sözləri anagramdır.")
# else:
#     print(f" Xeyr, '{soz1}' və '{soz2}' sözləri anagram deyil.")

#task2

# Verilmiş ballar siyahısı
ballar = [45, 89, 100, 75, 100, 92, 89]

# 1. Siyahıdakı ən yüksək balı tapırıq
en_boyuk_bal = max(ballar)

# 2. İkinci ən böyük balı yadda saxlamaq üçün başlanğıc dəyər təyin edirik
ikinci_bal = 0

# 3. Siyahıdakı hər bir balı tək-tək yoxlayırıq
for bal in ballar:
    # Əgər bal ən böyük baldan (100-dən) kiçikdirsə VƏ hazırkı 'ikinci_bal'-dan böyükdürsə:
    if bal < en_boyuk_bal and bal > ikinci_bal:
        ikinci_bal = bal

print(f"Ən yüksək ikinci bal: {ikinci_bal}")