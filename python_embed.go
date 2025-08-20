// python_embed.go - Embeds Python scripts at compile time
// 
// This file uses Go's embed package to include Python scripts in the binary.
// The Python files can be edited separately in the python/ directory
// and are automatically embedded when building the binary.

package main

import (
	_ "embed"
)

// Embed Python scripts at compile time
// These files are maintained separately in the python/ directory
// for easier development and testing

//go:embed python/pdf_converter.py
var pythonConvertScript string

//go:embed python/pdf_analyzer.py
var pythonAnalyzeScript string