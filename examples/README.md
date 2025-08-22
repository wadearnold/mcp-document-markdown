# MCP Client Configuration Guides

This directory contains step-by-step configuration guides for using the MCP PDF Converter server with various AI tools that support the Model Context Protocol (MCP).

## Available Clients

- **[Claude Desktop](claude-desktop.md)** - Anthropic's desktop application
- **[Claude Code](claude-code.md)** - Anthropic's CLI tool  
- **[GitHub Copilot](github-copilot.md)** - GitHub's AI coding assistant
- **[Cursor](cursor.md)** - AI-powered code editor
- **[Generic MCP Client](generic-mcp.md)** - Configuration guide for other MCP-compatible tools

## Quick Start

1. **Setup the server**: Follow the setup instructions in the main [README.md](../README.md)
2. **Choose your client**: Select the appropriate guide from the list above
3. **Follow the setup**: Each guide provides complete setup instructions
4. **Start converting**: Use natural language prompts to convert PDFs

## Environment Variables

All configurations support these environment variables:

- **`OUTPUT_DIR`**: Directory where converted files will be saved (default: `./docs`)
- **`PYTHON_PATH`**: Path to Python interpreter (default: `python3`)
- **`MAX_FILE_SIZE`**: Maximum PDF size in MB (default: `100`)
- **`DEBUG`**: Enable debug logging (`true`/`false`, default: `false`)

## Common Usage Examples

Once configured with any MCP client, you can use prompts like:

```
Convert the PDF at /path/to/document.pdf and create a summary of each chapter
```

```
Analyze the structure of /path/to/manual.pdf without converting it
```

```
Convert /path/to/report.pdf to markdown with tables preserved and save to ./my-docs/
```

## Troubleshooting

### Universal Issues

1. **Server not found**: Ensure the Python script exists and dependencies are installed
2. **Python errors**: Verify Python dependencies are installed (`make setup`)
3. **Permission denied**: Check file permissions and directory access
4. **Configuration not loading**: Restart your AI tool after adding configuration

### Client-Specific Issues

Check the individual client guides for detailed troubleshooting steps specific to your AI tool.

## Need Help?

- Check the specific client guide for troubleshooting
- Refer to the [generic MCP guide](generic-mcp.md) for protocol details
- Test the server directly: `make run`
- Open an issue on GitHub if you encounter problems

## Contributing

If you've successfully configured this server with an MCP client not listed here, please contribute a configuration guide! Follow the format of existing guides and submit a pull request.