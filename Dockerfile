# Use an official lightweight Python image
FROM python:3.12.3

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y cmake && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first for better caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Keep the container running
# CMD ["tail", "-f", "/dev/null"]

CMD ["python", "main.py"]
