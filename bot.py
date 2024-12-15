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
api_id = 16582302
api_hash = '336ae5acc37e4031e98ca682557cca66'
bot_token = '7877262940:AAH0ffDXn-OmKHwqvqyXyvinE24YLhv3XJc'

USER_ID = 957055438  # Replace with the actual user ID
MAX_LINKS_PER_BATCH = 10
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
MONGO_URL = "mongodb+srv://Puka12:puka12@cluster0.4xmyiyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "web_scraper_bot2"
COLLECTION_NAME = "sent_links2"

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DATABASE_NAME]
sent_links_collection = db[COLLECTION_NAME]

# Global variables for RSS feed management
rss_feed_url = None
rss_running = False

# Function to check if a link has already been sent
def is_link_sent(link):
    return sent_links_collection.find_one({"link": link}) is not None

# Function to mark a link as sent
def mark_link_as_sent(link):
    sent_links_collection.insert_one({"link": link, "timestamp": datetime.utcnow()})

def scrape_website(url):
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

# Function to send a message and auto-delete it after 1 second (except for the formatted_link with '/qbleech')
async def send_temp_message(user_id, message_text):
    """
    Sends a temporary message to the user and deletes it after 1 second, except the '/qbleech' message.
    """
    try:
        sent_message = await app.send_message(user_id, message_text)
        # Check if the message is not the '/qbleech' one to skip deletion
        if not message_text.startswith("**/qbleech2"):
            await asyncio.sleep(1)  # Wait for 1 second
            await app.delete_messages(chat_id=user_id, message_ids=sent_message.id)
    except Exception as e:
        print(f"Error in auto-deleting message: {str(e)}")

async def send_links_or_message(links, link_type="magnet"):
    if links:
        for i, link in enumerate(links[:MAX_LINKS_PER_BATCH]):
            formatted_link = f"**/qbleech2 {link} **\n**Tag: @Benzmawa 957055438**"

            if is_link_sent(formatted_link):
                formatted_link = f"**{link} **\n\n** #ArisuRSS**"
            
            await send_temp_message(USER_ID, formatted_link)
            mark_link_as_sent(formatted_link)
            await asyncio.sleep(1)
    else:
        message = f"**No {link_type} links found!**" if link_type == "magnet" else "**No suitable file links found!**"
        await app.send_message(USER_ID, message)

@app.on_message(filters.command("tmv"))
async def tmv(client, message):
    try:
        if message.from_user.id != USER_ID:
            await message.reply_text("**❌ You are not authorized to use this command!**")
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
                await message.reply_text("Usage: /tmv -i <number> <url>\nThe number of links must be an integer")
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

@app.on_message(filters.command("rss"))
async def handle_rss_command(client, message):
    global rss_feed_url, rss_running

    try:
        if message.from_user.id != USER_ID:
            await message.reply_text("**❌ You are not authorized to use this command!**")
            return

        parts = message.text.split(maxsplit=1)

        if len(parts) == 1:
            await message.reply_text("**Usage:**\n`/rss {sitelink}`\n`/rss -on`\n`/rss -off`")
            return

        command = parts[1].strip()

        if command.startswith("http"):
            rss_feed_url = command
            rss_running = False
            await message.reply_text(f"**✅ RSS feed updated:** `{rss_feed_url}`\n**Use** `/rss -on` **to start monitoring**")
        elif command == "-on":
            if not rss_feed_url:
                await message.reply_text("**❌ RSS feed URL not set! Use** `/rss {sitelink}` **to set the feed first**")
                return
            if rss_running:
                await message.reply_text("**⚠️ RSS feed is already running!**")
            else:
                rss_running = True
                asyncio.create_task(process_rss_feed())
                await message.reply_text("**✅ RSS feed monitoring started**")
        elif command == "-off":
            if not rss_running:
                await message.reply_text("**⚠️ RSS feed is already stopped!**")
            else:
                rss_running = False
                await message.reply_text("**✅ RSS feed monitoring stopped**")
        else:
            await message.reply_text("**❌ Invalid command!**\n**Use** `/rss {sitelink}`, `/rss -on`, **or** `/rss -off`")

    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")

async def process_rss_feed():
    global rss_running
    while rss_running:
        try:
            if not rss_feed_url:
                rss_running = False
                return

            feed = feedparser.parse(rss_feed_url)
            for entry in feed.entries:
                if not is_link_sent(entry.link):
                    magnet_links, file_links = scrape_website(entry.link)
                    if magnet_links:
                        await send_links_or_message(magnet_links, link_type="magnet")
                    elif file_links:
                        await send_links_or_message(file_links, link_type="file")
                    else:
                        await app.send_message(USER_ID, f"**No links found in the RSS entry:** {entry.link}")
                    mark_link_as_sent(entry.link)
        except Exception as e:
            print(f"Error processing RSS feed: {str(e)}")
        await asyncio.sleep(300)

async def main():
    await app.start()
    print("Bot is running...")
    await idle()
    await app.stop()

nest_asyncio.apply()
asyncio.run(main())
