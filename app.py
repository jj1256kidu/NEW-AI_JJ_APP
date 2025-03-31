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
from collections import defaultdict

# Load spaCy model
@st.cache_resource
def load_model():
    try:
        return spacy.load("en_core_web_sm")
    except Exception as e:
        st.error(f"Error loading spaCy model: {str(e)}")
        return None

nlp = load_model()

if nlp is None:
    st.error("Failed to load NLP model. Please try refreshing the page.")
    st.stop()

# Enhanced patterns for better detection
DESIGNATION_PATTERNS = [
    r"(?:is|was|as)\s+(?:the\s+)?(?:new\s+)?([A-Z][a-z]+\s+)?({role})",
    r"({role})\s+(?:of|at|for)\s+([A-Z][a-zA-Z\s]+)",
    r"([A-Z][a-zA-Z\s]+)'s\s+({role})",
]

ROLES = [
    "CEO", "CTO", "CFO", "COO", "President", "Vice President", "VP", "Director",
    "Managing Director", "Manager", "Head", "Chief", "Leader", "Founder",
    "Co-founder", "Executive", "Engineer", "Developer", "Architect", "Lead",
    "Principal", "Partner", "Associate", "Analyst", "Consultant", "Advisor"
]

def extract_people(text):
    """Extract real person names using spaCy with enhanced filtering"""
    doc = nlp(text)
    people = set()
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Filter valid names (at least 2 words, no numbers)
            if len(name.split()) >= 2 and not re.search(r'\d', name):
                # Avoid common false positives
                if not any(fp in name.lower() for fp in [
                    'new delhi', 'mumbai', 'bangalore', 'supreme court',
                    'high court', 'united states', 'new york', 'san francisco'
                ]):
                    people.add(name)
    
    return sorted(people)

def find_quotes(name, text):
    """Find quotes by or about a person"""
    quotes = []
    
    # Direct quotes pattern
    direct_quote_pattern = rf'"{name}[^"]*"|{name}[^"]*"([^"]+)"'
    direct_quotes = re.finditer(direct_quote_pattern, text, re.IGNORECASE)
    
    for match in direct_quotes:
        quote = match.group(0).strip('"')
        if len(quote) > 10:  # Minimum quote length
            quotes.append(quote)
    
    # Indirect quotes pattern
    indirect_pattern = rf"{name}\s+(?:said|says|stated|mentioned|added|noted|explained|pointed out|highlighted|emphasized)\s+(?:that\s+)?([^.!?]+[.!?])"
    indirect_quotes = re.finditer(indirect_pattern, text, re.IGNORECASE)
    
    for match in indirect_quotes:
        quote = match.group(1).strip()
        if len(quote) > 10:
            quotes.append(quote)
    
    return quotes[0] if quotes else "No quote found"

def find_designation(name, text):
    """Find person's designation and company"""
    # Initialize result
    result = {
        "designation": "Unknown",
        "company": "Unknown"
    }
    
    # Create combined role pattern
    roles_pattern = "|".join(ROLES)
    
    # Search for designation patterns
    for pattern in DESIGNATION_PATTERNS:
        pattern = pattern.format(role=roles_pattern)
        context_pattern = rf"{name}.{{0,100}}{pattern}|{pattern}.{{0,100}}{name}"
        
        matches = re.finditer(context_pattern, text, re.IGNORECASE)
        for match in matches:
            context = match.group(0)
            
            # Extract role
            role_match = re.search(roles_pattern, context, re.IGNORECASE)
            if role_match:
                result["designation"] = role_match.group(0)
                
                # Try to find company
                company_pattern = r"(?:at|of|for)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)"
                company_match = re.search(company_pattern, context)
                if company_match:
                    result["company"] = company_match.group(1).strip()
                
                return result
    
    return result

def build_people_table(text):
    """Build comprehensive people insights table"""
    names = extract_people(text)
    data = []
    
    for name in names:
        # Get quotes
        quote = find_quotes(name, text)
        
        # Get designation and company
        role_info = find_designation(name, text)
        
        # Create LinkedIn search URL
        search_terms = [name]
        if role_info["company"] != "Unknown":
            search_terms.append(role_info["company"])
        if role_info["designation"] != "Unknown":
            search_terms.append(role_info["designation"])
        
        search_url = f"https://www.google.com/search?q=LinkedIn+" + "+".join(term.replace(" ", "+") for term in search_terms)
        
        # Build entry
        entry = {
            "Name": name,
            "Designation": role_info["designation"],
            "Company": role_info["company"],
            "Quote": quote,
            "LinkedIn": search_url
        }
        
        data.append(entry)
    
    return pd.DataFrame(data)

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
                df = build_people_table(text)

            # Display results
            if not df.empty:
                st.success(f"Found {len(df)} verified people mentions!")
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("People Found", len(df))
                with col2:
                    st.metric("With Quotes", len(df[df["Quote"] != "No quote found"]))
                with col3:
                    st.metric("With Roles", len(df[df["Designation"] != "Unknown"]))
                
                # Display detailed insights
                st.subheader("Detailed People Insights")
                
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
                    json_str = df.to_json(orient="records", indent=2)
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
