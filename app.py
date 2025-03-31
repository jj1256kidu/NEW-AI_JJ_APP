import streamlit as st
import spacy
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Must be the first Streamlit command
st.set_page_config(
    page_title="Link2People - Professional Profile Extractor",
    page_icon="🧠",
    layout="wide"
)

@st.cache_resource
def load_nlp_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        st.info("Downloading language model...")
        spacy.cli.download("en_core_web_sm")
        return spacy.load("en_core_web_sm")

class ProfileExtractor:
    def __init__(self):
        self.nlp = load_nlp_model()
        self.invalid_terms = {
            'navratri', 'eid', 'diwali', 'asia', 'germany', 'mumbai', 'delhi',
            'digi yatra', 'free fire', 'wordle', 'top stocks', 'fire max'
        }

    def get_clean_text_from_url(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                verify=False
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
                element.decompose()
                
            # Remove ads and promotional content
            for element in soup.find_all(class_=re.compile(r'ad|promo|banner|sidebar')):
                element.decompose()
            
            # Extract text from paragraphs and headers
            text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article'])
            text = ' '.join(elem.get_text(strip=True) for elem in text_elements)
            
            # Clean text
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s\'-]', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Error fetching URL: {str(e)}")

    def is_valid_name(self, name):
        if not name or len(name) < 5:
            return False
            
        words = name.split()
        if len(words) < 2:
            return False
            
        caps = sum(1 for w in words if w and w[0].isupper())
        if caps < 2:
            return False
            
        if name.lower() in self.invalid_terms:
            return False
            
        if re.search(r'[^a-zA-Z\s\'-]', name):
            return False
            
        return True

    def extract_designation(self, text):
        patterns = [
            r"(?:is|was|as)\s+(?:the\s+)?(?:CEO|Chief|President|Director|Head|VP|Vice President|Founder)",
            r"(?:Senior|Global|Regional)?\s*(?:Director|Manager|Lead|Head|Chief|Officer)\s+(?:of|for|at)",
            r"(?:CEO|CTO|CIO|CFO|COO|CHRO|CMO)\s+(?:and|&)?\s*(?:Co-founder|Founder|Director|President)?",
            r"(?:Managing|Executive|General)\s+(?:Director|Partner|Manager|Principal)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        return ""

    def extract_company(self, text):
        patterns = [
            r"(?:at|of|for|with)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
            r"joined\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
            r"([A-Z][A-Za-z0-9\s&]+?)(?:'s|')\s+(?:CEO|Chief|President|Director)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                if company and company not in self.invalid_terms:
                    return company
        return ""

    def extract_profiles(self, text):
        doc = self.nlp(text)
        profiles = {}
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                
                if self.is_valid_name(name):
                    start = max(0, ent.start_char - 200)
                    end = min(len(text), ent.end_char + 200)
                    context = text[start:end]
                    
                    designation = self.extract_designation(context)
                    company = self.extract_company(context)
                    
                    if designation or company:
                        if name not in profiles:
                            profiles[name] = {
                                "Name": name,
                                "Designation": designation,
                                "Company": company,
                                "LinkedIn Search": ""
                            }
                        else:
                            if designation and not profiles[name]["Designation"]:
                                profiles[name]["Designation"] = designation
                            if company and not profiles[name]["Company"]:
                                profiles[name]["Company"] = company
        
        results = []
        for name, profile in profiles.items():
            search_terms = [name]
            if profile["Company"]:
                search_terms.append(profile["Company"])
            
            profile["LinkedIn Search"] = f"https://www.google.com/search?q=LinkedIn+" + "+".join(term.replace(" ", "+") for term in search_terms)
            results.append(profile)
        
        return results

def main():
    st.title("🧠 Link2People: Professional Profile Extractor")
    st.markdown("Extract professional profiles from any article URL")
    
    url = st.text_input("Enter article URL:", placeholder="https://example.com/article")
    
    if st.button("Extract Profiles"):
        if not url:
            st.warning("Please enter a URL to analyze.")
            return
            
        try:
            with st.spinner("Fetching and analyzing article..."):
                extractor = ProfileExtractor()
                
                text = extractor.get_clean_text_from_url(url)
                if not text:
                    st.warning("No readable content found in the article.")
                    return
                    
                profiles = extractor.extract_profiles(text)
                
                if profiles:
                    df = pd.DataFrame(profiles)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Profiles Found", len(df))
                    with col2:
                        complete = len(df[df["Designation"].astype(bool) & df["Company"].astype(bool)])
                        st.metric("Complete Profiles", complete)
                    
                    st.subheader("Extracted Profiles")
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
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download CSV",
                            csv,
                            "professional_profiles.csv",
                            "text/csv"
                        )
                    with col2:
                        json_str = df.to_json(orient="records", indent=2)
                        st.download_button(
                            "Download JSON",
                            json_str,
                            "professional_profiles.json",
                            "application/json"
                        )
                else:
                    st.info("No professional profiles found in the article.")
                    
        except Exception as e:
            st.error(f"Error processing article: {str(e)}")

    st.markdown("---")
    st.markdown("Made with ❤️ by AI")

if __name__ == "__main__":
    main()
