from pyrogram import Client, filters
from pymongo import MongoClient
from flask import Flask, jsonify, abort
from datetime import datetime, timedelta
import asyncio

# MongoDB setup
MONGO_URI = "mongodb+srv://shopngodeals:ultraamz@cluster0.wn2wr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['la_db']  # Replace with your desired database name
collection = db['files']  # Change to your desired collection name

# Telegram bot configuration
api_id = 24972774  # Your API ID
api_hash = '188f227d40cdbfaa724f1f3cd059fd8b'  # Your API Hash
bot_token = '7425634528:AAFGaQ1xb2ofq7qSfYNyys-VPGWSP5m5BnY'  # Your Bot Token

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Flask app setup
flask_app = Flask(__name__)

@app.on_message(filters.document)
async def handle_document(client, message):
    file_id = message.document.file_id
    async for new_file in client.get_file(file_id):  # Correctly await the generator
        # Save file info to MongoDB
        file_url = new_file.file_url
        expiry_time = datetime.utcnow() + timedelta(minutes=10)  # Set expiry to 10 minutes
        collection.insert_one({'file_id': file_id, 'file_url': file_url, 'expiry_time': expiry_time})

        # Send response with download URL
        download_url = f"http://pifbots.online/download/{file_id}"
        await message.reply(f"File saved! Download URL: {download_url}. This link will expire in 10 minutes.")
        break  # Exit the loop after processing

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome! Send me a document, and I'll save it for you.")

@app.on_message(filters.command("help"))
async def help(client, message):
    await message.reply("Send me a document, and I'll save it to my database!")

@flask_app.route('/download/<file_id>')
def download_file(file_id):
    document = collection.find_one({'file_id': file_id})

    if document:
        expiry_time = document['expiry_time']
        if datetime.utcnow() < expiry_time:
            # Return the file URL
            return jsonify({"file_url": document['file_url']})
        else:
            # Remove the document if expired
            collection.delete_one({'file_id': file_id})
            return abort(404, description="File link has expired")
    return abort(404, description="File not found")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(app.start())
    flask_app.run(host='0.0.0.0', port=5000)  # Start the Flask app
