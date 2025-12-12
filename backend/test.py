from sqlalchemy.sql._elements_constructors import true
from playwright.sync_api import sync_playwright

def process_certificate(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Going to: {url}")
        page.goto(url)

        try:
            print("Waiting for page content...")
            page.wait_for_load_state("networkidle")
            
            # --- STRATEGY 1: Take Screenshot IMMEDIATELY (Safety First) ---
            # We take the picture first so you have it even if text extraction fails
            page.screenshot(path="certificate_capture.png", full_page=True)
            print("✅ Screenshot saved as 'certificate_capture.png'")

            # --- STRATEGY 2: Visual Text Extraction ---
            # We look for the "Certificate Recipient:" label which we SAW in your screenshot
            print("Attempting to read text...")
            
            # Use a generic wait to ensure text is rendered
            page.wait_for_selector("text=Certificate", timeout=10000)

            # Get the full text of the page to parse with Python (More reliable than CSS selectors)
            full_text = page.inner_text("body")
            
            # Simple Python string parsing
            recipient = "Not Found"
            course = "Not Found"
            
            # Parse Recipient
            if "Certificate" in full_text:
                parts = full_text.split("Certificate")
                # The name is usually on the next line or right after
                recipient = parts[1].split("\n")[1].strip() 
                if not recipient: # If blank, try the next line
                    recipient = parts[1].split("\n")[2].strip()

            # Parse Course (It is usually the biggest header)
            # We try to grab the first H1 element
            if page.locator("h1").count() > 0:
                course = page.locator("h1").first.text_content().strip()

            print("-" * 30)
            print(f"🎓 Student Name: {recipient}")
            print(f"📚 Course Title: {course}")
            print("-" * 30)

        except Exception as e:
            print(f"❌ Extraction Error: {e}")
            # If it fails, we still dump the raw text so you can see what happened
            # print("DEBUG - Raw Page Text Snippet:", page.inner_text("body")[:500])

        finally:
            page.wait_for_timeout(3000)
            browser.close()

if __name__ == "__main__":
    link = "https://www.udemy.com/certificate/UC-9ba43c6a-3983-495c-beb2-329801af4557"
    process_certificate(link)