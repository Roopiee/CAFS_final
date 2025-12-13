"""
app/agents/verification/scanner.py
Handles web fetching using HTTPX and Playwright.
"""
import httpx
import asyncio
import random
import logging
import os
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
]

async def fetch_page_text(url: str, use_browser: bool = True, force_browser: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Scans a URL.
    Args:
        force_browser: If True, skips the fast HTTPX check and goes straight to Playwright.
    Returns:
        (text_content, screenshot_path)
    """
    # 1. Try Fast Fetch (HTTPX) - ONLY if not forced to use browser
    if not force_browser:
        text = await _fetch_httpx(url)
        if text and len(text) > 500:
            return text, None
        
    # 2. Try Browser Fetch (Playwright)
    if use_browser or force_browser:
        if not force_browser:
            logger.info(f"HTTPX failed for {url}, trying Playwright...")
        return await _fetch_playwright(url)
    
    return None, None

async def _fetch_httpx(url: str) -> Optional[str]:
    """Helper: Fast HTTP request"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
    except Exception:
        pass
    return None

async def _fetch_playwright(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Helper: Full Browser + Screenshot"""
    screenshot_path = None
    content = None
    
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            
            try:
                try:
                    # Primary attempt: Wait for network idle (most reliable for content)
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except Exception:
                    # Fallback: If network is busy (ads/tracking), just wait for DOM
                    logger.warning(f"Networkidle timed out for {url}, falling back to domcontentloaded.")
                    try:
                        # Ensure we at least have the DOM
                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                        # Give it a moment to hydrate/render content if networkidle failed
                        await page.wait_for_timeout(5000)
                    except Exception:
                        logger.warning(f"DOM load also timed out for {url}, proceeding with whatever is rendered.")

                # Snapshot Logic
                proof_dir = os.path.join(os.getcwd(), "proofs")
                os.makedirs(proof_dir, exist_ok=True)
                filename = f"proof_{int(time.time())}.png"
                screenshot_path = os.path.join(proof_dir, filename)
                
                await page.screenshot(path=screenshot_path, full_page=True)
                content = await page.inner_text("body")
                
            finally:
                await browser.close()
            
            return content, screenshot_path
            
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return None, None