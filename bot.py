import feedparser
import time
import requests
from pyrogram import Client, filters, idle
from bs4 import BeautifulSoup
import asyncio
import os
import uuid
import nest_asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Telegram bot configuration
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg'

USER_ID = 6290483448  # Replace with the actual user ID
MAX_LINKS_PER_BATCH = 20
session_name = f"web_scraper_bot_{api_id}_{uuid.uuid4()}"
os.makedirs("./sessions", exist_ok=True)

app = Client(
    session_name,
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    workdir="./sessions"
)

SENT_LINKS_FILE = "sent_links.txt"
sent_links = set()

if os.path.exists(SENT_LINKS_FILE):
    with open(SENT_LINKS_FILE, 'r') as f:
        sent_links = set(f.read().splitlines())


def scrape_website(url):
    """Scrape magnet links from a dynamically loaded website."""
    try:
        # Set up Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Open the URL
        driver.get(url)
        time.sleep(3)  # Wait for the page to load fully

        # Find all anchor tags with magnet links
        links = [
            a.get_attribute('href')
            for a in driver.find_elements(By.TAG_NAME, 'a')
            if "magnet:?" in a.get_attribute('href')
        ]
        driver.quit()
        return links
    except Exception as e:
        print(f"Error scraping website: {str(e)}")
        return []


async def send_links_or_message(links):
    """Send magnet links or a message to the user."""
    if links:
        for i, link in enumerate(links[:MAX_LINKS_PER_BATCH]):
            formatted_link = f"**/qbleech {link}** \n**Tag:** `@Arisu_0007 6290483448`"
            await app.send_message(USER_ID, formatted_link)
            await asyncio.sleep(1)
    else:
        await app.send_message(USER_ID, "**Links Not Found!!**")


@app.on_message(filters.command("tmv"))
async def tmv(client, message):
    """
    Handle the /tmv command to scrape links and send a specified number of them.
    Usage:
    - /tmv <url>         -> Sends all links.
    - /tmv -i <number> <url> -> Sends the first <number> links.
    """
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            await message.reply_text("**Usage:** /tmv <url> or /tmv -i <number> <url>")
            return

        num_links = None
        url = None

        if "-i" in parts:
            # Extract index and URL
            try:
                index_flag = parts.index("-i")
                num_links = int(parts[index_flag + 1])  # Validate number of links
                url = parts[index_flag + 2]  # Extract URL
            except (ValueError, IndexError):
                await message.reply_text("**Usage:** /tmv -i <number> <url>\nThe number of links must be an integer.")
                return
        else:
            # URL without `-i`
            url = parts[-1]

        if not url.startswith("http"):
            await message.reply_text("**Please provide a valid URL.**")
            return

        # Scrape links from the provided URL
        links = scrape_website(url)
        if not links:
            await message.reply_text("**No links found on the provided URL.**")
            return

        # Send specific number of links or all
        if num_links:
            links_to_send = links[:num_links]
            await message.reply_text(f"**Sending the first {num_links} links:**")
        else:
            links_to_send = links
            await message.reply_text(f"**Sending all {len(links)} links:**")

        await send_links_or_message(links_to_send)

    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")


async def main():
    await app.start()
    print("Bot is running...")
    await idle()
    await app.stop()


# Apply nest_asyncio to avoid event loop issues
nest_asyncio.apply()

# Run the bot
asyncio.run(main())
