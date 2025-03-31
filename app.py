import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="Link2People - Professional Insights",
    page_icon="👥",
    layout="wide"
)

import spacy
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

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

class ProfessionalProfileExtractor:
    def __init__(self):
        # Invalid terms for filtering
        self.invalid_terms = {
            # Events and festivals
            'navratri', 'eid mubarak', 'diwali', 'christmas', 'new year',
            # Locations
            'asia', 'germany', 'navi mumbai', 'new delhi', 'bangalore',
            # Apps and platforms
            'digi yatra', 'garena', 'free fire', 'wordle', 'crossword',
            # Common false positives
            'top stocks', 'fire max', 'latest news', 'breaking news'
        }
        
        # Valid professional contexts
        self.professional_contexts = {
            'ceo', 'chief', 'president', 'director', 'head', 'vp', 'vice president',
            'founder', 'co-founder', 'chairman', 'managing director', 'md', 'cto',
            'engineer', 'architect', 'leader', 'executive', 'manager', 'principal',
            'partner', 'associate', 'advisor', 'consultant', 'strategist', 'analyst'
        }
        
        # Professional departments/areas
        self.professional_areas = {
            'technology', 'engineering', 'operations', 'strategy', 'innovation',
            'research', 'development', 'product', 'digital', 'data', 'ai', 'ml',
            'cloud', 'security', 'infrastructure', 'solutions', 'enterprise'
        }

    def is_valid_professional_name(self, name):
        """Validate if a name meets professional criteria"""
        # Basic validation
        if not name or len(name) < 5:
            return False
            
        words = name.split()
        
        # Must have at least 2 capitalized words
        if len(words) < 2:
            return False
            
        capitalized_words = sum(1 for word in words if word and word[0].isupper())
        if capitalized_words < 2:
            return False
            
        # Check for invalid terms
        if name.lower() in self.invalid_terms:
            return False
            
        # No numbers or special characters (except hyphen and apostrophe)
        if re.search(r'[^a-zA-Z\s\'-]', name):
            return False
            
        return True

    def extract_designation(self, context):
        """Extract valid professional designation"""
        # Common designation patterns
        patterns = [
            r"(?:is|was|as)\s+(?:the\s+)?(?:new\s+)?([A-Z][a-z]+\s+)?(?:CEO|Chief|President|Director|Head|VP|Vice President|Founder|Executive)",
            r"(?:Senior|Global|Regional)?\s*(?:Director|Manager|Lead|Head|Chief|Officer)\s+(?:of|for|at)\s+[A-Z][A-Za-z\s]+",
            r"(?:CEO|CTO|CIO|CFO|COO|CHRO|CMO)\s+(?:and|&)?\s*(?:Co-founder|Founder|Director|President)?",
            r"(?:Managing|Executive|General)\s+(?:Director|Partner|Manager|Principal)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                designation = match.group(0).strip()
                # Validate designation has both role and area/department
                words = designation.lower().split()
                if (any(word in self.professional_contexts for word in words) and
                    any(word in self.professional_areas for word in words)):
                    return designation
        return ""

    def extract_company(self, context):
        """Extract valid company name"""
        patterns = [
            r"(?:at|of|for|with)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
            r"joined\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
            r"([A-Z][A-Za-z0-9\s&]+?)(?:'s|')\s+(?:CEO|Chief|President|Director)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context)
            if match:
                company = match.group(1).strip()
                # Validate company name
                if (company and 
                    company not in self.invalid_terms and
                    len(company) > 2 and
                    company[0].isupper()):
                    return company
        return ""

    def extract_profiles(self, text):
        """Extract professional profiles from text"""
        doc = nlp(text)
        profiles = {}
        
        # First pass: collect all mentions
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                
                if self.is_valid_professional_name(name):
                    # Get context around name
                    start_idx = max(0, ent.start_char - 200)
                    end_idx = min(len(text), ent.end_char + 200)
                    context = text[start_idx:end_idx]
                    
                    designation = self.extract_designation(context)
                    company = self.extract_company(context)
                    
                    # Only include if we found professional context
                    if designation or company:
                        if name not in profiles:
                            profiles[name] = {
                                "Name": name,
                                "Designation": designation,
                                "Company": company,
                                "LinkedIn Search": ""
                            }
                        else:
                            # Update existing profile if new info is found
                            if designation and not profiles[name]["Designation"]:
                                profiles[name]["Designation"] = designation
                            if company and not profiles[name]["Company"]:
                                profiles[name]["Company"] = company
        
        # Second pass: clean and format
        results = []
        for name, profile in profiles.items():
            # Create LinkedIn search URL
            search_terms = [name]
            if profile["Company"]:
                search_terms.append(profile["Company"])
            
            profile["LinkedIn Search"] = f"https://www.google.com/search?q=LinkedIn+" + "+".join(term.replace(" ", "+") for term in search_terms)
            results.append(profile)
        
        return results

# Page title and description
st.title("Link2People - Professional Insights")
st.markdown("Extract professional profiles from any article")

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
            with st.spinner("Extracting professional profiles..."):
                extractor = ProfessionalProfileExtractor()
                results = extractor.extract_profiles(text)

            # Display results
            if results:
                st.success(f"Found {len(results)} professional profiles!")
                
                # Convert to DataFrame for display
                df = pd.DataFrame(results)
                
                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Profiles Found", len(df))
                with col2:
                    st.metric("Complete Profiles", 
                             len(df[df["Designation"].astype(bool) & df["Company"].astype(bool)]))
                
                # Display detailed insights
                st.subheader("Professional Profiles")
                
                # Display as interactive table
                st.dataframe(
                    df,
                    column_config={
                        "Name": st.column_config.TextColumn("Name", width="medium"),
                        "Designation": st.column_config.TextColumn("Designation", width="medium"),
                        "Company": st.column_config.TextColumn("Company", width="medium"),
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
                        file_name="professional_profiles.csv",
                        mime="text/csv"
                    )
                with col2:
                    json_str = df.to_json(orient="records", indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="professional_profiles.json",
                        mime="application/json"
                    )
            else:
                st.info("No professional profiles were found in the article.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching the article: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by AI")
