FROM python:3.13-slim

# Prevents Python from buffering stdout and simplifies logging
ENV PYTHONUNBUFFERED=1

# Working directory inside the container
WORKDIR /app

# System deps (minimal - extend if something complains during pip install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better Docker cache)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Session secret for Starlette sessions (change in your environment!)
ENV SESSION_SECRET="change_me_to_random_string"

# Expose port (you can map it with -p 8000:8000)
EXPOSE 8000

# Start FastAPI app using Uvicorn
# If your app object is not in main:app, adjust this.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
