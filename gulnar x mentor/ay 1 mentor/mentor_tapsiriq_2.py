# task1
stekan_sayi = int(input("Gündə neçə stəkan su içirisiniz?"))
if stekan_sayi <= 3:
    print("Çox az su içirsiniz")
elif stekan_sayi <= 7:
    print("Yaxşıdır, amma biraz da artıra bilərsiniz")
else:
    print("Əla, normadan artıq içirsiniz")

# # task2
# alis_meblegi = float(input("Alış məbləğini qeyd edin: "))
#
# if alis_meblegi < 100:
#     print("Endirim yoxdur. Ödənişiniz:", alis_meblegi, "manat")
# elif alis_meblegi <= 300:
#     endirim = alis_meblegi * 0.10
#     son = alis_meblegi - endirim
#     print("Ödəniş:", son, "manat")
# else:
#     endirim = mebleg * 0.20
#     yekun = mebleg - endirim
#     print("Ödəniş:", yekun, "manat")
#
#     # task3
# gun_nomresi = int(input("Gun nomresini daxil edin"))
# if gun_nomresi == 6 or gun_nomresi == 7:
#     print("Bugun istirahet gunudur, dincelin")
# else:
#     print("Bugun is gunudur, ugurlar")
#
#     # task4
# sifaris_meblegi = float(input('sifaris meblegi necedir?'))
# if sifaris_meblegi > 50:
#     print(f"catdirilma pulsuzdur, yekun mebleg {sifaris_meblegi} azn")
# else:
#     print(f"catdirilma 3 azn, yekun mebleg {sifaris_meblegi + 3}azn")
#
#     # task5
# saat = int(input('saati deyin'))
# if saat >= 22 or saat < 7:
#     print('artiq gecedir, yatin')
# else:
#     print('artiq sabahdir, gununuz ugurlu olsun')
#
# # task6
# sefer_sayi = int(input('sefer sayiniz necedir'))
# ferdi = sefer_sayi * 0.3
# abonent = 10
# if ferdi < abonent:
#     ferq = abonent - ferdi
#     print("ferdi bilet daha serfelidir, qenaet meblegi:", round(ferdi, 2), "azn")
# else:
#     ferq = ferdi - abonement
#     print("Abonement sərfəlidir. Qənaət:", round(ferq, 2), "azn")
#
#     # task7
# imtahan_bali = int(input('imtahan_balinizi qeyd edin: '))
# davamiyyet = float(input("Davamiyyət faizinizi qeyd edin: "))
# if imtahan_bali > 60 and davamiyyet > 80:
#     print("siz kecdiniz")
# elif imtahan_bali < 60 and davamiyyet <= 80:
#     print("hec bir sert odenilmedi")
# elif imtahan_bali < 60:
#     print("baliniz azdir")
# else:
#     print("davamiyetiniz azdir")
#
#
#
