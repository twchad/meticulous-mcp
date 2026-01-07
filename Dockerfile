FROM python:3.11-slim

WORKDIR /app

# Copy the entire repository
COPY . /app

# Install git because python-sdk needs it for versioning
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies
# Install the local packages so metadata is available (fixes 'No package metadata was found for mcp')
RUN pip install --no-cache-dir ./python-sdk
RUN pip install --no-cache-dir ./pyMeticulous
RUN pip install --no-cache-dir ./meticulous-mcp

# Install uvicorn separately as it is used to run the server
RUN pip install uvicorn

# Expose port 8080
EXPOSE 8080

# Run the HTTP server wrapper
CMD ["python", "run_http.py"]
