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
    # Simplified client initialization
    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )
except ImportError:
    st.error("OpenAI package not found. Falling back to spaCy only mode.")
    client = None
except Exception as e:
    st.error(f"Error initializing OpenAI: {str(e)}")
    client = None

# Initialize spaCy for backup
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

# Enhanced system prompt
SYSTEM_PROMPT = """You are an intelligent assistant integrated into a news article analytics tool. Your job is to extract *only real human beings* mentioned in the article and generate clean, structured profiles from the text.

Follow these strict rules:

1. Only include **actual people** — do NOT include:
   - City names (e.g., Navi Mumbai)
   - Festivals/events (e.g., Eid Mubarak)
   - Brands, apps, or tools (e.g., Digi Yatra, Wordle, Crossword)
   - Fictional names or phrases
   - Generic words that are not names

2. For each valid person, extract:
   - Full Name (ensure it looks like a real name)
   - Designation (skip if not clearly mentioned)
   - Company/Organization (skip if unclear)
   - Quote (if any)
   - Create a Google search link to find them on LinkedIn

3. Avoid duplications. If the same person appears multiple times, include them only once — with the most complete and recent information.

4. Ignore promotional or ad text — do NOT include names found in "sponsored", "ads", or promotional sections of the article.

5. If you're unsure if a name is a person or not, do not include it.

Respond in JSON format:
[
  {
    "Name": "Full Name",
    "Designation": "Role/Title",
    "Company": "Organization",
    "Quote": "Direct quote if available",
    "LinkedIn": "https://www.google.com/search?q=LinkedIn+[Name]+[Company]"
  }
]
"""

def filter_insights(people_insights):
    """Apply additional filtering to remove low-quality entries"""
    filtered = []
    for person in people_insights:
        # Check if name has at least 2 words
        name_parts = person["Name"].split()
        if len(name_parts) < 2:
            continue
            
        # Skip entries with unknown company AND designation
        if person["Company"] == "Unknown" and person["Designation"] == "Unknown":
            continue
            
        # Create LinkedIn search URL if missing
        if "LinkedIn" not in person or not person["LinkedIn"]:
            name_query = person["Name"].replace(" ", "+")
            company_query = person["Company"].replace(" ", "+") if person["Company"] != "Unknown" else ""
            person["LinkedIn"] = f"https://www.google.com/search?q=LinkedIn+{name_query}+{company_query}"
            
        filtered.append(person)
    
    return filtered

def extract_people_with_gpt(text):
    """Extract people information using GPT-3.5"""
    if client is None:
        return None
        
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        # Parse the response
        content = response.choices[0].message.content
        people_insights = json.loads(content)
        
        # Apply additional filtering
        return filter_insights(people_insights)
    except Exception as e:
        st.error(f"Error processing with GPT-3.5: {str(e)}")
        return None

def extract_people_with_spacy(text, doc):
    """Fallback extraction using spaCy with enhanced filtering"""
    people_insights = []
    seen_names = set()
    
    for ent in doc.ents:
        if ent.label_ == 'PERSON' and ent.text.strip() and ent.text not in seen_names:
            name = ent.text.strip()
            if len(name.split()) < 2:  # Skip single word names
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
            
            # Create LinkedIn search URL
            name_query = name.replace(" ", "+")
            company_query = company.replace(" ", "+") if company != "Unknown" else ""
            linkedin_url = f"https://www.google.com/search?q=LinkedIn+{name_query}+{company_query}"
            
            people_insights.append({
                "Name": name,
                "Designation": "Unknown",
                "Company": company,
                "Quote": quote,
                "LinkedIn": linkedin_url
            })
            seen_names.add(name)
    
    return filter_insights(people_insights)

# Page title and description
st.title("Link2People - AI People Insights")
st.markdown("Extract detailed insights about people mentioned in any article")

# Add OpenAI API key status indicator
if "OPENAI_API_KEY" in st.secrets:
    st.success("OpenAI API key found! Using GPT-3.5 for enhanced extraction.")
else:
    st.warning("OpenAI API key not found. Using basic extraction mode.")

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
                
                # Remove ads and promotional content
                for ad in soup.find_all(class_=re.compile(r'ad|sponsored|promotion', re.IGNORECASE)):
                    ad.decompose()
                
                text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
                text = ' '.join([elem.get_text(strip=True) for elem in text_elements])

                if not text.strip():
                    st.warning("No readable content found in the article.")
                    st.stop()

            # Analyze content
            with st.spinner("Analyzing people mentions..."):
                # Try GPT-3.5 first
                people_insights = extract_people_with_gpt(text)
                
                # Fallback to spaCy if GPT-3.5 fails
                if people_insights is None:
                    st.info("Using fallback extraction method...")
                    doc = nlp(text[:1000000])
                    people_insights = extract_people_with_spacy(text, doc)

            # Display results
            if people_insights:
                st.success(f"Found {len(people_insights)} verified people mentions!")
                
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
                        "LinkedIn": st.column_config.LinkColumn("LinkedIn Search")
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
                st.info("No verified people were found in the article.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching the article: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by AI")
