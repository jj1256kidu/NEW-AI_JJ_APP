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
        
        # Invalid terms for filtering
        self.invalid_terms = {
            'india', 'china', 'usa', 'uk', 'europe', 'asia', 'africa',
            'america', 'australia', 'canada', 'japan', 'russia',
            'today', 'yesterday', 'tomorrow', 'news', 'latest', 'breaking',
            'digi', 'yatra', 'article', 'update'
        }

    def clean_name(self, name):
        """Clean and validate person name."""
        if not name or len(name) < 3 or len(name) > 50:
            return None
            
        name = name.strip()
        words = name.split()
        
        # Check basic name validity
        if len(words) < 2 or len(words) > 5:
            return None
            
        # Check for invalid terms
        if any(word.lower() in self.invalid_terms for word in words):
            return None
            
        # Ensure proper capitalization
        if not all(word[0].isupper() for word in words if word):
            return None
            
        # Remove any numbers or special characters
        if re.search(r'[0-9@#$%^&*()_+=\[\]{};:"|<>?]', name):
            return None
            
        return name

    def clean_text(self, text):
        """Clean and standardize extracted text."""
        if not text:
            return ""
        # Remove unwanted characters and normalize spacing
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s&\-\.]', '', text)
        return text.strip()

    def get_clean_text_from_url(self, url):
        """Extract and clean text from URL with improved error handling and multiple user agents."""
        if not url:
            return ""
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        headers = {'User-Agent': random.choice(user_agents)}
        
        try:
            # Add timeout and verify=False for better connection handling
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
                element.decompose()
            
            # Try multiple content extraction strategies
            content = ""
            
            # Strategy 1: Look for article content
            article = soup.find('article') or soup.find(class_=re.compile(r'article|story|content|main'))
            if article:
                content = article.get_text()
            
            # Strategy 2: Look for specific content divs
            if not content:
                content_divs = soup.find_all(['div', 'section'], class_=re.compile(r'content|article|story|text'))
                content = ' '.join(div.get_text() for div in content_divs)
            
            # Strategy 3: Look for paragraphs
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join(p.get_text() for p in paragraphs)
            
            # Clean the extracted content
            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
            content = re.sub(r'[^\w\s.,!?-]', '', content)  # Remove special characters
            content = re.sub(r'\s+([.,!?])', r'\1', content)  # Fix spacing around punctuation
            
            # Remove common unwanted phrases
            unwanted_phrases = [
                'cookie consent',
                'privacy policy',
                'terms of service',
                'advertisement',
                'subscribe now',
                'share this article'
            ]
            for phrase in unwanted_phrases:
                content = re.sub(rf'\b{phrase}\b', '', content, flags=re.IGNORECASE)
            
            return content.strip()
            
        except requests.RequestException as e:
            print(f"Error fetching URL: {str(e)}")
            return ""
        except Exception as e:
            print(f"Error processing content: {str(e)}")
            return ""

    def extract_profiles(self, text):
        """Extract and clean professional profiles using advanced AI-driven pattern recognition."""
        if not text:
            return []
        
        doc = self.nlp(text)
        profiles = []
        seen_names = set()
        
        # Expanded designation patterns with industry-specific roles
        designation_patterns = [
            # Executive Leadership
            r'(?:is|was|as|appointed|named|serves? as|joined as)?\s*(?:the\s+)?([^,\.]+(?:' + '|'.join([
                'Chief\s+[A-Za-z]+\s+Officer',
                'CEO|CTO|CFO|COO|CIO|CMO|CPO|CHRO|CSO',
                'Founder|Co-Founder|Managing\s+Partner',
                'Executive\s+Chairman|Chairman|Chairperson',
                'Board\s+(?:Member|Director|Advisor)',
                'Managing\s+Director|Executive\s+Director'
            ]) + ')[^,\.]*)',
            
            # Senior Management
            r'(?:the\s+)?([^,\.]+(?:' + '|'.join([
                'Senior\s+Vice\s+President|Executive\s+Vice\s+President',
                'Senior\s+VP|SVP|EVP|AVP',
                'Global\s+Head|Regional\s+Head|Country\s+Head',
                'Division\s+Head|Business\s+Head|Unit\s+Head',
                'Senior\s+Director|Group\s+Director',
                'Principal|Partner|Associate\s+Partner'
            ]) + ')[^,\.]*)',
            
            # Technical Leadership
            r'(?:the\s+)?([^,\.]+(?:' + '|'.join([
                'Distinguished\s+Engineer|Principal\s+Engineer',
                'Chief\s+Architect|Lead\s+Architect',
                'Technical\s+Fellow|Engineering\s+Fellow',
                'Distinguished\s+Researcher|Principal\s+Scientist',
                'R&D\s+(?:Head|Director|Manager)',
                'Innovation\s+(?:Lead|Head|Director)'
            ]) + ')[^,\.]*)',
            
            # Domain Specific
            r'(?:the\s+)?([^,\.]+(?:' + '|'.join([
                'Data\s+(?:Scientist|Architect|Engineer)',
                'AI|ML|Cloud|DevOps|SRE|Platform',
                'Product\s+(?:Manager|Owner|Lead)',
                'Program\s+(?:Manager|Director)',
                'Solution\s+(?:Architect|Engineer)',
                'Security\s+(?:Engineer|Architect|Lead)'
            ]) + ')[^,\.]*)',
            
            # Business Functions
            r'(?:the\s+)?([^,\.]+(?:' + '|'.join([
                'Strategy|Operations|Marketing|Sales',
                'Business\s+Development|Customer\s+Success',
                'Human\s+Resources|Talent\s+Acquisition',
                'Finance|Legal|Compliance|Risk',
                'Research|Analytics|Intelligence',
                'Consulting|Advisory'
            ]) + ')[^,\.]*)'
        ]
        
        # Enhanced company patterns with industry context
        company_patterns = [
            # Standard Company Identifiers
            r'(?:at|of|with|from|for)\s+([A-Z][A-Za-z0-9\s&\.]+(?:' + '|'.join([
                'Inc(?:orporated)?',
                'Ltd|Limited',
                'Corp(?:oration)?',
                'LLC|LLP|PLLC',
                'Group|Holdings|Ventures',
                'Technologies|Solutions|Systems',
                'International|Global|Worldwide',
                'Partners|Associates|Consultants'
            ]) + ')',
            
            # Industry-Specific Companies
            r'([A-Z][A-Za-z0-9\s&\.]+(?:' + '|'.join([
                'Bank|Financial|Insurance|Capital',
                'Healthcare|Medical|Pharma|Biotech',
                'Software|Digital|Cyber|Tech',
                'Consulting|Services|Solutions',
                'Manufacturing|Industries|Products',
                'Energy|Utilities|Resources',
                'Media|Entertainment|Communications',
                'Retail|Consumer|Brands'
            ]) + '))',
            
            # Organizational Context
            r'(?:joined|works?\s+(?:at|with|for)|employed\s+by|based\s+(?:at|in))\s+([A-Z][A-Za-z0-9\s&\.]+)',
            r'(?:the|a|an)\s+([A-Z][A-Za-z0-9\s&\.]+(?:\s+(?:company|organization|enterprise|firm|startup)))',
            r'(?:subsidiary|division|unit|branch)\s+of\s+([A-Z][A-Za-z0-9\s&\.]+)'
        ]

        def analyze_context(ent, doc):
            """Enhanced context analysis around entities."""
            # Find the containing sentence and its neighbors
            current_sent = None
            prev_sent = None
            next_sent = None
            
            for sent in doc.sents:
                if ent.start >= sent.start and ent.end <= sent.end:
                    current_sent = sent
                    break
            
            if current_sent:
                # Get surrounding sentences
                sents = list(doc.sents)
                sent_index = sents.index(current_sent)
                if sent_index > 0:
                    prev_sent = sents[sent_index - 1]
                if sent_index < len(sents) - 1:
                    next_sent = sents[sent_index + 1]
            
            # Combine context with weights
            context = ""
            if prev_sent:
                context += prev_sent.text + " "
            if current_sent:
                context += current_sent.text + " "
            if next_sent:
                context += next_sent.text
            
            # Extract additional context features
            features = {
                'has_role_indicators': bool(re.search(r'\b(?:appointed|named|joined|leads?|heading|manages?)\b', context, re.I)),
                'has_company_indicators': bool(re.search(r'\b(?:at|with|for|company|organization|firm)\b', context, re.I)),
                'has_duration': bool(re.search(r'\b(?:years?|months?|since|from)\b', context, re.I)),
                'has_location': bool(re.search(r'\b(?:based|located|headquarters|office)\b', context, re.I))
            }
            
            return context, features

        def validate_extraction(name, designation, company, context_features):
            """Validate extracted information using context features."""
            score = 0
            if context_features['has_role_indicators']:
                score += 2
            if context_features['has_company_indicators']:
                score += 2
            if context_features['has_duration']:
                score += 1
            if context_features['has_location']:
                score += 1
            
            # Additional validation rules
            if designation and any(word in designation.lower() for word in ['senior', 'chief', 'head', 'director', 'vp', 'president']):
                score += 2
            if company and len(company.split()) >= 2:
                score += 1
            
            return score >= 3  # Minimum threshold for validity

        # Process entities with enhanced context
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = self.clean_name(ent.text)
                if not name or name in seen_names:
                    continue
                
                context, context_features = analyze_context(ent, doc)
                
                designations = []
                companies = []
                
                for pattern in designation_patterns:
                    matches = re.finditer(pattern, context, re.IGNORECASE)
                    for match in matches:
                        designation = self.clean_text(match.group(1))
                        if designation and len(designation.split()) <= 7:
                            designations.append(designation)
                
                for pattern in company_patterns:
                    matches = re.finditer(pattern, context)
                    for match in matches:
                        company = self.clean_text(match.group(1))
                        if company and len(company.split()) <= 6:
                            companies.append(company)
                
                # Remove duplicates while preserving order
                designations = list(dict.fromkeys(designations))
                companies = list(dict.fromkeys(companies))
                
                # Validate and filter
                if designations or companies:
                    primary_designation = designations[0] if designations else ""
                    primary_company = companies[0] if companies else ""
                    
                    if validate_extraction(name, primary_designation, primary_company, context_features):
                        search_terms = [name]
                        if primary_designation:
                            search_terms.extend(primary_designation.split()[:2])
                        if primary_company:
                            search_terms.append(primary_company.split()[0])
                        
                        linkedin_url = (
                            "https://www.linkedin.com/search/results/people/?"
                            f"keywords={'+'.join(search_terms).replace(' ', '%20')}"
                        )
                        
                        profile = {
                            "name": name,
                            "designation": ' | '.join(designations) if designations else "",
                            "company": ' | '.join(companies) if companies else "",
                            "linkedin_search": linkedin_url,
                            "confidence_score": context_features
                        }
                        
                        profiles.append(profile)
                        seen_names.add(name)
        
        return profiles

def display_results(profiles):
    if not profiles:
        st.warning("No profiles found. Try with different content or ensure the text contains professional profiles.")
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

    # Create DataFrame
    df = pd.DataFrame(profiles)
    
    # Display results
    st.markdown("### 📋 Extracted Profiles")
    st.dataframe(
        df,
        use_container_width=True,
        height=400
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

    tab1, tab2 = st.tabs(["📰 URL Analysis", "📝 Text Analysis"])

    extractor = ProfileExtractor()
    
    with tab1:
        url = st.text_input("Enter news article URL:", placeholder="https://example.com/article")
        if st.button("Extract from URL", key="url_button"):
            if url:
                try:
                    with st.spinner("🔍 Analyzing article..."):
                        text = extractor.get_clean_text_from_url(url)
                        if text:
                            st.success(f"✅ Successfully retrieved article content ({len(text)} characters)")
                            profiles = extractor.extract_profiles(text)
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
                    display_results(profiles)
            else:
                st.warning("⚠️ Please enter some text")

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
