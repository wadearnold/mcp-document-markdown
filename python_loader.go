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

// loadPythonScript loads a single Python script by name
func loadPythonScript(scriptName string) (string, error) {
	// Check if we're in development mode
	scriptsDir := os.Getenv("PYTHON_SCRIPTS_DIR")
	if scriptsDir == "" {
		scriptsDir = "./python"  // Default to python directory
	}
	
	scriptPath := filepath.Join(scriptsDir, scriptName)
	
	// Try to read from file first (for development)
	if scriptBytes, err := os.ReadFile(scriptPath); err == nil {
		return string(scriptBytes), nil
	}
	
	// For embedded scripts in production, you would check the script name
	// and return the appropriate embedded script
	switch scriptName {
	case "pdf_converter.py":
		return pythonConvertScript, nil
	case "pdf_analyzer.py":
		return pythonAnalyzeScript, nil
	case "pdf_to_rag.py":
		// For now, try to load from file only since it's not embedded yet
		scriptBytes, err := os.ReadFile(scriptPath)
		if err != nil {
			return "", fmt.Errorf("failed to read RAG script: %v", err)
		}
		return string(scriptBytes), nil
	default:
		return "", fmt.Errorf("unknown script: %s", scriptName)
	}
}