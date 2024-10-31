FROM python:3.10-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y aria2 python3-libtorrent && \
    rm -rf /var/lib/apt/lists/*

# Create the aria2 config directory and file
RUN mkdir -p /root/.aria2 && \
    echo "enable-rpc=true\nrpc-listen-all=true\nrpc-allow-origin-all=true" > /root/.aria2/aria2.conf

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . /app

# Start aria2 in the background and then start the bot
CMD aria2c --conf-path=/root/.aria2/aria2.conf & python3 bot.py
