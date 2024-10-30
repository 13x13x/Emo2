from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from bson import ObjectId
import nest_asyncio

# MongoDB Configuration
MONGO_URI = "mongodb+srv://shopngodeals:ultraamz@cluster0.wn2wr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['la_db']  # Use your database name here
collection = db['files']

# Telegram Bot Configuration
API_ID = "24972774"  # Replace with your API ID
API_HASH = "188f227d40cdbfaa724f1f3cd059fd8b"  # Replace with your API Hash
BOT_TOKEN = "7460682763:AAF4bGSKPI4wrVHsuak6dIqFQ6hQTlEP5EE"  # Replace with your bot token

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ensure this URL points to your Netlify deployment
NETLIFY_URL = "https://pifoffcl.netlify.app/downloads"

@app.on_message(filters.document & filters.private)
async def store_file(client, message: Message):
    # Store document details in MongoDB
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_size = message.document.file_size
    file_data = {
        "file_id": file_id,
        "file_name": file_name,
        "file_size": file_size
    }
    inserted_file = collection.insert_one(file_data)
    file_db_id = str(inserted_file.inserted_id)
    
    # Respond with download command
    await message.reply_text(f"File stored successfully. Retrieve it with:\n"
                             f"`/download {file_db_id}`")

@app.on_message(filters.command("download") & filters.private)
async def download_file(client, message: Message):
    # Retrieve file ID from MongoDB
    if len(message.command) < 2:
        await message.reply_text("Please provide a valid file ID, e.g., `/download <file_id>`.")
        return
    
    file_db_id = message.command[1]
    file_data = collection.find_one({"_id": ObjectId(file_db_id)})
    
    if not file_data:
        await message.reply_text("File not found in the database.")
        return
    
    # Provide high-speed download link using Netlify
    file_name = file_data['file_name']
    high_speed_link = f"{NETLIFY_URL}/{file_name}"  # Generate link based on Netlify URL
    
    # Print message to console for debugging
    print(f"Generating download link for file: {file_name} -> {high_speed_link}")
    
    await message.reply_text(f"**File:** {file_name}\n"
                             f"**Download Link:** [High-speed link]({high_speed_link})",
                             disable_web_page_preview=True)

nest_asyncio.apply()  # Apply nest_asyncio patch
app.run()
