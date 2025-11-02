#!/bin/bash

# ============================================================================
# Beamer Slides Compilation Script
# ============================================================================

set -e

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLIDES_TEX="RL_Explanation_Slides.tex"
OUTPUT_PDF="RL_Explanation_Slides.pdf"

echo "=============================================="
echo "  RL System Explanation - Beamer Slides"
echo "  Compilation Script"
echo "=============================================="
echo ""

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "❌ ERROR: pdflatex not found!"
    echo ""
    echo "Please install a LaTeX distribution:"
    echo "  macOS:   brew install --cask basictex"
    echo "           Then run: eval \"\$(/usr/libexec/path_helper)\""
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
rm -f *.aux *.log *.out *.nav *.snm *.toc *.vrb *.fls *.fdb_latexmk *.synctex.gz
echo ""

# First compilation pass
echo "📝 Compilation Pass 1/2..."
pdflatex -interaction=nonstopmode "$SLIDES_TEX" > /dev/null 2>&1 || {
    echo "❌ Compilation failed! Check errors:"
    pdflatex -interaction=nonstopmode "$SLIDES_TEX"
    exit 1
}
echo ""

# Second compilation pass (for navigation)
echo "📝 Compilation Pass 2/2..."
pdflatex -interaction=nonstopmode "$SLIDES_TEX" > /dev/null 2>&1 || {
    echo "❌ Compilation failed! Check errors:"
    pdflatex -interaction=nonstopmode "$SLIDES_TEX"
    exit 1
}
echo ""

# Check if PDF was generated
if [ ! -f "$OUTPUT_PDF" ]; then
    echo "❌ ERROR: PDF was not generated!"
    exit 1
fi

# Get PDF file size and page count
PDF_SIZE=$(du -h "$OUTPUT_PDF" | cut -f1)
PDF_PAGES=$(pdfinfo "$OUTPUT_PDF" 2>/dev/null | grep "Pages:" | awk '{print $2}')

echo "=============================================="
echo "  ✅ Compilation Successful!"
echo "=============================================="
echo ""
echo "📄 Output File:  $OUTPUT_PDF"
echo "📊 File Size:    $PDF_SIZE"
echo "📖 Slide Count:  ${PDF_PAGES:-Unknown} slides"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open the PDF: open $OUTPUT_PDF"
echo "   2. Upload to Overleaf for editing"
echo "   3. Present to stakeholders!"
echo ""
echo "=============================================="

# Clean build artifacts
echo "🧹 Cleaning build artifacts..."
rm -f *.aux *.log *.out *.nav *.snm *.toc *.vrb *.fls *.fdb_latexmk *.synctex.gz
echo ""

echo "✨ Done! Your Beamer presentation is ready."

