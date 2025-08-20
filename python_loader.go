// python_loader.go - Optional development mode to load Python scripts from files
//
// This allows developers to test Python script changes without rebuilding
// the Go binary. Set PYTHON_SCRIPTS_DIR environment variable to use.

package main

import (
	"fmt"
	"os"
	"path/filepath"
)

// getPythonScripts returns the Python scripts either from embedded data
// or from files if in development mode
func getPythonScripts() (convertScript, analyzeScript string, err error) {
	// Check if we're in development mode
	scriptsDir := os.Getenv("PYTHON_SCRIPTS_DIR")
	if scriptsDir != "" {
		// Load from files for development
		convertPath := filepath.Join(scriptsDir, "pdf_converter.py")
		analyzePath := filepath.Join(scriptsDir, "pdf_analyzer.py")
		
		convertBytes, err := os.ReadFile(convertPath)
		if err != nil {
			return "", "", fmt.Errorf("failed to read converter script: %v", err)
		}
		
		analyzeBytes, err := os.ReadFile(analyzePath)
		if err != nil {
			return "", "", fmt.Errorf("failed to read analyzer script: %v", err)
		}
		
		return string(convertBytes), string(analyzeBytes), nil
	}
	
	// Use embedded scripts for production
	return pythonConvertScript, pythonAnalyzeScript, nil
}