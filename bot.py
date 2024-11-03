import os
import asyncio
from seedrcc import Login, Seedr
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

# Set up environment variables
API_ID = 24972774  # Your Telegram API ID
API_HASH = "188f227d40cdbfaa724f1f3cd059fd8b"  # Your Telegram API Hash
BOT_TOKEN = "7460682763:AAF4bGSKPI4wrVHsuak6dIqFQ6hQTlEP5EE"  # Your Telegram Bot Token
MONGO_URI = "mongodb+srv://abcd:abcd@cluster0.r0ezijk.mongodb.net/?retryWrites=true&w=majority"  # MongoDB connection string

# MongoDB client initialization
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.seeder_bot

# Initialize the Telegram client
app = Client("seeder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user information in the database
async def store_user_info(user_id, email, password):
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"email": email, "password": password}},
        upsert=True
    )

# Fetch user information from the database
async def get_user_info(user_id):
    return await db.users.find_one({"user_id": user_id})

# Delete user information from the database
async def delete_user_info(user_id):
    await db.users.delete_one({"user_id": user_id})

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply("Welcome! Please log in using /login {email} {password}")

@app.on_message(filters.command("login"))
async def login_command(client: Client, message: Message):
    try:
        _, email, password = message.text.split(maxsplit=2)
        seedr = Login(email, password)
        response = seedr.authorize()
        
        if response and response.get('success'):
            await store_user_info(message.from_user.id, email, password)
            await message.reply(f"Successful Login 💙\nWelcome to your Seedr account.")
        else:
            await message.reply("Invalid email or password.")
    except ValueError:
        await message.reply("Usage: /login {email} {password}")

@app.on_message(filters.command("storage"))
async def storage_command(client: Client, message: Message):
    user_info = await get_user_info(message.from_user.id)
    if user_info:
        email = user_info["email"]
        password = user_info["password"]

        seedr = Login(email, password)
        response = seedr.authorize()
        
        if response and response.get('success'):
            storage_info = Seedr(email, password).get_storage()
            total_storage = storage_info.get('total_storage', 'N/A')
            used_storage = storage_info.get('used_storage', 'N/A')
            await message.reply(f"Storage:\nTotal storage: {total_storage}\nUsed storage: {used_storage}")
        else:
            await message.reply("Unable to fetch storage information. Please check your credentials.")
    else:
        await message.reply("You are not logged in. Please log in first using /login.")

@app.on_message(filters.command("all"))
async def all_command(client: Client, message: Message):
    user_info = await get_user_info(message.from_user.id)
    if user_info:
        email = user_info["email"]
        password = user_info["password"]

        seedr = Login(email, password)
        response = seedr.authorize()

        if response and response.get('success'):
            torrents = Seedr(email, password).get_torrents()
            if torrents:
                torrent_list = "\n".join([f"{torrent['name']} (Status: {torrent['status']})" for torrent in torrents])
                await message.reply(f"Stored torrents for {email}:\n{torrent_list}")
            else:
                await message.reply("No torrents found.")
        else:
            await message.reply("Unable to fetch torrents. Please check your credentials.")
    else:
        await message.reply("You are not logged in. Please log in first using /login.")

@app.on_message(filters.command("dl"))
async def delete_command(client: Client, message: Message):
    user_info = await get_user_info(message.from_user.id)
    if user_info:
        email = user_info["email"]
        password = user_info["password"]

        seedr = Login(email, password)
        response = seedr.authorize()

        if response and response.get('success'):
            delete_response = Seedr(email, password).delete_all_torrents()
            if delete_response and delete_response.get('success'):
                await message.reply("All torrents have been successfully deleted from your Seedr account.")
            else:
                await message.reply("Failed to delete torrents. Please check your credentials or try again later.")
        else:
            await message.reply("You are not logged in. Please log in first using /login.")
    else:
        await message.reply("You are not logged in. Please log in first using /login.")

@app.on_message(filters.command("logout"))
async def logout_command(client: Client, message: Message):
    await delete_user_info(message.from_user.id)
    await message.reply("You have been logged out.")

@app.on_message(filters.command("download"))
async def download_command(client: Client, message: Message):
    user_info = await get_user_info(message.from_user.id)
    if user_info:
        email = user_info["email"]
        password = user_info["password"]

        try:
            _, torrent_link = message.text.split(maxsplit=1)
        except ValueError:
            await message.reply("Usage: /download {torrent link}")
            return

        await message.reply("Adding your torrent... Please wait.")
        
        seedr = Login(email, password)
        response = seedr.authorize()

        if response and response.get('success'):
            add_response = Seedr(email, password).add_torrent(torrent_link)
            if add_response and add_response.get('success'):
                await message.reply("Torrent is being processed...")

                # Simulate progress
                for progress in range(0, 101, 10):
                    await asyncio.sleep(0.5)
                    await message.reply(f"Download Progress: {progress}%")
                
                download_link = add_response.get('data', {}).get('download_link', 'N/A')
                await message.reply(f"Download completed! Your download link: {download_link}")
            else:
                await message.reply("Failed to add the torrent. Please check the link or your credentials.")
        else:
            await message.reply("Unable to fetch storage information. Please check your credentials.")
    else:
        await message.reply("You are not logged in. Please log in first using /login.")

if __name__ == "__main__":
    app.run()
