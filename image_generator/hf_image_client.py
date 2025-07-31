# image_generator/hf_image_client.py
import requests
import streamlit as st
import os
from huggingface_hub import InferenceClient # type: ignore
from PIL import Image
from io import BytesIO
from langchain_ollama import OllamaLLM

# config.py'den sabitleri import edin
from config import LLAMA3_MODEL_NAME, HUGGING_FACE_MODEL_NAME

def get_hf_inference_client():
    """
    Hugging Face InferenceClient'ı başlatır ve döndürür.
    """
    hf_token = os.getenv("HF_TOKEN")

    if hf_token:
        try:
            hf_client = InferenceClient(
                token=hf_token,
                provider="hf-inference",
            )
            return hf_client
        except Exception as e:
            st.error(f"Hugging Face istemcisi başlatılamadı: {e}. HF_TOKEN ortam değişkeninizi kontrol edin.")
            return None
    else:
        st.warning("Hugging Face görsel oluşturma için bir API token'ına ihtiyacınız var. Hugging Face web sitesinden alıp terminalinizde `export HF_TOKEN='hf_...'` komutuyla ayarlayabilirsiniz.")
        return None

def translate_to_english(text_to_translate):
    """
    Verilen Türkçe metni İngilizceye çevirir (Ollama llama3 modeli ile).
    """
    if not text_to_translate:
        return ""
    try:
        llm_translator = OllamaLLM(model=LLAMA3_MODEL_NAME) # config'den model adı kullanıldı
        translation_prompt = f"Please translate the following Turkish text to English, provide only the translated text and nothing else:\nTurkish: {text_to_translate}\nEnglish:"
        translated_text = llm_translator.invoke(translation_prompt).strip()

        if "\n" in translated_text:
            translated_text = translated_text.split('\n')[0].strip()
        
        if translated_text.startswith("English:"):
            translated_text = translated_text[len("English:"):].strip()

        return translated_text
    except Exception as e:
        st.warning(f"Çeviri sırasında bir hata oluştu: {e}. '{LLAMA3_MODEL_NAME}' modelinin yüklü olduğundan emin olun.")
        return text_to_translate


def generate_image_with_hf_client(prompt_text):
    """
    Hugging Face InferenceClient kullanarak metinden görsel oluşturur.
    """
    hf_client = get_hf_inference_client()
    if hf_client is None:
        return None

    try:
        image = hf_client.text_to_image(
            prompt_text,
            model=HUGGING_FACE_MODEL_NAME, # config'den model adı kullanıldı
            width=512,
            height=512,
        )
        return image

    except Exception as e:
        st.error(f"Görsel API çağrısında hata oluştu: {e}")
        st.warning(
            f"'{HUGGING_FACE_MODEL_NAME}' modeliyle görsel oluşturulamadı. Olası nedenler:\n"
            "- Hugging Face API token'ınız (HF_TOKEN) doğru ayarlanmadı veya geçersiz.\n"
            "- Model çok büyük ve genel Inference API'sinde veya belirtilen boyutta çalışmıyor.\n"
            "- Hız limitine ulaşıldı veya modelin yüklenmesi uzun sürüyor.\n"
            "- İnternet bağlantınız yok."
        )
        return None

def load_image_from_url(url):
    """
    Verilen URL'den bir görseli yükler.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except requests.exceptions.RequestException as e:
        st.error(f"URL'ye erişilemedi veya görsel indirilemedi: {e}. URL'nin doğru olduğundan ve internet bağlantınızın olduğundan emin olun.")
        return None
    except Exception as e:
        st.error(f"Görsel dosyası açılamadı veya geçerli bir görsel formatı değil: {e}.")
        return None