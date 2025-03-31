import streamlit as st

# Must be the first Streamlit command
st.set_page_config(page_title="Link2People", page_icon="🔍", layout="wide")

import os
import sys
import subprocess

# Install spaCy model
subprocess.run([f"{sys.executable}", "-m", "spacy", "download", "en_core_web_sm"])

import spacy
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Load spaCy
@st.cache_resource
def load_nlp():
    return spacy.load('en_core_web_sm')

nlp = load_nlp()

# Page title
st.title("Link2People - AI People Extractor")
st.markdown("Extract people information from any webpage")

# URL input
url = st.text_input("Enter webpage URL:", placeholder="https://example.com/article")

if st.button("Analyze"):
    if url:
        try:
            with st.spinner("Fetching webpage..."):
                # Get webpage content
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])])

            with st.spinner("Analyzing content..."):
                # Process with spaCy
                doc = nlp(text)
                
                # Extract information
                results = []
                seen_names = set()
                
                for ent in doc.ents:
                    if ent.label_ == 'PERSON' and ent.text not in seen_names:
                        context = text[max(0, ent.start_char-100):min(len(text), ent.end_char+100)]
                        
                        # Find title
                        title_pattern = r"(CEO|Chief|President|Director|Manager|Head|VP|Vice President|Founder)"
                        titles = re.findall(title_pattern, context, re.IGNORECASE)
                        
                        # Find company
                        company = None
                        for org in doc.ents:
                            if org.label_ == 'ORG' and abs(org.start - ent.start) < 10:
                                company = org.text
                                break
                        
                        results.append({
                            'Name': ent.text,
                            'Title': titles[0] if titles else 'Unknown',
                            'Company': company if company else 'Unknown',
                            'LinkedIn': f"https://www.linkedin.com/search/results/people/?keywords={ent.text.replace(' ', '%20')}"
                        })
                        seen_names.add(ent.text)

            if results:
                # Display results
                df = pd.DataFrame(results)
                st.success(f"Found {len(results)} people!")
                
                # Show metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("People Found", len(results))
                with col2:
                    st.metric("Companies Mentioned", len(df['Company'].unique()))
                
                # Display table
                st.dataframe(
                    df,
                    column_config={
                        "LinkedIn": st.column_config.LinkColumn("LinkedIn Profile")
                    },
                    hide_index=True
                )
                
                # Download options
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    "people_info.csv",
                    "text/csv"
                )
            else:
                st.warning("No people information found in the webpage")
                
        except Exception as e:
            st.error(f"Error analyzing webpage: {str(e)}")
    else:
        st.warning("Please enter a URL")
