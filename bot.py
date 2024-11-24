import asyncio
import os
import uuid
import aiohttp
import feedparser
from datetime import datetime, timedelta
from pyrogram import Client, filters, idle
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Telegram bot configuration
API_ID = 24972774
API_HASH = '188f227d40cdbfaa724f1f3cd059fd8b'
BOT_TOKEN = '6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg'
USER_ID = 6290483448  # Replace with the actual user ID
MAX_LINKS_PER_BATCH = 20
RSS_FEED_URL = 'https://www.1tamilmv.at/index.php?/discover/all.xml'

# Session configuration
session_name = f"web_scraper_bot_{API_ID}_{uuid.uuid4()}"
os.makedirs("./sessions", exist_ok=True)

app = Client(
    session_name,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="./sessions"
)

SENT_LINKS_FILE = "sent_links.txt"
sent_links = set()

# Load sent links from file
if os.path.exists(SENT_LINKS_FILE):
    with open(SENT_LINKS_FILE, 'r') as f:
        sent_links = set(f.read().splitlines())


async def scrape_website(url):
    """Scrape magnet and file links from the provided URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    # Extract both magnet and file links
                    magnet_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("magnet:?xt")]
                    file_links = [a['href'] for a in soup.find_all('a', href=True) if "applications/core/interface/file" in a['href']]
                    return magnet_links + file_links
                else:
                    logging.error(f"Non-200 response code: {response.status} for URL: {url}")
                    return []
    except Exception as e:
        logging.error(f"Error scraping website {url}: {str(e)}")
        return []


async def fetch_rss_links():
    """Fetch and process new links from the RSS feed."""
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        new_links = []

        for entry in feed.entries:
            link = entry.link
            if link not in sent_links:
                logging.info(f"New link found: {link}")
                new_links.append(link)
                sent_links.add(link)

        # Save sent links to file
        with open(SENT_LINKS_FILE, 'w') as f:
            f.write("\n".join(sent_links))

        return new_links
    except Exception as e:
        logging.error(f"Error fetching RSS feed: {str(e)}")
        return []


async def send_links_or_message(links):
    """Send magnet and file links or a message to the user."""
    if links:
        for i, link in enumerate(links[:MAX_LINKS_PER_BATCH]):
            formatted_link = f"**/qbleech {link}** \n**Tag:** `@Arisu_0007 {USER_ID}`"
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
            await message.reply_text("**🙏🏻 Invalid URL. Please provide a valid URL.**")
            return

        # Scrape links from the provided URL
        links = await scrape_website(url)
        if not links:
            await message.reply_text("**💀 No links found on the provided URL.**")
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
        logging.error(f"Error handling /tmv command: {str(e)}")
        await message.reply_text(f"**Error:** {str(e)}")


async def check_rss_feed():
    """Periodically check the RSS feed for new links and send them."""
    while True:
        try:
            new_links = await fetch_rss_links()
            if new_links:
                await send_links_or_message(new_links)
        except Exception as e:
            logging.error(f"Error during RSS feed check: {str(e)}")
        await asyncio.sleep(600)  # Check every 10 minutes


async def main():
    await app.start()
    logging.info("Bot is running...")
    # Start RSS feed monitoring in the background
    asyncio.create_task(check_rss_feed())
    await idle()
    await app.stop()


# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
