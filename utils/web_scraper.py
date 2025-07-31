# utils/web_scraper.py
import streamlit as st
import requests #' HTTP isteklerini yapmak ve yanıtlarını işlemek
from bs4 import BeautifulSoup # type: ignore   #HTML ve XML belgelerini ayrıştırmak için tasarlanmış bir Python kütüphanesidir
import json
from langchain_ollama import OllamaLLM # type: ignore # Ollama'ya gönderilen istekleri göndermek ve yanıtları almak
from langchain_core.prompts import PromptTemplate

# config.py'den sabitleri import edin
from config import MAX_TEXT_LENGTH_FOR_ANALYSIS, LLAMA3_MODEL_NAME

def get_website_content(url):
    """
    Belirtilen URL'deki web sitesinin metin içeriğini çeker ve ayrıştırır.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # HTTP hataları için hata yükselt
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('title').get_text() if soup.find('title') else ""
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description['content'] if meta_description and 'content' in meta_description.attrs else ""

        for script_or_style in soup(['script', 'style']):
            script_or_style.extract()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        if len(text) > MAX_TEXT_LENGTH_FOR_ANALYSIS:
            text = text[:MAX_TEXT_LENGTH_FOR_ANALYSIS] + "..."

        return title, description, text

    except requests.exceptions.ConnectionError:
        st.error(f"Web sitesine bağlantı kurulamadı. URL'yi kontrol edin, internet bağlantınızı doğrulayın ve web sitesinin erişilebilir olduğundan emin olun.")
        return None, None, None
    except requests.exceptions.Timeout:
        st.error(f"Web sitesinden yanıt alınamadı (zaman aşımı). Web sitesinin yüklenmesi uzun sürüyor veya erişilemiyor olabilir.")
        return None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Web sitesine erişim sırasında bir hata oluştu: {e}. URL'yi kontrol edin.")
        return None, None, None
    except Exception as e:
        st.error(f"Web sitesi içeriği işlenirken beklenmedik bir hata oluştu: {e}. Web sitesi yapısı beklenenden farklı olabilir.")
        return None, None, None

def analyze_website_with_llm(website_content_text):
    """
    Çekilen web sitesi içeriğini LLM ile analiz eder ve JSON formatında ürün/hizmet bilgileri döndürür.
    """
    prompt = PromptTemplate(
        input_variables=["website_content"],
        template="""
        Aşağıdaki web sitesi içeriğini analiz et ve bana aşağıdaki bilgileri JSON formatında döndür.
        Sadece JSON çıktısı ver, başka hiçbir açıklama veya ek metin içerme.
        Ürün/hizmet adı, açıklaması ve anahtar kelimeler ana web sayfasından çıkarılmalıdır.
        Anahtar kelimeler 5-7 adet olmalı ve virgülle ayrılmış olmalıdır.

        Web Sitesi İçeriği:
        {website_content}

        JSON Çıktısı Formatı:
        {{
            "product_name": "...",
            "product_description": "...",
            "keywords": "anahtar1, anahtar2, ..."
        }}
        """
    )
    llm_analyzer = OllamaLLM(model=LLAMA3_MODEL_NAME) # config'den model adı kullanıldı
    chain = prompt | llm_analyzer

    try:
        response = chain.invoke({"website_content": website_content_text})
        response = response.strip()
        if response.startswith("```json"):
            response = response[len("```json"):].strip()
        if response.endswith("```"):
            response = response[:-len("```")].strip()

        data = json.loads(response)
        return data.get("product_name", ""), data.get("product_description", ""), data.get("keywords", "")
    except json.JSONDecodeError as e:
        st.error(f"LLM çıktısı JSON olarak ayrıştırılamadı. Modelin doğru formatı döndürdüğünden emin olun. Hata: {e}")
        st.code(response, language="json")
        return "", "", ""
    except Exception as e:
        st.error(f"Web sitesi analizinde beklenmedik bir hata oluştu: {e}")
        return "", "", ""