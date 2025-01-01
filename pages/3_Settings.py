import streamlit as st
import json
import os
from src.config.constants import SETTINGS_FILE, STATIC_DIR
from src.utils.privacy import clear_privacy_cache

# Constants
SETTINGS_FILE = "config/privacy_settings.json"
DEFAULT_SETTINGS = {
    "id_patterns": []  # List of dictionaries with start_with, length, and description
}

# Page Configuration
st.set_page_config(
    page_title="مصنف",
    page_icon="🔒",
    layout="centered"
)

# Custom CSS for RTL and better design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@100;200;300;400;500;600;700;800;900&display=swap');
    
    /* Global font and RTL settings */
    * {
        font-family: 'Noto Kufi Arabic', sans-serif !important;
    }
    
    /* RTL Support */
    .element-container, .stMarkdown, .stButton, .stTextInput, .stNumberInput {
        direction: rtl;
        text-align: right;
    }
    
    /* Card-like container */
    .settings-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Pattern list styling */
    .pattern-item {
        background-color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    
    .pattern-item:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transform: translateY(-1px);
    }
    
    .pattern-info {
        font-size: 1.1rem;
        color: #1e293b;
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        align-items: center;
    }
    
    .pattern-info > div {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .pattern-info strong {
        color: #64748b;
        font-weight: 500;
        white-space: nowrap;
    }
    
    .pattern-value {
        background-color: #f0f9ff;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        color: #0369a1;
        font-weight: 600;
        display: inline-block;
        min-width: 3rem;
        text-align: center;
        border: 1px solid #bae6fd;
    }
    
    .pattern-description {
        color: #059669;
        padding: 0.4rem 1rem;
        background-color: #ecfdf5;
        border-radius: 6px;
        border: 1px solid #6ee7b7;
        display: inline-block;
        font-size: 0.95rem;
        min-width: 120px;
        max-width: 300px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 500;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        height: 2.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .add-button>button {
        width: 100%;
        background-color: #3b82f6;
        color: white;
        border: none;
        height: 3rem;
        font-weight: 600;
    }
    
    .add-button>button:hover {
        background-color: #2563eb;
    }
    
    .delete-btn {
        margin-top: 8px;
        margin-right: 15px;
    }
    
    .delete-btn button {
        background-color: #fef2f2 !important;
        color: #dc2626 !important;
        border: 1px solid #fecaca !important;
        padding: 4px 15px !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .delete-btn button:hover {
        background-color: #fee2e2 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(220, 38, 38, 0.1);
    }
    
    /* Hide the actual streamlit button */
    button[kind="primary"] {
        display: none;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        text-align: right;
        direction: rtl;
        font-family: 'Noto Kufi Arabic', sans-serif !important;
    }
    
    .stNumberInput>div>div>input {
        text-align: right;
        direction: rtl;
        font-family: 'Noto Kufi Arabic', sans-serif !important;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #1e3a8a;
        margin-bottom: 1rem;
        font-family: 'Noto Kufi Arabic', sans-serif !important;
        font-weight: 700;
    }
    
    /* Help text */
    .stMarkdown div {
        font-size: 0.95rem;
        color: #4b5563;
    }
    
    /* Custom styles for pattern display */
    .pattern-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Ensure config directory exists
os.makedirs("config", exist_ok=True)

def load_privacy_settings():
    """Load privacy settings from file"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"id_patterns": []}
    except Exception as e:
        st.error(f"خطأ في تحميل الإعدادات: {str(e)}")
        return {"id_patterns": []}

def save_privacy_settings(settings):
    """Save privacy settings to file"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"خطأ في حفظ الإعدادات: {str(e)}")

def clear_privacy_cache():
    """Clear privacy settings cache from session state"""
    if "privacy_patterns_cache" in st.session_state:
        del st.session_state["privacy_patterns_cache"]
    if "compiled_patterns" in st.session_state:
        del st.session_state["compiled_patterns"]
    if "masking_notified" in st.session_state:
        del st.session_state["masking_notified"]

def delete_pattern(index):
    """Delete a pattern from the settings"""
    settings = load_privacy_settings()
    if 0 <= index < len(settings["id_patterns"]):
        settings["id_patterns"].pop(index)
        save_privacy_settings(settings)
        clear_privacy_cache()
        st.session_state.show_toast = "delete"
        st.rerun()

def is_duplicate_pattern(settings, start_with, length):
    """Check if a pattern with the same start_with and length already exists"""
    return any(
        pattern["start_with"] == start_with and pattern["length"] == length
        for pattern in settings["id_patterns"]
    )

def main():
    # Initialize session state for toast messages
    if "show_toast" not in st.session_state:
        st.session_state.show_toast = None

    # Show toast messages based on session state
    if st.session_state.show_toast == "delete":
        st.toast("تم حذف النمط بنجاح!", icon="✅")
        st.session_state.show_toast = None
    elif st.session_state.show_toast == "add":
        st.toast("تم إضافة النمط بنجاح!", icon="✅")
        st.session_state.show_toast = None
    elif st.session_state.show_toast == "error_digits":
        st.toast("يجب أن يحتوي الحقل 'يبدأ بـ' على أرقام فقط", icon="⚠️")
        st.session_state.show_toast = None
    elif st.session_state.show_toast == "error_empty":
        st.toast("الرجاء إدخال الرقم/الأرقام التي يبدأ بها المعرف", icon="⚠️")
        st.session_state.show_toast = None
    elif st.session_state.show_toast == "error_duplicate":
        st.toast("هذا النمط موجود بالفعل!", icon="⚠️")
        st.session_state.show_toast = None

    st.title("🔒 إعدادات الخصوصية")
    
    # Container for better spacing
    with st.container():
        st.markdown("""
        <div class="settings-card">
            <p>قم بإدارة إعدادات الخصوصية وأنماط إخفاء المعرفات في النصوص. يمكنك تحديد أنماط مختلفة للمعرفات التي تريد إخفاءها.</p>
        </div>
        """, unsafe_allow_html=True)

    # Load current settings
    settings = load_privacy_settings()

    # Add new pattern section
    st.header("✨ إضافة نمط جديد")
    with st.container():        
        col1, col2 = st.columns(2)
        with col1:
            length = st.number_input(
                "عدد الأرقام",
                min_value=1,
                max_value=20,
                value=10,
                help="العدد الإجمالي للأرقام في المعرف"
            )
        
        with col2:
            start_with = st.text_input(
                "يبدأ بـ",
                help="الرقم/الأرقام التي يبدأ بها المعرف",
                placeholder="مثال: 2 أو 23"
            )
        
        description = st.text_input(
            "وصف النمط",
            help="وصف قصير للمساعدة في تحديد الغرض من هذا النمط",
            placeholder="مثال: رقم الهوية الوطنية"
        )

        st.markdown('<div class="add-button">', unsafe_allow_html=True)
        if st.button("💾 إضافة نمط جديد", use_container_width=True):
            if start_with.strip():
                if not start_with.isdigit():
                    st.session_state.show_toast = "error_digits"
                    st.rerun()
                elif is_duplicate_pattern(settings, start_with, length):
                    st.session_state.show_toast = "error_duplicate"
                    st.rerun()
                else:
                    new_pattern = {
                        "start_with": start_with,
                        "length": length,
                        "description": description.strip() if description.strip() else "بدون وصف"
                    }
                    settings["id_patterns"].append(new_pattern)
                    save_privacy_settings(settings)
                    clear_privacy_cache()
                    st.session_state.show_toast = "add"
                    st.rerun()
            else:
                st.session_state.show_toast = "error_empty"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Display current patterns
    st.header("📋 الأنماط الحالية")
    with st.container():
        if settings["id_patterns"]:
            for i, pattern in enumerate(settings["id_patterns"]):
                with st.container():
                    col1, col2 = st.columns([1, 6])
                    with col1:
                        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"delete_{i}"):
                            delete_pattern(i)
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="pattern-item">
                            <div class="pattern-info">
                                <div><strong>يبدأ بـ:</strong> <span class="pattern-value">{pattern['start_with']}</span></div>
                                <div><strong>عدد الأرقام:</strong> <span class="pattern-value">{pattern['length']}</span></div>
                                <div><strong>الوصف:</strong> <span class="pattern-description">{pattern.get('description', 'بدون وصف')}</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="settings-card" style="text-align: center; color: #6b7280;">
                لا توجد أنماط مضافة حالياً
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()