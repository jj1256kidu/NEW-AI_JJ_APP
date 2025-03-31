import streamlit as st

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Aurora AI People Extractor",
    page_icon="✨",
    layout="wide"
)

# Import required libraries
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import sys
import subprocess
import os

# Initialize spaCy with better error handling
def init_spacy():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        import spacy
        return spacy.load('en_core_web_sm')
    except Exception as e:
        st.error(f"Error initializing spaCy: {str(e)}")
        return None

# Load NLP model
@st.cache_resource
def load_nlp():
    return init_spacy()

# Rest of your Aurora CSS and functions...
# [Previous CSS code remains the same]

def extract_info(text, nlp):
    if nlp is None:
        return []
    
    try:
        doc = nlp(text)
        results = []
        seen_names = set()
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and ent.text not in seen_names:
                context = text[max(0, ent.start_char-100):min(len(text), ent.end_char+100)]
                
                title_pattern = r"(CEO|Chief\s+[A-Za-z]+\s+Officer|President|Director|Manager|Head|VP|Vice\s+President|Founder|Co-founder|Partner|Lead|Senior|Principal)"
                titles = re.findall(title_pattern, context, re.IGNORECASE)
                
                org = None
                for nearby_ent in doc.ents:
                    if nearby_ent.label_ == 'ORG' and abs(nearby_ent.start - ent.start) < 15:
                        org = nearby_ent.text
                        break
                
                confidence = 0.5
                if titles: confidence += 0.25
                if org: confidence += 0.25
                
                results.append({
                    'Name': ent.text,
                    'Title': titles[0] if titles else 'Unknown',
                    'Company': org if org else 'Unknown',
                    'Confidence': f"{confidence:.0%}",
                    'LinkedIn': f"https://www.linkedin.com/search/results/people/?keywords={ent.text.replace(' ', '%20')}"
                })
                seen_names.add(ent.text)
        
        return results
    except Exception as e:
        st.error(f"Error in extraction: {str(e)}")
        return []

# Main app
def main():
    st.markdown(aurora_css, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">Aurora AI People Extractor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Powered by Advanced AI to Extract People Information from Any Webpage</p>', unsafe_allow_html=True)
    
    # Load NLP model
    nlp = load_nlp()
    if nlp is None:
        st.error("Could not initialize AI model. Please try again.")
        return
    
    # URL input
    url = st.text_input("Enter webpage URL", placeholder="https://example.com/article")
    
    if st.button("Analyze with AI"):
        if url:
            try:
                with st.spinner("Analyzing webpage..."):
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
                    }
                    response = requests.get(url, headers=headers)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])])
                    
                    results = extract_info(text, nlp)
                    
                    if results:
                        df = pd.DataFrame(results)
                        
                        st.success(f"Found {len(results)} people mentions!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("People Found", len(results))
                        with col2:
                            st.metric("Companies Mentioned", len(df['Company'].unique()))
                        with col3:
                            st.metric("Average Confidence", f"{df['Confidence'].str.rstrip('%').astype(float).mean():.0f}%")
                        
                        st.dataframe(
                            df.style.background_gradient(subset=['Confidence'], cmap='Blues'),
                            column_config={
                                "LinkedIn": st.column_config.LinkColumn("LinkedIn Profile")
                            },
                            hide_index=True
                        )
                        
                        # Export options
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "Download CSV",
                                csv,
                                "people_info.csv",
                                "text/csv",
                                key='download-csv'
                            )
                        with col2:
                            excel_file = df.to_excel(index=False)
                            st.download_button(
                                "Download Excel",
                                excel_file,
                                "people_info.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key='download-excel'
                            )
                    else:
                        st.warning("No people information found in the webpage")
                        
            except Exception as e:
                st.error(f"Error analyzing webpage: {str(e)}")
        else:
            st.warning("Please enter a URL")

if __name__ == "__main__":
    main()
