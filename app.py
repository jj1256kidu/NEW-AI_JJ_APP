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
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Page configuration
st.set_page_config(
    page_title="NewsNex – From News to Next Opportunities",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with professional styling
st.markdown("""
<style>
    /* Modern Background with Dynamic Gradient */
    .stApp {
        background: linear-gradient(
            135deg,
            #0a192f 0%,
            #112240 50%,
            #1a365d 100%
        );
        background-attachment: fixed;
        position: relative;
        overflow-x: hidden;
    }
    
    /* Animated Gradient Overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 30%, rgba(64, 196, 255, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(128, 0, 255, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(0, 255, 209, 0.08) 0%, transparent 50%);
        animation: aurora 20s ease infinite;
        z-index: 0;
    }
    
    @keyframes aurora {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.2); }
        100% { transform: rotate(360deg) scale(1); }
    }
    
    /* Content Layer */
    .stApp > * {
        position: relative;
        z-index: 1;
    }
    
    /* Branding and Typography */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #40c4ff 0%, #00ffd1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 2rem 0 1rem;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.02em;
    }
    
    .tagline {
        font-size: 1.8rem;
        color: #40c4ff;
        text-align: center;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        text-shadow: 0 0 20px rgba(64, 196, 255, 0.3);
    }
    
    .sub-tagline {
        font-size: 1.4rem;
        color: #00ffd1;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
        font-style: italic;
        font-weight: 500;
        text-shadow: 0 0 20px rgba(0, 255, 209, 0.3);
    }
    
    /* Modern Card Design */
    .metric-card {
        background: rgba(17, 34, 64, 0.6);
        backdrop-filter: blur(12px);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid rgba(64, 196, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 255, 209, 0.1);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(64, 196, 255, 0.3);
        box-shadow: 0 12px 40px rgba(0, 255, 209, 0.2);
    }
    
    .metric-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #40c4ff;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        text-shadow: 0 0 20px rgba(64, 196, 255, 0.3);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #40c4ff 0%, #00ffd1 100%);
        color: #0a192f;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(64, 196, 255, 0.3);
    }
    
    /* Tab Design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(17, 34, 64, 0.6);
        padding: 1rem;
        border-radius: 12px;
        backdrop-filter: blur(12px);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(10, 25, 47, 0.7);
        border-radius: 8px;
        color: #40c4ff;
        padding: 0.75rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(26, 54, 93, 0.9);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #40c4ff 0%, #00ffd1 100%) !important;
        color: #0a192f !important;
        font-weight: 600;
    }
    
    /* Input Fields */
    .stTextInput > div > div,
    .stTextArea > div > div {
        background: rgba(17, 34, 64, 0.6);
        border: 1px solid rgba(64, 196, 255, 0.2);
        border-radius: 8px;
        color: white;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div:focus-within,
    .stTextArea > div > div:focus-within {
        border-color: #40c4ff;
        box-shadow: 0 0 15px rgba(64, 196, 255, 0.2);
    }
    
    /* DataFrame Styling */
    .dataframe {
        background: rgba(17, 34, 64, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        border: 1px solid rgba(64, 196, 255, 0.1);
        color: white;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem;
        background: rgba(10, 25, 47, 0.9);
        backdrop-filter: blur(12px);
        border-top: 1px solid rgba(64, 196, 255, 0.1);
        text-align: center;
        color: #40c4ff;
        font-size: 1.1rem;
        z-index: 1000;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: #40c4ff #40c4ff transparent transparent;
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
        self.session = requests.Session()
        
        # Common name prefixes
        self.name_prefixes = {
            'mr', 'mrs', 'ms', 'dr', 'prof', 'shri', 'smt', 'sir',
            'justice', 'adv', 'advocate', 'ca', 'er', 'eng'
        }
        
        # Standardized designations mapping
        self.designation_mapping = {
            # C-Suite
            'chief executive officer': 'CEO',
            'ceo': 'CEO',
            'chief technology officer': 'CTO',
            'cto': 'CTO',
            'chief financial officer': 'CFO',
            'cfo': 'CFO',
            'chief operating officer': 'COO',
            'coo': 'COO',
            'chief information officer': 'CIO',
            'cio': 'CIO',
            'chief marketing officer': 'CMO',
            'cmo': 'CMO',
            'chief product officer': 'CPO',
            'cpo': 'CPO',
            
            # Directors
            'managing director': 'Managing Director',
            'md': 'Managing Director',
            'director': 'Director',
            'board director': 'Board Director',
            'executive director': 'Executive Director',
            
            # Presidents
            'president': 'President',
            'vice president': 'Vice President',
            'vp': 'Vice President',
            'senior vice president': 'Senior Vice President',
            'svp': 'Senior Vice President',
            'executive vice president': 'Executive Vice President',
            'evp': 'Executive Vice President',
            
            # Founders
            'founder': 'Founder',
            'co-founder': 'Co-Founder',
            'cofounder': 'Co-Founder',
            'founding partner': 'Founding Partner',
            
            # Management
            'general manager': 'General Manager',
            'senior manager': 'Senior Manager',
            'manager': 'Manager',
            'head': 'Head',
            'department head': 'Department Head',
            'team lead': 'Team Lead',
            'group lead': 'Group Lead',
            
            # Technical
            'senior engineer': 'Senior Engineer',
            'principal engineer': 'Principal Engineer',
            'lead engineer': 'Lead Engineer',
            'software engineer': 'Software Engineer',
            'systems architect': 'Systems Architect',
            'solution architect': 'Solution Architect',
            'technical architect': 'Technical Architect',
            'data scientist': 'Data Scientist',
            'senior developer': 'Senior Developer',
            
            # Business
            'business head': 'Business Head',
            'partner': 'Partner',
            'senior partner': 'Senior Partner',
            'associate partner': 'Associate Partner',
            'principal consultant': 'Principal Consultant',
            'senior consultant': 'Senior Consultant',
            'consultant': 'Consultant'
        }
        
        # Invalid terms for filtering
        self.invalid_terms = {
            # Places
            'india', 'china', 'usa', 'uk', 'europe', 'asia', 'africa',
            'america', 'australia', 'canada', 'japan', 'russia',
            'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai',
            'kolkata', 'pune', 'ahmedabad', 'london', 'new york',
            
            # Time-related
            'today', 'yesterday', 'tomorrow', 'week', 'month', 'year',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'january', 'february', 'march', 'april', 'may', 'june',
            
            # Common article terms
            'news', 'latest', 'breaking', 'update', 'report', 'exclusive',
            'market', 'stock', 'shares', 'price', 'rates', 'article',
            'read more', 'click here', 'full story', 'advertisement',
            
            # Events/Festivals
            'diwali', 'christmas', 'new year', 'festival', 'event',
            'conference', 'summit', 'meeting', 'webinar', 'seminar'
        }

    def clean_name(self, name):
        """Clean and validate person name."""
        if not name or len(name) < 3 or len(name) > 50:  # Increased max length
            return None
            
        name = name.strip()
        
        # Remove any extra whitespace
        name = ' '.join(name.split())
        
        # Split into words
        words = name.split()
        
        # Check basic name validity
        if len(words) < 2 or len(words) > 5:
            return None
            
        # Check for invalid terms
        if any(word.lower() in self.invalid_terms for word in words):
            return None
            
        # Ensure proper capitalization and full words
        cleaned_words = []
        for word in words:
            if len(word) < 2:  # Skip single letters
                continue
            if not word[0].isupper():
                return None
            cleaned_words.append(word)
        
        if len(cleaned_words) < 2:
            return None
        
        # Remove any numbers or special characters
        name = ' '.join(cleaned_words)
        if re.search(r'[0-9@#$%^&*()_+=\[\]{};:"|<>?]', name):
            return None
            
        return name

    def standardize_designation(self, designation):
        """Standardize designation to common format."""
        if not designation:
            return None
            
        designation = designation.lower().strip()
        
        # Check mapping for exact matches
        if designation in self.designation_mapping:
            return self.designation_mapping[designation]
            
        # Check for partial matches
        for key, value in self.designation_mapping.items():
            if key in designation:
                return value
                
        return designation.title()

    def get_clean_text_from_url(self, url):
        """Extract and clean text from URL."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.48 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
        ]

        for user_agent in user_agents:
            try:
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                response = self.session.get(url, headers=headers, verify=False, timeout=30)
                response.raise_for_status()
                
                if 'charset' in response.headers.get('content-type', '').lower():
                    response.encoding = response.apparent_encoding
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                    element.decompose()

                text = ""
                
                # Try multiple methods to extract text
                if not text:
                    article = soup.find(['article', 'main', '[role="article"]'])
                    if article:
                        text = article.get_text()

                if not text:
                    content_divs = soup.find_all(['div', 'section'], 
                        class_=lambda x: x and any(word in str(x).lower() for word in 
                        ['article', 'content', 'story', 'body', 'text', 'main', 'news']))
                    if content_divs:
                        text = ' '.join(div.get_text() for div in content_divs)

                if not text:
                    paragraphs = soup.find_all('p')
                    text = ' '.join(p.get_text() for p in paragraphs)

                if text:
                    # Clean text
                    text = re.sub(r'\s+', ' ', text)
                    text = re.sub(r'\n+', ' ', text)
                    text = re.sub(r'[^\w\s.,!?-]', '', text)
                    text = text.strip()
                    
                    return text

            except Exception as e:
                continue

        raise Exception("Could not extract content from URL. Please try pasting the article text directly.")

    def extract_profiles(self, text):
        """Extract and clean professional profiles from text."""
        doc = self.nlp(text)
        profiles = []
        seen_names = set()
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = self.clean_name(ent.text)
                if not name or name in seen_names:
                    continue
                
                # Get context around the name (increased context window)
                start = max(0, ent.start_char - 150)
                end = min(len(text), ent.end_char + 150)
                context = text[start:end]
                
                # Extract designations and companies
                designations = []
                companies = []
                
                # Improved designation patterns
                designation_patterns = [
                    r'(?:is|was|as|appointed|named|serves? as|joined as)\s+(?:the\s+)?([^,.]+(?:' + '|'.join([
                        'CEO', 'Chief Executive Officer',
                        'CTO', 'Chief Technology Officer',
                        'Director', 'Managing Director',
                        'President', 'Vice President',
                        'Head', 'Senior Vice President',
                        'Operations'
                    ]) + ')[^,.]*)',
                    r'(?:the\s+)?([^,.]+(?:Director|Manager|Officer|President|Founder|Head|Lead|Engineer|Architect|Consultant|Partner)[^,.]*)'
                ]
                
                # Look for designations using patterns
                for pattern in designation_patterns:
                    matches = re.finditer(pattern, context, re.IGNORECASE)
                    for match in matches:
                        designation = match.group(1).strip()
                        if designation:
                            clean_designation = self.standardize_designation(designation)
                            if clean_designation:
                                designations.append(clean_designation)
                
                # Improved company patterns
                company_patterns = [
                    r'(?:at|of|with|from|joins?)\s+([A-Z][A-Za-z0-9\s&\.]+(?:Inc\.?|Ltd\.?|Limited|Corporation|Corp\.?|Company|Co\.?|Technologies|Solutions|Group|Holdings|Ventures|Capital|Partners|LLP))',
                    r'([A-Z][A-Za-z0-9\s&\.]+(?:Inc\.?|Ltd\.?|Limited|Corporation|Corp\.?|Company|Co\.?|Technologies|Solutions|Group|Holdings|Ventures|Capital|Partners|LLP))'
                ]
                
                # Look for companies
                for pattern in company_patterns:
                    matches = re.finditer(pattern, context)
                    for match in matches:
                        company = match.group(1).strip()
                        if company and len(company) > 2:
                            clean_company = self.clean_company(company)
                            if clean_company:
                                companies.append(clean_company)
                
                # Remove duplicates while preserving order
                designations = list(dict.fromkeys(designations))
                companies = list(dict.fromkeys(companies))
                
                # Only include profiles with at least one designation or company
                if designations or companies:
                    linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}"
                    
                    profile = {
                        "name": name,
                        "designations": designations,
                        "companies": companies,
                        "linkedin_search": linkedin_url
                    }
                    
                    profiles.append(profile)
                    seen_names.add(name)
        
        return profiles

def main():
    st.markdown('<h1 class="main-title">🧠 NewsNex 📰</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">Smarter Prospecting Starts with News ⚡</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-tagline">Where News Sparks the Next Deal 🎯</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📰 URL Analysis", "📝 Text Analysis"])

    extractor = ProfileExtractor()
    
    with tab1:
        url = st.text_input("Enter news article URL:", placeholder="https://example.com/article")
        if st.button("Extract from URL", key="url_button"):
            if url:
                try:
                    with st.spinner("🔍 Analyzing article..."):
                        text = extractor.get_clean_text_from_url(url)
                        st.success(f"✅ Successfully retrieved article content ({len(text)} characters)")
                        
                        profiles = extractor.extract_profiles(text)
                        if profiles:
                            display_results(profiles)
                        else:
                            st.warning("No profiles found in the article. Try:")
                            st.info("1. Checking if the URL is accessible")
                            st.info("2. Pasting the article text directly in the Text Analysis tab")
                            st.info("3. Verifying that the article contains professional profiles")
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
                    st.info("💡 Tip: Try pasting the article text directly in the Text Analysis tab")
            else:
                st.warning("⚠️ Please enter a URL")

    with tab2:
        text_input = st.text_area("Paste article text:", height=200,
                                 placeholder="Paste the article content here...")
        if st.button("Extract from Text", key="text_button"):
            if text_input:
                with st.spinner("🔍 Processing text..."):
                    profiles = extractor.extract_profiles(text_input)
                    if profiles:
                        display_results(profiles)
                    else:
                        st.warning("No profiles found in the text. Please ensure:")
                        st.info("1. The text contains professional profiles")
                        st.info("2. Names are mentioned with designations or companies")
            else:
                st.warning("⚠️ Please enter some text")

def display_results(profiles):
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
        st.markdown("### 📋 Extracted Profiles")
        
        # Create a clean DataFrame
        df = pd.json_normalize(profiles)
        
        # Format the lists in designations and companies columns
        if not df.empty:
            if 'designations' in df.columns:
                df['designations'] = df['designations'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            if 'companies' in df.columns:
                df['companies'] = df['companies'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            
            # Rename columns for better display
            df.columns = [col.replace('.', ' ').title() for col in df.columns]
        
        # Display the DataFrame with custom styling
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        with col2:
            json_str = json.dumps(profiles, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    st.markdown(
        """
        <div class='footer'>
            Made with ❤️ by NewsNex | Transform News into Opportunities
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
