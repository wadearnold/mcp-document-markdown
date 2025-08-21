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
		// Try modular converter first, fallback to monolithic
		convertPath := filepath.Join(scriptsDir, "modular_pdf_converter.py")
		if _, err := os.Stat(convertPath); err == nil {
			// Load modular converter
			convertBytes, err := os.ReadFile(convertPath)
			if err != nil {
				return "", "", fmt.Errorf("failed to read modular converter script: %v", err)
			}
			convertScript = string(convertBytes)
		} else {
			// Fallback to original converter
			convertPath = filepath.Join(scriptsDir, "pdf_converter.py")
			convertBytes, err := os.ReadFile(convertPath)
			if err != nil {
				return "", "", fmt.Errorf("failed to read converter script: %v", err)
			}
			convertScript = string(convertBytes)
		}
		
		// Load analyzer
		analyzePath := filepath.Join(scriptsDir, "pdf_analyzer.py")
		analyzeBytes, err := os.ReadFile(analyzePath)
		if err != nil {
			return "", "", fmt.Errorf("failed to read analyzer script: %v", err)
		}
		analyzeScript = string(analyzeBytes)
		
		return convertScript, analyzeScript, nil
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
	case "modular_pdf_converter.py":
		// For now, try to load from file only since it's not embedded yet
		scriptBytes, err := os.ReadFile(scriptPath)
		if err != nil {
			return "", fmt.Errorf("failed to read modular converter script: %v", err)
		}
		return string(scriptBytes), nil
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

// loadModularPythonFiles loads all Python files needed for the modular converter
func loadModularPythonFiles(baseDir string) (map[string]string, error) {
	files := make(map[string]string)
	
	// Define the modular structure files to load
	moduleFiles := []string{
		"modular_pdf_converter.py",
		"utils/token_counter.py",
		"utils/text_utils.py", 
		"utils/file_utils.py",
		"processors/__init__.py",
		"processors/pdf_extractor.py",
		"processors/table_processor.py",
		"processors/chunking_engine.py",
		"processors/concept_mapper.py",
		"processors/cross_referencer.py",
		"processors/summary_generator.py",
	}
	
	// Load each file
	for _, fileName := range moduleFiles {
		filePath := filepath.Join(baseDir, fileName)
		
		// Check if file exists
		if _, err := os.Stat(filePath); os.IsNotExist(err) {
			continue // Skip missing optional files
		}
		
		// Read file content
		content, err := os.ReadFile(filePath)
		if err != nil {
			return nil, fmt.Errorf("failed to read %s: %v", fileName, err)
		}
		
		files[fileName] = string(content)
	}
	
	return files, nil
}

// isModularConverterAvailable checks if the modular converter structure is available
func isModularConverterAvailable(baseDir string) bool {
	// Check for key modular files
	requiredFiles := []string{
		"modular_pdf_converter.py",
		"utils/token_counter.py",
		"processors/pdf_extractor.py",
	}
	
	for _, fileName := range requiredFiles {
		filePath := filepath.Join(baseDir, fileName)
		if _, err := os.Stat(filePath); os.IsNotExist(err) {
			return false
		}
	}
	
	return true
}