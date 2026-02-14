FROM python:3.11-slim

WORKDIR /app

# Copy the entire repository
COPY . /app

# Install git because python-sdk needs it for versioning
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r meticulous-mcp/requirements.txt
RUN pip install --no-cache-dir ./meticulous-mcp

# Install uvicorn separately as it is used to run the server
RUN pip install uvicorn

# Clone the profile schema repository (includes schema.json and rfc.md)
RUN git clone https://github.com/MeticulousHome/espresso-profile-schema.git /app/espresso-profile-schema

# Expose port 8080
EXPOSE 8080

# Run the HTTP server wrapper
CMD ["python", "run_http.py"]
