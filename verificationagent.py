"""
verification_agent.py
Core verification agent class for certificate validation
Strategy: Verify based on extraction quality + trusted domain due to anti-bot protection
"""

import httpx
import csv
import logging
from urllib.parse import urlparse
from typing import Optional, Tuple, List, Dict, Set
from difflib import SequenceMatcher
import re
import asyncio
import random

from app.config import config
from app.schemas import ExtractionResult, VerificationResult

logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


class VerificationAgent:
    """
    Enhanced verification agent that validates certificates by:
    1. Checking extraction quality (name, ID, issuer extracted)
    2. Verifying domain is trusted
    3. Attempting web verification (but not failing if blocked)
    """
    
    # URL patterns for major platforms  
    URL_PATTERNS = {
        "coursera": [
            "https://www.coursera.org/verify/{cert_id}",
            "https://www.coursera.org/account/accomplishments/certificate/{cert_id}",
        ],
        "udemy": [
            "https://www.udemy.com/certificate/{cert_id}",
            "https://ude.my/{cert_id}",
        ],
        "edx": [
            "https://credentials.edx.org/credentials/{cert_id}",
        ],
        "linkedin": [
            "https://www.linkedin.com/learning/certificates/{cert_id}",
        ],
        "google": [
            "https://skillshop.exceedlms.com/student/award/{cert_id}",
        ],
        "ibm": [
            "https://www.credly.com/badges/{cert_id}",
            "https://www.credly.com/organizations/ibm/badges/{cert_id}",
        ],
        "microsoft": [
            "https://learn.microsoft.com/en-us/users/{cert_id}/transcript",
        ],
        "credly": [
            "https://www.credly.com/badges/{cert_id}",
        ]
    }
    
    def __init__(self, csv_path: Optional[str] = None, use_playwright: bool = True):
        """Initialize the verification agent"""
        self.csv_path = csv_path or config.CSV_PATH
        self.use_playwright = use_playwright
        self.org_map, self.trusted_domains = self._load_trusted_sources()
        self.session_cache: Dict[str, str] = {}
        logger.info(f"✓ Loaded {len(self.org_map)} organizations, {len(self.trusted_domains)} trusted domains")

    def _load_trusted_sources(self) -> Tuple[dict, set]:
        """Load trusted organizations from CSV"""
        org_mapping = {}
        trusted_domains = set()
        
        try:
            with open(self.csv_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                
                for row in reader:
                    org_name = row.get("Organization Name", "").strip()
                    verify_url = row.get("Verification URL", "").strip()
                    
                    if verify_url:
                        if not verify_url.startswith(('http://', 'https://')):
                            verify_url = 'https://' + verify_url
                        
                        parsed = urlparse(verify_url)
                        domain = parsed.netloc.lower().replace("www.", "")
                        trusted_domains.add(domain)
                        
                        if org_name:
                            org_mapping[org_name.lower()] = verify_url
                
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
        
        # Add essential domains
        additional_domains = [
            "ude.my", "udemy.com", "coursera.org", "edx.org",
            "credentials.edx.org", "linkedin.com", "google.com",
            "skillshop.exceedlms.com", "credly.com"
        ]
        trusted_domains.update(additional_domains)
        
        return org_mapping, trusted_domains

    def _is_trusted_domain(self, url: str) -> bool:
        """Check if URL belongs to trusted domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            return domain in self.trusted_domains or any(
                domain.endswith(f".{trusted}") for trusted in self.trusted_domains
            )
        except:
            return False

    def _generate_verification_urls(self, url: str, cert_id: Optional[str], org_name: Optional[str]) -> List[str]:
        """Generate URL variations to try based on platform"""
        urls = []
        
        if url:
            urls.append(url)
        
        if org_name and cert_id:
            org_lower = org_name.lower()
            
            # Priority 1: Try to use CSV data (most accurate)
            if org_lower in self.org_map:
                base_url = self.org_map[org_lower]
                # Construct URL by appending cert_id
                if not base_url.endswith('/'):
                    constructed_url = base_url + '/' + cert_id
                else:
                    constructed_url = base_url + cert_id
                urls.append(constructed_url)
                logger.info(f"✓ Constructed URL from CSV: {constructed_url}")
            
            # Priority 2: Try hardcoded patterns as fallback
            for platform, patterns in self.URL_PATTERNS.items():
                if platform in org_lower:
                    for pattern in patterns:
                        try:
                            urls.append(pattern.format(cert_id=cert_id))
                        except:
                            pass
                    break
        
        return list(dict.fromkeys(urls))  # Remove duplicates

    def _fuzzy_match_name(self, name1: str, name2: str, threshold: float = 0.70) -> Tuple[bool, float]:
        """Perform fuzzy name matching"""
        if not name1 or not name2:
            return False, 0.0
        
        name1_clean = re.sub(r'[^a-z0-9\s]', '', name1.lower())
        name2_clean = re.sub(r'[^a-z0-9\s]', '', name2.lower())
        
        if name1_clean in name2_clean:
            return True, 1.0
        
        name1_parts = [p for p in name1_clean.split() if len(p) > 2]
        if all(part in name2_clean for part in name1_parts):
            return True, 0.95
        
        ratio = SequenceMatcher(None, name1_clean, name2_clean).ratio()
        return ratio >= threshold, ratio

    async def _fetch_with_httpx(self, url: str) -> Optional[str]:
        """Fetch with httpx and anti-bot headers"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                await asyncio.sleep(0.5)
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
        except:
            pass
        return None

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch with Playwright (if available)"""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=15000, wait_until='load')
                content = await page.inner_text("body")
                await browser.close()
                return content
        except:
            return None

    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """Try to fetch page content"""
        # Try httpx first (faster)
        content = await self._fetch_with_httpx(url)
        if content and len(content) > 200:
            return content
        
        # Try Playwright if enabled
        if self.use_playwright:
            return await self._fetch_with_playwright(url)
        
        return content

    async def verify(self, extraction_data: ExtractionResult) -> VerificationResult:
        """
        Main verification method
        
        Strategy: Verify through web crawling or mark as requiring manual verification
        1. If we have URL/ID → Try web verification
        2. If web fails → UNVERIFIED (requires manual check)
        
        We NEVER auto-verify without web confirmation (security risk!)
        """
        url = extraction_data.issuer_url
        cert_id = extraction_data.certificate_id
        org_name = extraction_data.issuer_name.value if extraction_data.issuer_name else None
        candidate_name = extraction_data.candidate_name
        
        logger.info(f"Verifying: {candidate_name}, {org_name}, {cert_id}")
        
        # Check extraction quality
        has_basic_extraction = bool(candidate_name and org_name)
        has_id_or_url = bool(cert_id or url)
        
        # Check if issuer is recognized (for better messaging)
        is_known_issuer = False
        if org_name:
            org_lower = org_name.lower()
            is_known_issuer = any(trusted in org_lower or org_lower in trusted 
                                 for trusted in ['udemy', 'coursera', 'edx', 'linkedin', 'google', 'microsoft', 'ibm'])
        
        logger.info(f"Extraction check - has_basic: {has_basic_extraction}, has_id_or_url: {has_id_or_url}, known_issuer: {is_known_issuer}")
        
        # Case 1: No URL or ID - Cannot verify
        if not has_id_or_url:
            if has_basic_extraction and is_known_issuer:
                return VerificationResult(
                    is_verified=False,
                    message=f"Certificate from {org_name} identified. However, no verification URL or certificate ID found on the document. Manual verification required by contacting the issuer directly.",
                    trusted_domain=True  # Known platform but can't auto-verify
                )
            else:
                return VerificationResult(
                    is_verified=False,
                    message="Incomplete extraction. Missing certificate ID, verification URL, or issuer information. Cannot verify.",
                    trusted_domain=False
                )
        
        # Case 2: We have URL/ID - Try web verification
        urls_to_try = self._generate_verification_urls(url, cert_id, org_name)
        
        if not urls_to_try:
            return VerificationResult(
                is_verified=False,
                message=f"Could not generate verification URL from available data. Manual verification required.",
                trusted_domain=is_known_issuer
            )
        
        primary_url = urls_to_try[0]
        is_trusted_domain = self._is_trusted_domain(primary_url)
        
        if not is_trusted_domain:
            return VerificationResult(
                is_verified=False,
                message=f"Domain not in trusted list: {primary_url}. Manual verification required.",
                trusted_domain=False
            )
        
        logger.info(f"✓ Domain trusted: {primary_url}")
        
        # Try web verification (this is the ONLY way to auto-verify)
        for idx, attempt_url in enumerate(urls_to_try[:2]):
            logger.info(f"Trying web verification ({idx+1}/2): {attempt_url}")
            
            if idx > 0:
                await asyncio.sleep(1)
            
            # Step 1: Try fast fetch with httpx
            page_content = await self._fetch_with_httpx(attempt_url)
            
            # Check if httpx result is sufficient
            match_found = False
            if page_content and candidate_name:
                is_match, similarity = self._fuzzy_match_name(candidate_name, page_content)
                if is_match:
                    match_found = True
                    logger.info(f"✓ Web verification SUCCESS (httpx)! Match: {similarity:.0%}")
                    return VerificationResult(
                        is_verified=True,
                        message=f"Certificate verified via web crawl. Name matched with {similarity:.0%} confidence at {attempt_url}",
                        trusted_domain=True
                    )
            
            # Step 2: If httpx failed to match (likely SPA/JS-heavy), try Playwright
            if not match_found and self.use_playwright:
                logger.info(f"httpx failed to find match, trying Playwright for {attempt_url}")
                page_content = await self._fetch_with_playwright(attempt_url)
                
                if page_content and candidate_name:
                    is_match, similarity = self._fuzzy_match_name(candidate_name, page_content)
                    if is_match:
                        logger.info(f"✓ Web verification SUCCESS (Playwright)! Match: {similarity:.0%}")
                        return VerificationResult(
                            is_verified=True,
                            message=f"Certificate verified via web crawl (browser). Name matched with {similarity:.0%} confidence at {attempt_url}",
                            trusted_domain=True
                        )
                    else:
                        logger.warning(f"Name not matched at {attempt_url} even with Playwright (similarity: {similarity:.0%})")
                else:
                    logger.warning(f"Could not fetch with Playwright: {attempt_url}")
        
        # Web verification failed - Cannot auto-verify for security
        logger.warning("Web verification failed - certificate UNVERIFIED")
        return VerificationResult(
            is_verified=False,
            message=f"Could not automatically verify via web crawl (anti-bot protection or name mismatch). Certificate appears to be from {org_name}. Manual verification recommended: {primary_url}",
            trusted_domain=True
        )

    def clear_cache(self):
        """Clear session cache"""
        self.session_cache.clear()