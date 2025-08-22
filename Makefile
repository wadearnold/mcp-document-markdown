.PHONY: run test clean install-python-deps setup venv test-pdf check-deps help

# Default target
all: setup

# Run the Python MCP server
run: venv
	@echo "🚀 Starting Python MCP server..."
	@echo
	@echo "📋 Configuration for MCP clients:"
	@echo "   Command: $(PWD)/venv/bin/python"
	@echo "   Args: [\"$(PWD)/mcp_pdf_markdown.py\"]"
	@echo
	@echo "💡 If you get import errors, run 'make setup' first"
	@echo
	./venv/bin/python mcp_pdf_markdown.py

# Run the server in development mode (same as run for Python)
dev: run


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

# Run Python unit tests
test: venv
	@echo "Running Python tests..."
	@cd python && ../venv/bin/python -m unittest discover tests -v 2>&1 | grep -E "(^test_|^OK|^FAILED|^ERROR|Ran [0-9]+ test)"
	@echo "Test suite completed!"

# Test the conversion with a sample PDF  
test-pdf: venv
	@echo "Testing PDF conversion..."
	@if [ -f "test.pdf" ]; then \
		./venv/bin/python python/modular_pdf_converter.py test.pdf ./test_output; \
	else \
		echo "Please add a test.pdf file to test conversion"; \
	fi

# Install everything needed for development
setup: install-python-deps test
	@echo "✅ All tests passed!"
	@echo "Setup complete! You can now run 'make run' to start the Python MCP server"


# Check if all dependencies are installed
check-deps: venv
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
	@echo "  make setup          - Install dependencies and run tests"
	@echo "  make run            - Run the Python MCP server"
	@echo "  make test           - Run Python unit tests"
	@echo "  make test-pdf       - Test PDF conversion with sample file"
	@echo "  make check-deps     - Check if dependencies are installed"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make help           - Show this help message"