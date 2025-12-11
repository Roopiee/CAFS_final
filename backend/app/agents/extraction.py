import pytesseract
from PIL import Image
import io
import re

class ExtractionAgent:

    def __init__(self, mistral_api_key: str):
        self.client = MistralClient(api_key=mistral_api_key)

    def __init__(self):
        # Load known organizations for detection
        self.known_orgs = self._load_org_list(config.CSV_PATH)

    def _load_org_list(self, csv_path):
        """
        Loads just the list of organization names for matching.
        """
        orgs = []
        try:
            with open(csv_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    name = row.get("Organization Name", "").strip()
                    if name:
                        orgs.append(name)
            return orgs
        except FileNotFoundError:
            return ["Coursera", "Udemy", "edX", "LinkedIn", "IBM", "Google", "Udacity"]

    def extract(self, image_bytes: bytes) -> ExtractionResult:
        try:
            # ----------- OCR STEP -----------
            image = Image.open(io.BytesIO(image_bytes))
            raw_text = pytesseract.image_to_string(image, lang='eng')
            
            # 1. Try Standard Extraction (Look for "Presented to", etc.)
            name = self._find_candidate_name(raw_text)
            
            # 2. Fallback: If no name found, guess based on exclusion logic
            if not name:
                name = self._fallback_name_search(raw_text)

            # 3. Extract and Repair URL
            raw_url = self._find_url(raw_text)
            clean_url = self._repair_url(raw_url) if raw_url else None

            data = {
                "candidate_name": name,
                "certificate_id": self._find_certificate_id(raw_text),
                "issuer_url": clean_url, 
                "raw_text_snippet": raw_text[:300].replace("\n", " ") + "..."
            }
            return data

        except Exception as e:
            return {
                "candidate_name": None, 
                "certificate_id": None, 
                "issuer_url": None,
                "raw_text_snippet": f"Error: {str(e)}"
            }

    def _find_url(self, text: str):
        # Matches http, www, ude.my, coursera.org
        url_pattern = r'(?:https?://|www\.|ude\.my/|coursera\.org/)[^\s]+'
        matches = re.findall(url_pattern, text)
        if matches:
            # Clean up trailing punctuation often grabbed by OCR
            return matches[0].rstrip('.,])')
        return None

    def _repair_url(self, url: str) -> str:
        """
        Fixes common OCR confusion in URLs/IDs.
        Swaps 'l' -> '1' and 'O' -> '0' if they appear inside the ID part of a Udemy link.
        """
        if not url: return None
        
        # Specific Fix for Udemy Short Links (ude.my/...)
        if "ude.my/" in url:
            # Split base and ID. Example: ["https://ude.my/", "le9fad..."]
            parts = url.split("ude.my/")
            if len(parts) > 1:
                base = parts[0] + "ude.my/"
                id_part = parts[1]
                
                # Fix: Replace 'l' with '1' and 'O' with '0' in the ID section only
                new_id = id_part.replace('l', '1').replace('O', '0')
                return base + new_id
        
        return url

    def _find_certificate_id(self, text: str):
        # Udemy specific ID (UC-...)
        udemy_pattern = r'(UC-[a-zA-Z0-9-]+)'
        match = re.search(udemy_pattern, text)
        if match:
            return match.group(1)

        # Standard ID
        id_pattern = r'(?i)(?:id|number|no\.?|code|credential)\s*[:#-]?\s*([A-Z0-9-]{5,})'
        match = re.search(id_pattern, text)
        return match.group(1) if match else None

    def _find_candidate_name(self, text: str):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        triggers_before = ["this is to certify that", "presented to", "awarded to", "certifies that", "name:"]
        triggers_after = ["successfully completed", "has completed", "for successfully completing"]

        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check "After" triggers (Name is BEFORE this line)
            for trigger in triggers_after:
                if trigger in line_lower:
                    if line_lower.startswith(trigger):
                         if i > 0: return self._clean_name(lines[i-1])
                    else:
                        return self._clean_name(line_lower.split(trigger)[0])

            # Check "Before" triggers (Name is AFTER this line)
            for trigger in triggers_before:
                if trigger in line_lower:
                    parts = line.split(trigger) 
                    if len(parts) > 1 and len(parts[1].strip()) > 3:
                        return self._clean_name(parts[1])
                    if i + 1 < len(lines):
                        return self._clean_name(lines[i+1])
        return None

    def _fallback_name_search(self, text: str):
        """
        Emergency Logic: Improved Blacklist to ignore course names and boilerplate.
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # INCREASED BLACKLIST to filter out noise
        blacklist = [
            "certificate", "completion", "instructors", "date", "number", "id:", "url:", 
            "course", "bootcamp", "bootcanpp", "complete", "language", "udemy", "coursera", "verify",
            "reference", "google", "president", "director", "chairman", "founder", "ceo",
            "programming", "python", "java", "data", "science", "introduction", "fundamentals",
            "beginner", "advanced", "masterclass", "development", "web", "design"
        ]

        possible_names = []

        for line in lines:
            line_lower = line.lower()
            
            # 1. Skip lines with blacklisted words
            if any(word in line_lower for word in blacklist):
                continue
            
            # 2. Skip lines that are too short or too long
            if len(line) < 4 or len(line) > 50:
                continue

            # 3. Skip lines that look like dates or raw numbers
            if re.search(r'\d', line): 
                continue

            possible_names.append(line)

        if possible_names:
            return self._clean_name(possible_names[0])
        
        return None

    def _clean_name(self, name_str: str):
        # Remove Date noise
        name_str = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}', '', name_str, flags=re.IGNORECASE)
        # Remove trailing punctuation/OCR noise
        name_str = re.sub(r'[^a-zA-Z\s\.]+$', '', name_str)
        return name_str.strip().title()