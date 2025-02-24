FROM python:3.9

# Install Java
RUN apt-get update && apt-get install -y openjdk-17-jre

# Set the working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the correct port
EXPOSE 10000

# Start the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "app:app"]
