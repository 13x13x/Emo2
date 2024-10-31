# Start with a Python base image
FROM python:3.10-slim

# Install necessary packages
RUN apt-get update && \
    apt-get install -y aria2 python3-libtorrent && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . /app

# Expose aria2 RPC port
EXPOSE 6800

# Start aria2 in the background with RPC mode enabled
RUN echo "enable-rpc=true\nrpc-listen-all=true\nrpc-allow-origin-all=true" > /root/.aria2/aria2.conf
CMD aria2c --conf-path=/root/.aria2/aria2.conf & python bot.py
