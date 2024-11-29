import os

# Configuration for the bot
class Config:
    API_ID = int(os.getenv("API_ID", 24972774))  # Default value for testing
    API_HASH = os.getenv("API_HASH", "188f227d40cdbfaa724f1f3cd059fd8b")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "6588497175:AAGTAjaV96SJMm8KyJ3HHioZJqRw51CRNqg")
    MONGO_URL = os.getenv(
        "MONGO_URL",
        "mongodb+srv://Puka12:puka12@cluster0.4xmyiyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    USER_ID = int(os.getenv("USER_ID", 6290483448))
    RSS_FEED_URL = os.getenv("RSS_FEED_URL", "")  # Replace with actual RSS URL
    MAX_LINKS_PER_BATCH = int(os.getenv("MAX_LINKS_PER_BATCH", 10))
