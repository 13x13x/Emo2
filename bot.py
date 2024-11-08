import feedparser
import time
import requests
from pyrogram import Client, filters
from bs4 import BeautifulSoup
import asyncio
import os
import uuid
import nest_asyncio
import re

# Telegram bot configuration
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg'
CHAT_ID = '5549620776'  # Replace with your chat ID

# URL of the RSS feed to monitor
RSS_FEED_URL = 'https://rss.app/feeds/FFh0vlIMaf9K5TPJ.xml'

session_name = f"web_scraper_bot_{api_id}_{uuid.uuid4()}"
os.makedirs("./sessions", exist_ok=True)

app = Client(
    session_name,
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    workdir="./sessions"
)

# Create a set to store previously sent links
sent_links = set()

def scrape_website(url):
    """Scrape magnet links from the provided URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True)
                     if a['href'].startswith("magnet:?xt")]
            return links
        else:
            return []
    except Exception as e:
        return []

async def send_links_or_message(chat_id, links):
    """Send the magnet links to the bot or notify if no links are found."""
    if links:
        for link in links:
            formatted_link = f"**/qbleech {link}** \n**Tag:** `@Arisu_0007 5549620776`"
            await app.send_message(chat_id, formatted_link)
            await asyncio.sleep(1)
    else:
        await app.send_message(chat_id, "**Links Not Found!!**")

async def check_rss_feed():
    """Check the RSS feed for new links and scrape them for additional links."""
    global sent_links
    feed = feedparser.parse(RSS_FEED_URL)

    for entry in feed.entries:
        link = entry.link
        # Send the link if it hasn't been sent before
        if link not in sent_links:
            # Scrape the link from RSS for magnet links
            scraped_links = scrape_website(link)
            await send_links_or_message(CHAT_ID, scraped_links)
            sent_links.add(link)  # Add to the sent set to avoid duplicates

@app.on_message(filters.command("tmv"))
async def tmv(client, message):
    """Handle the /tmv command by scraping the provided URL."""
    try:
        url_match = re.search(r'(https?://\S+)', message.text)
        if url_match:
            url = url_match.group(1)
            links = scrape_website(url)
            await send_links_or_message(message.chat.id, links)
        else:
            await message.reply_text("**Please provide a valid URL after the command, like this:** /tmv <url>")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

async def main():
    """Main loop to check RSS feed every 900 seconds and handle bot commands."""
    await app.start()
    try:
        while True:
            await check_rss_feed()
            await asyncio.sleep(900)  # Wait for 900 seconds (15 minutes)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await app.stop()

# Apply nest_asyncio to avoid event loop issues
nest_asyncio.apply()

# Run the main function
asyncio.run(main())
