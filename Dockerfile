# Dockerfile

# --- Stage 1: Build Stage ---
# Use an official Python runtime as a parent image.
# We choose a specific version (e.g., 3.9-slim-buster or 3.10-slim-bullseye)
# for stability and smaller image size. 'slim' images are highly recommended for production.
FROM python:3.9-slim-buster as builder

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker's build cache.
# If requirements.txt doesn't change, this layer (and subsequent pip install) will be cached.
COPY requirements.txt .

# Install any necessary system dependencies for Python packages (e.g., build tools)
# For 'pytz' and 'numpy', 'python3-dev' and 'gcc' might be needed if not pre-compiled.
# 'build-essential' provides common compilation tools.
# 'libffi-dev' is sometimes needed for cryptography dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
# --no-cache-dir prevents pip from storing cache, reducing image size.
# --upgrade pip ensures pip is up-to-date.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Image Stage ---
# Use a fresh, smaller base image for the final runtime to keep the image lean.
# This is a multi-stage build, so only the necessary artifacts (installed packages)
# from the 'builder' stage are copied.
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the rest of your application code into the container
# The '.' means copy everything from the current directory (your_bot_project)
# into the /app directory in the container.
COPY . .

# Set environment variables for the bot.
# DISCORD_BOT_TOKEN and DISCORD_GUILD_NAME will be passed at runtime, not built into the image.
# This ensures sensitive data is not baked into the image.
ENV PYTHONUNBUFFERED=1

# Command to run the application when the container starts.
# CMD is the default command that gets executed when you run the container.
# It should point to your main bot script.
CMD ["python", "main.py"]

