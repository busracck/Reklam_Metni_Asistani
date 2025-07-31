# utils/llm_helpers.py
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# config.py'den sabitleri import edin
from config import GEMMA_MODEL_NAME, MAX_HEADLINE_CHARS, MAX_BODY_CHARS

def get_ad_gen_chain():
    """
    Reklam metni oluşturma LLM zincirini döndürür.
    """
    llm_gemma = OllamaLLM(model=GEMMA_MODEL_NAME)

    prompt_template = PromptTemplate(
        input_variables=[
            "product_name", "product_description", "target_audience",
            "ad_platform", "tone_of_voice", "keywords",
            "num_headlines", "num_ctas", "num_slogans"
        ],
        template=f"""
        Sen bir reklam metni yazarı asistanısın. Aşağıdaki bilgilere dayanarak yaratıcı ve etkili reklam metinleri oluştur.
        Lütfen tüm sayısal (adet) ve karakter (uzunluk) sınırlamalarına **KESİNLİKLE** uyun.
        Lütfen sadece reklam metinlerini ve ilgili başlıkları/sloganları üret, başka açıklama veya giriş/çıkış cümlesi ekleme.
        Her bir maddeyi yeni bir satırda ve madde işareti (-) ile başlat.

        Ürün/Hizmet Adı: {{product_name}}
        Ürün/Hizmet Açıklaması: {{product_description}}
        Hedef Kitle: {{target_audience}}
        Reklam Platformu: {{ad_platform}}
        Marka Tonu: {{tone_of_voice}}
        Anahtar Kelimeler: {{keywords}}

        ---
        Görev: Yukarıdaki bilgilere göre, aşağıdaki formatta reklam metinleri oluştur:

        **1. Reklam Başlıkları ({{num_headlines}} adet):**
        Kesinlikle ve yalnızca {{num_headlines}} adet farklı ve ilgi çekici reklam başlığı oluştur. Her başlık **KESİNLİKLE {MAX_HEADLINE_CHARS} karakteri geçmemelidir.**
        - [Başlık 1]
        - [Başlık 2]
        ...
        - [Başlık {{num_headlines}}]

        **2. Reklam Gövde Metni (1 adet):**
        Ürünün/hizmetin temel özelliklerini ve faydalarını vurgulayan, **KESİNLİKLE {MAX_BODY_CHARS} karakteri geçmeyen** tek bir reklam gövde metni oluştur.
        [Gövde Metni]

        **3. Harekete Geçirici Mesaj (Call to Action - CTA) Önerileri ({{num_ctas}} adet):**
        Kesinlikle ve yalnızca {{num_ctas}} adet farklı ve etkili harekete geçirici mesaj (CTA) önerisi oluştur.
        - [CTA 1]
        - [CTA 2]
        ...
        - [CTA {{num_ctas}}]

        **4. Slogan Önerileri ({{num_slogans}} adet):**
        Kesinlikle ve yalnızca {{num_slogans}} adet farklı ve akılda kalıcı slogan önerisi oluştur.
        - [Slogan 1]
        - [Slogan 2]
        ...
        - [Slogan {{num_slogans}}]
        """
    )
    return prompt_template | llm_gemma