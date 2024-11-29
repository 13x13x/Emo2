# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the bot.py and Config.py files into the container
COPY bot.py Config.py /app/

# Copy the requirements.txt file (if you have one) or specify dependencies
COPY requirements.txt /app/

# Install necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port if your bot uses any (optional, not needed for Telegram bots)
# EXPOSE 8080

# Set the default command to run the bot
CMD ["python", "bot.py"]
