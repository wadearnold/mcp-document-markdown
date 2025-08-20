#!/bin/bash

# Repository Setup Script for MCP PDF Markdown Server
# This script creates the complete project structure from the artifacts

set -e

REPO_NAME="mcp-pdf-markdown"
echo "Setting up $REPO_NAME repository..."

# Create repository directory
mkdir -p $REPO_NAME
cd $REPO_NAME

# Initialize git repository
git init

# Create directory structure
mkdir -p bin
mkdir -p test
mkdir -p examples
mkdir -p docs
mkdir -p .github/workflows

# Create main.go - Main server implementation
cat > main.go << 'EOF'
# [Copy the content from the "MCP PDF Converter Server - Main Implementation" artifact]
EOF

# Create python_scripts.go - Embedded Python scripts
cat > python_scripts.go << 'EOF'
# [Copy the content from the "Python PDF Conversion Scripts" artifact]
EOF

# Create test_client.go - Test client
cat > test_client.go << 'EOF'
# [Copy the content from the "MCP Server Test Client" artifact]
EOF

# Create go.mod
cat > go.mod << 'EOF'
module github.com/yourusername/mcp-pdf-markdown

go 1.21

require (
    github.com/sourcegraph/jsonrpc2 v0.2.0
)

require (
    github.com/gorilla/websocket v1.5.0 // indirect
)
EOF

# Create go.sum
cat > go.sum << 'EOF'
github.com/gorilla/websocket v1.5.0 h1:PPwGk2jz7EePpoHN/+ClbZu8SPxiqlu12wZP/3sWmnc=
github.com/gorilla/websocket v1.5.0/go.mod h1:YR8l580nyteQvAITg2hZ9XVh4b55+EU/adAjf1fMHhE=
github.com/sourcegraph/jsonrpc2 v0.2.0 h1:KjN/dC4fP6aN9030MZCJs9WQbTOjWHhrtKVpzzSrr/U=
github.com/sourcegraph/jsonrpc2 v0.2.0/go.mod h1:ZafdZgk/axhT1cvZAPOhw+95nz2I/Ra5qMlU4gTRwIo=
EOF

# Create Makefile
cat > Makefile << 'EOF'
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
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
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
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
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
EOF

# Create README.md
cat > README.md << 'EOF'
# [Copy the content from the "MCP PDF Converter Server - README" artifact]
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Binaries
bin/
*.exe
*.dll
*.so
*.dylib
mcp-pdf-server

# Test binary
*.test

# Output directories
converted_docs/
output/
test_output/
benchmark_output_*/

# Go dependencies
vendor/

# IDE files
.idea/
.vscode/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Python cache
__pycache__/
*.py[cod]
*$py.class

# Environment files
.env
.env.local

# PDF test files (optional - remove if you want to track test PDFs)
*.pdf
!examples/*.pdf

# Temporary files
*.tmp
*.temp
temp_converted.md

# Docker volumes
input/
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Python interpreter path (default: python3)
PYTHON_PATH=python3

# Default output directory for converted files
OUTPUT_DIR=./converted_docs

# Maximum file size in MB (default: 100)
MAX_FILE_SIZE=100

# Enable debug logging
DEBUG=false
EOF

# Create LICENSE
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create examples directory with sample config
cat > examples/claude-desktop-config.json << 'EOF'
{
  "mcpServers": {
    "pdf-converter": {
      "command": "/usr/local/bin/mcp-pdf-server",
      "env": {
        "OUTPUT_DIR": "/Users/username/Documents/converted_pdfs"
      }
    }
  }
}
EOF

# Create GitHub Actions workflow
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Python dependencies
      run: |
        pip install pypdf pdfplumber pymupdf pandas pillow tabulate markdown
    
    - name: Install Go dependencies
      run: go mod download
    
    - name: Build
      run: go build -v ./...
    
    - name: Test
      run: go test -v ./...

  docker:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t mcp-pdf-server .
EOF

# Create initial documentation
cat > docs/ARCHITECTURE.md << 'EOF'
# Architecture Overview

## System Components

### 1. MCP Server (Go)
- Implements Model Context Protocol
- Manages tool registration and execution
- Handles JSON-RPC communication

### 2. Python Conversion Engine
- Multi-library approach for robustness
- PyMuPDF: Text and image extraction
- pdfplumber: Table preservation
- pypdf: Document structure analysis

### 3. Chapter Detection System
- Pattern-based chapter identification
- Configurable splitting rules
- Automatic TOC generation

## Data Flow

1. Client sends PDF conversion request via MCP
2. Go server validates request and parameters
3. Python scripts process PDF using multiple methods
4. Content is analyzed and split by chapters
5. Markdown files are generated with proper structure
6. Response sent back through MCP protocol

## Design Decisions

- **Go for MCP Server**: Better performance and concurrency
- **Python for PDF Processing**: Best library ecosystem
- **Embedded Scripts**: Simplifies deployment
- **Multiple Extraction Methods**: Ensures robustness
EOF

# Create CONTRIBUTING.md
cat > CONTRIBUTING.md << 'EOF'
# Contributing to MCP PDF Markdown

We welcome contributions! Please follow these guidelines:

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Install dependencies
make setup

# Run tests
make test

# Build the project
make build
```

## Code Style

- Go: Follow standard Go formatting (use `go fmt`)
- Python: Follow PEP 8
- Comments: Be descriptive and explain "why" not "what"

## Testing

- Add tests for new functionality
- Ensure all tests pass before submitting PR
- Include sample PDFs for testing (if applicable)

## Pull Request Process

1. Update README.md with any new features
2. Update the documentation
3. Ensure CI passes
4. Request review from maintainers
EOF

echo "Repository structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Copy the artifact contents into the respective files"
echo "2. Update LICENSE with your name"
echo "3. Update go.mod with your GitHub username"
echo "4. Run: go mod tidy"
echo "5. Run: make setup"
echo "6. Add and commit files"
echo "7. Create GitHub repository and push"