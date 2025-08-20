.PHONY: build run test clean deps install-python-deps setup docker-build docker-run venv

# Default target
all: build

# Build the Go binary
build:
	go build -o bin/mcp-pdf-server main.go python_scripts.go

# Build the test client
build-test:
	go build -o bin/test-client test_client.go

# Run the server
run: build venv
	./bin/mcp-pdf-server

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
	@./venv/bin/pip install pypdf pdfplumber pymupdf pandas pillow tabulate markdown

# Build Docker image
docker-build:
	docker build -t mcp-pdf-server .

# Run with Docker Compose
docker-run:
	docker-compose up

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
		./bin/mcp-pdf-server test test.pdf ./test_output; \
	else \
		echo "Please add a test.pdf file to test conversion"; \
	fi

# Install everything needed for development
setup: deps install-python-deps
	@echo "Setup complete! You can now run 'make run' to start the server"

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
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run with Docker"
	@echo "  make help           - Show this help message"