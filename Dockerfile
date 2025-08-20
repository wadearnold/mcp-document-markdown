FROM golang:1.21-alpine AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
RUN go build -o mcp-server .

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    pypdf \
    pdfplumber \
    pymupdf \
    pandas \
    pillow \
    tabulate \
    markdown

WORKDIR /app
COPY --from=builder /build/mcp-server .

# Create directories
RUN mkdir -p /app/input /app/docs

ENTRYPOINT ["./mcp-server"]