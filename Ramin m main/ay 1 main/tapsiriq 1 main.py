#Ev tapsirigi_1 Ramin m

ad = input('Adınızı daxil edin: ')
yas = int(input("Yaşınızı qeyd edin: "))
ayliq_gelir = float(input('Aylıq gəlirinizi yazın: '))

dogum_ili = 2026-yas
ayliq_vergi = ayliq_gelir*0.2
xalis_gelir = ayliq_gelir-ayliq_vergi


print(f'Salam, hörmətli {ad}! , Təqdim etdiyiniz məlumatlara'
      f'\n əsasən Sizin: Təxmini doğum iliniz: {dogum_ili};')


print(f'Aylıq 20 faiz vergi məbləğiniz: {ayliq_vergi} AZN;')
print(f'Vergiən sonra qalan xalis gəliriniz: {xalis_gelir} AZN-dir')


