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

# Initialize OpenAI - with error handling
try:
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except ImportError:
    st.error("OpenAI package not found. Falling back to spaCy only mode.")
    client = None
except Exception as e:
    st.error(f"Error initializing OpenAI: {str(e)}")
    client = None

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

# System prompt for GPT-4
SYSTEM_PROMPT = """You are an intelligent assistant designed to analyze news articles. When provided with raw extracted content from a news URL, your task is to identify all relevant human individuals mentioned in the article and generate structured insights about each of them.

Instructions:
1. Parse the given text carefully and identify **real human individuals** only. Avoid generic words, company names, or common nouns.
2. For each individual, extract the following details:
   - Full Name
   - Designation or Role
   - Company or Organization (if mentioned)
   - Relevant Quote (if any)
   - Context or Summary of their mention in the article (1-2 lines)

3. If multiple people are mentioned, list each of them in a structured format.
4. DO NOT include irrelevant names, fictional characters, or repeated names unless they are mentioned in different contexts.
5. Make sure each entry is **accurate, concise, and context-aware**.

Respond in JSON format suitable for processing:
[
  {
    "Name": "Full Name",
    "Designation": "Role/Title",
    "Company": "Organization",
    "Quote": "Direct quote if available",
    "Context": "Brief summary of mention"
  }
]
"""

def extract_people_with_gpt4(text):
    """Extract people information using GPT-4"""
    if client is None:
        return None
        
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Parse the response
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        st.error(f"Error processing with GPT-4: {str(e)}")
        return None

def extract_people_with_spacy(text, doc):
    """Fallback extraction using spaCy"""
    people_insights = []
    seen_names = set()
    
    for ent in doc.ents:
        if ent.label_ == 'PERSON' and ent.text.strip() and ent.text not in seen_names:
            name = ent.text.strip()
            if len(name.split()) < 2:
                continue
            
            # Get surrounding context
            start_idx = max(0, ent.start_char - 150)
            end_idx = min(len(text), ent.end_char + 150)
            context = text[start_idx:end_idx].strip()
            
            # Find organization
            company = "Unknown"
            for org in doc.ents:
                if org.label_ == 'ORG' and abs(org.start - ent.start) < 10:
                    company = org.text
                    break
            
            # Extract quote if available
            quote_match = re.search(r'"([^"]*)"', context)
            quote = quote_match.group(1) if quote_match else "No direct quote found"
            
            people_insights.append({
                "Name": name,
                "Designation": "Unknown",
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
                # Try GPT-4 first
                people_insights = extract_people_with_gpt4(text)
                
                # Fallback to spaCy if GPT-4 fails
                if people_insights is None:
                    st.info("Using fallback extraction method...")
                    doc = nlp(text[:1000000])
                    people_insights = extract_people_with_spacy(text, doc)

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
