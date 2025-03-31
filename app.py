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

# [Previous CSS styles remain unchanged]
# ... (Keep all the CSS styling from the previous version)

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
            'conference', 'summit', 'meeting', 'webinar', 'seminar',
            
            # Products/Services
            'product', 'service', 'solution', 'platform', 'system',
            'software', 'hardware', 'device', 'application', 'app'
        }
        
        # Company suffixes for validation
        self.company_suffixes = {
            'ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation',
            'llc', 'llp', 'company', 'co', 'group', 'holdings', 'plc',
            'technologies', 'technology', 'solutions', 'services',
            'ventures', 'capital', 'partners', 'industries', 'enterprises'
        }
    def clean_name(self, name):
        """Clean and validate person name."""
        if not name or len(name) < 3 or len(name) > 40:
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

    def clean_company(self, company):
        """Clean and validate company name."""
        if not company or len(company) < 2:
            return None
            
        company = company.strip()
        
        # Remove common article prefixes
        company = re.sub(r'^(at|with|for|in|of)\s+', '', company, flags=re.IGNORECASE)
        
        # Check for company suffixes
        has_suffix = any(suffix.lower() in company.lower() for suffix in self.company_suffixes)
        
        # Must start with capital letter
        if not company[0].isupper():
            return None
            
        # Remove any quoted text
        company = re.sub(r'".*?"', '', company)
        company = re.sub(r"'.*?'", '', company)
        
        # Clean up extra spaces
        company = ' '.join(company.split())
        
        return company if has_suffix or len(company.split()) > 1 else None

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
                
                # Get context around the name
                start = max(0, ent.start_char - 200)
                end = min(len(text), ent.end_char + 200)
                context = text[start:end].lower()
                
                # Extract designations and companies
                raw_designations = self.extract_designations(context)
                raw_companies = self.extract_companies(context)
                
                # Clean and standardize designations
                designations = [self.standardize_designation(d) for d in raw_designations]
                designations = [d for d in designations if d]
                
                # Clean companies
                companies = [self.clean_company(c) for c in raw_companies]
                companies = [c for c in companies if c]
                
                # Only include profiles with at least one designation or company
                if designations or companies:
                    linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}"
                    
                    profile = {
                        "name": name,
                        "designations": list(set(designations)),
                        "companies": list(set(companies)),
                        "linkedin_search": linkedin_url
                    }
                    
                    profiles.append(profile)
                    seen_names.add(name)
        
        return profiles

    def extract_designations(self, text):
        """Extract designations from text."""
        designations = []
        
        # Use regex patterns for designation extraction
        patterns = [
            r'(?i)(Chief\s+[A-Za-z]+\s+Officer|CEO|CTO|CFO|COO|CIO|CMO|CPO)',
            r'(?i)(Managing\s+Director|Director|MD|Board\s+Director)',
            r'(?i)(Vice\s+President|President|VP|SVP|EVP)',
            r'(?i)(Founder|Co-founder|Chairman)',
            r'(?i)(Head\s+of\s+[A-Za-z\s]+)',
            r'(?i)(Senior\s+[A-Za-z]+\s+Manager|Manager)',
            r'(?i)(Lead\s+[A-Za-z]+|Team\s+Lead)',
            r'(?i)(Senior\s+[A-Za-z]+|Principal\s+[A-Za-z]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                designation = match.group().strip()
                if designation:
                    designations.append(designation)
        
        return list(set(designations))

    def extract_companies(self, text):
        """Extract company names from text."""
        companies = []
        
        patterns = [
            r'(?i)(?:at|with|for|in|of)\s+([A-Z][A-Za-z0-9\s&]+(?:' + '|'.join(self.company_suffixes) + '))',
            r'(?i)([A-Z][A-Za-z0-9\s&]+(?:' + '|'.join(self.company_suffixes) + '))',
            r'(?i)(?:joined|works\s+at|employed\s+by)\s+([A-Z][A-Za-z0-9\s&]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                company = match.group(1).strip() if len(match.groups()) > 0 else match.group().strip()
                if company:
                    companies.append(company)
        
        return list(set(companies))

# [Previous main() function and display_results() function remain unchanged]
# ... (Keep the main() and display_results() functions from the previous version)

if __name__ == "__main__":
    main()
