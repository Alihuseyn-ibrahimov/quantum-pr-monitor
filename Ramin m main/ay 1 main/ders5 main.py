# 1. Dictionary yaratmaq
alet_kataloqu = {
    "hava": "Hava durumunu deyir",
    "tercume": "Mətni tərcümə edir"
}

# 2. .items() və for dövrü ilə alətləri çap etmək
for alet, i in alet_kataloqu.items():
    print(f"Alət: {alet} | İş: {i}")

# 3. .get() ilə "musiqi" adlı aləti yoxlamaq
musiqi_yoxlanisi = alet_kataloqu.get("musiqi", "Bu alət yoxdur")
print(f"Musiqi aləti: {musiqi_yoxlanisi}")

# 4. Kataloqa yeni "axtaris" alətini əlavə etmək
alet_kataloqu["axtaris"] = "İnternetdə axtarış edir"
print(alet_kataloqu)

# 5. Listdəki təkrarları set() ilə silmək
tekrarlanan_siyahi = ["hava", "tercume", "hava", "axtaris"]
unikal_siyahi = list(set(tekrarlanan_siyahi))

print(f"Unikal elementlər: {unikal_siyahi}")