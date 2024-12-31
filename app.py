import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import plotly.express as px
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots   
from collections import Counter
import re

# Constants and Configurations
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DEFAULT_CATEGORIES = ["إيجابي", "سلبي", "محايد"]
DEFAULT_BATCH_SIZE = 20
DEFAULT_SEPARATOR = "\n"
CUSTOM_COLORS = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f', '#9b59b6', '#1abc9c']
STOP_WORDS = {'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'تم', 'فيه'}
SEPARATOR_OPTIONS = [
    ("\n", "سطر جديد (↵)"),
    (",", "فاصلة (,)"),
    (".", "نقطة (.)"),
    (";", "فاصلة منقوطة (;)"),
    ("custom", "فاصل مخصص ➕")
]

# Load environment variables
load_dotenv()

# Model Management
@st.cache_resource
def get_gemini_model():
    """Lazy load Gemini model"""
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-1.5-flash')

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

# File Processing
def process_file(file, file_type, categories, batch_size=10, column=None, separator=None):
    """Process either CSV or TXT file using batch classification"""
    try:
        if file_type == "CSV":
            df = pd.read_csv(file)
            if column not in df.columns:
                st.error(f"Column '{column}' not found in CSV file")
                return None
            texts = df[column].tolist()
        else:  
            content = file.getvalue().decode('utf-8')
            texts = [text.strip() for text in content.split(separator) if text.strip()]
        
        total_items = len(texts)
        classifications = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        start_time = time.time()
        
        for i in range(0, total_items, batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_classifications = classify_texts_batch_gemini(batch_texts, categories)
            classifications.extend(batch_classifications)
            
            progress = (i + batch_size) / total_items
            progress_bar.progress(min(progress, 1.0))
            
            elapsed_time = time.time() - start_time
            estimated_total_time = elapsed_time / progress if progress > 0 else 0
            remaining_time = estimated_total_time - elapsed_time
            status_text.text(f"تمت معالجة {min(i + batch_size, total_items)}/{total_items} نص. الوقت المتبقي: {remaining_time:.1f} ثانية")
        
        if file_type == "CSV":
            df['classification'] = classifications
        else:
            df = pd.DataFrame({'text': texts, 'classification': classifications})
        
        return df
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

# Visualization Functions
def get_top_words(texts, n=5, min_length=2):
    """Get top words from texts"""
    words = ' '.join(texts)
    words = re.findall(r'[\u0600-\u06FF]+', words)
    words = [w for w in words if len(w) >= min_length and w not in STOP_WORDS]
    return Counter(words).most_common(n)

def create_dashboard(df):
    """Create a comprehensive dashboard of classification results"""
    text_column = 'text' if 'text' in df.columns else df.columns[0]
    
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            'توزيع التصنيفات',
            'متوسط طول النص حسب الفئة',
            'الكلمات الأكثر شيوعاً'
        ),
        specs=[[{"type": "pie"}, {"type": "bar"}, {"type": "bar"}]],
        horizontal_spacing=0.15
    )

    # Pie Chart
    counts = df['classification'].value_counts()
    percentages = (counts / len(df) * 100).round(1)
    labels = [f"{cat}<br>({pct}%)" for cat, pct in zip(counts.index, percentages)]
    
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=counts.values,
            hole=0.4,
            marker=dict(colors=CUSTOM_COLORS),
            textinfo='label',
            textposition='outside',
            textfont=dict(size=14, family="Noto Kufi Arabic"),
            direction='clockwise',
            hovertemplate="<b>%{label}</b><br>العدد: %{value}<extra></extra>"
        ),
        row=1, col=1
    )

    # Text Length Bar Chart
    avg_lengths = df.groupby('classification')[text_column].apply(lambda x: x.str.len().mean()).round(1)
    
    fig.add_trace(
        go.Bar(
            x=avg_lengths.index,
            y=avg_lengths.values,
            marker_color=CUSTOM_COLORS[:len(avg_lengths)],
            text=avg_lengths.values,
            textposition='auto',
            textfont=dict(size=14, family="Noto Kufi Arabic"),
            hovertemplate="<b>%{x}</b><br>متوسط الطول: %{y:.1f} حرف<extra></extra>",
            showlegend=False
        ),
        row=1, col=2
    )

    # Word Frequency Chart
    word_data = []
    categories = df['classification'].unique()
    
    if len(categories) > 0:
        for category in categories:
            category_texts = df[df['classification'] == category][text_column]
            if not category_texts.empty:
                top_words = get_top_words(category_texts)
                for word, count in top_words:
                    word_data.append({
                        'category': str(category),  # Ensure category is string
                        'word': word,
                        'count': count
                    })

    word_df = pd.DataFrame(word_data)
    
    if not word_df.empty:
        for idx, category in enumerate(categories):
            category_words = word_df[word_df['category'] == str(category)]  # Match string category
            if not category_words.empty:
                category_words = category_words.sort_values('count', ascending=True)
                fig.add_trace(
                    go.Bar(
                        name=str(category),
                        x=category_words['count'],
                        y=category_words['word'],
                        marker_color=CUSTOM_COLORS[idx % len(CUSTOM_COLORS)],  # Cycle through colors
                        textfont=dict(size=14, family="Noto Kufi Arabic"),
                        hovertemplate="<b>%{y}</b><br>التكرار: %{x}<br>الفئة: " + str(category) + "<extra></extra>",
                        orientation='h',
                        showlegend=False
                    ),
                    row=1, col=3
                )

    # Update layout
    fig.update_layout(
        height=800,
        width=1600,
        showlegend=False,
        title=dict(
            text="لوحة تحليل تصنيف النصوص",
            x=0.5,
            font=dict(size=28, family="Noto Kufi Arabic")
        ),
        paper_bgcolor='white',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=150, l=80, r=80, b=80),
        font=dict(family="Noto Kufi Arabic", size=14)
    )

    # Update axes styling
    fig.update_xaxes(title_font=dict(size=16, family="Noto Kufi Arabic"), tickfont=dict(size=14, family="Noto Kufi Arabic"))
    fig.update_yaxes(title_font=dict(size=16, family="Noto Kufi Arabic"), tickfont=dict(size=14, family="Noto Kufi Arabic"))

    # Update subplot titles
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=18, family="Noto Kufi Arabic")

    return fig

# UI Components
def setup_page_config():
    """Configure page settings and styling"""
    st.set_page_config(
        page_title="مصنف النصوص",
        page_icon="🤖",
        layout="centered"
    )
    
    # Load external CSS
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    setup_page_config()
    
    st.title("🤖 مصنف النصوص العربية")
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
                    st.dataframe(df_preview.head(100), use_container_width=True)
                    column = st.selectbox("اختر العمود المراد تصنيفه:", df_preview.columns)
                else:
                    st.error("ملف CSV فارغ أو لا يحتوي على أعمدة.")
                    return
            else:
                content = uploaded_file.getvalue().decode('utf-8')
                if content.strip():
                    st.text_area("محتوى الملف:", value=content, height=200)
                    
                    # Separator selection with preview
                    st.write("**اختر الفاصل:**")
                    separator_choice = st.selectbox(
                        "نوع الفاصل",
                        options=[opt[0] for opt in SEPARATOR_OPTIONS],
                        format_func=lambda x: next((opt[1] for opt in SEPARATOR_OPTIONS if opt[0] == x), x),
                        label_visibility="collapsed"
                    )
                    
                    if separator_choice == "custom":
                        custom_separator = st.text_input(
                            "أدخل الفاصل المخصص:",
                            value="",
                            help="أدخل الرمز أو النص الذي يفصل بين النصوص",
                            label_visibility="collapsed"
                        )
                        if custom_separator:
                            separator = custom_separator
                            st.markdown(f"""
                            <div class='separator-preview'>
                                الفاصل المختار: "{separator}"
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        separator = separator_choice
                        display_separator = "↵" if separator == "\n" else separator
                        st.markdown(
                            "<div class='separator-preview'>"
                            f"الفاصل المختار: \"{display_separator}\""
                            "</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.error("ملف TXT فارغ.")
                    return
            
            # Categories and Processing
            st.header("2️⃣ الفئات والمعالجة")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                use_default = st.checkbox("استخدام الفئات الافتراضية", value=True)
                categories = DEFAULT_CATEGORIES if use_default else [
                    cat.strip() for cat in st.text_area(
                        "أدخل الفئات (فئة واحدة في كل سطر)",
                        value="\n".join(DEFAULT_CATEGORIES)
                    ).split("\n") if cat.strip()
                ]
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

            if st.button("🚀 بدء التصنيف", use_container_width=True):
                uploaded_file.seek(0)
                df = process_file(uploaded_file, file_type, categories, batch_size, column, separator)
                if df is not None:
                    st.header("📊 النتائج")
                    st.dataframe(df, use_container_width=True)
                    
                    fig = create_dashboard(df)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 تحميل النتائج (CSV)",
                        data=csv,
                        file_name="classification_results.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")

    if 'gemini_model' in st.session_state:
        del st.session_state['gemini_model']

if __name__ == "__main__":
    main() 