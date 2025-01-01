import streamlit as st
import pandas as pd
import os
from src.config.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_SEPARATOR,
    SEPARATOR_OPTIONS,
    STATIC_DIR
)
from src.utils.privacy import mask_ids
from src.utils.file_processing import process_file
from src.visualization.dashboard import create_dashboard

def setup_page_config():
    """Configure page settings and styling"""
    st.set_page_config(
        page_title="مصنف",
        page_icon="📜",
        layout="centered"
    )
    
    # Load external CSS
    css_path = os.path.join(STATIC_DIR, "style.css")
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Add custom CSS for categories input
    st.markdown("""
        <style>
        .stTextArea textarea {
            font-size: 14px !important;
            line-height: 1.5 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    setup_page_config()
    
    st.title("📜 مصنف النصوص العربية")
    st.write("قم برفع ملفك وتحديد الفئات لتصنيف النصوص تلقائياً.")
    
    # File upload section
    st.header("1️⃣ رفع الملف")
    col1, col2 = st.columns([2, 1])
    
    with col2:
        file_type = st.selectbox("نوع الملف:", ["CSV", "TXT"])
    
    with col1:
        uploaded_file = st.file_uploader(f"قم برفع ملف {file_type}", type=[file_type.lower()])
    
    if uploaded_file:
        try:
            st.subheader("📄 معاينة الملف")
            column = None
            separator = DEFAULT_SEPARATOR
            
            if file_type == "CSV":
                df_preview = pd.read_csv(uploaded_file)
                if not df_preview.empty and len(df_preview.columns) > 0:
                    column = st.selectbox("اختر العمود المراد تصنيفه:", df_preview.columns)
                    
                    if column:
                        # Store original texts and create masked version
                        original_texts = df_preview[column].tolist()
                        masked_texts = [mask_ids(text) for text in original_texts]
                        
                        # Check if any masking was applied
                        was_masked = any(orig != masked for orig, masked in zip(original_texts, masked_texts))
                        
                        if was_masked:
                            st.markdown("### النص الأصلي")
                            st.dataframe(df_preview[[column]].head(100), use_container_width=True)
                            
                            st.markdown("### النص بعد إخفاء المعرفات")
                            masked_df = df_preview.copy()
                            masked_df[column] = masked_texts
                            st.dataframe(masked_df[[column]].head(100), use_container_width=True)
                            
                            if "masking_notified" not in st.session_state:
                                st.toast("تم تطبيق إخفاء المعرفات على النصوص 🔒", icon="ℹ️")
                                st.session_state.masking_notified = True
                        else:
                            st.dataframe(df_preview.head(100), use_container_width=True)
                    
                    # Display file information in one line
                    st.markdown(f"""
                    <div style='background-color: #f1f5f9; padding: 0.7rem; border-radius: 8px; margin: 0.5rem 0;'>
                        <div style='display: flex; align-items: center; justify-content: space-between;'>
                            <h3 style='margin: 0; color: #1E3A8A;'>📊 معلومات الملف</h3>
                            <span>عدد الصفوف: {len(df_preview):,} | عدد الأعمدة: {len(df_preview.columns)}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("ملف CSV فارغ أو لا يحتوي على أعمدة.")
                    return
            else:
                content = uploaded_file.getvalue().decode('utf-8')
                if content.strip():
                    # Split content and create masked version
                    texts = [text.strip() for text in content.split(separator) if text.strip()]
                    masked_texts = [mask_ids(text) for text in texts]
                    
                    # Check if any masking was applied
                    was_masked = any(orig != masked for orig, masked in zip(texts, masked_texts))
                    
                    if was_masked:
                        st.markdown("### النص الأصلي")
                        st.text_area("", value=content, height=200)
                        
                        st.markdown("### النص بعد إخفاء المعرفات")
                        masked_content = separator.join(masked_texts)
                        st.text_area("", value=masked_content, height=200)
                        
                        if "masking_notified" not in st.session_state:
                            st.toast("تم تطبيق إخفاء المعرفات على النصوص 🔒", icon="ℹ️")
                            st.session_state.masking_notified = True
                    else:
                        st.text_area("محتوى الملف:", value=content, height=200)
                    
                    # Separator selection with preview
                    st.write("**اختر الفاصل:**")
                    custom_col, select_col = st.columns([1, 1])
                    
                    with select_col:
                        separator_choice = st.selectbox(
                            "نوع الفاصل",
                            options=[opt[0] for opt in SEPARATOR_OPTIONS],
                            format_func=lambda x: next((opt[1] for opt in SEPARATOR_OPTIONS if opt[0] == x), x),
                            label_visibility="collapsed"
                        )
                    
                    with custom_col:
                        if separator_choice == "custom":
                            custom_separator = st.text_input(
                                "أدخل الفاصل المخصص:",
                                value="",
                                help="أدخل الرمز أو النص الذي يفصل بين النصوص",
                                label_visibility="collapsed"
                            )
                            if custom_separator:
                                separator = custom_separator
                                st.markdown(f"<div class='separator-preview'>الفاصل المختار: \"{separator}\"</div>", unsafe_allow_html=True)
                        else:
                            separator = separator_choice
                            display_separator = "↵" if separator == "\n" else separator
                            st.markdown(f"<div class='separator-preview'>الفاصل المختار: \"{display_separator}\"</div>", unsafe_allow_html=True)

                    # Recalculate texts based on current separator
                    current_texts = [text.strip() for text in content.split(separator) if text.strip()]
                    total_texts = len(current_texts)
                    avg_length = sum(len(text) for text in current_texts) / total_texts if total_texts > 0 else 0
                    
                    st.markdown(f"""
                    <div style='background-color: #f1f5f9; padding: 0.7rem; border-radius: 8px; margin: 0.5rem 0;'>
                        <div style='display: flex; align-items: center; justify-content: space-between;'>
                            <h3 style='margin: 0; color: #1E3A8A;'>📄 معلومات الملف</h3>
                            <span>عدد النصوص: {total_texts:,} | متوسط طول النص: {avg_length:.1f} حرف</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("ملف TXT فارغ.")
                    return
            
            # Categories and Processing
            st.header("2️⃣ الفئات والمعالجة")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                categories_input = st.text_area(
                    "أدخل الفئات (فئة واحدة في كل سطر)",
                    help="يجب إدخال فئة واحدة على الأقل"
                )
                categories = [cat.strip() for cat in categories_input.split("\n") if cat.strip()]
                if categories:
                    st.write("الفئات:", categories)

            with col2:
                st.write("**⚙️ إعدادات المعالجة**")
                batch_size = st.number_input(
                    "حجم الدفعة",
                    min_value=1,
                    max_value=100,
                    value=DEFAULT_BATCH_SIZE,
                    help="عدد النصوص التي سيتم معالجتها في كل طلب"
                )

            if 'classification_results' not in st.session_state:
                st.session_state.classification_results = None

            if st.button("🚀 بدء التصنيف", use_container_width=True):
                if not categories:
                    st.toast("يجب إدخال فئة واحدة على الأقل ⚠️", icon="⚠️")
                else:
                    uploaded_file.seek(0)
                    results, was_masked = process_file(uploaded_file, file_type, categories, batch_size, column, separator)
                    st.session_state.classification_results = results
                    st.session_state.was_masked = was_masked
                
            if st.session_state.classification_results is not None:
                st.header("📊 النتائج")
                st.dataframe(st.session_state.classification_results, use_container_width=True)
                
                fig = create_dashboard(st.session_state.classification_results)
                st.plotly_chart(fig, use_container_width=True)
                
                # CSV export with proper BOM for Excel compatibility
                csv_data = st.session_state.classification_results.to_csv(index=False, encoding='utf-8-sig', quoting=1)
                st.download_button(
                    label="📥 تحميل النتائج (CSV)",
                    data=csv_data.encode('utf-8-sig'),
                    file_name="classification_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")

if __name__ == "__main__":
    main() 