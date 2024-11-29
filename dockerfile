FROM python:3.10-slim

WORKDIR /app

# Copy Python files into the container
COPY bot.py Config.py /app/

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run the bot
CMD ["python", "bot.py"]
