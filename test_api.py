import google.generativeai as genai

# DİQQƏT: Öz əsl API açarınızı aşağıdakı dırnaqların içinə yazın (secrets faylından yox, birbaşa bura)
API_KEY = "AQ.Ab8RN6LsGT7TshcZw1eWfZ7zA205-3FdVv5Uv9pTzCqtnTmCrA"
genai.configure(api_key=API_KEY)

print("Google serverinə qoşulur...")

try:
    # Ən stabil modeli yoxlayırıq
    model = genai.GenerativeModel('gemini-1.5-flash')
    cavab = model.generate_content("Salam, məni eşidirsən? Cəmi 1 cümlə ilə cavab ver.")

    print("\n✅ TƏBRİKLƏR! API TAM İŞLƏK VƏZİYYƏTDƏDİR:")
    print(cavab.text)

except Exception as e:
    print("\n❌ XƏTA BAŞ VERDİ:")
    print(e)