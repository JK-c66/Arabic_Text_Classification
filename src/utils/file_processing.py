import pandas as pd
import streamlit as st
from src.utils.privacy import mask_ids
from src.models.gemini_model import classify_texts_batch_gemini
import time

def process_file(file, file_type, categories, batch_size=10, column=None, separator=None):
    """Process either CSV or TXT file using batch classification"""
    try:
        # Reset masking notification state for new file processing
        if "masking_notified" in st.session_state:
            del st.session_state.masking_notified
            
        if file_type == "CSV":
            df = pd.read_csv(file)
            if column not in df.columns:
                st.error(f"Column '{column}' not found in CSV file")
                return None
            texts = df[column].tolist()
            # Apply privacy masking and check if any masking occurred
            masked_texts = [mask_ids(text) for text in texts]
            was_masked = any(orig != masked for orig, masked in zip(texts, masked_texts))
            
            if was_masked:
                df['original_text'] = texts
                df[column] = masked_texts
                texts = masked_texts
            else:
                texts = df[column].tolist()
        else:  
            content = file.getvalue().decode('utf-8')
            texts = [text.strip() for text in content.split(separator) if text.strip()]
            # Apply privacy masking and check if any masking occurred
            masked_texts = [mask_ids(text) for text in texts]
            was_masked = any(orig != masked for orig, masked in zip(texts, masked_texts))
            
            if was_masked:
                df = pd.DataFrame({
                    'original_text': texts,
                    'text': masked_texts
                })
                texts = masked_texts
            else:
                df = pd.DataFrame({'text': texts})
        
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
        
        df['classification'] = classifications
        return df, was_masked
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None, False 