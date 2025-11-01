# Enterprise Data Ingestion Platform - Technical Documentation

## 📚 Comprehensive Technical Manual

This directory contains the complete technical documentation for the Enterprise Data Ingestion Platform in LaTeX format.

### 📖 Document Structure

```
docs/
├── technical_manual.tex          # Main document (includes all chapters)
├── chapters/
│   ├── 02_usage_guide.tex       # End-to-end user workflows
│   ├── 03_features.tex          # Detailed feature documentation
│   ├── 04_api_reference.tex     # Complete API reference
│   ├── 05_operations.tex        # Operations & maintenance
│   ├── 06_troubleshooting.tex   # Troubleshooting guide
│   └── 07_advanced.tex          # Advanced topics & customization
└── README.md                     # This file
```

### 🎯 Documentation Coverage

This comprehensive manual includes:

1. **Chapter 1: Introduction**
   - Executive Summary
   - System Architecture
   - Key Features
   - Hardware/Software Requirements
   - Installation & Setup Guide
   - Network Configuration & IP Mapping

2. **Chapter 2: User Guide**
   - Login & Dashboard Overview
   - Document Ingestion (PDF, PubMed)
   - Classification System
   - Knowledge Hub (3D WebGL Visualization)
   - ICSR Reviewer Workflow
   - Investigation Boards
   - Monitoring & Performance
   - User Management & Security

3. **Chapter 3: Feature Reference**
   - Multi-Source Data Ingestion
   - AI-Powered Classification (3-Tier Ensemble)
   - Knowledge Graph Visualization
   - ICSR Automation
   - Reinforcement Learning Intelligence
   - Security & Compliance

4. **Chapter 4: API Reference**
   - Authentication Endpoints
   - Document Management API
   - Classification API
   - Knowledge Hub API
   - Ingestion API
   - RL Intelligence API
   - Rate Limiting & Error Codes

5. **Chapter 5: Operations & Maintenance**
   - Starting/Stopping Services
   - Health Monitoring
   - Database Maintenance
   - Performance Optimization
   - Security Operations
   - Scaling Strategies
   - Disaster Recovery

6. **Chapter 6: Troubleshooting**
   - Common Issues & Solutions
   - Error Messages & Meanings
   - Debugging Techniques
   - Performance Profiling
   - Support Channels

7. **Chapter 7: Advanced Topics**
   - Custom Model Training
   - API Integration Examples (Python, JavaScript)
   - Custom Workflows & Automation
   - Production Deployment (AWS, Kubernetes)
   - Security Hardening
   - Appendix (Port Reference, Environment Variables, Glossary)

### 🛠️ Compiling the Documentation

#### Prerequisites

Install a LaTeX distribution:

**macOS:**
```bash
# Install MacTeX (3.9 GB)
brew install --cask mactex

# Or install BasicTeX (smaller, 90 MB)
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install collection-latexextra
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install texlive-full
```

**Windows:**
Download and install [MiKTeX](https://miktex.org/download)

#### Required LaTeX Packages

The document uses these packages (install if missing):
```bash
sudo tlmgr install geometry xcolor listings hyperref tcolorbox fancyhdr \
  titlesec enumitem tabularx longtable booktabs caption subcaption \
  amsmath amssymb fontawesome5 tikz
```

#### Compile to PDF

```bash
# Navigate to docs directory
cd docs/

# Compile (run twice for cross-references)
pdflatex technical_manual.tex
pdflatex technical_manual.tex

# Or use latexmk for automated compilation
latexmk -pdf technical_manual.tex

# Output: technical_manual.pdf
```

#### Compile with Bibliography (if needed)

```bash
pdflatex technical_manual.tex
bibtex technical_manual
pdflatex technical_manual.tex
pdflatex technical_manual.tex
```

### 📄 Output

The compiled PDF will include:

- **~150 pages** of comprehensive technical documentation
- Table of Contents with hyperlinks
- List of Figures and Tables
- Professional formatting with color-coded sections
- Code examples with syntax highlighting
- Command boxes for easy reference
- Warning/Info boxes for critical information
- Placeholder markers for screenshots (to be added)

### 🖼️ Adding Screenshots

Throughout the document, you'll find placeholders like:

```latex
\begin{figure}[h]
\centering
\fbox{\textit{[SCREENSHOT PLACEHOLDER: Login Page with Username/Password Fields]}}
\caption{Enterprise Login Screen}
\label{fig:login}
\end{figure}
```

To add actual screenshots:

1. Capture screenshots as PNG or JPG
2. Save to `docs/images/` directory
3. Replace placeholder with:
```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{images/login_screen.png}
\caption{Enterprise Login Screen}
\label{fig:login}
\end{figure}
```

### 📝 Customization

#### Branding

Update branding in `technical_manual.tex`:
```latex
% Title Page
{\Huge\bfseries Your Company Name\par}

% Header/Footer
\fancyhead[LE]{Your Company - Technical Manual}
```

#### Colors

Modify color scheme:
```latex
\definecolor{primaryblue}{RGB}{66,126,234}      % Change primary color
\definecolor{successgreen}{RGB}{16,185,129}     % Change success color
```

#### Logo

Add company logo to title page:
```latex
\begin{titlepage}
    \centering
    \includegraphics[width=0.3\textwidth]{images/company_logo.png}
    \vspace{1cm}
    {\Huge\bfseries Enterprise Data Ingestion Platform\par}
    ...
\end{titlepage}
```

### 🎨 Style Guidelines

- **Code Blocks**: Use `bashstyle` for shell commands, `pythonstyle` for Python
- **Info Boxes**: Use `infobox`, `warningbox`, or `commandbox` environments
- **Tables**: Use `tabularx` for flexible column widths
- **Cross-References**: Use `\ref{fig:label}` or `\pageref{sec:label}`

### 📤 Distribution

#### PDF Distribution
```bash
# Compress PDF for email
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=technical_manual_compressed.pdf technical_manual.pdf
```

#### Print-Ready Version
```bash
# Generate print-ready PDF (300 DPI)
pdflatex -output-format=pdf technical_manual.tex
```

#### HTML Export (via pandoc)
```bash
# Convert to HTML for web viewing
pandoc technical_manual.tex -o technical_manual.html --standalone
```

### 🔄 Version Control

Document version is on the title page. Update after major changes:

```latex
\begin{tabular}{ll}
    \textbf{Document Type:} & Technical Manual \\
    \textbf{Classification:} & Private (Enterprise) \\
    \textbf{Status:} & Production Ready \\
    \textbf{Version:} & 1.1 \\  % Update here
    \textbf{Last Updated:} & \today
\end{tabular}
```

### 📋 Checklist for Release

Before distributing the manual:

- [ ] Compile successfully without errors
- [ ] All cross-references working
- [ ] Screenshots added and properly sized
- [ ] Commands tested and verified
- [ ] IP addresses and URLs updated
- [ ] Version number updated
- [ ] Copyright year current
- [ ] Table of Contents complete
- [ ] Index generated (if applicable)
- [ ] PDF bookmarks enabled

### 🤝 Contributing

To add new sections:

1. Create new `.tex` file in `chapters/`
2. Include in main document: `\input{chapters/your_chapter}`
3. Follow existing formatting style
4. Add section to Table of Contents
5. Update this README

### 📞 Support

For documentation issues or questions:
- **Email**: support@auburn.edu
- **GitHub Issues**: [data-ingestion-platform/issues](https://github.com/sree181/data-ingestion-platform/issues)

---

**Document Created**: November 2025  
**Last Updated**: \today  
**Maintained by**: Auburn University - Pharmacovigilance Intelligence Team

