import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    artifact_dir = "/config/.gemini/antigravity/brain/77ced538-db19-466f-9ed3-60e7bb7c8aa1"
    os.makedirs(artifact_dir, exist_ok=True)
    video_dir = os.path.join(artifact_dir, "video_temp")
    os.makedirs(video_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=video_dir,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print("Navigating to http://localhost:8080...")
        await page.goto("http://localhost:8080")
        await page.wait_for_timeout(2000)

        print("Clicking prompt chip 1...")
        chips = await page.query_selector_all(".chip")
        if chips:
            await chips[0].click()
            await page.wait_for_timeout(500)
            await page.click("button[type='submit']")
        else:
            await page.fill("input#input", "Show me the burger menu")
            await page.click("button[type='submit']")

        print("Waiting for response to 1st prompt...")
        await page.wait_for_function("""
            () => {
                const bubbles = document.querySelectorAll('.msg.agent .bubble');
                if (bubbles.length === 0) return false;
                const last = bubbles[bubbles.length - 1];
                return last.textContent !== '…' && last.textContent.length > 5;
            }
        """, timeout=45000)
        await page.wait_for_timeout(4000)

        print("Sending 2nd prompt (Image Generation)...")
        await page.fill("input#input", "Generate a gourmet marketing photo of our Valley View Double Smash Burger with melted cheddar, bacon, and house sauce.")
        await page.wait_for_timeout(1000)
        await page.click("button[type='submit']")

        print("Waiting for response to 2nd prompt...")
        await page.wait_for_function("""
            () => {
                const bubbles = document.querySelectorAll('.msg.agent .bubble');
                if (bubbles.length < 2) return false;
                const last = bubbles[bubbles.length - 1];
                return last.textContent !== '…' && last.textContent.length > 5;
            }
        """, timeout=60000)
        await page.wait_for_timeout(6000)

        await page.close()
        await context.close()
        await browser.close()

        videos = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith(".webm")]
        if videos:
            target_path = os.path.join(artifact_dir, "demo_video.webm")
            os.rename(videos[0], target_path)
            print("Demo video successfully saved to:", target_path)

if __name__ == "__main__":
    asyncio.run(main())
