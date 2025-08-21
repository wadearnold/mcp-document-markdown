FROM golang:1.21-alpine AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
COPY python/ ./python/
RUN go build -o mcp-server main.go python_embed.go python_loader.go

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY --from=builder /build/mcp-server .

# Create directories
RUN mkdir -p /app/input /app/docs

ENTRYPOINT ["./mcp-server"]