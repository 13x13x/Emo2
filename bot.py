import os
import requests
from flask import Flask
from pyrogram import Client, filters

# Initialize the Flask app
app = Flask(__name__)

# Set your Seedr account credentials
SEEDR_EMAIL = os.getenv("SEEDR_EMAIL", "djsaahus@gmail.com")
SEEDR_PASSWORD = os.getenv("SEEDR_PASSWORD", "saahus123")

# Set your Telegram API credentials
API_ID = os.getenv("API_ID", "24972774")  # Replace with your API ID
API_HASH = os.getenv("API_HASH", "188f227d40cdbfaa724f1f3cd059fd8b)  # Replace with your API Hash

# Initialize the Pyrogram Client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=os.getenv("7460682763:AAF4bGSKPI4wrVHsuak6dIqFQ6hQTlEP5EE"))

# Seedr API URL
SEEDR_API_URL = 'https://www.seedr.cc/rest'

def add_magnet(magnet_link):
    response = requests.post(
        f"{SEEDR_API_URL}/transfer/magnet",
        auth=(SEEDR_EMAIL, SEEDR_PASSWORD),
        data={'magnet': magnet_link}
    )
    return response.json()

def get_user_data():
    response = requests.get(f"{SEEDR_API_URL}/user", auth=(SEEDR_EMAIL, SEEDR_PASSWORD))
    return response.json()

@bot.on_message(filters.text)
def handle_message(client, message):
    magnet_link = message.text.strip()
    
    # Add the magnet link to Seedr
    result = add_magnet(magnet_link)

    if 'id' in result:
        transfer_id = result['id']
        message.reply(f"Magnet link added successfully! Transfer ID: {transfer_id}")
        
        # Optionally, you can fetch and show user data
        user_data = get_user_data()
        message.reply(f"User Data: {user_data}")
        
    else:
        message.reply("Error adding magnet link: " + str(result))

# Start the bot
if __name__ == "__main__":
    bot.start()
    print("Bot is running...")
    app.run()
