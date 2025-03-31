import streamlit as st
import spacy
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3
import subprocess
import os

# Check if setup.sh exists and is executable
if os.path.exists('setup.sh'):
    try:
        os.chmod('setup.sh', 0o755)
    except Exception as e:
        st.warning(f"Note: Could not set execute permissions on setup.sh: {str(e)}")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Must be the first Streamlit command
st.set_page_config(
    page_title="NewsNex - From News to Next Opportunities",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for styling with new background
st.markdown("""
<style>
    /* Modern Gradient Background */
    .stApp {
        background: linear-gradient(
            135deg,
            #1A1F38 0%,
            #20294E 50%,
            #254153 100%
        );
        background-attachment: fixed;
        position: relative;
        overflow: hidden;
    }
    
    /* Animated particles effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 30%, rgba(0, 163, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(143, 0, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(0, 255, 209, 0.1) 0%, transparent 50%);
        animation: aurora 20s ease infinite;
        z-index: 0;
    }
    
    @keyframes aurora {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.2); }
        100% { transform: rotate(360deg) scale(1); }
    }
    
    /* Ensure content appears above background */
    .stApp > * {
        position: relative;
        z-index: 1;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: #00FFD1;
        margin-bottom: 0;
        text-shadow: 0 0 10px rgba(0, 255, 209, 0.5);
    }
    
    .tagline {
        font-size: 1.4rem;
        color: #00A3FF;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 8px rgba(0, 163, 255, 0.5);
    }
    
    .sub-tagline {
        font-size: 1.2rem;
        color: #8F00FF;
        font-style: italic;
        margin-bottom: 1rem;
        text-shadow: 0 0 8px rgba(143, 0, 255, 0.5);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #00FFD1 0%, #00A3FF 100%);
        color: #1A1F38;
        width: 100%;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00A3FF 0%, #8F00FF 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 255, 209, 0.3);
    }
    
    .metric-card {
        background: rgba(26, 31, 56, 0.7);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 255, 209, 0.1);
        border: 1px solid rgba(0, 255, 209, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 255, 209, 0.2);
    }
    
    .metric-title {
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        color: #00FFD1;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: white;
        text-shadow: 0 0 10px rgba(0, 255, 209, 0.5);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(26, 31, 56, 0.7);
        padding: 10px;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: rgba(32, 41, 78, 0.7);
        border-radius: 8px;
        color: #00FFD1;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(37, 65, 83, 0.9);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00FFD1 0%, #00A3FF 100%) !important;
        color: #1A1F38 !important;
    }
    
    /* DataFrame styling */
    .dataframe {
        background: rgba(26, 31, 56, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        border: 1px solid rgba(0, 255, 209, 0.1);
    }
    
    /* Input fields styling */
    .stTextInput > div > div {
        background: rgba(26, 31, 56, 0.7);
        border: 1px solid rgba(0, 255, 209, 0.3);
        border-radius: 8px;
    }
    
    .stTextArea > div > div {
        background: rgba(26, 31, 56, 0.7);
        border: 1px solid rgba(0, 255, 209, 0.3);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)
@st.cache_resource(show_spinner=False)
def load_nlp_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        st.info("📚 Downloading language model...")
        spacy.cli.download("en_core_web_sm")
        return spacy.load("en_core_web_sm")

class ProfileExtractor:
    def __init__(self):
        self.nlp = load_nlp_model()
        # Extended invalid terms
        self.invalid_terms = {
            'navratri', 'eid', 'diwali', 'christmas', 'new year',
            'asia', 'germany', 'mumbai', 'delhi', 'bangalore', 'india', 'china',
            'digi yatra', 'free fire', 'wordle', 'android', 'ios',
            'top stocks', 'fire max', 'breaking news', 'latest news',
            'read more', 'share market', 'stock market', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        }
        
        self.name_prefixes = {
            'mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'er', 'eng',
            'advocate', 'justice', 'honorable', 'shri', 'smt'
        }
        
        self.professional_contexts = {
            'ceo', 'chief', 'president', 'director', 'head', 'vp', 'vice president',
            'founder', 'co-founder', 'chairman', 'managing director', 'md', 'cto',
            'engineer', 'architect', 'leader', 'executive', 'manager', 'principal',
            'partner', 'associate', 'advisor', 'consultant', 'strategist', 'analyst',
            'lead', 'head', 'specialist', 'expert', 'professional'
        }

    def get_clean_text_from_url(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'aside', 'nav', 'footer', 'iframe', 'header']):
                element.decompose()
            
            # Get text content
            text = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
            
            # Clean text
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error fetching URL: {str(e)}")

    def is_valid_name(self, name):
        if not name or len(name) < 2 or len(name) > 40:
            return False
        
        name_lower = name.lower()
        
        if any(term in name_lower for term in self.invalid_terms):
            return False
        
        has_valid_context = any(prefix in name_lower for prefix in self.name_prefixes) or \
                          any(context in name_lower for context in self.professional_contexts)
        
        words = name.split()
        if len(words) < 2:
            return False
        
        if not all(word[0].isupper() for word in words if word):
            return False
        
        if re.search(r'[0-9@#$%^&*()_+=\[\]{};:"|<>?]', name):
            return False
        
        return True

    def extract_designation(self, text):
        designation_patterns = [
            r'(?i)(Chief\s+[A-Za-z]+\s+Officer|CEO|CTO|CFO|COO|CIO)',
            r'(?i)(Managing\s+Director|Director|MD)',
            r'(?i)(Vice\s+President|VP|President)',
            r'(?i)(Founder|Co-founder|Chairman)',
            r'(?i)(Head\s+of\s+[A-Za-z\s]+)',
            r'(?i)(Senior\s+[A-Za-z]+\s+Manager|Manager)',
            r'(?i)(Lead\s+[A-Za-z]+|Team\s+Lead)',
        ]
        
        designations = []
        for pattern in designation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                designation = match.group().strip()
                if designation and len(designation) > 2:
                    designations.append(designation)
        
        return list(set(designations))

    def extract_company(self, text):
        company_patterns = [
            r'(?i)(?:at|with|for|in)\s+([A-Z][A-Za-z0-9\s&]+(?:Inc\.?|Ltd\.?|Limited|Corporation|Corp\.?|Company|Co\.?|Technologies|Solutions|Group|Holdings|Ventures|Capital|Partners|LLP)?)',
            r'(?i)([A-Z][A-Za-z0-9\s&]+(?:Inc\.?|Ltd\.?|Limited|Corporation|Corp\.?|Company|Co\.?|Technologies|Solutions|Group|Holdings|Ventures|Capital|Partners|LLP))',
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                company = match.group(1).strip() if len(match.groups()) > 0 else match.group().strip()
                if company and len(company) > 2:
                    companies.append(company)
        
        return list(set(companies))

    def extract_profiles(self, text):
        doc = self.nlp(text)
        profiles = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                
                if self.is_valid_name(name):
                    start = max(0, ent.start_char - 100)
                    end = min(len(text), ent.end_char + 100)
                    context = text[start:end]
                    
                    designations = self.extract_designation(context)
                    companies = self.extract_company(context)
                    
                    linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}"
                    
                    profile = {
                        "name": name,
                        "designations": designations,
                        "companies": companies,
                        "linkedin_search": linkedin_url
                    }
                    
                    profiles.append(profile)
        
        return profiles

def main():
    st.markdown('<h1 class="main-title">NewsNex</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">From News to Next Opportunities</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-tagline">Extract professional profiles from news articles</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📰 URL Input", "📝 Text Input"])

    extractor = ProfileExtractor()
    
    with tab1:
        url = st.text_input("Enter news article URL:")
        if st.button("Extract from URL", key="url_button"):
            if url:
                try:
                    with st.spinner("🔍 Analyzing article..."):
                        text = extractor.get_clean_text_from_url(url)
                        profiles = extractor.extract_profiles(text)
                        display_results(extractor, text, profiles)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
            else:
                st.warning("⚠️ Please enter a URL")

    with tab2:
        text_input = st.text_area("Paste article text:", height=200)
        if st.button("Extract from Text", key="text_button"):
            if text_input:
                with st.spinner("🔍 Processing text..."):
                    profiles = extractor.extract_profiles(text_input)
                    display_results(extractor, text_input, profiles)
            else:
                st.warning("⚠️ Please enter some text")

def display_results(extractor, text, profiles):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📊 Total Prospects</div>
                <div class="metric-value">{len(profiles)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    complete_profiles = sum(1 for p in profiles if p['designations'] and p['companies'])
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">✨ Complete Profiles</div>
                <div class="metric-value">{complete_profiles}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    unique_companies = len(set(company for p in profiles for company in p['companies']))
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🏢 Unique Companies</div>
                <div class="metric-value">{unique_companies}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if profiles:
        df = pd.json_normalize(profiles)
        
        st.markdown("### 📋 Extracted Profiles")
        st.dataframe(df)
        
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="profiles.csv",
                mime="text/csv"
            )
        with col2:
            json_str = json.dumps(profiles, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name="profiles.json",
                mime="application/json"
            )
    else:
        st.info("🔍 No profiles found in the provided content.")

if __name__ == "__main__":
    main()
