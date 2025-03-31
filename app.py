import streamlit as st

# Must be the first Streamlit command
st.set_page_config(page_title="Link2People", page_icon="🔍", layout="wide")

import os
import sys
import subprocess
import importlib

# Initialize spaCy with better error handling
@st.cache_resource
def initialize_spacy():
    try:
        import spacy
        try:
            # Try to load the model directly
            return spacy.load('en_core_web_sm')
        except OSError:
            # If model isn't found, install it using pip
            st.info("Installing spaCy model...")
            subprocess.check_call([
                sys.executable, 
                "-m", 
                "pip", 
                "install", 
                "--no-deps",
                "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"
            ])
            # Reload spacy after installing the model
            importlib.reload(spacy)
            return spacy.load('en_core_web_sm')
    except Exception as e:
        st.error(f"Error initializing spaCy: {str(e)}")
        return None

# Import remaining packages
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# Load NLP model
nlp = initialize_spacy()

if nlp is None:
    st.error("Failed to load NLP model. Please try refreshing the page.")
    st.stop()

# Page title and description
st.title("Link2People - AI People Extractor")
st.markdown("Extract people information from any webpage")

# Custom CSS for better styling
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stButton > button {
        border-radius: 10px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# URL input
url = st.text_input("Enter webpage URL:", placeholder="https://example.com/article")

if st.button("Analyze"):
    if not url:
        st.warning("Please enter a URL to analyze.")
    else:
        try:
            # Fetch webpage content
            with st.spinner("Fetching webpage content..."):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()  # Raise an exception for bad status codes
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text from relevant HTML elements
                text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
                text = ' '.join([elem.get_text(strip=True) for elem in text_elements])

            # Analyze content
            with st.spinner("Analyzing content..."):
                doc = nlp(text)
                results = []
                seen_names = set()
                
                # Enhanced title patterns
                title_pattern = r"(CEO|Chief\s+[A-Za-z]+\s+Officer|President|Director|Manager|Head\s+of\s+[A-Za-z]+|VP|Vice\s+President|Founder|Co-founder|Executive|Leader)"
                
                # Process entities
                for ent in doc.ents:
                    if ent.label_ == 'PERSON' and ent.text.strip() and ent.text not in seen_names:
                        # Get surrounding context
                        start_idx = max(0, ent.start_char - 150)
                        end_idx = min(len(text), ent.end_char + 150)
                        context = text[start_idx:end_idx]
                        
                        # Extract title
                        titles = re.findall(title_pattern, context, re.IGNORECASE)
                        title = titles[0] if titles else 'Unknown'
                        
                        # Find closest organization
                        company = 'Unknown'
                        min_distance = float('inf')
                        for org in doc.ents:
                            if org.label_ == 'ORG':
                                distance = abs(org.start - ent.start)
                                if distance < min_distance and distance < 10:
                                    min_distance = distance
                                    company = org.text
                        
                        # Create LinkedIn search URL
                        linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={ent.text.replace(' ', '%20')}"
                        if company != 'Unknown':
                            linkedin_url += f"%20{company.replace(' ', '%20')}"
                        
                        results.append({
                            'Name': ent.text,
                            'Title': title,
                            'Company': company,
                            'LinkedIn': linkedin_url
                        })
                        seen_names.add(ent.text)

            # Display results
            if results:
                df = pd.DataFrame(results)
                
                # Success message and metrics
                st.success(f"Successfully analyzed the webpage!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("People Found", len(results))
                with col2:
                    st.metric("Companies Mentioned", len(df['Company'].unique()))
                with col3:
                    st.metric("Known Titles", len(df[df['Title'] != 'Unknown']))
                
                # Display results table
                st.dataframe(
                    df,
                    column_config={
                        "LinkedIn": st.column_config.LinkColumn("LinkedIn Profile")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Download options
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="extracted_people.csv",
                    mime="text/csv"
                )
            else:
                st.info("No people were found in the provided webpage.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching the webpage: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by AI")
