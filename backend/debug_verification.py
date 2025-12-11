import asyncio
import re
from playwright.async_api import async_playwright

async def fetch_and_check_playwright():
    url = "https://verify.w3schools.com/1MLSETIMEL"
    candidate_name = "Your Name"
    
    print(f"Fetching {url} with Playwright...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000, wait_until='networkidle')
            content = await page.inner_text("body")
            print(f"Content Length: {len(content)}")
            
            # Check for name
            name1_clean = re.sub(r'[^a-z0-9\s]', '', candidate_name.lower())
            content_clean = re.sub(r'[^a-z0-9\s]', '', content.lower())
            
            if name1_clean in content_clean:
                print("Match found (exact/clean) with Playwright!")
            else:
                print("Match NOT found with Playwright.")
                print("Content snippet:", content[:500])
            
            await browser.close()
    except Exception as e:
        print(f"Error with Playwright: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_and_check_playwright())
