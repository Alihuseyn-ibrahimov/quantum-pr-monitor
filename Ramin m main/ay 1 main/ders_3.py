adlar  = ["Anar", "Leyla", "Rauf", "Günel", "Tural"]
ballar = [72, 45, 88, 51, 38]


for ad, bal in zip(adlar, ballar):
    print(f'hormetli, {ad}, sizin baliniz {bal}-dir')
    if bal < 50:
        print(' ve neticeniz zeifdir.')
    else:
        print('ve siz kecdiniz.')






