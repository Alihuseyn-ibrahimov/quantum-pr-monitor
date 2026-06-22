 #Task1 suret heddi xeberdarligi
 suret=float(input('hazirki suretinizi yazin: '))
 if suret > 110:
     print('Siz suret heddini asdiniz,cerime tetbiq oluna biler')
 elif suret > 60 and suret < 110:
     print('siz normal suretle hereket edirsiniz')
 else:
     print('cox yavas gedirsiniz,sag zolaga kecin')


 #Task2 Endirim Hesablayıcı
 mehsulun_qiymeti = float(input('mehsulun qiymeti necedir?'))
 endirim = mehsulun_qiymeti - (mehsulun_qiymeti * 0.15)
 print((f'Endirimli qiymet:  {endirim} -dir'))



#Task3
 tam_eded = float(input('Tam eded yazin: '))
 if tam_eded > 0:
     print('Eded musbettir')
 elif tam_eded < 0:
     print('Eded menfidir')
 else:
     print('Daxil edilən ədəd sıfırdır')



 #Task4
 yas = int(input('yasinizi qeyd edin: '))
 if yas < 12 or yas > 65:
     print('biletler size pulsuzdur')
 else:
     print('bilet qiymeti 10 AZN-dir')



#Task5
 eded = int(input("Eded : "))
 if eded % 2 == 0:
     print("cutdur")
 else:
     print("tekdir")


 #Task6
 a = int(input('a: '))
 b = int(input('b: '))
 c = int(input('c: '))
 if a > b and a > c:
     print('en boyuk', a)

 elif b > c:
     print('en boyuk', b)
 else:
     print('en boyuk', c)


#Task7
bal=int(input('bal: '))
if bal>=90:
    print('qiymet A')
elif bal>=75:
    print('qiymet B')
elif bal>=60:
    print('qiymet C')
else:
    print('qiymet F kesildiniz')


#Task8
 a=float(input('birinci eded: '))
 b=float(input('ikinci eded: '))
 op = input("emeliyyat(+,-,*,/): ")
 if op=='+':
     print(a+b)
 elif op=='-':
     print(a-b)
 elif op=='*':
    print(a*b)
 elif op=='/'and b !=0:
     print(a/b)
 else:
     print('xeta sifira bolme!')
