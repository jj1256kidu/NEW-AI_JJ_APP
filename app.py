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
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fuzzywuzzy import fuzz
import time
import nltk

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="NewsNex – From News to Next Opportunities",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Download required NLTK data
@st.cache_resource
def setup_nltk():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

# Initialize NLTK
try:
    setup_nltk()
except Exception as e:
    st.error("Failed to initialize NLTK. Please ensure NLTK data is properly installed.")
    st.stop()

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
        font-family: 'Inter', 'sans serif';
        letter-spacing: -0.02em;
    }
    
    .tagline {
        font-size: 1.8rem;
        color: #40c4ff;
        text-align: center;
        margin-bottom: 0.5rem;
        font-family: 'Inter', 'sans serif';
        font-weight: 600;
        text-shadow: 0 0 20px rgba(64, 196, 255, 0.3);
    }
    
    .sub-tagline {
        font-size: 1.4rem;
        color: #00ffd1;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Inter', 'sans serif';
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

@st.cache_resource(show_spinner=False)
def setup_selenium():
    """Setup Selenium WebDriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return driver

class ProfileExtractor:
    def __init__(self):
        self.nlp = load_nlp_model()
        self.session = requests.Session()
        self.seen_profiles = set()  # Cache for deduplication
        
        # Common name prefixes
        self.name_prefixes = {
            'mr', 'mrs', 'ms', 'dr', 'prof', 'shri', 'smt', 'sir',
            'justice', 'adv', 'advocate', 'ca', 'er', 'eng'
        }
        
        # Invalid terms for filtering
        self.invalid_terms = {
            'india', 'china', 'usa', 'uk', 'europe', 'asia', 'africa',
            'america', 'australia', 'canada', 'japan', 'russia',
            'today', 'yesterday', 'tomorrow', 'news', 'latest', 'breaking',
            'digi', 'yatra', 'article', 'update'
        }

    def get_profile_key(self, name, company):
        """Generate a unique key for deduplication."""
        return f"{name.lower()}|{company.lower()}" if company else name.lower()

    def is_duplicate(self, name, company):
        """Check if a profile is a duplicate based on name and company."""
        key = self.get_profile_key(name, company)
        return key in self.seen_profiles

    def add_to_cache(self, name, company):
        """Add a profile to the deduplication cache."""
        key = self.get_profile_key(name, company)
        self.seen_profiles.add(key)

    def clear_cache(self):
        """Clear the deduplication cache."""
        self.seen_profiles.clear()

    def clean_name(self, name):
        """Basic name cleaning with minimal validation."""
        if not name:
            return ""
        
        # Basic cleaning
        name = name.strip()
        
        # Remove numbers and special characters
        name = re.sub(r'[0-9]', '', name)
        name = re.sub(r'[^\w\s\-\']', '', name)
        
        # Basic validation
        name = name.strip()
        if not name:
            return ""
        
        # Split into parts
        name_parts = name.split()
        if not name_parts:
            return ""
        
        # Must start with capital letter
        if not name_parts[0][0].isupper():
            return ""
        
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name_parts)
        
        return name

    def clean_text(self, text):
        """Clean and standardize extracted text."""
        if not text:
            return ""
        # Remove unwanted characters and normalize spacing
        text = text.strip()
        text = re.sub(r'\\s+', ' ', text)
        text = re.sub(r'[^\\w\\s&\\-\\.]', '', text)
        return text.strip()

    def get_clean_text_from_url(self, url):
        """Extract and clean text from URL with improved handling for modern news sites."""
        if not url:
            return ""
        
        # Modern browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Cache-Control': 'max-age=0'
        }
        
        try:
            # Create a session to handle cookies and redirects
            session = requests.Session()
            
            # First request to handle redirects and get cookies
            response = session.get(
                url,
                headers=headers,
                timeout=30,
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript', 'aside', 'form']):
                element.decompose()
            
            # Initialize content
            content = ""
            
            # Strategy 1: Look for article content with common class names
            article_classes = [
                'article-content',
                'story-content',
                'main-content',
                'article-body',
                'story-body',
                'content-body',
                'entry-content',
                'post-content',
                'article__content',
                'article__body',
                'story__content',
                'story__body',
                'cms-content',
                'paywall-article-content'
            ]
            
            for class_name in article_classes:
                article = soup.find(['article', 'div', 'section'], class_=class_name)
                if article:
                    content = article.get_text(separator=' ', strip=True)
                    break
            
            # Strategy 2: Look for article tag or main content div
            if not content:
                article = (
                    soup.find('article') or 
                    soup.find(['div', 'section'], class_=re.compile(r'article|story|content|main|post|entry', re.I)) or
                    soup.find('main')
                )
                if article:
                    content = article.get_text(separator=' ', strip=True)
            
            # Strategy 3: Look for paragraphs within content divs
            if not content:
                content_divs = soup.find_all(['div', 'section'], class_=re.compile(r'content|article|story|text|body|main', re.I))
                paragraphs = []
                for div in content_divs:
                    paragraphs.extend(div.find_all('p'))
                if paragraphs:
                    content = ' '.join(p.get_text(strip=True) for p in paragraphs)
            
            # Strategy 4: Fall back to all paragraphs if no content found
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join(p.get_text(strip=True) for p in paragraphs)
            
            if not content:
                return ""
            
            # Clean the content
            content = self.clean_article_content(content)
            
            return content
            
        except requests.RequestException:
            return ""
        except Exception:
            return ""
    
    def clean_article_content(self, content):
        """Clean and normalize article content."""
        if not content:
            return ""
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common unwanted phrases
        unwanted_phrases = [
            'cookie consent',
            'privacy policy',
            'terms of service',
            'advertisement',
            'subscribe now',
            'share this article',
            'read more',
            'click here',
            'follow us',
            'related articles',
            'also read',
            'more from',
            'newsletter',
            'sign up',
            'log in',
            'register',
            'download app',
            'install app',
            'copyright',
            'all rights reserved',
            'please wait',
            'loading',
            'sponsored content',
            'advertisement',
            'recommended for you',
            'trending now',
            'popular stories',
            'share on',
            'bookmark',
            'print article',
            'save article',
            'comments'
        ]
        
        # Create a pattern that matches any of these phrases
        pattern = '|'.join(map(re.escape, unwanted_phrases))
        content = re.sub(rf'\b(?:{pattern})\b', '', content, flags=re.IGNORECASE)
        
        # Remove URLs
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        
        # Remove email addresses
        content = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', content)
        
        # Remove multiple spaces and normalize punctuation
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\s+([.,!?])', r'\1', content)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return content

    def extract_profiles(self, text):
        """Extract profiles with simplified rules."""
        if not text:
            return []
        
        doc = self.nlp(text)
        profiles = []
        seen_names = set()
        
        # First pass: Find all quoted statements and their speakers
        quote_speakers = {}
        quote_pattern = r'"([^"]+)"\s*(?:,\s*)?(?:said|says|according to)\s+([A-Z][a-zA-Z]+)'
        for match in re.finditer(quote_pattern, text):
            quote = match.group(1).strip()
            speaker = match.group(2).strip()
            if speaker:
                quote_speakers[speaker] = quote
        
        # Second pass: Find company associations
        company_associations = {}
        company_patterns = [
            (r'([A-Z][a-zA-Z]+)(?:\s+(?:of|from|at|with))?\s+([A-Z][A-Za-z0-9]+(?:\s*,?\s*(?:Inc|Ltd|LLC|Corp|Corporation|Company|Group|Technologies|Solutions))?)', 2),
            (r'([A-Z][a-zA-Z]+)\s*,?\s*([A-Z][A-Za-z0-9]+(?:\s*,?\s*(?:Inc|Ltd|LLC|Corp|Corporation|Company|Group|Technologies|Solutions))?)', 2),
        ]
        
        for pattern, group in company_patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                company = match.group(group).strip()
                if name and company:
                    company_associations[name] = company
        
        # Process sentences for additional context
        for sent in doc.sents:
            sent_text = sent.text
            
            # Look for names in the sentence
            for ent in sent.ents:
                if ent.label_ == "PERSON":
                    name = self.clean_name(ent.text)
                    if not name or name in seen_names:
                        continue
                    
                    # Check if we have a quote or company for this name
                    quote = quote_speakers.get(name, "")
                    company = company_associations.get(name, "")
                    
                    # If we have either a quote or company, create a profile
                    if quote or company:
                        # Look for designation in the sentence
                        designation = ""
                        designation_pattern = r'(?:is|was|as|serves?\s+as)?\s*(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Chief|CEO|CTO|CFO|COO|CIO|President|Director|Manager|Lead|Head|Officer|Executive))'
                        designation_match = re.search(designation_pattern, sent_text, re.IGNORECASE)
                        if designation_match:
                            designation = designation_match.group(1).strip()
                        
                        # Generate LinkedIn search URL
                        search_terms = [name]
                        if company:
                            search_terms.append(company.split()[0])
                        
                        linkedin_url = (
                            "https://www.google.com/search?q=LinkedIn+"
                            + "+".join(search_terms).replace(" ", "+")
                        )
                        
                        profile = {
                            "name": name,
                            "designation": designation,
                            "company": company,
                            "quote": quote,
                            "linkedin_search": linkedin_url,
                            "confidence": "high" if (company and quote) else "medium"
                        }
                        
                        profiles.append(profile)
                        seen_names.add(name)
            
            # Also check for single-word names in quotes
            for name, quote in quote_speakers.items():
                if name not in seen_names:
                    clean_name = self.clean_name(name)
                    if not clean_name:
                        continue
                    
                    company = company_associations.get(name, "")
                    
                    # Generate LinkedIn search URL
                    search_terms = [clean_name]
                    if company:
                        search_terms.append(company.split()[0])
                    
                    linkedin_url = (
                        "https://www.google.com/search?q=LinkedIn+"
                        + "+".join(search_terms).replace(" ", "+")
                    )
                    
                    profile = {
                        "name": clean_name,
                        "designation": "",
                        "company": company,
                        "quote": quote,
                        "linkedin_search": linkedin_url,
                        "confidence": "high" if company else "medium"
                    }
                    
                    profiles.append(profile)
                    seen_names.add(clean_name)
        
        return profiles

def validate_profile(name, designation, company, context):
    """Enhanced profile validation with scoring system."""
    score = 0
    confidence = "low"
    
    # Name validation (0-2 points)
    if name and len(name.split()) >= 2:
        score += 1
        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', name):  # Proper capitalization
            score += 1
    
    # Designation validation (0-2 points)
    if designation:
        score += 1
        if len(designation.split()) >= 2:  # Detailed designation
            score += 1
    
    # Company validation (0-2 points)
    if company:
        score += 1
        if len(company.split()) >= 2:  # Multi-word company name
            score += 1
    
    # Context validation (0-2 points)
    context_lower = context['text'].lower()
    if any(term in context_lower for term in ['joined', 'appointed', 'promoted', 'leads', 'heading']):
        score += 1
    if any(term in context_lower for term in ['years', 'experience', 'professional', 'career']):
        score += 1
    
    # Determine confidence level
    if score >= 4:  # Lowered threshold from 5 to 4
        confidence = "very_high"
    elif score >= 3:
        confidence = "high"
    elif score >= 2:  # Lowered threshold from 3 to 2
        confidence = "medium"
    
    return {
        'is_valid': score >= 2,  # Lowered threshold from 3 to 2
        'score': score,
        'confidence': confidence
    }

def display_results(profiles):
    if not profiles:
        st.warning("No profiles found.")
        return
    
    # Calculate metrics
    total_prospects = len(profiles)
    complete_profiles = sum(1 for p in profiles if p['designation'] and p['company'])
    unique_companies = len(set(p['company'] for p in profiles if p['company']))
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">📊 Total Prospects</div>
                <div class="metric-value">{total_prospects}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
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

    # Create DataFrame with clean formatting
    df = pd.DataFrame(profiles)
    df['confidence'] = df['confidence'].apply(lambda x: f"{x:.0f}%")
    
    # Display results
    st.markdown("### 📋 Extracted Profiles")
    st.dataframe(
        df,
        use_container_width=True,
        height=400,
        column_config={
            "name": "Name",
            "designation": "Designation",
            "company": "Company",
            "quote": st.column_config.ListColumn("Quotes"),
            "linkedin_search": st.column_config.LinkColumn("LinkedIn Search"),
            "confidence": "Confidence"
        }
    )
    
    # Download options
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

def main():
    st.markdown('<h1 class="main-title">🧠 NewsNex 📰</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">Smarter Prospecting Starts with News ⚡</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-tagline">Where News Sparks the Next Deal 🎯</p>', unsafe_allow_html=True)

    # Add deduplication toggle
    deduplicate = st.checkbox("Enable deduplication across articles", value=True,
                            help="Prevents the same person from appearing multiple times across different articles")

    tab1, tab2 = st.tabs(["📰 URL Analysis", "Text Analysis"])

    extractor = ProfileExtractor()
    
    with tab1:
        url = st.text_input("Enter news article URL:", placeholder="https://example.com/article")
        if st.button("Extract from URL", key="url_button"):
            if url:
                try:
                    with st.spinner("🔍 Analyzing article..."):
                        text = extractor.get_clean_text_from_url(url)
                        if text and not text.startswith("⚠️"):
                            st.text_area("Extracted Article Content:", text, height=200)
                            profiles = extractor.extract_profiles(text)
                            
                            # Apply deduplication if enabled
                            if deduplicate:
                                unique_profiles = []
                                for profile in profiles:
                                    if not extractor.is_duplicate(profile['name'], profile['company']):
                                        unique_profiles.append(profile)
                                        extractor.add_to_cache(profile['name'], profile['company'])
                                profiles = unique_profiles
                            
                            if profiles:
                                display_results(profiles)
                            else:
                                st.warning("No profiles found in the article. Try a different article or paste the text directly.")
                        else:
                            st.warning(text)
                except Exception as e:
                    st.error(f"Error processing URL: {str(e)}")

    with tab2:
        text_input = st.text_area("Paste article text:", height=200,
                                 placeholder="Paste the article content here...")
        if st.button("Extract from Text", key="text_button"):
            if text_input:
                with st.spinner("🔍 Processing text..."):
                    profiles = extractor.extract_profiles(text_input)
                    
                    # Apply deduplication if enabled
                    if deduplicate:
                        unique_profiles = []
                        for profile in profiles:
                            if not extractor.is_duplicate(profile['name'], profile['company']):
                                unique_profiles.append(profile)
                                extractor.add_to_cache(profile['name'], profile['company'])
                        profiles = unique_profiles
                    
                    if profiles:
                        display_results(profiles)
                    else:
                        st.warning("No profiles found in the text. Try a different article.")
            else:
                st.warning("Please enter some text")

    # Add clear cache button
    if deduplicate and st.button("Clear deduplication cache"):
        extractor.clear_cache()
        st.success("✅ Deduplication cache cleared")

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
