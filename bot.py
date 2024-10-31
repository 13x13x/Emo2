from pyrogram import Client, filters
from pymongo import MongoClient
import aria2p

# Initialize MongoDB
mongo_client = MongoClient("mongodb+srv://abcd:abcd@cluster0.r0ezijk.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["torrent_bot"]
downloads_collection = db["downloads"]

# Initialize Aria2 for downloading torrents
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)

API_ID = "24972774"  # Replace with your API ID
API_HASH = "188f227d40cdbfaa724f1f3cd059fd8b"  # Replace with your API Hash
BOT_TOKEN = "7460682763:AAF4bGSKPI4wrVHsuak6dIqFQ6hQTlEP5EE"  # Replace with your bot token

# Initialize Telegram Bot
bot = Client("torrent_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Hello! Send me a torrent link or magnet link to download.")

@bot.on_message(filters.text)
async def download_torrent(client, message):
    link = message.text
    if "magnet:" in link or link.endswith(".torrent"):
        # Add torrent/magnet link to aria2
        download = aria2.add_magnet(link) if "magnet:" in link else aria2.add_torrent(link)
        
        # Wait for download to complete (you may want to add a real async handler for this)
        download_status = aria2.get_download(download.gid)
        while not download_status.is_complete:
            download_status.update()
        
        # Generate a high-speed download link (using your method)
        high_speed_link = f"https://highspeeddownloadservice.com/download/{download.gid}"

        # Save to MongoDB
        downloads_collection.insert_one({
            "user_id": message.from_user.id,
            "download_link": link,
            "high_speed_link": high_speed_link
        })
        
        # Send the high-speed link to the user
        await message.reply(f"Download complete! Here is your high-speed download link: {high_speed_link}")
    else:
        await message.reply("Please send a valid torrent link or magnet link.")

bot.run()
