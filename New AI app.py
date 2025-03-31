# ADD THESE LINES AT THE VERY TOP OF YOUR app.py
import streamlit as st
import spacy
import subprocess
import sys

def install_spacy_model():
    try:
        spacy.load('en_core_web_sm')
    except OSError:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])

# Call this before your main code
install_spacy_model()

# ============ YOUR EXISTING CODE STARTS HERE ============
# Rest of your imports
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from datetime import datetime

# Aurora Theme CSS
aurora_css = """
<style>
    /* Your existing CSS */
</style>
"""

# Rest of your code...

# app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import spacy
import pandas as pd
import re
from datetime import datetime
import time

# Custom CSS for Aurora theme
aurora_css = """
<style>
    /* Aurora Theme */
    .stApp {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
    }
    
    .main-title {
        background: linear-gradient(120deg, #89f7fe 0%, #66a6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: 700;
        margin-bottom: 1em;
        text-align: center;
    }
    
    .subtitle {
        color: #a8e6cf;
        font-size: 1.2em;
        text-align: center;
        margin-bottom: 2em;
    }
    
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid #66a6ff;
        border-radius: 10px;
    }
    
    .stButton > button {
        background: linear-gradient(120deg, #89f7fe 0%, #66a6ff 100%);
        color: #0F2027;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.5em 2em;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 166, 255, 0.4);
    }
    
    .results-container {
        background: rgba(255, 255, 255, 0.1);
        padding: 2em;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        margin: 2em 0;
    }
    
    .metrics-container {
        display: flex;
        justify-content: space-around;
        margin: 2em 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1em;
        border-radius: 10px;
        text-align: center;
    }
    
    .dataframe {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    .stProgress > div > div > div > div {
        background-color: #66a6ff;
    }
    
    .download-btn {
        background: linear-gradient(120deg, #a8e6cf 0%, #66a6ff 100%);
        color: #0F2027;
        padding: 0.5em 2em;
        border-radius: 10px;
        text-decoration: none;
        display: inline-block;
        margin-top: 1em;
    }
</style>
"""

# Load spaCy model
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

def extract_info(text, nlp):
    doc = nlp(text)
    results = []
    seen_names = set()
    
    for ent in doc.ents:
        if ent.label_ == 'PERSON' and ent.text not in seen_names:
            context = text[max(0, ent.start_char-100):min(len(text), ent.end_char+100)]
            
            # Enhanced title pattern
            title_pattern = r"(CEO|Chief\s+[A-Za-z]+\s+Officer|President|Director|Manager|Head|VP|Vice\s+President|Founder|Co-founder|Partner|Lead|Senior|Principal)"
            titles = re.findall(title_pattern, context, re.IGNORECASE)
            
            # Look for organization
            org = None
            for nearby_ent in doc.ents:
                if nearby_ent.label_ == 'ORG' and abs(nearby_ent.start - ent.start) < 15:
                    org = nearby_ent.text
                    break
            
            # Calculate confidence score
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

def main():
    st.set_page_config(
        page_title="Aurora AI People Extractor",
        page_icon="✨",
        layout="wide"
    )
    
    # Apply custom CSS
    st.markdown(aurora_css, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-title">Aurora AI People Extractor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Powered by Advanced AI to Extract People Information from Any Webpage</p>', unsafe_allow_html=True)
    
    # Load AI model
    nlp = load_model()
    
    # Input section
    url = st.text_input("Enter webpage URL", placeholder="https://example.com/article")
    
    if st.button("Analyze with AI"):
        if url:
            try:
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Fetch webpage
                status_text.text("Fetching webpage content...")
                progress_bar.progress(20)
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
                }
                response = requests.get(url, headers=headers)
                
                # Step 2: Parse content
                status_text.text("Parsing content...")
                progress_bar.progress(40)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])])
                
                # Step 3: AI Analysis
                status_text.text("Performing AI analysis...")
                progress_bar.progress(60)
                
                results = extract_info(text, nlp)
                
                # Step 4: Process results
                status_text.text("Processing results...")
                progress_bar.progress(80)
                
                if results:
                    df = pd.DataFrame(results)
                    
                    # Step 5: Display results
                    status_text.text("Analysis complete!")
                    progress_bar.progress(100)
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("People Found", len(results))
                    with col2:
                        st.metric("Companies Mentioned", len(df['Company'].unique()))
                    with col3:
                        st.metric("Average Confidence", f"{df['Confidence'].str.rstrip('%').astype(float).mean():.0f}%")
                    
                    # Display results table
                    st.markdown('<div class="results-container">', unsafe_allow_html=True)
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
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("No people information found in the webpage")
                
            except Exception as e:
                st.error(f"Error analyzing webpage: {str(e)}")
        else:
            st.warning("Please enter a URL")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #a8e6cf; padding: 2em;'>
        <p>Built with ❄️ Aurora AI Technology</p>
        <p>Last updated: {}}</p>
    </div>
    """.format(datetime.now().strftime("%B %Y")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
