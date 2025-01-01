import google.generativeai as genai
import streamlit as st
# from src.config.constants import GEMINI_API_KEY


GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_MODEL_NAME = 'gemini-1.5-flash'

@st.cache_resource
def get_gemini_model():
    """Lazy load Gemini model"""
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL_NAME)

def classify_texts_batch_gemini(texts, categories):
    """Classify multiple texts at once using Gemini API"""
    try:
        model = get_gemini_model()
        numbered_texts = "\n".join([f"{i}. {text}" for i, text in enumerate(texts, 1)])
        prompt = f"""Classify each of the following numbered texts into exactly one of these categories: {', '.join(categories)}

Texts to classify:
{numbered_texts}

For your response:
1. Return ONLY a numbered list matching the input numbers
2. Each line should contain ONLY the number and category
3. Format: "1. Category"
4. No explanations or additional text"""
        
        response = model.generate_content([prompt])
        return [line.split('. ')[1].strip() for line in response.text.strip().split('\n')]
        
    except Exception as e:
        raise Exception(f"Gemini batch classification failed: {str(e)}") 