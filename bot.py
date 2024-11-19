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
from datetime import datetime, timedelta

# Telegram bot configuration
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg'

# The user ID where the RSS feed links should be sent
USER_ID = 6290483448  # Replace with the actual user ID

# URL of the RSS feed to monitor
RSS_FEED_URL = 'https://www.1tamilmv.wf/index.php?/discover/all.xml'

# Maximum number of links to send in one batch to avoid Telegram rate limit
MAX_LINKS_PER_BATCH = 20  # Adjust this number based on your needs (default is 5)

session_name = f"web_scraper_bot_{api_id}_{uuid.uuid4()}"
os.makedirs("./sessions", exist_ok=True)

app = Client(
    session_name,
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
    workdir="./sessions"
)

# Path to store the sent links in a file (to persist the sent state)
SENT_LINKS_FILE = "sent_links.txt"

# Create a set to store previously sent links
sent_links = set()

# Load sent links from the file if it exists
if os.path.exists(SENT_LINKS_FILE):
    with open(SENT_LINKS_FILE, 'r') as f:
        sent_links = set(f.read().splitlines())

# To keep track of the last processed RSS entry
last_processed_entry = None

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
        print(f"Error scraping website: {str(e)}")
        return []

async def send_links_or_message(links):
    """Send the magnet links to the specified user or notify if no links are found."""
    if links:
        # Limit the number of links to send in one batch to avoid rate limits
        for i, link in enumerate(links[:MAX_LINKS_PER_BATCH]):
            formatted_link = f"**/qbleech {link}** \n**Tag:** `@Arisu_0007 6290483448`"
            await app.send_message(USER_ID, formatted_link)
            await asyncio.sleep(1)  # Small delay to avoid rate limits
    else:
        await app.send_message(USER_ID, "**Links Not Found!!**")

async def check_rss_feed():
    """Check the RSS feed for new links and scrape them for additional links."""
    global sent_links, last_processed_entry
    feed = feedparser.parse(RSS_FEED_URL)

    # If this is the first time or after an app restart, set last_processed_entry to the latest in the feed
    if not last_processed_entry:
        last_processed_entry = feed.entries[0].link

    # Get the current time
    current_time = datetime.now()

    for entry in feed.entries:
        link = entry.link
        published_time = datetime(*entry.published_parsed[:6])

        # Check if the link is within the last hour
        if (current_time - published_time) > timedelta(hours=1):
            print(f"Skipping old link: {link}")
            continue

        # If we already processed this link or it's older than the last processed entry, skip it
        if link in sent_links or entry.link <= last_processed_entry:
            continue

        # Scrape the link from RSS for magnet links
        scraped_links = scrape_website(link)
        await send_links_or_message(scraped_links)  # Send to the specified user
        sent_links.add(link)  # Add to the sent set to avoid duplicates

        # Save the sent links to the file
        with open(SENT_LINKS_FILE, 'a') as f:
            f.write(link + '\n')

        # Update last processed entry to the current one
        last_processed_entry = link

@app.on_message(filters.command("tmv"))
async def tmv(client, message):
    """
    Handle the /tmv command to scrape links from a URL and send a specific number of links.
    Usage examples:
      /tmv <url>         - Sends all links from the URL.
      /tmv -i <number> <url> - Sends only the specified number of links from the URL.
    """
    try:
        # Split the message text into parts
        parts = message.text.split()

        if len(parts) < 2:
            await message.reply_text("**Usage:** /tmv <url> or /tmv -i <number> <url>")
            return

        # Check if the `-i` flag is present
        if "-i" in parts:
            index_flag = parts.index("-i")
            if len(parts) <= index_flag + 2:
                # Insufficient arguments after `-i`
                await message.reply_text("**Usage:** /tmv -i <number> <url>")
                return

            try:
                num_links = int(parts[index_flag + 1])  # Number of links to send
                url = parts[index_flag + 2]  # URL to scrape
            except ValueError:
                await message.reply_text("**The number of links must be an integer.**")
                return
        else:
            # If no `-i` flag, treat the last part as the URL
            url = parts[-1]
            num_links = None  # Send all links

        # Scrape links from the provided URL
        links = scrape_website(url)
        if not links:
            await message.reply_text("**No links found on the provided URL.**")
            return

        # If `-i` was used, limit the number of links to send
        if num_links:
            links_to_send = links[:num_links]
            await message.reply_text(f"**Sending the first {num_links} links:**")
        else:
            links_to_send = links
            await message.reply_text(f"**Sending all {len(links)} links:**")

        # Send the links
        await send_links_or_message(links_to_send)

    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")

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
