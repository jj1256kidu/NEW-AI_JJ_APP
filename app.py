import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="Link2People - AI People Insights",
    page_icon="👥",
    layout="wide"
)

import os
import sys
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# Initialize Hugging Face (free) - you'll need to get a free token from huggingface.co
HUGGINGFACE_API_TOKEN = st.secrets.get("HUGGINGFACE_API_TOKEN", "")

def query_huggingface(text):
    """Query Hugging Face model for text analysis"""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": text, "parameters": {"candidate_labels": ["person", "organization", "location"]}}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error querying Hugging Face API: {str(e)}")
        return None

# Initialize spaCy
import spacy

@st.cache_resource
def load_model():
    try:
        return spacy.load("en_core_web_sm")
    except Exception as e:
        st.error(f"Error loading spaCy model: {str(e)}")
        return None

# Load NLP model
nlp = load_model()

if nlp is None:
    st.error("Failed to load NLP model. Please try refreshing the page.")
    st.stop()

def extract_people_with_enhanced_spacy(text, doc):
    """Enhanced people extraction using spaCy and rules"""
    people_insights = []
    seen_names = set()
    
    # Common titles to help identify people
    titles = r"(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|CEO|Chief|President|Director|Manager|Head|VP|Vice President|Founder|Co-founder|Executive|Leader|Chairman)"
    
    # Find sentences with potential people mentions
    sentences = [sent.text for sent in doc.sents]
    
    for sent in sentences:
        # Process each sentence
        sent_doc = nlp(sent)
        
        for ent in sent_doc.ents:
            if ent.label_ == 'PERSON' and ent.text.strip() and ent.text not in seen_names:
                name = ent.text.strip()
                if len(name.split()) < 2:  # Skip single word names
                    continue
                
                # Get surrounding context
                context = sent.strip()
                
                # Find title/designation
                title_match = re.search(titles, context, re.IGNORECASE)
                designation = title_match.group(0) if title_match else "Unknown"
                
                # Find organization
                company = "Unknown"
                for org in sent_doc.ents:
                    if org.label_ == 'ORG':
                        company = org.text
                        break
                
                # Extract quote if available
                quote_match = re.search(r'"([^"]*)"', context)
                quote = quote_match.group(1) if quote_match else "No direct quote found"
                
                people_insights.append({
                    "Name": name,
                    "Designation": designation,
                    "Company": company,
                    "Quote": quote,
                    "Context": context
                })
                seen_names.add(name)
    
    return people_insights

# Page title and description
st.title("Link2People - AI People Insights")
st.markdown("Extract detailed insights about people mentioned in any article")

# URL input
url = st.text_input("Enter article URL:", placeholder="https://example.com/article")

if st.button("Analyze"):
    if not url:
        st.warning("Please enter a URL to analyze.")
    else:
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Fetch webpage content
            with st.spinner("Fetching article content..."):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
                text = ' '.join([elem.get_text(strip=True) for elem in text_elements])

                if not text.strip():
                    st.warning("No readable content found in the article.")
                    st.stop()

            # Analyze content
            with st.spinner("Analyzing people mentions..."):
                doc = nlp(text[:1000000])  # Limit text length to prevent memory issues
                people_insights = extract_people_with_enhanced_spacy(text, doc)

            # Display results
            if people_insights:
                st.success(f"Found {len(people_insights)} people mentioned in the article!")
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("People Found", len(people_insights))
                with col2:
                    st.metric("With Quotes", len([p for p in people_insights if p["Quote"] != "No direct quote found"]))
                with col3:
                    st.metric("With Titles", len([p for p in people_insights if p["Designation"] != "Unknown"]))
                
                # Display detailed insights
                st.subheader("Detailed People Insights")
                df = pd.DataFrame(people_insights)
                
                # Display as interactive table
                st.dataframe(
                    df,
                    column_config={
                        "Name": st.column_config.TextColumn("Name", width="medium"),
                        "Designation": st.column_config.TextColumn("Designation", width="medium"),
                        "Company": st.column_config.TextColumn("Company", width="medium"),
                        "Quote": st.column_config.TextColumn("Quote", width="large"),
                        "Context": st.column_config.TextColumn("Context", width="large")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Export options
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="people_insights.csv",
                        mime="text/csv"
                    )
                with col2:
                    json_str = json.dumps(people_insights, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="people_insights.json",
                        mime="application/json"
                    )
            else:
                st.info("No people were found in the article.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching the article: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by AI")
