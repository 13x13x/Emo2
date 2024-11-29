import os
import feedparser
import requests
from pyrogram import Client, filters, idle
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
mongo_url = os.getenv("MONGO_URL")
user_id = int(os.getenv("USER_ID"))
rss_feed_url = os.getenv("RSS_FEED_URL")
max_links_per_batch = int(os.getenv("MAX_LINKS_PER_BATCH", 20))

# Initialize Pyrogram client
app = Client(
    "web_scraper_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)

# Initialize MongoDB
mongo_client = MongoClient(mongo_url)
db = mongo_client["web_scraper_bot"]
sent_links_collection = db["sent_links"]

# Helper functions
def is_link_sent(link):
    """Check if a link has already been sent."""
    return sent_links_collection.find_one({"link": link}) is not None

def mark_link_as_sent(link):
    """Mark a link as sent by adding it to the database."""
    sent_links_collection.insert_one({"link": link, "timestamp": datetime.utcnow()})

def scrape_website(url):
    """Scrape the given URL for magnet and file links."""
    try:
        logger.info(f"Scraping URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        magnet_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("magnet:?xt")]
        file_links = [a['href'] for a in soup.find_all('a', href=True) if "applications" in a['href']]
        return magnet_links, file_links
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return [], []

async def send_links_or_message(links, link_type="magnet"):
    """Send links or notify if none are found."""
    if links:
        for i, link in enumerate(links[:max_links_per_batch]):
            formatted_link = f"/qbleech {link} **\n**Tag: @Arisu_0007 6290483448"
            
            # Avoid duplicates
            if is_link_sent(formatted_link):
                formatted_link = f"{link} \n\n** #rss**"
            
            await app.send_message(user_id, formatted_link)
            mark_link_as_sent(formatted_link)
            await asyncio.sleep(1)
    else:
        message = "Links Not Found!!" if link_type == "magnet" else "No suitable links found!"
        await app.send_message(user_id, message)

@app.on_message(filters.command("tmv"))
async def tmv_handler(client, message):
    """Handle /tmv command."""
    if message.from_user.id != user_id:
        await message.reply_text("❌ You are not authorized to use this command!")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply_text("Usage: /tmv <url> or /tmv -i <number> <url>")
        return

    num_links = None
    url = None

    if "-i" in parts:
        try:
            index_flag = parts.index("-i")
            num_links = int(parts[index_flag + 1])
            url = parts[index_flag + 2]
        except (ValueError, IndexError):
            await message.reply_text("Usage: /tmv -i <number> <url>")
            return
    else:
        url = parts[-1]

    if not url.startswith("http"):
        await message.reply_text("Invalid URL provided!")
        return

    magnet_links, file_links = scrape_website(url)
    if magnet_links:
        links_to_send = magnet_links[:num_links] if num_links else magnet_links
        await send_links_or_message(links_to_send, link_type="magnet")
    elif file_links:
        links_to_send = file_links[:num_links] if num_links else file_links
        await send_links_or_message(links_to_send, link_type="file")
    else:
        await message.reply_text("No links of either type were found on the page.")

async def process_rss_feed():
    """Fetch and process new RSS feed entries."""
    while True:
        try:
            logger.info("Checking RSS feed for new entries...")
            feed = feedparser.parse(rss_feed_url)
            for entry in feed.entries:
                if not is_link_sent(entry.link):
                    magnet_links, file_links = scrape_website(entry.link)
                    if magnet_links:
                        await send_links_or_message(magnet_links, link_type="magnet")
                    elif file_links:
                        await send_links_or_message(file_links, link_type="file")
                    else:
                        await app.send_message(user_id, f"No links found in RSS entry: {entry.link}")
                    mark_link_as_sent(entry.link)
        except Exception as e:
            logger.error(f"Error processing RSS feed: {e}")
        await asyncio.sleep(300)

async def main():
    """Start the bot and RSS feed processor."""
    await app.start()
    logger.info("Bot is running...")
    asyncio.create_task(process_rss_feed())
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
