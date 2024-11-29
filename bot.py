import feedparser
import requests
from pyrogram import Client, filters, idle
from bs4 import BeautifulSoup
import asyncio
import os
import uuid
import nest_asyncio
from datetime import datetime
from pymongo import MongoClient

# Telegram bot configuration
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg'

USER_ID = 6290483448  # Replace with the actual user ID
RSS_FEED_URL = ''  # Add your RSS feed URL
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

# MongoDB Configuration
MONGO_URL = "mongodb+srv://Puka12:puka12@cluster0.4xmyiyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URL
DATABASE_NAME = "web_scraper_bot"
COLLECTION_NAME = "sent_links"

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DATABASE_NAME]
sent_links_collection = db[COLLECTION_NAME]

# Function to check if a link has already been sent
def is_link_sent(link):
    """Check if the given link is already sent"""
    return sent_links_collection.find_one({"link": link}) is not None

# Function to mark a link as sent
def mark_link_as_sent(link):
    """Mark the given link as sent by saving it to the database"""
    sent_links_collection.insert_one({"link": link, "timestamp": datetime.utcnow()})

def scrape_website(url):
    """Scrape links from the provided URL"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            magnet_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("magnet:?xt")]
            file_links = [a['href'] for a in soup.find_all('a', href=True) if "applications" in a['href']]
            return magnet_links, file_links
        else:
            return [], []
    except Exception as e:
        print(f"Error scraping website: {str(e)}")
        return [], []

async def send_links_or_message(links, link_type="magnet"):
    """Send magnet or fallback links, or a message if no links are found"""
    if links:
        for i, link in enumerate(links[:MAX_LINKS_PER_BATCH]):
            formatted_link = f"**/qbleech {link} **\n**Tag: @Arisu_0007 6290483448**"

            # Check for duplicates in MongoDB
            if is_link_sent(formatted_link):
                formatted_link = f"**{link} **\n\n** #rss**"
            
            # Send only the formatted link without "Magnet Link 1:"
            await app.send_message(USER_ID, formatted_link)
            mark_link_as_sent(formatted_link)  # Save the link in MongoDB
            await asyncio.sleep(1)
    else:
        message = f"**No {link_type} links found!**" if link_type == "magnet" else "**No suitable file links found!**"
        await app.send_message(USER_ID, message)

@app.on_message(filters.command("tmv"))
async def tmv(client, message):
    """Handle the /tmv command for scraping and sending links"""
    try:
        # Restrict command to USER_ID
        if message.from_user.id != USER_ID:
            await message.reply_text("**❌ You are not authorized to use this command!**")
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.reply_text("**Usage: /tmv <url> or /tmv -i <number> <url>**")
            return

        num_links = None
        url = None

        if "-i" in parts:
            try:
                index_flag = parts.index("-i")
                num_links = int(parts[index_flag + 1])
                url = parts[index_flag + 2]
            except (ValueError, IndexError):
                await message.reply_text("**Usage: /tmv -i <number> <url>**\n**The number of links must be an integer**")
                return
        else:
            url = parts[-1]

        if not url.startswith("http"):
            await message.reply_text("**❌ Invalid URL provided!**")
            return

        magnet_links, file_links = scrape_website(url)
        if magnet_links:
            links_to_send = magnet_links[:num_links] if num_links else magnet_links
            await message.reply_text(f"**Sending {len(links_to_send)} Magnet Links..**")
            await send_links_or_message(links_to_send, link_type="magnet")
        elif file_links:
            links_to_send = file_links[:num_links] if num_links else file_links
            await message.reply_text(f"**No magnet links found, sending {len(links_to_send)} file links**")
            await send_links_or_message(links_to_send, link_type="file")
        else:
            await message.reply_text("**❌ No links of either type were found on the page**")

    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")

async def process_rss_feed():
    """Fetch and process new entries from the RSS feed, skipping old links."""
    last_processed_time = datetime.utcnow()  # Initialize with the current time

    while True:
        try:
            feed = feedparser.parse(RSS_FEED_URL)
            for entry in feed.entries:
                # Parse the publication time of the entry
                pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                
                # Skip if the entry is older than the last processed time
                if pub_date and pub_date <= last_processed_time:
                    continue
                
                # Skip if the link was already processed
                if is_link_sent(entry.link):
                    continue

                # Process the entry for links
                magnet_links, file_links = scrape_website(entry.link)
                if magnet_links:
                    await send_links_or_message(magnet_links, link_type="magnet")
                elif file_links:
                    await send_links_or_message(file_links, link_type="file")
                else:
                    await app.send_message(USER_ID, f"**No links found in the RSS entry:** {entry.link}")
                
                # Mark the link as sent and update the last processed time
                mark_link_as_sent(entry.link)
                if pub_date and pub_date > last_processed_time:
                    last_processed_time = pub_date

        except Exception as e:
            print(f"**Error processing RSS feed: {str(e)}**")
        
        # Wait for 5 minutes before checking again
        await asyncio.sleep(300)

async def main():
    """Start the bot and process RSS feed."""
    await app.start()
    print("Bot is running...")
    asyncio.create_task(process_rss_feed())  # Start RSS feed processing
    await idle()
    await app.stop()

# Apply nest_asyncio to avoid event loop issues
nest_asyncio.apply()

# Run the bot
asyncio.run(main())
