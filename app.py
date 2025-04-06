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
        """Enhanced name cleaning with better validation."""
        if not name:
            return ""
        
        # Basic cleaning
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        
        # Remove titles and common prefixes/suffixes
        titles = r'(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sir|Madam|Miss|Shri|Smt|Jr\.|Sr\.|I|II|III|IV|V|MD|PhD|MBA|CPA|Esq\.)'
        name = re.sub(f'^{titles}\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(f'\s*{titles}$', '', name, flags=re.IGNORECASE)
        
        # Remove numbers and special characters
        name = re.sub(r'[0-9]', '', name)
        name = re.sub(r'[^\w\s\-\']', '', name)
        
        # Validate name
        name = name.strip()
        if not name or len(name.split()) < 2 or len(name) < 4:
            return ""
        
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name.split())
        
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
            st.warning("No URL provided")
            return ""
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        headers = {'User-Agent': random.choice(user_agents)}
        
        try:
            st.info(f"Fetching content from URL: {url}")
            # Add timeout and verify=False for better connection handling
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            st.info(f"Response status: {response.status_code}")
            
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
                st.info("Found content using article tag strategy")
            
            # Strategy 2: Look for specific content divs
            if not content:
                content_divs = soup.find_all(['div', 'section'], class_=re.compile(r'content|article|story|text'))
                content = ' '.join(div.get_text() for div in content_divs)
                if content:
                    st.info("Found content using content divs strategy")
            
            # Strategy 3: Look for paragraphs
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join(p.get_text() for p in paragraphs)
                if content:
                    st.info("Found content using paragraphs strategy")
            
            if not content:
                st.warning("No content found using any extraction strategy")
                return ""
            
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
            
            st.info(f"Extracted content length: {len(content)} characters")
            return content.strip()
            
        except requests.RequestException as e:
            st.error(f"Error fetching URL: {str(e)}")
            return ""
        except Exception as e:
            st.error(f"Error processing content: {str(e)}")
            return ""

    def extract_profiles(self, text):
        """Extract and clean professional profiles with comprehensive pattern matching."""
        if not text:
            st.warning("No text provided for analysis.")
            return []
        
        doc = self.nlp(text)
        profiles = []
        seen_names = set()
        
        # Debug information
        st.info(f"Processing text with {len(list(doc.sents))} sentences...")
        
        # Expanded designation patterns
        designation_patterns = [
            # C-Suite and Executive Leadership
            r'(?:is|was|as|serves?\s+as|joined\s+as|appointed\s+as|named\s+as)?\s*(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Chief\s+[A-Za-z]+\s+Officer|CEO|CTO|CFO|COO|CIO|CMO|CHRO|CSO|CPO|President|Vice\s+President|Executive\s+Vice\s+President|Senior\s+Vice\s+President|Global\s+Vice\s+President|Regional\s+Vice\s+President|SVP|EVP|VP|AVP|Managing\s+Director|Executive\s+Director|General\s+Manager|Country\s+Manager|Regional\s+Manager))',
            
            # Senior Management and Leadership
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Senior\s+Director|Group\s+Director|Department\s+Director|Program\s+Director|Project\s+Director|Division\s+Head|Department\s+Head|Business\s+Head|Unit\s+Head|Practice\s+Head|Center\s+Head|Function\s+Head|Senior\s+Manager|Principal\s+Manager))',
            
            # Technical Leadership
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Distinguished\s+Engineer|Principal\s+Engineer|Senior\s+Principal|Chief\s+Architect|Principal\s+Architect|Lead\s+Architect|Technical\s+Fellow|Senior\s+Fellow|Distinguished\s+Researcher|Principal\s+Scientist|Senior\s+Scientist|Technical\s+Director|Engineering\s+Director|Research\s+Director))',
            
            # Technology and Engineering
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Software\s+Engineer|Systems\s+Engineer|Data\s+Engineer|Cloud\s+Engineer|DevOps\s+Engineer|ML\s+Engineer|AI\s+Engineer|Security\s+Engineer|Full\s+Stack\s+Developer|Backend\s+Developer|Frontend\s+Developer|Software\s+Developer|Application\s+Developer|Mobile\s+Developer))',
            
            # Data and Analytics
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Data\s+Scientist|Analytics\s+Manager|Data\s+Analyst|Business\s+Analyst|Research\s+Analyst|Quantitative\s+Analyst|Machine\s+Learning\s+Engineer|AI\s+Researcher|Data\s+Architect|Analytics\s+Lead|Data\s+Lead|Insights\s+Manager))',
            
            # Product and Project Management
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Product\s+Manager|Program\s+Manager|Project\s+Manager|Product\s+Owner|Scrum\s+Master|Agile\s+Coach|Delivery\s+Manager|Release\s+Manager|Portfolio\s+Manager|Innovation\s+Manager))',
            
            # Business Functions
            r'(?:the\s+)?([A-Z][A-Za-z\s\-]+(?:Business\s+Development\s+Manager|Sales\s+Manager|Marketing\s+Manager|Operations\s+Manager|Finance\s+Manager|HR\s+Manager|Strategy\s+Manager|Consulting\s+Manager|Account\s+Manager|Customer\s+Success\s+Manager))'
        ]
        
        # Enhanced company patterns
        company_patterns = [
            # Standard company formats
            r'(?:at|with|for|from|of)\s+([A-Z][A-Za-z0-9\s&\.\-]+(?:Inc\.|Ltd\.|LLC|Corp\.|Corporation|Company|Group|Holdings|Technologies|Solutions|Services|International|Global|Digital|Software|Systems|Consulting|Capital|Partners|Ventures))',
            
            # Industry-specific companies
            r'([A-Z][A-Za-z0-9\s&\.\-]+(?:Bank(?:ing)?|Financial|Insurance|Healthcare|Pharma(?:ceuticals)?|Medical|Tech(?:nologies)?|Digital|Cyber|Analytics|Consulting|Manufacturing|Industries|Energy|Media|Retail))',
            
            # Company with location
            r'([A-Z][A-Za-z0-9\s&\.\-]+(?:\s+(?:India|US|UK|Global|Asia|Europe|Pacific)))',
            
            # Generic company patterns
            r'(?:joined|works?\s+(?:at|with|for)|employed\s+by|based\s+(?:at|in))\s+([A-Z][A-Za-z0-9\s&\.\-]+)',
            r'(?:the|a|an)\s+([A-Z][A-Za-z0-9\s&\.\-]+(?:\s+(?:company|organization|enterprise|firm|startup)))',
            r'(?:subsidiary|division|unit|branch)\s+of\s+([A-Z][A-Za-z0-9\s&\.\-]+)'
        ]

        def get_extended_context(doc, sent_index, window_size=3):
            """Get extended context around a sentence with configurable window size."""
            sentences = list(doc.sents)
            start_idx = max(0, sent_index - window_size)
            end_idx = min(len(sentences), sent_index + window_size + 1)
            
            context = {
                'text': ' '.join(sent.text for sent in sentences[start_idx:end_idx]),
                'prev_context': ' '.join(sent.text for sent in sentences[start_idx:sent_index]) if start_idx < sent_index else "",
                'current': sentences[sent_index].text,
                'next_context': ' '.join(sent.text for sent in sentences[sent_index+1:end_idx]) if sent_index+1 < end_idx else ""
            }
            return context

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
            if score >= 5:
                confidence = "very_high"
            elif score >= 4:
                confidence = "high"
            elif score >= 3:
                confidence = "medium"
            
            return {
                'is_valid': score >= 3,  # Lowered threshold from 5 to 3
                'score': score,
                'confidence': confidence
            }

        # Process text with enhanced context
        sentences = list(doc.sents)
        for i, sent in enumerate(sentences):
            for ent in sent.ents:
                if ent.label_ == "PERSON":
                    name = self.clean_name(ent.text)
                    if not name or name in seen_names:
                        continue
                    
                    # Get extended context
                    context = get_extended_context(doc, i)
                    
                    # Extract designations and companies with context
                    designations = []
                    companies = []
                    
                    # Process patterns with context awareness
                    for pattern in designation_patterns:
                        matches = re.finditer(pattern, context['text'], re.IGNORECASE)
                        for match in matches:
                            designation = self.clean_text(match.group(1))
                            if designation and len(designation.split()) <= 7:
                                designations.append(designation)
                    
                    for pattern in company_patterns:
                        matches = re.finditer(pattern, context['text'])
                        for match in matches:
                            company = self.clean_text(match.group(1))
                            if company and len(company.split()) <= 6:
                                companies.append(company)
                    
                    # Debug information for each potential profile
                    if name and (designations or companies):
                        st.write(f"Found potential profile: {name}")
                        if designations:
                            st.write(f"Designations: {', '.join(designations)}")
                        if companies:
                            st.write(f"Companies: {', '.join(companies)}")
                    
                    # Validate and create profile
                    if designations or companies:
                        validation_result = validate_profile(
                            name,
                            designations[0] if designations else "",
                            companies[0] if companies else "",
                            context
                        )
                        
                        if validation_result['is_valid']:
                            search_terms = [name]
                            if designations:
                                search_terms.extend(designations[0].split()[:2])
                            if companies:
                                search_terms.append(companies[0].split()[0])
                            
                            linkedin_url = (
                                "https://www.linkedin.com/search/results/people/?"
                                f"keywords={'+'.join(search_terms).replace(' ', '%20')}"
                            )
                            
                            profile = {
                                "name": name,
                                "designation": ' | '.join(designations) if designations else "",
                                "company": ' | '.join(companies) if companies else "",
                                "linkedin_search": linkedin_url,
                                "confidence": validation_result['confidence'],
                                "score": validation_result['score']
                            }
                            
                            profiles.append(profile)
                            seen_names.add(name)
        
        if not profiles:
            st.warning("No valid profiles found. Try with different content or ensure the text contains professional profiles.")
            st.info("Tips for better results:")
            st.info("1. Make sure the text contains full names (first and last name)")
            st.info("2. Include professional titles or designations")
            st.info("3. Mention company names or organizations")
            st.info("4. Provide context about the person's role or position")
        
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
                        if text:
                            st.success(f"✅ Successfully retrieved article content ({len(text)} characters)")
                            
                            # Display a sample of the extracted content
                            st.info("Sample of extracted content:")
                            st.text(text[:500] + "..." if len(text) > 500 else text)
                            
                            profiles = extractor.extract_profiles(text)
                            
                            # Apply deduplication if enabled
                            if deduplicate:
                                unique_profiles = []
                                for profile in profiles:
                                    if not extractor.is_duplicate(profile['name'], profile['company']):
                                        unique_profiles.append(profile)
                                        extractor.add_to_cache(profile['name'], profile['company'])
                                profiles = unique_profiles
                            
                            display_results(profiles)
                        else:
                            st.warning("No content could be extracted from the URL. Try:")
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
                    
                    # Apply deduplication if enabled
                    if deduplicate:
                        unique_profiles = []
                        for profile in profiles:
                            if not extractor.is_duplicate(profile['name'], profile['company']):
                                unique_profiles.append(profile)
                                extractor.add_to_cache(profile['name'], profile['company'])
                        profiles = unique_profiles
                    
                    display_results(profiles)
            else:
                st.warning("⚠️ Please enter some text")

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
