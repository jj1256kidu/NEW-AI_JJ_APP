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

def is_valid_name(name):
    """Check if a name looks like a real person name"""
    # Must have at least 2 words
    if len(name.split()) < 2:
        return False
    
    # Avoid common false positives
    false_positives = [
        'new delhi', 'navi mumbai', 'eid mubarak', 'digi yatra', 
        'artificial intelligence', 'machine learning', 'data science',
        'supreme court', 'high court', 'united states', 'new york',
        'san francisco', 'hong kong', 'new jersey', 'wall street'
    ]
    
    if name.lower() in false_positives:
        return False
    
    # Check for common location indicators
    location_indicators = ['street', 'road', 'avenue', 'boulevard', 'lane', 'drive', 'court', 'city', 'town']
    if any(indicator in name.lower() for indicator in location_indicators):
        return False
    
    return True

def extract_designation(context):
    """Extract designation from context"""
    designation_patterns = [
        r"(CEO|Chief\s+[A-Za-z]+\s+Officer)",
        r"(Managing Director|Director|MD)",
        r"(President|Vice President|VP)",
        r"(Head\s+of\s+[A-Za-z\s]+)",
        r"(Senior|Jr\.|Sr\.|Junior|Senior)\s+[A-Za-z]+",
        r"([A-Za-z]+\s+Manager)",
        r"(Founder|Co-founder|Executive|Leader|Chairman)",
        r"(Professor|Doctor|Dr\.|Prof\.)",
        r"(Engineer|Architect|Analyst|Consultant)",
        r"(Partner|Associate|Principal)"
    ]
    
    for pattern in designation_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(0)
    return "Unknown"

def clean_company_name(name):
    """Clean and validate company name"""
    if not name or name.lower() in ['unknown', 'none', 'na', 'n/a']:
        return "Unknown"
    
    # Remove common suffixes
    suffixes = [' ltd', ' limited', ' inc', ' llc', ' corp', ' corporation']
    cleaned = name
    for suffix in suffixes:
        cleaned = re.sub(f"{suffix}$", "", cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()

def extract_quote(text, name, window=200):
    """Extract quote around person mention"""
    quotes = []
    name_pos = text.lower().find(name.lower())
    
    if name_pos != -1:
        start = max(0, name_pos - window)
        end = min(len(text), name_pos + window)
        context = text[start:end]
        
        # Find quotes in context
        quote_matches = re.finditer(r'"([^"]+)"', context)
        for match in quote_matches:
            quotes.append(match.group(1))
    
    return quotes[0] if quotes else "No direct quote found"

def extract_people_insights(text):
    """Enhanced people extraction using spaCy and rules"""
    doc = nlp(text)
    people_insights = []
    seen_names = set()
    
    # Process each sentence for better context
    for sent in doc.sents:
        sent_doc = nlp(sent.text)
        
        for ent in sent_doc.ents:
            if ent.label_ == 'PERSON':
                name = ent.text.strip()
                
                # Validate name
                if not is_valid_name(name) or name in seen_names:
                    continue
                
                # Get context (+-200 characters)
                start_idx = max(0, ent.start_char - 200)
                end_idx = min(len(sent.text), ent.end_char + 200)
                context = sent.text[start_idx:end_idx]
                
                # Extract designation
                designation = extract_designation(context)
                
                # Find organization
                company = "Unknown"
                min_distance = float('inf')
                for org in sent_doc.ents:
                    if org.label_ == 'ORG':
                        distance = abs(org.start - ent.start)
                        if distance < min_distance and distance < 10:
                            min_distance = distance
                            company = clean_company_name(org.text)
                
                # Extract quote
                quote = extract_quote(text, name)
                
                # Create LinkedIn search URL
                name_query = name.replace(" ", "+")
                company_query = company.replace(" ", "+") if company != "Unknown" else ""
                linkedin_url = f"https://www.google.com/search?q=LinkedIn+{name_query}+{company_query}"
                
                # Add to insights
                people_insights.append({
                    "Name": name,
                    "Designation": designation,
                    "Company": company,
                    "Quote": quote,
                    "LinkedIn": linkedin_url
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
                people_insights = extract_people_insights(text)

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
