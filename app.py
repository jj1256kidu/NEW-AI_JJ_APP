import streamlit as st

# Must be the first Streamlit command
st.set_page_config(page_title="Link2People", page_icon="🔍", layout="wide")

try:
    import spacy
    import numpy as np
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    import re
except Exception as e:
    st.error(f"Error importing libraries: {str(e)}")

# Download spaCy model if not present
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Page title
st.title("Link2People - AI People Extractor")
st.markdown("Extract people information from any webpage")

# URL input
url = st.text_input("Enter webpage URL:", placeholder="https://example.com/article")

if st.button("Analyze"):
    if url:
        try:
            with st.spinner("Fetching webpage..."):
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])])

            with st.spinner("Analyzing content..."):
                doc = nlp(text)
                results = []
                seen_names = set()
                
                for ent in doc.ents:
                    if ent.label_ == 'PERSON' and ent.text not in seen_names:
                        context = text[max(0, ent.start_char-100):min(len(text), ent.end_char+100)]
                        
                        title_pattern = r"(CEO|Chief|President|Director|Manager|Head|VP|Vice President|Founder)"
                        titles = re.findall(title_pattern, context, re.IGNORECASE)
                        
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
                df = pd.DataFrame(results)
                st.success(f"Found {len(results)} people!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("People Found", len(results))
                with col2:
                    st.metric("Companies Mentioned", len(df['Company'].unique()))
                
                st.dataframe(
                    df,
                    column_config={
                        "LinkedIn": st.column_config.LinkColumn("LinkedIn Profile")
                    },
                    hide_index=True
                )
                
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
