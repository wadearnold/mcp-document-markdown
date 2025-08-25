.PHONY: run test clean install-python-deps setup venv test-pdf check-deps help

# Default target
all: setup

# Show configuration info for Claude Code
config: venv
	@echo "📋 MCP Server Configuration for Claude Code:"
	@echo "   Command: $(PWD)/venv/bin/python"
	@echo "   Args: $(PWD)/mcp_pdf_markdown.py"
	@echo
	@echo "To add this server to Claude Code, run:"
	@echo "  claude mcp add pdf-markdown -- \"$(PWD)/venv/bin/python\" \"$(PWD)/mcp_pdf_markdown.py\""

# Test/Debug the MCP server (NOT needed for normal operation)
# IMPORTANT: This is NOT starting a daemon server! MCP stdio servers are spawned 
# on-demand by Claude Code. This command is for:
#   1. Smoke testing that the server starts without errors
#   2. Displaying the configuration paths you need for Claude Code
#   3. Debugging import/dependency issues before using with Claude Code
# The server will wait for JSON-RPC input on stdin (which won't come when run manually).
# Use Ctrl+C to exit - this is expected behavior.
run: venv
	@echo "🧪 Testing MCP PDF-to-Markdown server (stdio mode)..."
	@echo
	@echo "📋 MCP Server Configuration:"
	@echo "   Command: $(PWD)/venv/bin/python"
	@echo "   Args: $(PWD)/mcp_pdf_markdown.py"
	@echo
	@echo "To add this server to Claude Code, use:"
	@echo "  claude mcp add pdf-markdown -- \"$(PWD)/venv/bin/python\" \"$(PWD)/mcp_pdf_markdown.py\""
	@echo
	@echo "ℹ️  This is a stdio server - Claude Code starts it on-demand"
	@echo "💡 You don't need to keep this running. Use Ctrl+C to exit."
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
setup: install-python-deps
	@echo "Running tests..."
	@if $(MAKE) test; then \
		echo "✅ All tests passed!"; \
		echo "Setup complete! You can now run 'make run' to start the Python MCP server"; \
	else \
		echo "⚠️  Some tests failed, but setup is complete."; \
		echo "You can still run 'make run' to start the Python MCP server"; \
		exit 1; \
	fi


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
	@echo "  make config         - Show MCP server configuration for Claude Code"
	@echo "  make run            - Test/debug the MCP server (smoke test, not a daemon)"
	@echo "  make test           - Run Python unit tests"
	@echo "  make test-pdf       - Test PDF conversion with sample file"
	@echo "  make check-deps     - Check if dependencies are installed"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make help           - Show this help message"