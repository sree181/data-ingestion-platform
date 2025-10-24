#!/bin/bash

# IP RL Framework Presentation Compilation Script
# Compiles LaTeX Beamer presentation with all dependencies

echo "🚀 Compiling IP RL Framework Presentation..."

# Check if pdflatex is available
if ! command -v pdflatex &> /dev/null; then
    echo "❌ Error: pdflatex not found. Please install LaTeX distribution."
    echo "   - macOS: brew install --cask mactex"
    echo "   - Ubuntu: sudo apt-get install texlive-full"
    echo "   - Windows: Install MiKTeX or TeX Live"
    exit 1
fi

# Check if required files exist
if [ ! -f "IP_RL_FRAMEWORK_DETAILED_PRESENTATION.tex" ]; then
    echo "❌ Error: IP_RL_FRAMEWORK_DETAILED_PRESENTATION.tex not found"
    exit 1
fi

# Create output directory
mkdir -p presentation_output

# Compile the presentation
echo "📝 Compiling LaTeX presentation..."
pdflatex -output-directory=presentation_output IP_RL_FRAMEWORK_DETAILED_PRESENTATION.tex

# Check if compilation was successful
if [ $? -eq 0 ]; then
    echo "✅ First compilation successful"
else
    echo "❌ First compilation failed"
    exit 1
fi

# Run again to resolve references
echo "📝 Running second compilation for references..."
pdflatex -output-directory=presentation_output IP_RL_FRAMEWORK_DETAILED_PRESENTATION.tex

# Check if second compilation was successful
if [ $? -eq 0 ]; then
    echo "✅ Second compilation successful"
else
    echo "❌ Second compilation failed"
    exit 1
fi

# Run third time to ensure everything is resolved
echo "📝 Running third compilation for final resolution..."
pdflatex -output-directory=presentation_output IP_RL_FRAMEWORK_DETAILED_PRESENTATION.tex

# Check if final compilation was successful
if [ $? -eq 0 ]; then
    echo "✅ Final compilation successful"
else
    echo "❌ Final compilation failed"
    exit 1
fi

# Check if PDF was created
if [ -f "presentation_output/IP_RL_FRAMEWORK_DETAILED_PRESENTATION.pdf" ]; then
    echo "🎉 Presentation compiled successfully!"
    echo "📄 Output: presentation_output/IP_RL_FRAMEWORK_DETAILED_PRESENTATION.pdf"
    echo "📊 File size: $(du -h presentation_output/IP_RL_FRAMEWORK_DETAILED_PRESENTATION.pdf | cut -f1)"
else
    echo "❌ Error: PDF not created"
    exit 1
fi

# Clean up auxiliary files
echo "🧹 Cleaning up auxiliary files..."
rm -f presentation_output/*.aux
rm -f presentation_output/*.log
rm -f presentation_output/*.nav
rm -f presentation_output/*.out
rm -f presentation_output/*.snm
rm -f presentation_output/*.toc

echo "✨ Presentation compilation complete!"
echo "📁 Output directory: presentation_output/"
echo "📄 PDF file: IP_RL_FRAMEWORK_DETAILED_PRESENTATION.pdf"