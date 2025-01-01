import re
import json
import streamlit as st
from src.config.constants import SETTINGS_FILE, PRIVACY_CACHE_KEY
import os

def load_privacy_settings():
    """Load privacy settings from file with caching"""
    try:
        if PRIVACY_CACHE_KEY not in st.session_state:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    st.session_state[PRIVACY_CACHE_KEY] = json.load(f)
            else:
                st.session_state[PRIVACY_CACHE_KEY] = {"id_patterns": []}
        return st.session_state[PRIVACY_CACHE_KEY]
    except Exception:
        return {"id_patterns": []}

def compile_patterns(settings):
    """Compile regex patterns for better performance"""
    compiled_patterns = []
    for pattern in settings["id_patterns"]:
        start_with = pattern["start_with"]
        length = pattern["length"]
        regex_pattern = f"\\b{start_with}\\d{{{length - len(start_with)}}}\\b"
        compiled_patterns.append({
            "regex": re.compile(regex_pattern),
            "length": length,
            "description": pattern.get("description", "")
        })
    return compiled_patterns

def mask_ids(text):
    """Mask IDs in text based on privacy settings with improved performance"""
    if not isinstance(text, str):
        return text
        
    settings = load_privacy_settings()
    
    # Get or compile patterns
    if "compiled_patterns" not in st.session_state:
        st.session_state.compiled_patterns = compile_patterns(settings)
    
    if not st.session_state.compiled_patterns:
        return text
    
    masked_text = text
    original_text = text
    for pattern in st.session_state.compiled_patterns:
        masked_text = pattern["regex"].sub("X" * pattern["length"], masked_text)
    
    # Check if any masking was applied
    if masked_text != original_text and "masking_notified" not in st.session_state:
        st.toast("تم تطبيق إخفاء المعرفات على النصوص 🔒", icon="ℹ️")
        st.session_state.masking_notified = True
    
    return masked_text 