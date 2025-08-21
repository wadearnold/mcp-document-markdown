.PHONY: build run test clean deps install-python-deps setup venv

# Default target
all: build

# Build the Go binary (embeds Python scripts from python/ directory)
build: check-python
	go build -o bin/mcp-pdf-markdown main.go python_embed.go python_loader.go

# Build the test client
build-test:
	go build -o bin/test-client test_client.go

# Run the server
run: build venv
	./bin/mcp-pdf-markdown

# Run the server in development mode (for testing Python changes without rebuilding)
dev: check-python venv
	PYTHON_SCRIPTS_DIR=./python go run main.go python_embed.go python_loader.go

# Run the test client
run-test: build-test
	./bin/test-client interactive

# Install Go dependencies
deps:
	go mod download
	go mod tidy

# Create Python virtual environment if it doesn't exist
venv:
	@if [ ! -d "venv" ]; then \
		echo "Creating Python virtual environment..."; \
		python3 -m venv venv; \
	fi

# Install Python dependencies
install-python-deps: venv
	@echo "Installing Python packages..."
	@./venv/bin/pip install --upgrade pip
	@./venv/bin/pip install -r requirements.txt || echo "Warning: Some optional packages may have failed to install"


# Clean build artifacts
clean:
	rm -rf bin/
	rm -rf docs/
	rm -rf test_output/
	rm -rf venv/

# Test the conversion with a sample PDF
test: build
	@echo "Testing PDF conversion..."
	@if [ -f "test.pdf" ]; then \
		./bin/mcp-pdf-markdown test test.pdf ./test_output; \
	else \
		echo "Please add a test.pdf file to test conversion"; \
	fi

# Install everything needed for development
setup: deps install-python-deps
	@echo "Setup complete! You can now run 'make build' to build the MCP server binary"

# Check if Python scripts exist for embedding
check-python:
	@if [ ! -f "python/pdf_converter.py" ] || [ ! -f "python/pdf_analyzer.py" ]; then \
		echo "Error: Python scripts not found in python/ directory"; \
		echo "Run 'make extract-python' to extract from python_scripts.go"; \
		exit 1; \
	fi

# Extract Python scripts from python_scripts.go (for migration)
extract-python:
	@echo "Extracting Python scripts from python_scripts.go..."
	@mkdir -p python
	@sed -n '7,311p' python_scripts.go > python/pdf_converter.py
	@sed -n '316,430p' python_scripts.go > python/pdf_analyzer.py
	@echo "Python scripts extracted to python/ directory"

# Check if all dependencies are installed
check-deps: venv
	@echo "Checking Go installation..."
	@go version || (echo "Go is not installed" && exit 1)
	@echo "Checking Python installation..."
	@python3 --version || (echo "Python 3 is not installed" && exit 1)
	@echo "Checking Python packages in virtual environment..."
	@./venv/bin/python -c "import pypdf" 2>/dev/null || echo "  ⚠️  pypdf not installed"
	@./venv/bin/python -c "import pdfplumber" 2>/dev/null || echo "  ⚠️  pdfplumber not installed"
	@./venv/bin/python -c "import fitz" 2>/dev/null || echo "  ⚠️  pymupdf not installed"
	@./venv/bin/python -c "import pandas" 2>/dev/null || echo "  ⚠️  pandas not installed"
	@./venv/bin/python -c "import PIL" 2>/dev/null || echo "  ⚠️  pillow not installed"
	@./venv/bin/python -c "import tiktoken" 2>/dev/null || echo "  ⚠️  tiktoken not installed (optional but recommended for accurate token counts)"
	@echo "Dependency check complete!"

# Help command
help:
	@echo "Available targets:"
	@echo "  make build          - Build the MCP server"
	@echo "  make run            - Build and run the server"
	@echo "  make test           - Run tests"
	@echo "  make setup          - Install all dependencies"
	@echo "  make check-deps     - Check if dependencies are installed"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make help           - Show this help message"