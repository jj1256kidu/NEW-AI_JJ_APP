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
        self.seen_profiles = set()
        self.driver = None
        self.profile_cache = set()  # Add cache for deduplication
        
        # Load designation patterns
        self.designation_patterns = [
            r'(?:is|was|as|serves?\s+as|joined\s+as|appointed\s+as)?\s*(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Chief|CEO|CTO|CFO|COO|CIO|President|Director|Manager|Lead|Head|Officer|Executive))',
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Executive|Senior|Principal|Global|Regional|Technical|Engineering|Product|Project)\s+(?:Director|Manager|Lead|Officer|Head))',
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Founder|Co-founder|Partner|Managing Partner|General Partner|VP|Vice President|SVP|EVP))',
        ]
        
        # Load company patterns
        self.company_patterns = [
            r'(?:at|with|from|of|,?\s+(?:of|at|from))?\s+([A-Z][A-Za-z0-9\s&\.\-]+(?:Inc\.|Ltd\.|LLC|Corp\.|Corporation|Company|Group|Technologies|Solutions))',
            r'([A-Z][A-Za-z0-9\s&\.\-]+)\'s\s+(?:executive|manager|director|officer|lead|head)',
            r'([A-Z][A-Za-z0-9\s&\.\-]+(?:Bank|Tech|Software|Systems|Digital|Global|International))'
        ]

    def is_duplicate(self, name, company):
        """Check if a profile is a duplicate based on name and company."""
        profile_key = f"{name.lower()}_{company.lower()}" if company else name.lower()
        return profile_key in self.profile_cache

    def add_to_cache(self, name, company):
        """Add a profile to the deduplication cache."""
        profile_key = f"{name.lower()}_{company.lower()}" if company else name.lower()
        self.profile_cache.add(profile_key)

    def clear_cache(self):
        """Clear the deduplication cache."""
        self.profile_cache.clear()

    def get_clean_text_from_url(self, url):
        """Get clean article content from URL with precise extraction."""
        if not url:
            return "No URL provided"

        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Check for problematic domains
            problematic_domains = [
                'indiatimes.com', 'timesofindia.indiatimes.com',
                'hindustantimes.com', 'thehindu.com'
            ]
            if any(domain in url for domain in problematic_domains):
                return (
                    "⚠️ This news site may have restrictions. "
                    "Please copy and paste the article content directly in the 'Text Analysis' tab."
                )
            
            # First try with requests
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type:
                    return f"URL does not contain HTML content. Content type: {content_type}"
                
                content = self._extract_content_from_html(response.text)
                
                # If content is too short, try with selenium if available
                if len(content.split()) < 50:
                    try:
                        selenium_content = self._get_text_with_selenium(url)
                        if selenium_content and len(selenium_content.split()) > len(content.split()):
                            content = selenium_content
                    except Exception:
                        pass
                
                if not content or len(content.split()) < 20:
                    return "Could not extract meaningful content from the URL. Please check if the URL is correct and accessible."
                
                return content

            except requests.RequestException as e:
                error_msg = f"Error fetching URL: {str(e)}"
                try:
                    # Try selenium as fallback
                    content = self._get_text_with_selenium(url)
                    if content and len(content.split()) >= 20:
                        return content
                except Exception:
                    pass
                return error_msg

        except Exception as e:
            return f"Unexpected error processing URL: {str(e)}"

    def _get_text_with_requests(self, url):
        """Extract text using requests."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            response = self.session.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            return self._extract_content_from_html(response.text)
        except:
            return ""

    def _get_text_with_selenium(self, url):
        """Extract text using Selenium with improved error handling."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Initialize driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Load page
                driver.get(url)
                
                # Wait for content to load
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Get page source
                html = driver.page_source
                
                # Extract content
                content = self._extract_content_from_html(html)
                
                return content
                
            finally:
                driver.quit()
                
        except ImportError:
            return "Selenium is not available. Please install it for enhanced URL processing."
        except Exception as e:
            return f"Error with Selenium extraction: {str(e)}"

    def _extract_content_from_html(self, html):
        """Extract and clean content from HTML with precise targeting."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 
                           'noscript', 'aside', 'form', 'ad', 'ads', 'advertisement',
                           'trending', 'subscribe', 'newsletter', 'related', 'popular',
                           'comments', 'social', 'share', 'recommended']):
            element.decompose()
        
        # Try multiple content extraction strategies
        content = ""
        
        # Strategy 1: Look for article content with common class names
        article_classes = [
            'article-content', 'story-content', 'main-content',
            'article-body', 'story-body', 'content-body',
            'entry-content', 'post-content', 'article__content',
            'article__body', 'story__content', 'story__body',
            'cms-content', 'paywall-article-content'
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
        
        # Strategy 4: Fall back to all paragraphs
        if not content:
            paragraphs = soup.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in paragraphs)
        
        # If still no content, try getting all text
        if not content:
            content = soup.get_text(separator=' ', strip=True)
        
        return self.clean_article_content(content)

    def clean_name(self, name):
        """Clean and validate names with stricter rules."""
        if not name:
            return ""
        
        # Basic cleaning
        name = name.strip()
        name = re.sub(r'[0-9]', '', name)
        name = re.sub(r'[^\w\s\-\']', '', name)
        
        # Split into parts
        name_parts = name.split()
        if not name_parts:
            return ""
        
        # Must have at least first and last name
        if len(name_parts) < 2:
            return ""
        
        # Each part must be at least 2 characters
        if any(len(part) < 2 for part in name_parts):
            return ""
        
        # Must start with capital letter
        if not all(part[0].isupper() for part in name_parts):
            return ""
        
        # Check against common non-name words
        non_name_words = {
            'city', 'state', 'country', 'region', 'district',
            'company', 'organization', 'institute', 'university',
            'news', 'article', 'story', 'report', 'update',
            'today', 'yesterday', 'tomorrow', 'website'
        }
        
        # Use fuzzy matching to check for non-name words
        for part in name_parts:
            if any(fuzz.ratio(part.lower(), word) > 85 for word in non_name_words):
                return ""
        
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name_parts)
        
        return name

    def validate_designation(self, designation):
        """Validate designation with fuzzy matching."""
        if not designation:
            return False
        
        valid_titles = [
            'Chief', 'CEO', 'CTO', 'CFO', 'COO', 'CIO',
            'President', 'Director', 'Manager', 'Lead',
            'Head', 'Officer', 'Executive', 'Founder',
            'Partner', 'VP', 'Vice President'
        ]
        
        # Check if any valid title appears in the designation
        return any(
            any(fuzz.partial_ratio(title.lower(), word.lower()) > 85
                for word in designation.split())
            for title in valid_titles
        )

    def validate_company(self, company):
        """Validate company name with fuzzy matching."""
        if not company:
            return False
        
        # Company must start with capital letter and have at least 2 characters
        if len(company) < 2 or not company[0].isupper():
            return False
        
        # Check against common non-company words
        non_company_words = {
            'news', 'article', 'story', 'report', 'update',
            'today', 'yesterday', 'tomorrow', 'website'
        }
        
        # Use fuzzy matching to check for non-company words
        return not any(
            fuzz.ratio(company.lower(), word) > 85
            for word in non_company_words
        )

    def clean_article_content(self, content):
        """Clean and normalize article content."""
        if not content:
            return ""
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common unwanted phrases
        unwanted_phrases = [
            'cookie consent', 'privacy policy', 'terms of service',
            'advertisement', 'subscribe now', 'share this article',
            'read more', 'click here', 'follow us', 'related articles',
            'also read', 'more from', 'newsletter', 'sign up', 'log in',
            'register', 'download app', 'install app', 'copyright',
            'all rights reserved', 'please wait', 'loading',
            'sponsored content', 'advertisement', 'recommended for you',
            'trending now', 'popular stories', 'share on', 'bookmark',
            'print article', 'save article', 'comments'
        ]
        
        # Create a pattern that matches any of these phrases
        pattern = '|'.join(map(re.escape, unwanted_phrases))
        content = re.sub(rf'\b(?:{pattern})\b', '', content, flags=re.IGNORECASE)
        
        # Remove URLs and email addresses
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        content = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', content)
        
        # Remove multiple spaces and normalize punctuation
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\s+([.,!?])', r'\1', content)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return content

    def extract_quotes(self, text, name):
        """Extract and validate quotes attributed to a person."""
        if not text or not name:
            return []
        
        quotes = []
        
        # Pattern 1: Direct quotes with attribution
        patterns = [
            # "Quote," said Name
            rf'"([^"]+)"\s*,?\s*(?:said|says|according to|told)\s+{re.escape(name)}',
            # Name said: "Quote"
            rf'{re.escape(name)}\s+(?:said|says|added|noted|mentioned|explained|stated|commented):\s*"([^"]+)"',
            # According to Name, "Quote"
            rf'(?:According to|As per)\s+{re.escape(name)}[^"]*"([^"]+)"',
            # Name: "Quote"
            rf'{re.escape(name)}:\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                quote = match.group(1).strip()
                if self.validate_quote(quote):
                    quotes.append(quote)
        
        return quotes

    def validate_quote(self, quote):
        """Validate a quote based on various criteria."""
        if not quote:
            return False
        
        # Length validation (20-500 characters)
        if len(quote) < 20 or len(quote) > 500:
            return False
        
        # Must contain word characters
        if not re.search(r'\w', quote):
            return False
        
        # Should not be just a URL or email
        if re.match(r'^https?://|^[\w\.-]+@[\w\.-]+\.\w+$', quote):
            return False
        
        # Should not be just numbers or special characters
        if not re.search(r'[a-zA-Z]{3,}', quote):
            return False
        
        return True

    def calculate_confidence_score(self, name, designation, company, quotes):
        """Calculate confidence score for a profile."""
        score = 0
        max_score = 10
        
        # Name scoring (0-2 points)
        if name:
            score += 1
            if len(name.split()) >= 2:  # Full name
                score += 1
        
        # Designation scoring (0-3 points)
        if designation:
            score += 1
            if len(designation.split()) >= 2:  # Detailed designation
                score += 1
            if self.validate_designation(designation):  # Valid designation
                score += 1
        
        # Company scoring (0-2 points)
        if company:
            score += 1
            if self.validate_company(company):  # Valid company
                score += 1
        
        # Quote scoring (0-3 points)
        if quotes:
            score += 1
            if len(quotes) >= 2:  # Multiple quotes
                score += 1
            if any(len(quote.split()) > 10 for quote in quotes):  # Substantial quote
                score += 1
        
        # Calculate percentage and determine confidence level
        confidence_percent = (score / max_score) * 100
        return confidence_percent

    def extract_profiles(self, text):
        """Extract profiles from text with enhanced validation."""
        if not text:
            return []

        profiles = []
        seen_profiles = set()
        
        # Find potential profile sections
        sentences = nltk.sent_tokenize(text)
        
        for i, sentence in enumerate(sentences):
            # Get context (previous and next sentences)
            context_start = max(0, i - 2)
            context_end = min(len(sentences), i + 3)
            context = ' '.join(sentences[context_start:context_end])
            
            # Extract names
            doc = self.nlp(sentence)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = self.clean_name(ent.text)
                    if not name or self.is_duplicate(name):
                        continue
                    
                    # Extract designation and company
                    designation, company = self.extract_designation_and_company(context)
                    if not designation and not company:
                        continue
                    
                    # Extract quotes
                    quotes = self.extract_quotes(context, name)
                    
                    # Generate LinkedIn search URL
                    search_terms = [name]
                    if company:
                        search_terms.append(company.split()[0])
                    
                    linkedin_url = (
                        "https://www.google.com/search?q=LinkedIn+"
                        + "+".join(search_terms).replace(" ", "+")
                    )
                    
                    # Calculate confidence score
                    confidence = self.calculate_confidence_score(name, designation, company, quotes)
                    
                    # Only include profiles with high confidence
                    if confidence >= 60:  # 60% confidence threshold
                        profile = {
                            "name": name,
                            "designation": designation,
                            "company": company,
                            "quotes": quotes,
                            "linkedin_search": linkedin_url,
                            "confidence": confidence
                        }
                        
                        # Add to profiles if not seen
                        profile_key = self.get_profile_key(name, company)
                        if profile_key not in seen_profiles:
                            profiles.append(profile)
                            seen_profiles.add(profile_key)
        
        # Sort profiles by confidence
        profiles.sort(key=lambda x: x["confidence"], reverse=True)
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
            "quotes": st.column_config.ListColumn("Quotes"),
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
