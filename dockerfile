# Use Python 3.10 as the base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the bot script to the working directory
COPY bot.py .

# Run the bot
CMD ["python", "bot.py"]
