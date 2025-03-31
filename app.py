# ... (previous imports remain the same)

class PersonExtractor:
    def __init__(self, text: str):
        self.text = text
        self.doc = nlp(text)
        
    def is_valid_name(self, name: str) -> bool:
        """Validate person names with balanced rules"""
        # Basic validation
        if not name or len(name) < 4:
            return False
            
        words = name.split()
        
        # Must have at least 2 words
        if len(words) < 2:
            return False
            
        # First word must be capitalized
        if not words[0][0].isupper():
            return False
            
        # Check for obvious non-names
        if name.lower() in INVALID_TERMS:
            return False
            
        # No numbers or special characters (except hyphen and apostrophe)
        if re.search(r'[^a-zA-Z\s\'-]', name):
            return False
            
        # Check for common false positives
        false_positives = [
            'breaking news', 'latest news', 'top stories',
            'read more', 'click here', 'find out'
        ]
        if name.lower() in false_positives:
            return False
            
        return True
        
    def extract_quote(self, name: str) -> Optional[str]:
        """Extract quotes with improved patterns"""
        quote_patterns = [
            # Direct quotes
            rf'"{name}[^"]*"|{name}[^"]*"([^"]+)"',
            # Said/says patterns
            rf"{name}\s+(?:said|says|stated|added|noted|mentioned)\s*(?:that\s+)?([^.!?]+[.!?])",
            # According to patterns
            rf'According to\s+{name},?\s+([^.!?]+[.!?])',
            # Reverse attribution
            rf'"([^"]+)"\s*(?:said|says|stated)\s+{name}'
        ]
        
        for pattern in quote_patterns:
            matches = re.finditer(pattern, self.text, re.IGNORECASE)
            for match in matches:
                quote = match.group(1) if len(match.groups()) > 0 else match.group(0)
                quote = quote.strip('"').strip()
                
                # Basic quote validation
                if (10 < len(quote) < 500 and  # More flexible length
                    not any(term in quote.lower() for term in INVALID_TERMS)):
                    return quote
        return None
        
    def extract_role_info(self, name: str) -> Dict[str, Optional[str]]:
        """Extract designation and company with improved patterns"""
        result = {"designation": None, "company": None}
        
        # Find context around name (expanded window)
        name_idx = self.text.find(name)
        if name_idx != -1:
            context_start = max(0, name_idx - 150)
            context_end = min(len(self.text), name_idx + 150)
            context = self.text[context_start:context_end]
            
            # Enhanced designation patterns
            designation_patterns = [
                r"(?:is|was|as)\s+(?:the\s+)?(?:new\s+)?([A-Z][a-z]+\s+)?(?:CEO|Chief|President|Director|Manager|Head|VP|Vice President|Founder|Executive|Lead|Senior|Principal)",
                r"(?:CEO|Chief|President|Director|Manager|Head|VP|Vice President|Founder|Executive)\s+(?:of|at|for)",
                r"(?:Senior|Lead|Principal)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?"
            ]
            
            for pattern in designation_patterns:
                designation_match = re.search(pattern, context, re.IGNORECASE)
                if designation_match:
                    result["designation"] = designation_match.group(0).strip()
                    break
            
            # Enhanced company patterns
            company_patterns = [
                r"(?:at|of|for)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
                r"joined\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)",
                r"with\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|\s|$)"
            ]
            
            for pattern in company_patterns:
                company_match = re.search(pattern, context)
                if company_match:
                    company = company_match.group(1).strip()
                    if (company not in INVALID_TERMS and 
                        len(company) > 2 and 
                        company[0].isupper()):
                        result["company"] = company
                        break
                    
        return result
        
    def extract_people(self) -> List[Dict]:
        """Extract person information with improved logic"""
        people_info = {}
        
        # First pass: collect all mentions
        for ent in self.doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                
                if self.is_valid_name(name):
                    if name not in people_info:
                        people_info[name] = {
                            "Name": name,
                            "Designation": None,
                            "Company": None,
                            "Quote": None,
                            "LinkedIn Search": None
                        }
                    
                    # Get role information
                    role_info = self.extract_role_info(name)
                    if role_info["designation"]:
                        people_info[name]["Designation"] = role_info["designation"]
                    if role_info["company"]:
                        people_info[name]["Company"] = role_info["company"]
                    
                    # Get quote
                    quote = self.extract_quote(name)
                    if quote:
                        people_info[name]["Quote"] = quote
        
        # Second pass: clean and format
        clean_results = []
        for name, info in people_info.items():
            # Include entries with any additional information
            if info["Designation"] or info["Quote"] or info["Company"]:
                # Create LinkedIn search URL
                search_terms = [name]
                if info["Company"]:
                    search_terms.append(info["Company"])
                if info["Designation"]:
                    # Add key terms from designation
                    key_terms = re.findall(r'(?:CEO|Chief|President|Director|Manager|Head|VP|Founder)', 
                                         info["Designation"], 
                                         re.IGNORECASE)
                    if key_terms:
                        search_terms.extend(key_terms)
                
                info["LinkedIn Search"] = f"https://www.google.com/search?q=LinkedIn+" + "+".join(term.replace(" ", "+") for term in search_terms)
                
                clean_results.append(info)
        
        return clean_results

# ... (rest of the code remains the same)
