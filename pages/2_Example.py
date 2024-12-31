import streamlit as st
import pandas as pd
from app import process_file, create_dashboard

# Constants
EXAMPLE_FILE = "examples/Legal_Documents_Examples.csv"
CATEGORIES = ["الجنائي", "التجاري", "الأسري", "الإداري"]
BATCH_SIZE = 25

# Configure page
st.set_page_config(
    page_title="مصنف",
    page_icon="📜",
    layout="centered"
)

# Add custom CSS for RTL support and improved styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;700&display=swap');
    
    /* Global font settings */
    * {
        font-family: 'Noto Kufi Arabic', sans-serif !important;
    }
    
    /* RTL Support */
    .element-container, .stMarkdown, .stButton, .stText {
        direction: rtl;
        text-align: right;
    }
    
    /* Title styling */
    h1, h2, h3, .stTitle {
        font-family: 'Noto Kufi Arabic', sans-serif !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
    }
    
    /* Card styling */
    .css-card {
        border-radius: 10px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Category pill styling */
    .category-pill {
        display: inline-flex;
        padding: 8px 16px;
        border-radius: 20px;
        background-color: #3B82F6;
        color: white;
        font-weight: 600;
        margin: 0;
    }
    
    /* Categories container */
    .categories-container {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        gap: 15px;
        margin-top: 15px;
        flex-wrap: nowrap;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        width: 100% !important;
        font-family: 'Noto Kufi Arabic', sans-serif !important;
    }
    
    /* Button styling */
    .stButton > button {
        font-family: 'Noto Kufi Arabic', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 10px 25px !important;
        background-color: #2563EB !important;
        color: white !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        background-color: #1D4ED8 !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Add this at the beginning of main() to store results
    if 'results_df' not in st.session_state:
        st.session_state.results_df = None

    # Title section with description
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #1E3A8A; margin-bottom: 10px;'>🔍 مثال على تصنيف النصوص القانونية</h1>
        <p style='font-size: 1.2em; color: #4B5563;'>هذا المثال يوضح كيفية تصنيف النصوص القانونية إلى فئات مختلفة باستخدام الذكاء الاصطناعي</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Categories section
    categories_html = "".join([f"<span class='category-pill'>{cat}</span>" for cat in CATEGORIES])
    
    st.markdown(f"""
    <div class='css-card'>
        <h2>📑 الفئات المستخدمة في التصنيف</h2>
        <div class='categories-container'>
            {categories_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Data preview section
    st.markdown("""
    <div class='css-card'>
        <h2>📄 معاينة البيانات</h2>
        <p style='color: #4B5563;'>عينة من النصوص القانونية التي سيتم تصنيفها</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        df = pd.read_csv(EXAMPLE_FILE)
        st.dataframe(df.head(50), use_container_width=True)
    except Exception as e:
        st.error(f"خطأ في قراءة ملف المثال: {str(e)}")
        return
    
    # Modified process button section
    st.markdown("<div style='text-align: center; padding: 20px 0;'>", unsafe_allow_html=True)
    if st.button("🚀 تصنيف النصوص", use_container_width=True):
        try:
            with st.spinner("جاري معالجة النصوص..."):
                st.session_state.results_df = process_file(
                    open(EXAMPLE_FILE, 'rb'),
                    "CSV",
                    CATEGORIES,
                    BATCH_SIZE,
                    "Description"
                )
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {str(e)}")
            return
                
    # Move results display outside the button condition
    if st.session_state.results_df is not None:
        # Results section
        st.markdown("""
        <div class='css-card'>
            <h2>📊 نتائج التصنيف</h2>
            <p style='color: #4B5563;'>نتائج تصنيف النصوص القانونية مع التحليلات البيانية</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.dataframe(st.session_state.results_df, use_container_width=True)
        
        # Create and display dashboard
        fig = create_dashboard(st.session_state.results_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Modified download button with proper encoding
        csv = st.session_state.results_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 تحميل النتائج كملف CSV",
            data=csv,
            file_name="legal_classification_results.csv",
            mime="text/csv",
            use_container_width=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()