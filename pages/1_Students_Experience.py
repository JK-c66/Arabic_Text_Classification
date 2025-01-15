import streamlit as st
import pandas as pd
import os
import time
import json
from io import StringIO
from app import process_file
from src.models.gemini_model import get_gemini_model
from src.config.constants import EXAMPLES_DIR, BASE_DIR

# Configure page
st.set_page_config(
    page_title="محلل تجربة الطلاب",
    page_icon="👨‍🎓",
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
        border-radius: 15px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        border: 1px solid #E5E7EB;
    }
    
    /* Analysis result styling */
    .result-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Progress circle */
    .progress-circle {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: conic-gradient(from 0deg, #3B82F6 var(--progress), #EEF2FF var(--progress));
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
    }
    
    .progress-circle:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 8px rgba(59, 130, 246, 0.2);
    }
    
    .progress-circle::before {
        content: '';
        position: absolute;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: white;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .progress-value {
        position: relative;
        z-index: 1;
        font-size: 16px;
        font-weight: 600;
        color: #1E3A8A;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 2px;
    }
    
    .progress-value::after {
        content: '%';
        font-size: 12px;
        opacity: 0.8;
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

def analyze_student_experience(text):
    """Analyze student experience text using Gemini"""
    start_time = time.time()
    model = get_gemini_model()
    
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }
    
    prompt = f"""
قم بتحليل نص تجربة الطالب التالي وتقديم النتائج بتنسيق JSON محدد.
يجب أن يكون التنسيق بالضبط كما يلي:
{{
    "categories": [
        {{
            "name": "اسم الفئة",
            "percentage": النسبة_المئوية,
            "explanation": "شرح تفصيلي للفئة"
        }}
    ]
}}

ملاحظات مهمة:
- النسبة_المئوية يجب أن تكون رقماً فقط بدون علامة %
- يجب أن يكون مجموع النسب المئوية 100
- الشرح يجب أن يكون موجزاً وواضحاً
- يجب أن تكون جميع النصوص باللغة العربية

النص للتحليل:
{text}
"""
    
    try:
        response = model.generate_content([prompt], generation_config=generation_config)
        if time.time() - start_time > 30:
            raise Exception("انتهت مهلة الاستجابة. يرجى المحاولة مرة أخرى.")
            
        response_text = response.text.strip()
        
        # Validate response format
        if not response_text or len(response_text) < 10:
            raise Exception("استجابة غير صالحة من النموذج")
            
        # Try to clean the response if it contains markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        # Basic validation of Arabic content
        if not any('\u0600' <= c <= '\u06FF' for c in response_text):
            raise Exception("لم يتم العثور على نص عربي في الاستجابة")
            
        # Parse the response as JSON
        result = json.loads(response_text)
        
        # Validate JSON structure
        if 'categories' not in result or not isinstance(result['categories'], list):
            raise Exception("تنسيق JSON غير صالح")
            
        # Validate categories
        total_percentage = 0
        for category in result['categories']:
            if not all(key in category for key in ['name', 'percentage', 'explanation']):
                raise Exception("بيانات الفئة غير مكتملة")
            total_percentage += category['percentage']
        
        if not (95 <= total_percentage <= 105):  # Allow small deviation
            raise Exception("مجموع النسب المئوية غير صحيح")
        
        # Calculate time taken
        time_taken = time.time() - start_time
        result["analysis_time"] = round(time_taken, 2)
        
        return result
        
    except json.JSONDecodeError as e:
        st.error("فشل تحليل استجابة النموذج. يرجى المحاولة مرة أخرى.")
        raise Exception(f"فشل تحليل استجابة النموذج كـ JSON: {str(e)}")
    except Exception as e:
        st.error("حدث خطأ أثناء التحليل. يرجى المحاولة مرة أخرى.")
        raise Exception(f"فشل التحليل: {str(e)}")

def display_analysis_results(results):
    """Display analysis results in a nice format"""
    # Display time taken if available
    if "analysis_time" in results:
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <p style='color: #4B5563;'>⏱️ زمن التحليل: {results['analysis_time']} ثانية</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sort categories by percentage in descending order
    sorted_categories = sorted(results['categories'], key=lambda x: x['percentage'], reverse=True)
    
    # Display header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2>📊 نتائج التحليل</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for each pair of results
    for i in range(0, len(sorted_categories), 2):
        col1, col2 = st.columns(2)
        
        # First column
        with col1:
            category = sorted_categories[i]
            name = category['name'].replace('**', '').strip()
            percentage = category['percentage']
            explanation = category['explanation'].replace('**', '').strip()
            
            st.markdown(f"""
            <div class='result-card' style='background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; height: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                    <h3 style='margin: 0; color: #1E3A8A;'>{name}</h3>
                    <div class='progress-circle' style='--progress: {percentage * 3.6}deg'>
                        <span class='progress-value'>{percentage}%</span>
                    </div>
                </div>
                <p style='margin: 0; color: #4B5563; font-size: 0.95em;'>{explanation}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Second column (if available)
        if i + 1 < len(sorted_categories):
            with col2:
                category = sorted_categories[i + 1]
                name = category['name'].replace('**', '').strip()
                percentage = category['percentage']
                explanation = category['explanation'].replace('**', '').strip()
                
                st.markdown(f"""
                <div class='result-card' style='background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; height: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                        <h3 style='margin: 0; color: #1E3A8A;'>{name}</h3>
                        <div class='progress-circle' style='--progress: {percentage * 3.6}deg'>
                            <span class='progress-value'>{percentage}%</span>
                        </div>
                    </div>
                    <p style='margin: 0; color: #4B5563; font-size: 0.95em;'>{explanation}</p>
                </div>
                """, unsafe_allow_html=True)

def main():
    # Add this at the beginning of main() to store results
    if 'results_df' not in st.session_state:
        st.session_state.results_df = None

    # Title section with description
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #1E3A8A; margin-bottom: 10px;'>👨‍🎓 محلل تجربة الطلاب</h1>
        <p style='font-size: 1.2em; color: #4B5563;'>تحليل تجارب الطلاب وتصنيفها تلقائياً مع تحديد نسب الجوانب المختلفة</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    csv_tab, text_tab = st.tabs(["📁 تحليل ملف CSV", "✍️ تحليل نص مباشر"])
    
    # CSV Analysis Tab
    with csv_tab:
        uploaded_file = st.file_uploader(
            label="اختر ملف CSV",
            type=['csv']
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Add column selection
                if not df.empty and len(df.columns) > 0:
                    column = st.selectbox("اختر العمود المراد تحليله:", df.columns)
                    
                    if column:
                        # Display file preview
                        st.subheader("📄 معاينة الملف")
                        st.dataframe(df[[column]].head(100), use_container_width=True)
                        
                        # Display file information
                        st.markdown(f"""
                        <div style='background-color: #f1f5f9; padding: 0.7rem; border-radius: 8px; margin: 0.5rem 0;'>
                            <div style='display: flex; align-items: center; justify-content: space-between;'>
                                <h3 style='margin: 0; color: #1E3A8A;'>📊 معلومات الملف</h3>
                                <span>عدد الصفوف: {len(df):,} | عدد الأعمدة: {len(df.columns)}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Processing settings
                        st.write("**⚙️ إعدادات المعالجة**")
                        batch_size = st.number_input(
                            "حجم الدفعة",
                            min_value=1,
                            max_value=100,
                            value=10,
                            help="عدد النصوص التي سيتم معالجتها في كل طلب"
                        )

                        if st.button("🚀 بدء التحليل", use_container_width=True):
                            try:
                                with st.spinner("جاري معالجة النصوص..."):
                                    # Convert DataFrame to file-like object
                                    from io import StringIO
                                    csv_buffer = StringIO()
                                    df.to_csv(csv_buffer, index=False)
                                    csv_buffer.seek(0)
                                    
                                    # Process the file
                                    results_tuple = process_file(
                                        csv_buffer,
                                        "CSV",
                                        categories=[
                                            "رضا الطالب بالتخصص",
                                            "عدم الرضا عن اساتذة الجامعة",
                                            "المشاكل الأكاديمية",
                                            "الخدمات الطلابية",
                                            "البيئة التعليمية"
                                        ],
                                        batch_size=batch_size,
                                        column=column
                                    )
                                    
                                    if results_tuple:
                                        results, was_masked = results_tuple
                                        if results is not None:
                                            st.success("تم تحليل الملف بنجاح!")
                                            st.session_state.results_df = results
                                        else:
                                            st.error("فشل في تحليل الملف")
                                    else:
                                        st.error("لم يتم استلام نتائج من المعالجة")
                            except Exception as e:
                                st.error(f"حدث خطأ أثناء معالجة الملف: {str(e)}")
                                return

                        # Display results if available
                        if st.session_state.results_df is not None:
                            st.header("📊 النتائج")
                            st.dataframe(st.session_state.results_df, use_container_width=True)
                            
                            # CSV export with proper BOM for Excel compatibility
                            csv_data = st.session_state.results_df.to_csv(index=False, encoding='utf-8-sig', quoting=1)
                            st.download_button(
                                label="📥 تحميل النتائج (CSV)",
                                data=csv_data.encode('utf-8-sig'),
                                file_name="student_experience_results.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                else:
                    st.error("ملف CSV فارغ أو لا يحتوي على أعمدة.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء تحليل الملف: {str(e)}")
    
    # Text Analysis Tab
    with text_tab:
        user_text = st.text_area(
            label="أدخل نص تجربة الطالب",
            height=200,
            key="student_experience_input"
        )
        
        # Analysis button
        if st.button("🔍 تحليل النص", use_container_width=True):
            if not user_text:
                st.warning("الرجاء إدخال نص للتحليل")
                return
                
            try:
                with st.spinner("جاري التحليل..."):
                    # Process the text using analyze_student_experience
                    results = analyze_student_experience(user_text)
                    
                    if results:
                        st.success("تم تحليل النص بنجاح!")
                        
                        # Display results
                        display_analysis_results(results)
                    else:
                        st.error("فشل في تحليل النص")
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحليل: {str(e)}")

if __name__ == "__main__":
    main() 