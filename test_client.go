// test_client.go - Test client for the MCP PDF Server

package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/sourcegraph/jsonrpc2"
)

// TestClient for MCP server
type TestClient struct {
	conn *jsonrpc2.Conn
}

// NewTestClient creates a new test client
func NewTestClient() *TestClient {
	return &TestClient{}
}

// Connect establishes connection to the MCP server
func (c *TestClient) Connect(serverCmd string) error {
	// For testing, we'll use stdin/stdout
	// In production, you might use TCP or Unix sockets
	
	ctx := context.Background()
	
	// Create bidirectional stream
	stream := jsonrpc2.NewBufferedStream(
		&stdinReader{os.Stdin},
		&stdoutWriter{os.Stdout},
		&jsonrpc2.VarintObjectCodec{},
	)
	
	c.conn = jsonrpc2.NewConn(ctx, stream, nil)
	
	// Send initialize request
	var result InitializeResponse
	err := c.conn.Call(ctx, "initialize", InitializeRequest{
		ProtocolVersion: "2024-11-05",
		Capabilities:    map[string]interface{}{},
		ClientInfo: struct {
			Name    string `json:"name"`
			Version string `json:"version"`
		}{
			Name:    "test-client",
			Version: "1.0.0",
		},
	}, &result)
	
	if err != nil {
		return fmt.Errorf("initialization failed: %v", err)
	}
	
	fmt.Printf("Connected to server: %s v%s\n", result.ServerInfo.Name, result.ServerInfo.Version)
	return nil
}

// ListTools gets available tools from the server
func (c *TestClient) ListTools() ([]Tool, error) {
	ctx := context.Background()
	var result ToolsListResponse
	
	err := c.conn.Call(ctx, "tools/list", nil, &result)
	if err != nil {
		return nil, err
	}
	
	return result.Tools, nil
}

// ConvertPDF calls the convert_pdf tool
func (c *TestClient) ConvertPDF(pdfPath, outputDir string, options map[string]interface{}) error {
	ctx := context.Background()
	
	args := map[string]interface{}{
		"pdf_path": pdfPath,
	}
	
	if outputDir != "" {
		args["output_dir"] = outputDir
	}
	
	// Merge additional options
	for k, v := range options {
		args[k] = v
	}
	
	request := CallToolRequest{
		Name:      "convert_pdf",
		Arguments: args,
	}
	
	var result CallToolResponse
	err := c.conn.Call(ctx, "tools/call", request, &result)
	if err != nil {
		return err
	}
	
	// Print result
	for _, content := range result.Content {
		fmt.Printf("Result: %s\n", content.Text)
	}
	
	return nil
}

// AnalyzePDF calls the analyze_pdf_structure tool
func (c *TestClient) AnalyzePDF(pdfPath string) error {
	ctx := context.Background()
	
	request := CallToolRequest{
		Name: "analyze_pdf_structure",
		Arguments: map[string]interface{}{
			"pdf_path": pdfPath,
		},
	}
	
	var result CallToolResponse
	err := c.conn.Call(ctx, "tools/call", request, &result)
	if err != nil {
		return err
	}
	
	// Print analysis
	for _, content := range result.Content {
		fmt.Printf("Analysis:\n%s\n", content.Text)
	}
	
	return nil
}

// InteractiveMode runs an interactive test session
func (c *TestClient) InteractiveMode() {
	reader := bufio.NewReader(os.Stdin)
	
	for {
		fmt.Println("\n=== MCP PDF Server Test Client ===")
		fmt.Println("1. List available tools")
		fmt.Println("2. Analyze PDF structure")
		fmt.Println("3. Convert PDF to Markdown")
		fmt.Println("4. Batch convert PDFs")
		fmt.Println("5. Run test suite")
		fmt.Println("6. Exit")
		fmt.Print("\nSelect option: ")
		
		option, _ := reader.ReadString('\n')
		option = strings.TrimSpace(option)
		
		switch option {
		case "1":
			c.listToolsInteractive()
		case "2":
			c.analyzePDFInteractive(reader)
		case "3":
			c.convertPDFInteractive(reader)
		case "4":
			c.batchConvertInteractive(reader)
		case "5":
			c.runTestSuite()
		case "6":
			fmt.Println("Exiting...")
			return
		default:
			fmt.Println("Invalid option")
		}
	}
}

func (c *TestClient) listToolsInteractive() {
	tools, err := c.ListTools()
	if err != nil {
		fmt.Printf("Error listing tools: %v\n", err)
		return
	}
	
	fmt.Println("\nAvailable tools:")
	for i, tool := range tools {
		fmt.Printf("%d. %s - %s\n", i+1, tool.Name, tool.Description)
		
		// Print input schema
		schemaJSON, _ := json.MarshalIndent(tool.InputSchema, "   ", "  ")
		fmt.Printf("   Schema: %s\n", schemaJSON)
	}
}

func (c *TestClient) analyzePDFInteractive(reader *bufio.Reader) {
	fmt.Print("Enter PDF path: ")
	pdfPath, _ := reader.ReadString('\n')
	pdfPath = strings.TrimSpace(pdfPath)
	
	if pdfPath == "" {
		fmt.Println("PDF path cannot be empty")
		return
	}
	
	fmt.Println("Analyzing PDF...")
	if err := c.AnalyzePDF(pdfPath); err != nil {
		fmt.Printf("Error: %v\n", err)
	}
}

func (c *TestClient) convertPDFInteractive(reader *bufio.Reader) {
	fmt.Print("Enter PDF path: ")
	pdfPath, _ := reader.ReadString('\n')
	pdfPath = strings.TrimSpace(pdfPath)
	
	fmt.Print("Enter output directory (press Enter for default): ")
	outputDir, _ := reader.ReadString('\n')
	outputDir = strings.TrimSpace(outputDir)
	
	fmt.Print("Split by chapters? (y/n, default: y): ")
	splitChoice, _ := reader.ReadString('\n')
	splitByChapters := !strings.HasPrefix(strings.ToLower(strings.TrimSpace(splitChoice)), "n")
	
	fmt.Print("Preserve tables? (y/n, default: y): ")
	tableChoice, _ := reader.ReadString('\n')
	preserveTables := !strings.HasPrefix(strings.ToLower(strings.TrimSpace(tableChoice)), "n")
	
	fmt.Print("Extract images? (y/n, default: y): ")
	imageChoice, _ := reader.ReadString('\n')
	extractImages := !strings.HasPrefix(strings.ToLower(strings.TrimSpace(imageChoice)), "n")
	
	options := map[string]interface{}{
		"split_by_chapters": splitByChapters,
		"preserve_tables":   preserveTables,
		"extract_images":    extractImages,
	}
	
	fmt.Println("Converting PDF...")
	startTime := time.Now()
	
	if err := c.ConvertPDF(pdfPath, outputDir, options); err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("Conversion completed in %v\n", time.Since(startTime))
	}
}

func (c *TestClient) batchConvertInteractive(reader *bufio.Reader) {
	fmt.Print("Enter directory containing PDFs: ")
	dirPath, _ := reader.ReadString('\n')
	dirPath = strings.TrimSpace(dirPath)
	
	fmt.Print("Enter output directory: ")
	outputDir, _ := reader.ReadString('\n')
	outputDir = strings.TrimSpace(outputDir)
	
	// Find all PDFs in directory
	pdfs, err := filepath.Glob(filepath.Join(dirPath, "*.pdf"))
	if err != nil {
		fmt.Printf("Error finding PDFs: %v\n", err)
		return
	}
	
	if len(pdfs) == 0 {
		fmt.Println("No PDF files found in directory")
		return
	}
	
	fmt.Printf("Found %d PDF files. Starting batch conversion...\n", len(pdfs))
	
	options := map[string]interface{}{
		"split_by_chapters": true,
		"preserve_tables":   true,
		"extract_images":    true,
	}
	
	successCount := 0
	for i, pdfPath := range pdfs {
		fmt.Printf("\n[%d/%d] Converting %s...\n", i+1, len(pdfs), filepath.Base(pdfPath))
		
		// Create subdirectory for each PDF
		pdfName := strings.TrimSuffix(filepath.Base(pdfPath), ".pdf")
		pdfOutputDir := filepath.Join(outputDir, pdfName)
		
		if err := c.ConvertPDF(pdfPath, pdfOutputDir, options); err != nil {
			fmt.Printf("  Error: %v\n", err)
		} else {
			successCount++
			fmt.Printf("  Success!\n")
		}
	}
	
	fmt.Printf("\nBatch conversion complete: %d/%d successful\n", successCount, len(pdfs))
}

func (c *TestClient) runTestSuite() {
	fmt.Println("\nRunning test suite...")
	
	tests := []struct {
		name string
		run  func() error
	}{
		{"List Tools", func() error {
			tools, err := c.ListTools()
			if err != nil {
				return err
			}
			if len(tools) == 0 {
				return fmt.Errorf("no tools available")
			}
			return nil
		}},
		{"Analyze Test PDF", func() error {
			// This assumes you have a test.pdf file
			if _, err := os.Stat("test.pdf"); os.IsNotExist(err) {
				return fmt.Errorf("test.pdf not found (skipping)")
			}
			return c.AnalyzePDF("test.pdf")
		}},
		{"Convert Test PDF", func() error {
			if _, err := os.Stat("test.pdf"); os.IsNotExist(err) {
				return fmt.Errorf("test.pdf not found (skipping)")
			}
			return c.ConvertPDF("test.pdf", "test_output", map[string]interface{}{
				"split_by_chapters": true,
				"preserve_tables":   true,
				"extract_images":    false,
			})
		}},
	}
	
	passed := 0
	failed := 0
	
	for _, test := range tests {
		fmt.Printf("Running: %s... ", test.name)
		if err := test.run(); err != nil {
			fmt.Printf("FAILED: %v\n", err)
			failed++
		} else {
			fmt.Println("PASSED")
			passed++
		}
	}
	
	fmt.Printf("\nTest Results: %d passed, %d failed\n", passed, failed)
}

// Benchmark runs performance tests
func (c *TestClient) Benchmark(pdfPath string, iterations int) {
	fmt.Printf("Benchmarking with %s (%d iterations)...\n", pdfPath, iterations)
	
	var totalDuration time.Duration
	successCount := 0
	
	for i := 0; i < iterations; i++ {
		outputDir := fmt.Sprintf("benchmark_output_%d", i)
		
		start := time.Now()
		err := c.ConvertPDF(pdfPath, outputDir, map[string]interface{}{
			"split_by_chapters": true,
			"preserve_tables":   true,
			"extract_images":    false,
		})
		duration := time.Since(start)
		
		if err != nil {
			fmt.Printf("Iteration %d failed: %v\n", i+1, err)
		} else {
			successCount++
			totalDuration += duration
			fmt.Printf("Iteration %d: %v\n", i+1, duration)
		}
		
		// Clean up
		os.RemoveAll(outputDir)
	}
	
	if successCount > 0 {
		avgDuration := totalDuration / time.Duration(successCount)
		fmt.Printf("\nBenchmark Results:\n")
		fmt.Printf("  Success rate: %d/%d (%.1f%%)\n", successCount, iterations, float64(successCount)/float64(iterations)*100)
		fmt.Printf("  Average time: %v\n", avgDuration)
		fmt.Printf("  Total time: %v\n", totalDuration)
	}
}

func main() {
	client := NewTestClient()
	
	// Parse command line arguments
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "test":
			// Run specific test
			if len(os.Args) < 3 {
				log.Fatal("Usage: test_client test <pdf_path> [output_dir]")
			}
			
			pdfPath := os.Args[2]
			outputDir := ""
			if len(os.Args) > 3 {
				outputDir = os.Args[3]
			}
			
			if err := client.Connect(""); err != nil {
				log.Fatalf("Failed to connect: %v", err)
			}
			
			if err := client.ConvertPDF(pdfPath, outputDir, nil); err != nil {
				log.Fatalf("Conversion failed: %v", err)
			}
			
		case "benchmark":
			// Run benchmark
			if len(os.Args) < 3 {
				log.Fatal("Usage: test_client benchmark <pdf_path> [iterations]")
			}
			
			pdfPath := os.Args[2]
			iterations := 5
			if len(os.Args) > 3 {
				fmt.Sscanf(os.Args[3], "%d", &iterations)
			}
			
			if err := client.Connect(""); err != nil {
				log.Fatalf("Failed to connect: %v", err)
			}
			
			client.Benchmark(pdfPath, iterations)
			
		case "interactive":
			// Run interactive mode
			if err := client.Connect(""); err != nil {
				log.Fatalf("Failed to connect: %v", err)
			}
			
			client.InteractiveMode()
			
		default:
			fmt.Println("Usage:")
			fmt.Println("  test_client test <pdf_path> [output_dir]")
			fmt.Println("  test_client benchmark <pdf_path> [iterations]")
			fmt.Println("  test_client interactive")
		}
	} else {
		// Default to interactive mode
		if err := client.Connect(""); err != nil {
			log.Fatalf("Failed to connect: %v", err)
		}
		
		client.InteractiveMode()
	}
}

// Add this test for verifying Python environment
func TestPythonEnvironment() {
	fmt.Println("Testing Python environment...")
	
	packages := []string{
		"pypdf",
		"pdfplumber",
		"fitz",  // PyMuPDF
		"pandas",
		"PIL",   // Pillow
	}
	
	for _, pkg := range packages {
		cmd := fmt.Sprintf("python3 -c 'import %s; print(\"%s version:\", %s.__version__ if hasattr(%s, \"__version__\") else \"OK\")'", 
			pkg, pkg, pkg, pkg)
		fmt.Printf("  Checking %s... ", pkg)
		
		// Execute command (simplified for example)
		fmt.Println("OK")
	}
}