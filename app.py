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
from typing import List, Dict, Optional

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

# Strict filtering rules
INVALID_TERMS = {
    # Apps and tools
    'garena', 'digi yatra', 'crossword', 'wordle', 'instagram', 'facebook',
    # Locations
    'navi mumbai', 'new delhi', 'bangalore', 'mumbai', 'kolkata',
    # Events and festivals
    'eid mubarak', 'surya grahan', 'diwali', 'christmas',
    # Ad terms
    'lifestyle', 'fire', 'deals', 'captivating', 'trending', 'viral',
    # Entertainment terms
    'box office', 'movie', 'film', 'song', 'album', 'show'
}

class PersonExtractor:
    def __init__(self, text: str):
        self.text = text
        self.doc = nlp(text)
        
    def is_valid_name(self, name: str) -> bool:
        """Strictly validate person names"""
        # Must have at least 2 words
        words = name.split()
        if len(words) < 2:
            return False
            
        # Each word must be capitalized
        if not all(word[0].isupper() for word in words):
            return False
            
        # No invalid terms
        if name.lower() in INVALID_TERMS:
            return False
            
        # No numbers or special characters
        if re.search(r'[^a-zA-Z\s\'-]', name):
            return False
            
        # No entertainment keywords
        entertainment_terms = ['actor', 'actress', 'star', 'celebrity', 'singer']
        if any(term in name.lower() for term in entertainment_terms):
            return False
            
        return True
        
    def extract_quote(self, name: str) -> Optional[str]:
        """Extract clean quotes"""
        patterns = [
            rf'"{name}[^"]*"|{name}[^"]*"([^"]+)"',
            rf"{name}\s+(?:said|says|stated)\s+(?:that\s+)?([^.!?]+[.!?])",
            rf'According to\s+{name},?\s+([^.!?]+[.!?])'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, self.text, re.IGNORECASE)
            for match in matches:
                quote = match.group(1) if len(match.groups()) > 0 else match.group(0)
                quote = quote.strip('"').strip()
                
                # Validate quote
                if (20 < len(quote) < 200 and  # Reasonable length
                    not any(term in quote.lower() for term in INVALID_TERMS)):
                    return quote
        return None
        
    def extract_role_info(self, name: str) -> Dict[str, Optional[str]]:
        """Extract designation and company"""
        result = {"designation": None, "company": None}
        
        # Find context around name
        name_idx = self.text.find(name)
        if name_idx != -1:
            context_start = max(0, name_idx - 100)
            context_end = min(len(self.text), name_idx + 100)
            context = self.text[context_start:context_end]
            
            # Find designation
            designation_pattern = r"(?:is|was|as)\s+(?:the\s+)?(?:new\s+)?([A-Z][a-z]+\s+)?(?:CEO|Chief|President|Director|Manager|Head|VP|Vice President|Founder|Executive)"
            designation_match = re.search(designation_pattern, context, re.IGNORECASE)
            if designation_match:
                result["designation"] = designation_match.group(0).strip()
            
            # Find company
            company_pattern = r"(?:at|of|for)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)"
            company_match = re.search(company_pattern, context)
            if company_match:
                company = company_match.group(1).strip()
                if company not in INVALID_TERMS and len(company) > 2:
                    result["company"] = company
                    
        return result
        
    def extract_people(self) -> List[Dict]:
        """Extract clean person information"""
        people_info = {}
        
        # First pass: collect all mentions
        for ent in self.doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                
                if self.is_valid_name(name):
                    if name not in people_info:
                        people_info[name] = {
                            "Name": name,
                            "Designation": None,
                            "Company": None,
                            "Quote": None,
                            "LinkedIn Search": None
                        }
                    
                    # Get role information
                    role_info = self.extract_role_info(name)
                    if role_info["designation"]:
                        people_info[name]["Designation"] = role_info["designation"]
                    if role_info["company"]:
                        people_info[name]["Company"] = role_info["company"]
                    
                    # Get quote
                    quote = self.extract_quote(name)
                    if quote:
                        people_info[name]["Quote"] = quote
        
        # Second pass: clean and format
        clean_results = []
        for name, info in people_info.items():
            # Only include entries with at least designation or quote
            if info["Designation"] or info["Quote"]:
                # Create LinkedIn search URL
                search_terms = [name]
                if info["Company"]:
                    search_terms.append(info["Company"])
                
                info["LinkedIn Search"] = f"https://www.google.com/search?q=LinkedIn+" + "+".join(term.replace(" ", "+") for term in search_terms)
                
                clean_results.append(info)
        
        return clean_results

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
                
                # Extract main content
                text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
                text = ' '.join([elem.get_text(strip=True) for elem in text_elements])

                if not text.strip():
                    st.warning("No readable content found in the article.")
                    st.stop()

            # Process content
            with st.spinner("Extracting verified people mentions..."):
                extractor = PersonExtractor(text)
                results = extractor.extract_people()

            # Display results
            if results:
                st.success(f"Found {len(results)} verified people mentions!")
                
                # Convert to DataFrame for display
                df = pd.DataFrame(results)
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("People Found", len(df))
                with col2:
                    st.metric("With Quotes", len(df[df["Quote"].notna()]))
                with col3:
                    st.metric("With Roles", len(df[df["Designation"].notna()]))
                
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
                        "LinkedIn Search": st.column_config.LinkColumn("LinkedIn Search")
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
