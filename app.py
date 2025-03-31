import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="Link2People - AI People Insights",
    page_icon="👥",
    layout="wide"
)

import spacy
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json

# Initialize spaCy
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

# Page title and description
st.title("Link2People - AI People Insights")
st.markdown("Extract detailed insights about people mentioned in any article")

def extract_quote_around_name(text, name, window=100):
    """Extract a relevant quote around the person's name"""
    name_pos = text.find(name)
    if name_pos == -1:
        return None
    
    start = max(0, name_pos - window)
    end = min(len(text), name_pos + window)
    context = text[start:end]
    
    quote_match = re.search(r'"([^"]*)"', context)
    if quote_match:
        return quote_match.group(1)
    return None

def extract_context(text, name, window=150):
    """Extract relevant context around the person's mention"""
    name_pos = text.find(name)
    if name_pos == -1:
        return None
    
    start = max(0, name_pos - window)
    end = min(len(text), name_pos + window)
    context = text[start:end].strip()
    return re.sub(r'\s+', ' ', context)

def get_designation(doc, ent):
    """Extract designation from surrounding text"""
    title_patterns = [
        r"(CEO|Chief\s+[A-Za-z]+\s+Officer|President|Director|Manager|Head\s+of\s+[A-Za-z]+|VP|Vice\s+President|Founder|Co-founder|Executive|Leader|Chairman|Managing Director)",
        r"(Professor|Doctor|Dr\.|Prof\.|Senior|Junior|Principal|Assistant|Associate)\s+[A-Za-z]+",
        r"[A-Za-z]+\s+(Manager|Director|Lead|Head|Chief|Officer)"
    ]
    
    start_idx = max(0, ent.start_char - 100)
    end_idx = min(len(doc.text), ent.end_char + 100)
    context = doc.text[start_idx:end_idx]
    
    for pattern in title_patterns:
        matches = re.finditer(pattern, context, re.IGNORECASE)
        for match in matches:
            if abs(match.start() - (ent.start_char - start_idx)) < 50:
                return match.group(0)
    
    return "Unknown"

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
                people_insights = []
                seen_names = set()
                
                for ent in doc.ents:
                    if ent.label_ == 'PERSON' and ent.text.strip() and ent.text not in seen_names:
                        name = ent.text.strip()
                        if len(name.split()) < 2:  # Skip single word names
                            continue
                        
                        designation = get_designation(doc, ent)
                        
                        company = "Unknown"
                        for org in doc.ents:
                            if org.label_ == 'ORG' and abs(org.start - ent.start) < 10:
                                company = org.text
                                break
                        
                        quote = extract_quote_around_name(text, name)
                        context = extract_context(text, name)
                        
                        people_insights.append({
                            "Name": name,
                            "Designation": designation,
                            "Company": company,
                            "Quote": quote if quote else "No direct quote found",
                            "Context": context if context else "No additional context found"
                        })
                        seen_names.add(name)

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
