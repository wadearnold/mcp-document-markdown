package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/sourcegraph/jsonrpc2"
)

// MCPServer represents our MCP server
type MCPServer struct {
	pythonPath string
	outputDir  string
}

// Request/Response types for MCP protocol
type InitializeRequest struct {
	ProtocolVersion string                 `json:"protocolVersion"`
	Capabilities    map[string]interface{} `json:"capabilities"`
	ClientInfo      struct {
		Name    string `json:"name"`
		Version string `json:"version"`
	} `json:"clientInfo"`
}

type InitializeResponse struct {
	ProtocolVersion string                 `json:"protocolVersion"`
	Capabilities    map[string]interface{} `json:"capabilities"`
	ServerInfo      struct {
		Name    string `json:"name"`
		Version string `json:"version"`
	} `json:"serverInfo"`
}

type ToolsListResponse struct {
	Tools []Tool `json:"tools"`
}

type Tool struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	InputSchema map[string]interface{} `json:"inputSchema"`
}

type CallToolRequest struct {
	Name      string                 `json:"name"`
	Arguments map[string]interface{} `json:"arguments"`
}

type CallToolResponse struct {
	Content []ToolContent `json:"content"`
}

type ToolContent struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

// NewMCPServer creates a new MCP server instance
func NewMCPServer() *MCPServer {
	pythonPath := os.Getenv("PYTHON_PATH")
	if pythonPath == "" {
		// Try to find the best Python installation
		candidates := []string{
			"./venv/bin/python",  // Local venv (if running from project dir)
			"/Users/wadearnold/Documents/GitHub/wadearnold/mcp-pdf-markdown/venv/bin/python", // Absolute path to our venv
			"python3",            // System Python as fallback
		}
		
		for _, candidate := range candidates {
			if _, err := os.Stat(candidate); err == nil {
				pythonPath = candidate
				break
			}
		}
		
		// Final fallback
		if pythonPath == "" {
			pythonPath = "python3"
		}
	}
	
	outputDir := os.Getenv("OUTPUT_DIR")
	if outputDir == "" {
		outputDir = "./docs"
	}
	
	return &MCPServer{
		pythonPath: pythonPath,
		outputDir:  outputDir,
	}
}

// Handle processes incoming JSON-RPC requests
func (s *MCPServer) Handle(ctx context.Context, conn *jsonrpc2.Conn, req *jsonrpc2.Request) (interface{}, error) {
	log.Printf("Received request: method=%s, id=%v", req.Method, req.ID)
	switch req.Method {
	case "initialize":
		var params InitializeRequest
		if err := json.Unmarshal(*req.Params, &params); err != nil {
			return nil, err
		}
		return s.handleInitialize(params)
	
	case "tools/list":
		return s.handleToolsList()
	
	case "tools/call":
		var params CallToolRequest
		if err := json.Unmarshal(*req.Params, &params); err != nil {
			return nil, err
		}
		return s.handleToolCall(params)
	
	default:
		return nil, &jsonrpc2.Error{
			Code:    jsonrpc2.CodeMethodNotFound,
			Message: fmt.Sprintf("method not found: %s", req.Method),
		}
	}
}

// handleInitialize handles the initialization request
func (s *MCPServer) handleInitialize(req InitializeRequest) (*InitializeResponse, error) {
	// Check Python dependencies
	if err := s.checkDependencies(); err != nil {
		return nil, fmt.Errorf("dependency check failed: %v", err)
	}

	return &InitializeResponse{
		ProtocolVersion: "2024-11-05",
		Capabilities: map[string]interface{}{
			"tools": map[string]interface{}{},
		},
		ServerInfo: struct {
			Name    string `json:"name"`
			Version string `json:"version"`
		}{
			Name:    "mcp-pdf-markdown",
			Version: "1.0.0",
		},
	}, nil
}

// handleToolsList returns available tools
func (s *MCPServer) handleToolsList() (*ToolsListResponse, error) {
	tools := []Tool{
		{
			Name:        "convert_pdf",
			Description: "Convert a PDF file to organized markdown files with preserved tables and graphs",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"pdf_path": map[string]interface{}{
						"type":        "string",
						"description": "Path to the PDF file to convert",
					},
					"output_dir": map[string]interface{}{
						"type":        "string",
						"description": "Directory where markdown files will be saved",
					},
					"split_by_chapters": map[string]interface{}{
						"type":        "boolean",
						"description": "Whether to split the document by chapters",
						"default":     true,
					},
					"preserve_tables": map[string]interface{}{
						"type":        "boolean",
						"description": "Whether to preserve table formatting",
						"default":     true,
					},
					"extract_images": map[string]interface{}{
						"type":        "boolean",
						"description": "Whether to extract and reference images",
						"default":     true,
					},
					"enable_chunking": map[string]interface{}{
						"type":        "boolean",
						"description": "Whether to enable smart chunking by token limits for optimal LLM context usage",
						"default":     true,
					},
				},
				"required": []string{"pdf_path"},
			},
		},
		{
			Name:        "analyze_pdf_structure",
			Description: "Analyze PDF structure to identify chapters, sections, and other elements",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"pdf_path": map[string]interface{}{
						"type":        "string",
						"description": "Path to the PDF file to analyze",
					},
				},
				"required": []string{"pdf_path"},
			},
		},
	}

	return &ToolsListResponse{Tools: tools}, nil
}

// handleToolCall executes the requested tool
func (s *MCPServer) handleToolCall(req CallToolRequest) (*CallToolResponse, error) {
	switch req.Name {
	case "convert_pdf":
		return s.convertPDF(req.Arguments)
	case "analyze_pdf_structure":
		return s.analyzePDFStructure(req.Arguments)
	default:
		return nil, fmt.Errorf("unknown tool: %s", req.Name)
	}
}

// convertPDF handles the PDF conversion process
func (s *MCPServer) convertPDF(args map[string]interface{}) (*CallToolResponse, error) {
	pdfPath, ok := args["pdf_path"].(string)
	if !ok {
		return nil, fmt.Errorf("pdf_path is required")
	}

	outputDir := s.outputDir
	if dir, ok := args["output_dir"].(string); ok {
		outputDir = dir
	}

	preserveTables := true
	if preserve, ok := args["preserve_tables"].(bool); ok {
		preserveTables = preserve
	}

	extractImages := true
	if extract, ok := args["extract_images"].(bool); ok {
		extractImages = extract
	}

	enableChunking := true
	if chunking, ok := args["enable_chunking"].(bool); ok {
		enableChunking = chunking
	}

	// Create output directory
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create output directory: %v", err)
	}

	// Convert PDF using Python script (handles all organization automatically)
	log.Printf("Converting PDF: %s", pdfPath)
	err := s.runPythonConverter(pdfPath, outputDir, preserveTables, extractImages, enableChunking)
	if err != nil {
		return nil, fmt.Errorf("PDF conversion failed: %v", err)
	}

	// Check what was created and report back
	var resultMessage string
	
	// Check for organized sections directory
	sectionsDir := filepath.Join(outputDir, "sections")
	if files, err := os.ReadDir(sectionsDir); err == nil && len(files) > 0 {
		// Count section files (exclude index.md and other metadata files)
		sectionCount := 0
		for _, file := range files {
			if strings.HasSuffix(file.Name(), ".md") && !strings.HasPrefix(file.Name(), "00-") {
				sectionCount++
			}
		}
		
		// Check for additional organized content
		hasComplete := false
		hasSummary := false
		hasIndex := false
		hasMetadata := false
		hasLLMReport := false
		hasAPIEndpoints := false
		apiEndpointCount := 0
		
		if _, err := os.Stat(filepath.Join(outputDir, "complete", "full-document.md")); err == nil {
			hasComplete = true
		}
		if _, err := os.Stat(filepath.Join(outputDir, "summary.md")); err == nil {
			hasSummary = true
		}
		if _, err := os.Stat(filepath.Join(outputDir, "index.md")); err == nil {
			hasIndex = true
		}
		if _, err := os.Stat(filepath.Join(outputDir, "metadata.json")); err == nil {
			hasMetadata = true
		}
		if _, err := os.Stat(filepath.Join(outputDir, "llm-compatibility-report.md")); err == nil {
			hasLLMReport = true
		}
		
		// Check for API endpoints directory
		apiDir := filepath.Join(outputDir, "api-endpoints")
		if files, err := os.ReadDir(apiDir); err == nil {
			hasAPIEndpoints = true
			// Count .md files (excluding README.md)
			for _, file := range files {
				if strings.HasSuffix(file.Name(), ".md") && file.Name() != "README.md" {
					apiEndpointCount++
				}
			}
		}
		
		// Check for chunked sections directory
		hasChunkedSections := false
		chunkedSectionCount := 0
		chunkedDir := filepath.Join(outputDir, "chunked")
		if _, err := os.Stat(chunkedDir); err == nil {
			hasChunkedSections = true
			// Count all chunk files across all size directories
			sizeDirs := []string{"small", "medium", "large", "xlarge"}
			for _, sizeDir := range sizeDirs {
				sizePath := filepath.Join(chunkedDir, sizeDir)
				if files, err := os.ReadDir(sizePath); err == nil {
					for _, file := range files {
						if strings.HasSuffix(file.Name(), ".md") {
							chunkedSectionCount++
						}
					}
				}
			}
		}
		
		var extras []string
		if hasIndex {
			extras = append(extras, "navigation index")
		}
		if hasSummary {
			extras = append(extras, "document summary")
		}
		if hasComplete {
			extras = append(extras, "complete document")
		}
		if hasMetadata {
			extras = append(extras, "metadata.json")
		}
		if hasLLMReport {
			extras = append(extras, "LLM compatibility report")
		}
		if hasAPIEndpoints {
			extras = append(extras, fmt.Sprintf("%d API endpoints", apiEndpointCount))
		}
		if hasChunkedSections {
			extras = append(extras, fmt.Sprintf("%d smart chunks", chunkedSectionCount))
		}
		
		extrasStr := ""
		if len(extras) > 0 {
			extrasStr = fmt.Sprintf(" with %s", strings.Join(extras, ", "))
		}
		
		resultMessage = fmt.Sprintf("Successfully converted PDF to %d organized sections%s in %s", 
			sectionCount, extrasStr, outputDir)
	} else {
		// Fallback to single file
		resultMessage = fmt.Sprintf("Successfully converted PDF to markdown in %s", outputDir)
	}

	return &CallToolResponse{
		Content: []ToolContent{
			{
				Type: "text",
				Text: resultMessage,
			},
		},
	}, nil
}

// analyzePDFStructure analyzes the structure of a PDF
func (s *MCPServer) analyzePDFStructure(args map[string]interface{}) (*CallToolResponse, error) {
	pdfPath, ok := args["pdf_path"].(string)
	if !ok {
		return nil, fmt.Errorf("pdf_path is required")
	}

	// Get Python scripts (embedded or from files in dev mode)
	_, analyzeScript, err := getPythonScripts()
	if err != nil {
		return nil, fmt.Errorf("failed to load Python scripts: %v", err)
	}
	
	// Run Python script to analyze PDF structure
	cmd := exec.Command(s.pythonPath, "-", pdfPath)
	cmd.Stdin = strings.NewReader(analyzeScript)
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("analysis failed: %v\nOutput: %s", err, output)
	}

	return &CallToolResponse{
		Content: []ToolContent{
			{
				Type: "text",
				Text: string(output),
			},
		},
	}, nil
}

// runPythonConverter executes the Python PDF conversion script
func (s *MCPServer) runPythonConverter(pdfPath, outputDir string, preserveTables, extractImages, enableChunking bool) error {
	// Get Python scripts (embedded or from files in dev mode)
	convertScript, _, err := getPythonScripts()
	if err != nil {
		return fmt.Errorf("failed to load Python scripts: %v", err)
	}
	
	args := []string{"-", pdfPath, outputDir}
	if preserveTables {
		args = append(args, "--preserve-tables")
	}
	if extractImages {
		args = append(args, "--extract-images")
	}
	if enableChunking {
		args = append(args, "--enable-chunking")
	}

	cmd := exec.Command(s.pythonPath, args...)
	cmd.Stdin = strings.NewReader(convertScript)
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("conversion failed: %v\nOutput: %s", err, output)
	}

	// Clean up temporary file if it exists
	mdPath := filepath.Join(outputDir, "temp_converted.md")
	if _, err := os.Stat(mdPath); err == nil {
		if removeErr := os.Remove(mdPath); removeErr != nil {
			log.Printf("Warning: failed to remove temporary file %s: %v", mdPath, removeErr)
		}
	}

	return nil
}

// Chapter represents a document chapter
type Chapter struct {
	Number   int
	Title    string
	Content  string
	FileName string
}

// splitIntoChapters splits markdown content into chapters
func (s *MCPServer) splitIntoChapters(content string, outputDir string) ([]Chapter, error) {
	// Patterns for detecting chapters
	chapterPatterns := []*regexp.Regexp{
		regexp.MustCompile(`(?m)^#\s+(?:Chapter|CHAPTER)\s+(\d+)[:\s]+(.+)$`),
		regexp.MustCompile(`(?m)^#\s+(\d+)\.\s+(.+)$`),
		regexp.MustCompile(`(?m)^##\s+(?:Chapter|CHAPTER)\s+(\d+)[:\s]+(.+)$`),
	}

	var chapters []Chapter
	lines := strings.Split(content, "\n")
	currentChapter := Chapter{Number: 0, Title: "Introduction", Content: ""}
	chapterStarted := false

	for i, line := range lines {
		isChapterHeader := false
		
		for _, pattern := range chapterPatterns {
			if matches := pattern.FindStringSubmatch(line); matches != nil {
				// Save previous chapter if exists
				if chapterStarted && currentChapter.Content != "" {
					currentChapter.Content = strings.TrimSpace(currentChapter.Content)
					currentChapter.FileName = s.generateFileName(currentChapter.Number, currentChapter.Title)
					chapters = append(chapters, currentChapter)
				}

				// Start new chapter
				chapterNum := 1
				if num := parseChapterNumber(matches[1]); num > 0 {
					chapterNum = num
				}
				
				currentChapter = Chapter{
					Number:  chapterNum,
					Title:   strings.TrimSpace(matches[2]),
					Content: line + "\n",
				}
				chapterStarted = true
				isChapterHeader = true
				break
			}
		}

		if !isChapterHeader && (chapterStarted || i < 50) {
			currentChapter.Content += line + "\n"
			if !chapterStarted && strings.TrimSpace(line) != "" {
				chapterStarted = true
			}
		}
	}

	// Add the last chapter
	if currentChapter.Content != "" {
		currentChapter.Content = strings.TrimSpace(currentChapter.Content)
		currentChapter.FileName = s.generateFileName(currentChapter.Number, currentChapter.Title)
		chapters = append(chapters, currentChapter)
	}

	// Write chapters to files
	for _, chapter := range chapters {
		filePath := filepath.Join(outputDir, chapter.FileName)
		if err := os.WriteFile(filePath, []byte(chapter.Content), 0644); err != nil {
			return nil, fmt.Errorf("failed to write chapter %d: %v", chapter.Number, err)
		}
	}

	return chapters, nil
}

// generateFileName creates a filename for a chapter
func (s *MCPServer) generateFileName(number int, title string) string {
	// Clean title for filename
	cleanTitle := regexp.MustCompile(`[^a-zA-Z0-9\s-]`).ReplaceAllString(title, "")
	cleanTitle = strings.ToLower(strings.TrimSpace(cleanTitle))
	cleanTitle = regexp.MustCompile(`\s+`).ReplaceAllString(cleanTitle, "_")
	
	if len(cleanTitle) > 50 {
		cleanTitle = cleanTitle[:50]
	}
	
	return fmt.Sprintf("%02d_%s.md", number, cleanTitle)
}

// createTableOfContents creates a table of contents file
func (s *MCPServer) createTableOfContents(chapters []Chapter, outputPath string) error {
	var toc strings.Builder
	toc.WriteString("# Table of Contents\n\n")
	
	for _, chapter := range chapters {
		toc.WriteString(fmt.Sprintf("- [Chapter %d: %s](%s)\n", 
			chapter.Number, chapter.Title, chapter.FileName))
	}
	
	return os.WriteFile(outputPath, []byte(toc.String()), 0644)
}

// parseChapterNumber extracts chapter number from string
func parseChapterNumber(s string) int {
	var num int
	fmt.Sscanf(s, "%d", &num)
	return num
}

// checkDependencies verifies Python and required packages are installed
func (s *MCPServer) checkDependencies() error {
	// Check Python
	cmd := exec.Command(s.pythonPath, "--version")
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("Python not found: %v", err)
	}

	// Check required Python packages  
	checkScript := `
import sys
packages = ["pypdf", "pdfplumber", "markdown", "pandas", "PIL"]
missing = []
for pkg in packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print("Missing packages: " + ", ".join(missing))
    sys.exit(1)
print("All dependencies installed")
`

	cmd = exec.Command(s.pythonPath, "-c", checkScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("dependency check failed: %s\nPlease install: pip install pypdf pdfplumber markdown pandas pillow pymupdf", output)
	}

	return nil
}

func main() {
	server := NewMCPServer()

	// Set up JSON-RPC connection
	// Create a combined ReadWriteCloser
	rwc := &stdioReadWriteCloser{
		reader: &stdinReader{os.Stdin},
		writer: &stdoutWriter{os.Stdout},
	}
	
	conn := jsonrpc2.NewConn(
		context.Background(),
		jsonrpc2.NewPlainObjectStream(rwc),
		jsonrpc2.HandlerWithError(server.Handle),
	)

	log.SetOutput(os.Stderr) // Ensure logs go to stderr, not stdout
	log.Println("MCP PDF-to-Markdown Converter started")
	<-conn.DisconnectNotify()
	log.Println("Server disconnected")
}

// IO helpers for JSON-RPC
type stdinReader struct{ *os.File }
func (r stdinReader) Read(p []byte) (int, error) { return r.File.Read(p) }
func (r stdinReader) Close() error { return nil }

type stdoutWriter struct{ *os.File }
func (w stdoutWriter) Write(p []byte) (int, error) { return w.File.Write(p) }
func (w stdoutWriter) Close() error { return nil }

type stdioReadWriteCloser struct {
	reader *stdinReader
	writer *stdoutWriter
}

func (rwc *stdioReadWriteCloser) Read(p []byte) (int, error) {
	return rwc.reader.Read(p)
}

func (rwc *stdioReadWriteCloser) Write(p []byte) (int, error) {
	return rwc.writer.Write(p)
}

func (rwc *stdioReadWriteCloser) Close() error {
	return nil
}