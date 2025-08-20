# docker-compose.yml
version: '3.8'

services:
  mcp-pdf-server:
    build: .
    container_name: mcp-pdf-converter
    volumes:
      - ./input:/app/input
      - ./output:/app/output
    environment:
      - OUTPUT_DIR=/app/output
    stdin_open: true
    tty: true

---
# Dockerfile
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
RUN mkdir -p /app/input /app/output

ENTRYPOINT ["./mcp-server"]

---
# go.mod
module github.com/yourusername/mcp-pdf-server

go 1.21

require (
    github.com/sourcegraph/jsonrpc2 v0.2.0
)

require (
    github.com/gorilla/websocket v1.5.0 // indirect
)

---
# go.sum
github.com/gorilla/websocket v1.5.0 h1:PPwGk2jz7EePpoHN/+ClbZu8SPxiqlu12wZP/3sWmnc=
github.com/gorilla/websocket v1.5.0/go.mod h1:YR8l580nyteQvAITg2hZ9XVh4b55+EU/adAjf1fMHhE=
github.com/sourcegraph/jsonrpc2 v0.2.0 h1:KjN/dC4fP6aN9030MZCJs9WQbTOjWHhrtKVpzzSrr/U=
github.com/sourcegraph/jsonrpc2 v0.2.0/go.mod h1:ZafdZgk/axhT1cvZAPOhw+95nz2I/Ra5qMlU4gTRwIo=

---
# Makefile
.PHONY: build run test clean deps install-python-deps

# Build the Go binary
build:
	go build -o bin/mcp-pdf-server .

# Run the server
run: build
	./bin/mcp-pdf-server

# Install Go dependencies
deps:
	go mod download
	go mod tidy

# Install Python dependencies
install-python-deps:
	pip install pypdf pdfplumber pymupdf pandas pillow tabulate markdown

# Build Docker image
docker-build:
	docker build -t mcp-pdf-server .

# Run with Docker Compose
docker-run:
	docker-compose up

# Clean build artifacts
clean:
	rm -rf bin/
	rm -rf converted_docs/
	rm -rf output/

# Test the conversion with a sample PDF
test: build
	@echo "Testing PDF conversion..."
	@if [ -f "test.pdf" ]; then \
		./bin/mcp-pdf-server test test.pdf ./test_output; \
	else \
		echo "Please add a test.pdf file to test conversion"; \
	fi

# Install everything needed for development
setup: deps install-python-deps
	@echo "Setup complete! You can now run 'make run' to start the server"

---
# config.json - MCP Server Configuration
{
  "mcpServers": {
    "pdf-converter": {
      "command": "go",
      "args": ["run", "."],
      "env": {
        "OUTPUT_DIR": "./converted_docs"
      }
    }
  }
}

---
# .env.example
# Python interpreter path (default: python3)
PYTHON_PATH=python3

# Default output directory for converted files
OUTPUT_DIR=./converted_docs

# Maximum file size in MB (default: 100)
MAX_FILE_SIZE=100

# Enable debug logging
DEBUG=false