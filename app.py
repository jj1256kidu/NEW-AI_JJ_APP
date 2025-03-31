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
    page_title="NewsNex - From News to Next Opportunities",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 0;
    }
    .tagline {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .sub-tagline {
        font-size: 1.1rem;
        color: #6B7280;
        font-style: italic;
    }
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #1E40AF;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    .metric-title {
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        color: rgba(255, 255, 255, 0.9);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }
    .metric-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .st-emotion-cache-1y4p8pa {
        max-width: 100rem;
    }
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        }
        .metric-title {
            color: rgba(255, 255, 255, 0.95);
        }
    }
</style>
""", unsafe_allow_html=True)

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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
            for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'header', 'aside', 'meta']):
                element.decompose()
            
            text = ""
            
            # Method 1: Look for article content
            article = soup.find('article')
            if article:
                text = article.get_text(separator=' ', strip=True)
            
            # Method 2: Look for main content
            if not text:
                main_content = soup.find(['main', 'div'], class_=re.compile(r'content|article|post|story|body', re.I))
                if main_content:
                    text = main_content.get_text(separator=' ', strip=True)
            
            # Method 3: Look for paragraphs
            if not text:
                paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # Method 4: Get all text if nothing else worked
            if not text:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean the text
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s\'-]', ' ', text)
            text = ' '.join(word for word in text.split() if len(word) > 1)
            
            if not text:
                st.warning("Debug: No text extracted from the webpage")
                return ""
                
            return text.strip()
            
        except Exception as e:
            st.error(f"Debug: Error in get_clean_text_from_url: {str(e)}")
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
            r"(?:is|was|as)\s+(?:the\s+)?(?:new\s+)?([A-Z][a-z]+\s+)?(?:CEO|Chief|President|Director|Head|VP|Vice President|Founder|Executive)",
            r"(?:Senior|Global|Regional)?\s*(?:Director|Manager|Lead|Head|Chief|Officer)\s+(?:of|for|at)\s+[A-Z][A-Za-z\s]+",
            r"(?:CEO|CTO|CIO|CFO|COO|CHRO|CMO)\s+(?:and|&)?\s*(?:Co-founder|Founder|Director|President)?",
            r"(?:Managing|Executive|General)\s+(?:Director|Partner|Manager|Principal)",
            r"(?:Technical|Technology|Product|Program|Project)\s+(?:Director|Manager|Lead|Head|Architect)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return ""

    def extract_company(self, text):
        patterns = [
            r"(?:at|of|for|with)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
            r"joined\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
            r"([A-Z][A-Za-z0-9\s&]+?)(?:'s|')\s+(?:CEO|Chief|President|Director)",
            r"(?:works|working)\s+(?:at|for|with)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)"
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
    # Updated header with new branding
    st.markdown('<p class="main-title">🎯 NewsNex</p>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">Where News Sparks the Next Deal</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-tagline">🧠 Smarter Prospecting Starts with News</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    url = st.text_input("📰 Enter news article URL:", placeholder="https://example.com/article")
    
    if st.button("⚡ Extract Opportunities"):
        if not url:
            st.warning("⚠️ Please enter a URL to analyze.")
            return
            
        try:
            with st.spinner("🔍 Analyzing article for business opportunities..."):
                extractor = ProfileExtractor()
                
                text = extractor.get_clean_text_from_url(url)
                if not text:
                    st.warning("📭 No readable content found in the article.")
                    st.write("🔍 Debug: Please check if the URL is accessible and contains article content.")
                    return
                
                with st.expander("📝 View extracted content"):
                    st.text(text[:500] + "...")
                    
                profiles = extractor.extract_profiles(text)
                
                if profiles:
                    df = pd.DataFrame(profiles)
                    
                    st.markdown("### 📊 Opportunity Overview")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(
                            f"""
                            <div class="metric-card">
                                <div class="metric-icon">🎯</div>
                                <div class="metric-title">Total Prospects</div>
                                <div class="metric-value">{len(df)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with col2:
                        complete = len(df[df["Designation"].astype(bool) & df["Company"].astype(bool)])
                        st.markdown(
                            f"""
                            <div class="metric-card">
                                <div class="metric-icon">✅</div>
                                <div class="metric-title">Complete Profiles</div>
                                <div class="metric-value">{complete}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with col3:
                        st.markdown(
                            f"""
                            <div class="metric-card">
                                <div class="metric-icon">🏢</div>
                                <div class="metric-title">Companies</div>
                                <div class="metric-value">{df['Company'].nunique()}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    st.markdown("### 🎯 Identified Prospects")
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
                    
                    st.markdown("### 📥 Export Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📊 Download CSV",
                            csv,
                            "newsnex_prospects.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    with col2:
                        json_str = df.to_json(orient="records", indent=2)
                        st.download_button(
                            "📋 Download JSON",
                            json_str,
                            "newsnex_prospects.json",
                            "application/json",
                            use_container_width=True
                        )
                else:
                    st.info("ℹ️ No business prospects found in this article.")
                    
        except Exception as e:
            st.error(f"❌ Error processing article: {str(e)}")

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            Made with ❤️ by NewsNex | Transform News into Opportunities
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
