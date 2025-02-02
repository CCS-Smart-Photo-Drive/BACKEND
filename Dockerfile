# Use an official lightweight Python image
FROM python:3.12.3

# Set the working directory inside the container
WORKDIR /app

# Copy all files from the current directory to /app inside the container
COPY . .

# Install dependencies (if you have a requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Python script
CMD ["python", "main.py"]
