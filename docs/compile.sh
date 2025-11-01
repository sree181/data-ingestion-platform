#!/bin/bash

# ============================================================================
# LaTeX Technical Documentation Compilation Script
# ============================================================================

set -e  # Exit on error

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_TEX="technical_manual.tex"
OUTPUT_PDF="technical_manual.pdf"

echo "=============================================="
echo "  Enterprise Data Ingestion Platform"
echo "  Technical Documentation Compiler"
echo "=============================================="
echo ""

# Check if LaTeX is installed
if ! command -v pdflatex &> /dev/null; then
    echo "❌ ERROR: pdflatex not found!"
    echo ""
    echo "Please install a LaTeX distribution:"
    echo "  macOS:   brew install --cask basictex"
    echo "  Ubuntu:  sudo apt-get install texlive-full"
    echo "  Windows: Download MiKTeX from https://miktex.org"
    echo ""
    exit 1
fi

echo "✅ LaTeX installation found"
echo ""

# Navigate to docs directory
cd "$DOCS_DIR"

# Clean previous build artifacts
echo "🧹 Cleaning previous build..."
rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
rm -f chapters/*.aux
echo ""

# First compilation pass
echo "📝 Compilation Pass 1/2..."
pdflatex -interaction=nonstopmode "$MAIN_TEX" > /dev/null 2>&1 || {
    echo "❌ Compilation failed! Check errors:"
    pdflatex -interaction=nonstopmode "$MAIN_TEX"
    exit 1
}
echo ""

# Second compilation pass (for cross-references)
echo "📝 Compilation Pass 2/2..."
pdflatex -interaction=nonstopmode "$MAIN_TEX" > /dev/null 2>&1 || {
    echo "❌ Compilation failed! Check errors:"
    pdflatex -interaction=nonstopmode "$MAIN_TEX"
    exit 1
}
echo ""

# Check if PDF was generated
if [ ! -f "$OUTPUT_PDF" ]; then
    echo "❌ ERROR: PDF was not generated!"
    exit 1
fi

# Get PDF file size
PDF_SIZE=$(du -h "$OUTPUT_PDF" | cut -f1)
PDF_PAGES=$(pdfinfo "$OUTPUT_PDF" 2>/dev/null | grep "Pages:" | awk '{print $2}')

echo "=============================================="
echo "  ✅ Compilation Successful!"
echo "=============================================="
echo ""
echo "📄 Output File:  $OUTPUT_PDF"
echo "📊 File Size:    $PDF_SIZE"
echo "📖 Page Count:   ${PDF_PAGES:-Unknown} pages"
echo ""
echo "🎯 Next Steps:"
echo "   1. Review the PDF: open $OUTPUT_PDF"
echo "   2. Add screenshots to docs/images/"
echo "   3. Replace placeholders with \\includegraphics"
echo "   4. Recompile with this script"
echo ""
echo "=============================================="

# Clean build artifacts
echo "🧹 Cleaning build artifacts..."
rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
rm -f chapters/*.aux
echo ""

echo "✨ Done! Your technical manual is ready."

