# app.py
import streamlit as st
import json
import datetime
import os

# Yeni oluşturduğumuz modüllerden importlar
from config import MAX_HEADLINE_CHARS, MAX_BODY_CHARS, HUGGING_FACE_MODEL_NAME
from utils.web_scraper import get_website_content, analyze_website_with_llm
from utils.llm_helpers import get_ad_gen_chain
from image_generator.hf_image_client import get_hf_inference_client, translate_to_english, generate_image_with_hf_client, load_image_from_url

# --- Streamlit Arayüzü Başlangıç Ayarları ---
st.set_page_config(page_title="Yerel Reklam Metni Asistanı", page_icon="💡", layout="wide")

st.title("💡 Yerel Reklam Metni Asistanı")
st.subheader("Ürün/Hizmetleriniz İçin Yaratıcı Reklam Metinleri Oluşturun")

# --- Session state başlangıç ayarları ---
if 'product_name' not in st.session_state:
    st.session_state.product_name = ""
if 'product_description' not in st.session_state:
    st.session_state.product_description = ""
if 'target_audience' not in st.session_state:
    st.session_state.target_audience = ""
if 'keywords' not in st.session_state:
    st.session_state.keywords = ""

# --- 1. Kullanıcı Girdileri ---
st.markdown("---")
st.header("Reklam Bilgilerini Girin")

st.info("Aşağıdaki alanları manuel olarak doldurabilir veya bir web sitesi URL'si girerek bilgileri otomatik olarak çekebilirsiniz.")

# Manuel Giriş Alanları (Değerler session_state'ten alınacak)
product_name_input = st.text_input("Ürün veya Hizmet Adı:", value=st.session_state.product_name, key="manual_product_name_input", help="Örn: 'Akıllı Telefon', 'Online İngilizce Kursu', 'Kuzu Kebabı'")
product_description_input = st.text_area("Ürünün/Hizmetin Açıklaması:", value=st.session_state.product_description, key="manual_product_description_input", help="Ürününüzün ne olduğunu, temel özelliklerini ve faydalarını açıklayın.")
target_audience_input = st.text_input("Hedef Kitle:", value=st.session_state.target_audience, key="manual_target_audience_input", help="Örn: 'Genç profesyoneller', 'Yeni anneler', 'Küçük işletme sahipleri'")

col1, col2 = st.columns(2)
with col1:
    ad_platform = st.selectbox(
        "Reklam Platformu:",
        options=["Genel", "Google Ads", "Facebook/Instagram", "Twitter/X", "E-posta Pazarlaması"],
        key="ad_platform_select",
        help="Reklamın yayınlanacağı platformu seçin."
    )
with col2:
    tone_of_voice = st.selectbox(
        "Marka Tonu:",
        options=["Profesyonel", "Samimi", "Mizahi", "İkna Edici", "Bilgilendirici", "Yaratıcı"],
        key="tone_of_voice_select",
        help="Reklam metninin hangi tonda olmasını istersiniz?"
    )

keywords_input = st.text_input("Anahtar Kelimeler (virgülle ayırın):", value=st.session_state.keywords, key="manual_keywords_input", help="Reklamda geçmesini istediğiniz anahtar kelimeler.")

st.markdown("---")
st.header("Veya Web Sitesi URL'sinden Bilgileri Çekin")
st.info("Aşağıya bir web sitesi URL'si girerek, ürün/hizmet bilgilerini otomatik olarak çekebilir ve yukarıdaki alanları önceden doldurabilirsiniz.")

website_url_input = st.text_input("Web Sitesi URL'si:", help="Reklam oluşturmak istediğiniz web sitesinin tam adresini girin (örn: https://www.example.com).", key="website_url_input_field")
analyze_url_button = st.button("URL'yi Analiz Et ve Bilgileri Çek", key="analyze_url_button")

if analyze_url_button:
    if website_url_input:
        with st.spinner("Web sitesi içeriği analiz ediliyor..."):
            title, description, full_text = get_website_content(website_url_input)
            if full_text:
                extracted_data = analyze_website_with_llm(full_text)
                if extracted_data[0] or extracted_data[1] or extracted_data[2]:
                    st.session_state.product_name = extracted_data[0]
                    st.session_state.product_description = extracted_data[1]
                    st.session_state.keywords = extracted_data[2]
                    st.success("Web sitesi başarıyla analiz edildi ve bilgiler çekildi! Yukarıdaki alanlar güncellendi.")
                    st.rerun()
                else:
                    st.error("LLM'den bilgi çekilemedi veya JSON ayrıştırma hatası oluştu. Lütfen konsolu kontrol edin ve LLM'nin doğru çalıştığından emin olun.")
            else:
                st.error("Web sitesi içeriği çekilemedi. Lütfen URL'yi veya bağlantınızı kontrol edin ve tekrar deneyin.")
    else:
        st.warning("Lütfen analiz etmek istediğiniz web sitesinin URL'sini girin.")

st.markdown("---")
st.header("Oluşturulacak İçerik Sayısı")

col_num1, col_num2, col_num3 = st.columns(3)
with col_num1:
    num_headlines = st.number_input(
        "Kaç Adet Başlık Oluşturulsun?",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="num_headlines_input",
        help="Oluşturulacak reklam başlığı sayısını belirleyin."
    )
with col_num2:
    num_ctas = st.number_input(
        "Kaç Adet Harekete Geçirici Mesaj (CTA) Oluşturulsun?",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="num_ctas_input",
        help="Oluşturulacak Harekete Geçirici Mesaj (CTA) sayısını belirleyin."
    )
with col_num3:
    num_slogans = st.number_input(
        "Kaç Adet Slogan Oluşturulsun?",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="num_slogans_input",
        help="Oluşturulacak Slogan sayısını belirleyin."
    )

# LLM zincirini utils/llm_helpers.py'den çağır
llm_chain = get_ad_gen_chain()

# --- 3. Reklam Metni Üretme Butonu ---
st.markdown("---")
generate_button = st.button("Reklam Metni Oluştur", type="primary")

if generate_button:
    if not product_name_input or not product_description_input or not target_audience_input:
        st.warning("Lütfen Ürün/Hizmet Adı, Açıklaması ve Hedef Kitle alanlarını doldurun.")
    else:
        with st.spinner("Reklam metinleri oluşturuluyor..."):
            try:
                inputs = {
                    "product_name": product_name_input,
                    "product_description": product_description_input,
                    "target_audience": target_audience_input,
                    "ad_platform": ad_platform,
                    "tone_of_voice": tone_of_voice,
                    "keywords": keywords_input,
                    "num_headlines": num_headlines,
                    "num_ctas": num_ctas,
                    "num_slogans": num_slogans
                }

                response = llm_chain.invoke(inputs)

                st.markdown("### Oluşturulan Reklam Metinleri")
                
                # --- Üretilen Metinleri Ayrıştırma ve Karakter Sayısıyla Gösterme ---
                output_parts = response.split('**1. Reklam Başlıkları')
                headlines_raw = ""
                body_text_raw = ""
                ctas_raw = ""
                slogans_raw = ""

                if len(output_parts) > 1:
                    headlines_part = output_parts[1].split('**2. Reklam Gövde Metni')
                    headlines_raw = headlines_part[0].strip() if len(headlines_part) > 0 else ""

                    if len(headlines_part) > 1:
                        body_text_part = headlines_part[1].split('**3. Harekete Geçirici Mesaj')
                        body_text_raw = body_text_part[0].strip() if len(body_text_part) > 0 else ""

                        if len(body_text_part) > 1:
                            ctas_part = body_text_part[1].split('**4. Slogan Önerileri')
                            ctas_raw = ctas_part[0].strip() if len(ctas_part) > 0 else ""

                            if len(ctas_part) > 1:
                                slogans_raw = ctas_part[1].strip()

                st.markdown("#### Reklam Başlıkları:")
                headlines_list = []
                headlines = [h.strip('- ').strip() for h in headlines_raw.split('\n') if h.strip().startswith('-')]
                for h in headlines:
                    char_count = len(h)
                    display_text = f"**{h}**({char_count} karakter)"
                    if char_count > MAX_HEADLINE_CHARS:
                        st.warning(f"{display_text} - **UYARI: {MAX_HEADLINE_CHARS} karakter limitini aşıyor!**")
                    else:
                        st.write(display_text)
                    headlines_list.append({"text": h, "char_count": char_count})
                if not headlines: st.info("Başlık oluşturulamadı.")

                st.markdown("#### Reklam Gövde Metni:")
                body_text = body_text_raw.replace(f" ({{num_headlines}} adet):", "").replace(f" ({{num_ctas}} adet):", "").replace(f" ({{num_slogans}} adet):", "").strip()
                body_text = body_text.replace("Ürünün/hizmetin temel özelliklerini ve faydalarını vurgulayan, 90 karakteri geçmeyen tek bir reklam gövde metni oluştur.", "").replace("[Gövde Metni]", "").strip()
                
                if '\n' in body_text:
                    temp_body_lines = [line.strip() for line in body_text.split('\n') if line.strip()]
                    body_text = temp_body_lines[0] if temp_body_lines else ""

                char_count_body = len(body_text)
                if body_text:
                    display_text_body = f"**{body_text}**({char_count_body} karakter)"
                    if char_count_body > MAX_BODY_CHARS:
                        st.warning(f"{display_text_body} - **UYARI: {MAX_BODY_CHARS} karakter limitini aşıyor!**")
                    else:
                        st.write(display_text_body)
                else:
                    st.info("Gövde metni oluşturulamadı.")

                st.markdown("#### Harekete Geçirici Mesaj (CTA) Önerileri:")
                ctas_list = []
                ctas = [c.strip('- ').strip() for c in ctas_raw.split('\n') if c.strip().startswith('-')]
                for c in ctas:
                    char_count = len(c)
                    st.write(f"**{c}**({char_count} karakter)")
                    ctas_list.append({"text": c, "char_count": char_count})
                if not ctas: st.info("CTA oluşturulamadı.")

                st.markdown("#### Slogan Önerileri:")
                slogans_list = []
                slogans = [s.strip('- ').strip() for s in slogans_raw.split('\n') if s.strip().startswith('-')]
                for s in slogans:
                    char_count = len(s)
                    st.write(f"**{s}**({char_count} karakter)")
                    slogans_list.append({"text": s, "char_count": char_count})
                if not slogans: st.info("Slogan oluşturulamadı.")


                # --- Üretilen Metinleri ve Metadatayı JSON'a Kaydetme ---
                output_data = {
                    "request_parameters": {
                        "product_name": product_name_input,
                        "product_description": product_description_input,
                        "target_audience": target_audience_input,
                        "ad_platform": ad_platform,
                        "tone_of_voice": tone_of_voice,
                        "keywords": [k.strip() for k in keywords_input.split(',')] if keywords_input else [],
                        "num_headlines": num_headlines,
                        "num_ctas": num_ctas,
                        "num_slogans": num_slogans
                    },
                    "generated_content": {
                        "headlines": headlines_list,
                        "body_text": {"text": body_text, "char_count": char_count_body},
                        "ctas": ctas_list,
                        "slogans": slogans_list
                    },
                    "raw_llm_response": response
                }

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_folder = "json_outputs"
                os.makedirs(output_folder, exist_ok=True)

                file_name = os.path.join(output_folder, f"reklam_metni_{timestamp}.json")

                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=4)

                st.success(f"Reklam metni ve bilgileri '{output_folder}/{os.path.basename(file_name)}' dosyasına kaydedildi!")

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
                st.warning("Ollama sunucunuzun çalıştığından ve 'gemma3:4b' modelinin yüklü olduğundan emin olun (terminalde `ollama run gemma3:4b`).")


# --- 4. Görsel Oluşturma Bölümü ---
st.markdown("---")
st.header("Reklam Görseli Oluştur")
st.info("İsterseniz bir görsel URL'si girerek hazır bir görsel kullanabilir veya ürün adınızı kullanarak yeni bir görsel oluşturabilirsiniz.")

# Seçenek 1: URL'den Görsel Yükleme
st.subheader("1. URL'den Görsel Yükle")
image_url = st.text_input("Görselin URL'sini Girin:", help="Reklamınızda kullanmak istediğiniz görselin web adresini buraya yapıştırın.", key="url_image_input")
load_image_from_url_button = st.button("URL'den Görseli Yükle", key="load_image_url_button")

if load_image_from_url_button:
    if image_url:
        with st.spinner(f"'{image_url}' adresindeki görsel yükleniyor..."):
            loaded_image = load_image_from_url(image_url)
            if loaded_image:
                st.markdown("#### Yüklenen Reklam Görseli")
                st.image(loaded_image, caption="Yüklenen Görsel", use_container_width=True)
            else:
                st.error("Belirtilen URL'den görsel yüklenemedi. Lütfen URL'yi kontrol edin ve tekrar deneyin.")
    else:
        st.warning("Lütfen bir görsel URL'si girin.")


# Seçenek 2: Metin ile Görsel Oluşturma (Hugging Face)
st.subheader("2. Metin ile Görsel Oluştur (Hugging Face)")

hf_client = get_hf_inference_client()

generate_image_button_hf = st.button("Metin ile Reklam Görseli Oluştur", key="generate_image_huggingface_button")

if generate_image_button_hf:
    if not product_name_input:
        st.warning("Görsel oluşturmak için lütfen 'Ürün veya Hizmet Adı' alanını doldurun.")
    else:
        if hf_client:
            with st.spinner(f"'{product_name_input}' için görsel oluşturuluyor... (Model: {HUGGING_FACE_MODEL_NAME})"):
                try:
                    translated_product_name = translate_to_english(product_name_input)
                    if not translated_product_name:
                        st.error("Ürün adı çevrilemedi veya boş döndü. Lütfen geçerli bir ürün adı girin ve 'llama3' çeviri modelini kontrol edin.")
                        translated_product_name = product_name_input

                    image_prompt = f"high-quality, realistic advertising image for {translated_product_name}, emphasizing its best features, an engaging and professional composition, product photography style"

                    generated_pil_image = generate_image_with_hf_client(image_prompt) # Artık model adı fonksiyonda

                    if generated_pil_image:
                        st.markdown("#### Oluşturulan Reklam Görseli")
                        st.image(generated_pil_image, caption=f"'{product_name_input}' için Oluşturulan Görsel", use_container_width=False)
                    else:
                        st.error("Görsel oluşturulamadı. Lütfen yukarıdaki hata mesajlarını kontrol edin.")

                except Exception as e:
                    st.error(f"Görsel oluşturma sırasında beklenmedik bir hata oluştu: {e}")
                    st.warning("Lütfen internet bağlantınızı ve Hugging Face API erişiminizi kontrol edin.")
        else:
            st.error("Hugging Face istemcisi başlatılamadığı için görsel oluşturulamıyor. Lütfen HF_TOKEN ortam değişkeninizi kontrol edin.")


st.markdown("---")
st.caption("Powered by Ollama, Gemma, LangChain, Streamlit ve Hugging Face")