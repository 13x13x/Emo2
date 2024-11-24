import feedparser
import requests
from pyrogram import Client, filters, idle
from bs4 import BeautifulSoup
import asyncio
import os
import uuid
import nest_asyncio
from datetime import datetime

# Telegram bot configuration
api_id = 24972774
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'
bot_token = '6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg'

USER_ID = 6290483448  # Replace with the actual user ID
RSS_FEED_URL = 'https://www.1tamilmv.at/index.php?/discover/all.xml'
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

# Load already processed links from the file
if os.path.exists(SENT_LINKS_FILE):
    with open(SENT_LINKS_FILE, 'r') as f:
        sent_links = set(f.read().splitlines())

def save_sent_link(link):
    """Save processed links to the file."""
    sent_links.add(link)
    with open(SENT_LINKS_FILE, 'a') as f:
        f.write(link + "\n")

def scrape_website(url):
    """Scrape links from the provided URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            magnet_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("magnet:?xt")]
            file_links = [a['href'] for a in soup.find_all('a', href=True) if "applications/core/interface/file" in a['href']]
            return magnet_links, file_links
        else:
            return [], []
    except Exception as e:
        print(f"Error scraping website: {str(e)}")
        return [], []

async def send_links_or_message(links, link_type="magnet"):
    """Send magnet or fallback links, or a message if no links are found."""
    if links:
        for i, link in enumerate(links[:MAX_LINKS_PER_BATCH]):
            formatted_link = f"**/qbleech {link}** \n**Tag:** `@Arisu_0007 6290483448`"
            await app.send_message(USER_ID, formatted_link)
            await asyncio.sleep(1)
    else:
        message = "**Links Not Found!!**" if link_type == "magnet" else "**No suitable links found!**"
        await app.send_message(USER_ID, message)

@app.on_message(filters.command("tmv"))
async def tmv(client, message):
    """Handle the /tmv command for scraping and sending links."""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply_text("**Usage:** /tmv <url> or /tmv -i <number> <url>")
            return

        num_links = None
        url = None

        if "-i" in parts:
            try:
                index_flag = parts.index("-i")
                num_links = int(parts[index_flag + 1])
                url = parts[index_flag + 2]
            except (ValueError, IndexError):
                await message.reply_text("**Usage:** /tmv -i <number> <url>\nThe number of links must be an integer.")
                return
        else:
            url = parts[-1]

        if not url.startswith("http"):
            await message.reply_text("**Invalid URL provided!**")
            return

        magnet_links, file_links = scrape_website(url)
        if magnet_links:
            links_to_send = magnet_links[:num_links] if num_links else magnet_links
            await message.reply_text(f"**Sending {len(links_to_send)} magnet links:**")
            await send_links_or_message(links_to_send, link_type="magnet")
        elif file_links:
            links_to_send = file_links[:num_links] if num_links else file_links
            await message.reply_text(f"**No magnet links found. Sending {len(links_to_send)} file links instead:**")
            await send_links_or_message(links_to_send, link_type="file")
        else:
            await message.reply_text("**No links of either type were found on the page.**")

    except Exception as e:
        await message.reply_text(f"**Error:** {str(e)}")

async def process_rss_feed():
    """Fetch and process new entries from the RSS feed."""
    global sent_links
    while True:
        try:
            feed = feedparser.parse(RSS_FEED_URL)
            for entry in feed.entries:
                if entry.link not in sent_links:
                    magnet_links, file_links = scrape_website(entry.link)
                    if magnet_links:
                        await send_links_or_message(magnet_links, link_type="magnet")
                    elif file_links:
                        await send_links_or_message(file_links, link_type="file")
                    else:
                        await app.send_message(USER_ID, f"No links found in the RSS entry: {entry.link}")
                    save_sent_link(entry.link)
        except Exception as e:
            print(f"Error processing RSS feed: {str(e)}")
        await asyncio.sleep(300)  # Wait for 5 minutes before checking again

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
