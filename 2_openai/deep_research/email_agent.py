import os
import base64
import datetime
import traceback
from pathlib import Path
from typing import Dict

import requests
from playwright.async_api import async_playwright
from agents import Agent, function_tool


REPORTS_DIR = Path(__file__).parent / "reports"

async def _html_to_jpeg_bytes(html_content: str) -> bytes:
    """Render a full-page JPEG screenshot of the HTML document entirely in memory.
    Uses a headless Chromium browser via Playwright with full_page=True so the
    entire document height is captured — no cropping, no temp files.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
     
        await page.set_content(html_content, wait_until="networkidle")
        jpeg_bytes = await page.screenshot(full_page=True, type="jpeg", quality=85)
     
        await browser.close()
    return jpeg_bytes


@function_tool
async def send_email(subject: str, html_body: str, summary: str) -> Dict[str, str]:
    """Render the HTML report as a JPEG image, attach it to a Pushover notification,
    and also save the original HTML file locally.

    Args:
        subject: The report title / subject line.
        html_body: A complete HTML document (including <!DOCTYPE html>, <html>, <head>,
                   <body> tags) with nicely styled report content.
        summary: A brief plain-text summary (≤ 500 chars) for the notification body.
    """
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_url = "https://api.pushover.net/1/messages.json"

    # --- Persist HTML + render JPEG ---
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject = "".join(c if c.isalnum() or c in " _-" else "_" for c in subject)[:60]

    html_path = REPORTS_DIR / f"{timestamp}_{safe_subject}.html"
    html_path.write_text(html_body, encoding="utf-8")
    print(f"HTML report saved to: {html_path}")

    # --- Render full-page JPEG entirely in memory (no cropping) ---
    jpeg_b64: str | None = None
    try:
        jpeg_bytes = await _html_to_jpeg_bytes(html_body)
        jpeg_b64 = base64.b64encode(jpeg_bytes).decode("ascii")
        print(f"Full-page JPEG rendered in memory ({len(jpeg_bytes):,} bytes)")
    
    except Exception:
        print("WARNING: HTML→JPEG conversion failed — sending notification without image.")
        traceback.print_exc()

    # --- Send Pushover notification ---
    print(f"Sending Pushover notification: {subject}")
    data: dict = {
        "user": pushover_user,
        "token": pushover_token,
        "title": subject,
        "message": summary,
    }
    if jpeg_b64:
        data["attachment_base64"] = jpeg_b64
        data["attachment_type"] = "image/jpeg"

    response = requests.post(pushover_url, data=data)
    print(f"Pushover response [{response.status_code}]: {response.text}")

    if response.ok:
        return {"status": "success", "html_path": str(html_path)}
    return {"status": "error", "details": response.text}


INSTRUCTIONS = """You are able to send a nicely HTML formatted report notification based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one notification with:

1. subject: A concise, descriptive title for the report.

2. html_body: A complete, well-formatted HTML document. It will be rendered as a JPEG image
   attached to the notification, so make it visually polished:
   - Include <!DOCTYPE html>, <html>, <head> (with <meta charset="utf-8"> and <title>), and <body>.
   - Use a clean sans-serif font, good contrast, and clear visual hierarchy.
   - Use <h1>, <h2>, <h3>, <p>, <ul>, <li>, <table> with inline CSS for professional styling.
   - Set a white background and comfortable padding on the body.
   - Avoid very wide fixed widths; use max-width: 1100px on the body so the render fits nicely.

3. summary: A short plain-text summary (2–5 sentences, under 500 characters) of the key findings.
   This appears as the notification message text alongside the image attachment."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
