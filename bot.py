from pyrogram import Client, filters
from pymongo import MongoClient
import requests
from pyrogram import errors
import requests

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# MongoDB setup
MONGO_URI = "mongodb+srv://shopngodeals:ultraamz@cluster0.wn2wr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['la_db']  # Replace with your desired database name
collection = db['la_db']  # Replace with your desired collection name

# Telegram bot configuration
api_id = 24972774  # Your API ID
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'  # Your API Hash
bot_token = '7425634528:AAFGaQ1xb2ofq7qSfYNyys-VPGWSP5m5BnY'  # Your Bot Token

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.document)
def handle_document(client, message):
    file_id = message.document.file_id
    new_file = client.get_file(file_id)

    # Save file info to MongoDB
    file_url = new_file.file_url
    collection.insert_one({'file_id': file_id, 'file_url': file_url})

    # Send response with download URL
    download_url = f"http://pifbots.online/download/{file_id}"
    message.reply(f"File saved! Download URL: {download_url}")

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply("Welcome! Send me a document, and I'll save it for you.")

@app.on_message(filters.command("help"))
def help(client, message):
    message.reply("Send me a document, and I'll save it to my database!")

@app.route('/download/<file_id>')
def download_file(file_id):
    document = collection.find_one({'file_id': file_id})
    if document:
        file_url = document['file_url']
        return f"<a href='{file_url}'>Click here to download the file</a>"
    return "File not found!", 404

if __name__ == "__main__":
    app.run()
