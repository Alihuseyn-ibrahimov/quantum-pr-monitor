# # # # # # # # ad= 'Kamran'
# # # # # # # # # yas= 21
# # # # # # # # # sheher= 'Bakı'
# # # # # # # # # print(f'Salam,mənim adım {ad} yaşım {yas} şəhərim {sheher}')
# # # # # # # #
# # # # # # # # # mehsul1 = 4.50
# # # # # # # # #
# # # # # # # # # mehsul2 = 12.99
# # # # # # # # #
# # # # # # # # # mehsul3 = 7.25
# # # # # # # # #
# # # # # # # # # umumi = mehsul1+mehsul2+mehsul3
# # # # # # # # #
# # # # # # # # # print(umumi)
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # # dogum_ili = int(input("Dogum ilinizi yazin:"))
# # # # # # # # yas=2025-dogum_ili
# # # # # # # # print(yas)
# # # # # # #
# # # # # # # en=float(input('duzbucaqlinin enini qeyd edin'))
# # # # # # # uzunluq=float(input('duzbucaqlinin uzunlugunu qeyd edin'))
# # # # # # # sahe=uzunluq*en
# # # # # # # perimetr=2*(en+uzunluq)
# # # # # # # print(sahe)
# # # # # # # print(perimetr)
# # # # # # a= int(input('a-i daxil et'))
# # # # # # b= int(input('b-i daxil et'))
# # # # # # print(a/b)
# # # # # # print(a//b)
# # # # # # print(a%b)
# # # # #
# # # # # a=int(input('a-i daxil et'))
# # # # # b=int(input('b-daxil et'))
# # # # # print(a==b)
# # # # # print(a>b)
# # # # # print(a>=b)
# # #
# # # bal = int(input("İmtahan balını daxil edin: "))
# # # davamiyyet = int(input("Davamiyyəti daxil edin: "))
# # #
# # # netice = bal >= 60 and davamiyyet >= 80
# # # print("Qəbul olundu:", netice)
# #
# # qiymet= int(input('malin qiymetin yaz'))
# # endirim=int(input('malin endirimin yaz'))
# # print(qiymet*endirim/100)
#
eded = float(input('onluq eded yazin'))
print(abs(eded))
print(round(eded,2))

# eded = -9.7341
#
# print("Mütləq dəyər:", abs(eded))
# print("Yuvarlaqlaşdırılmış:", round(eded, 2))






# istifadeci_adi = input("İstifadəçi adını daxil edin: ")
# shifre = input("Şifrəni daxil edin: ")
#
# giris_ugurlu = istifadeci_adi == "admin" and shifre == "1234"
# print("Giriş uğurlu:", giris_ugurlu)
# print("Giriş uğursuz:", not giris_ugurlu)