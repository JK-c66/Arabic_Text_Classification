import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import re
import pandas as pd
from src.config.constants import CUSTOM_COLORS, STOP_WORDS

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
        for idx, category in enumerate(categories):
            category_texts = df[df['classification'] == category][text_column]
            if not category_texts.empty:
                top_words = get_top_words(category_texts)
                for word, count in top_words:
                    word_data.append({
                        'category': str(category),
                        'word': word,
                        'count': count,
                        'color': CUSTOM_COLORS[idx % len(CUSTOM_COLORS)]
                    })

    word_df = pd.DataFrame(word_data)
    
    if not word_df.empty:
        for idx, category in enumerate(categories):
            category_words = word_df[word_df['category'] == str(category)]
            if not category_words.empty:
                category_words = category_words.sort_values('count', ascending=True)
                fig.add_trace(
                    go.Bar(
                        name=str(category),
                        x=category_words['count'],
                        y=category_words['word'],
                        marker_color=category_words['color'].tolist(),
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