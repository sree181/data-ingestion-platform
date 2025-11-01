# 📸 Screenshot Capture Guide for Technical Manual

This guide provides detailed instructions for capturing the 65 screenshots needed for the technical documentation.

## 🎯 Screenshot Standards

### Technical Requirements
- **Resolution**: 1920x1080 (Full HD)
- **Format**: PNG (lossless)
- **Color Depth**: 24-bit color
- **Browser**: Chrome (latest version)
- **Zoom Level**: 100% (no browser zoom)

### Capture Guidelines
- ✅ Clean browser (no extra tabs/extensions visible)
- ✅ Default system font size
- ✅ Clear data (realistic but not sensitive)
- ✅ Hide cursor (unless showing interaction)
- ✅ Consistent time/date across screenshots (if visible)

---

## 📋 Screenshot Checklist (65 Total)

### Chapter 1: Introduction (2 screenshots)

**1. System Architecture Diagram**
- File: `system_architecture.png`
- Type: Create diagram (draw.io, Lucidchart, or LaTeX TikZ)
- Content: Show all microservices, databases, and data flow
- Annotations: Service names, ports, data direction arrows

**2. Docker Services Status**
- File: `docker_ps_status.png`
- Command: `docker-compose ps`
- Content: Terminal showing all services as "Up (healthy)"
- Crop: Terminal window only, hide system UI

---

### Chapter 2: User Guide (11 screenshots)

**3. Login Page**
- File: `login_screen.png`
- URL: `http://localhost:3000/login`
- Content: Username/password fields, "Sign In" button
- State: Empty fields (no entered data)

**4. Dashboard Home View**
- File: `dashboard_home.png`
- URL: `http://localhost:3000/dashboard`
- Content: Key metrics cards, charts, recent documents
- State: With realistic data (100+ documents, 70% classified)

**5. Project Spaces - Document Upload**
- File: `document_upload_interface.png`
- URL: `http://localhost:3000/spaces`
- Content: Upload area, drag-and-drop zone, options panel
- State: Show classification options (checkboxes visible)

**6. PubMed Ingestion Configuration**
- File: `pubmed_config_panel.png`
- URL: `http://localhost:3000/spaces` → Configure Source → PubMed
- Content: Query fields, date range, max results slider
- State: Example query entered ("COVID-19 adverse events")

**7. Document Library with Classification Badges**
- File: `document_library_classified.png`
- URL: `http://localhost:3000/documents`
- Content: List of documents with colored classification badges
- State: Mix of ICSR (green), Safety_Information (blue), Non-ICSR (gray)

**8. Knowledge Hub - 3D WebGL Graph**
- File: `knowledge_hub_webgl_graph.png`
- URL: `http://localhost:3000/knowledge-hub`
- Content: Full 3D graph with colored nodes, relationships
- State: 3D mode enabled, 200-300 nodes visible, diverse colors

**9. Knowledge Hub - Multiple Angles**
- File: `knowledge_hub_3d_angles.png`
- URL: `http://localhost:3000/knowledge-hub`
- Content: 2x2 grid showing graph from different camera angles
- State: Use screenshot tool to combine 4 views

**10. Knowledge Hub with Community Detection**
- File: `knowledge_hub_communities.png`
- URL: `http://localhost:3000/knowledge-hub`
- Content: Graph with community colors visible
- State: "Show Communities" toggle ON, clustered color groups

**11. Entity Details Drawer**
- File: `entity_details_drawer.png`
- URL: `http://localhost:3000/knowledge-hub` → Click any Drug node
- Content: Entity info, source documents, chat interface
- State: Drawer open on right side, scrolled to show all sections

**12. ICSR Reviewer - Side-by-Side View**
- File: `icsr_reviewer_interface.png`
- URL: `http://localhost:3000/icsr-reviewer`
- Content: Document on left, extraction form on right
- State: Fields populated with extracted data

**13. Investigation Board - Collaborative Workspace**
- File: `investigation_board_active.png`
- URL: `http://localhost:3000/investigation-boards` → Open board
- Content: Pinned entities, documents, comments, task list
- State: Board with 5-10 pinned items, some tasks completed

**14. Grafana Dashboard - System Metrics**
- File: `grafana_system_metrics.png`
- URL: `http://localhost:3001` (Grafana)
- Content: Multiple panels (CPU, memory, requests, errors)
- State: Time range: Last 1 hour, realistic metrics

**15. User Management Interface**
- File: `user_management_dashboard.png`
- URL: `http://localhost:3000/settings/users`
- Content: User list table, roles, "Add User" button
- State: 5-10 users visible, mix of roles

---

### Chapter 3: Feature Reference (4 screenshots)

**16. Classification Performance Comparison Chart**
- File: `model_performance_comparison.png`
- Type: Create chart (Excel, Google Sheets, Plotly)
- Content: Bar chart comparing Precision/Recall/F1 for Rule/BERT/LLM/Ensemble
- Data: From section 3.2 performance tables

**17. 3D Graph Controls Panel**
- File: `graph_controls_panel.png`
- URL: `http://localhost:3000/knowledge-hub`
- Content: Right-side control buttons (Zoom In/Out, Center, Fullscreen, etc.)
- State: Hover over buttons to show tooltips

**18. WebGL Graph - Professional Rendering**
- File: `webgl_professional_rendering.png`
- URL: `http://localhost:3000/knowledge-hub`
- Content: Close-up of nodes showing PBR materials, shadows, glow
- State: 3D mode, zoomed in to show material quality

**19. RL Training Curve**
- File: `rl_training_reward_curve.png`
- URL: `http://localhost:3000/rl-intelligence`
- Content: Training history chart (line chart, reward over episodes)
- State: Full chart visible (0-1000 episodes)

---

### Chapter 4: API Reference (0 screenshots)

*No screenshots needed - API responses shown as code blocks*

---

### Chapter 5: Operations & Maintenance (1 screenshot)

**20. Grafana Monitoring Dashboard**
- File: `grafana_monitoring_overview.png`
- URL: `http://localhost:3001`
- Content: Overview dashboard with 6-8 panels
- State: Time range: Last 6 hours, all services healthy

---

### Chapter 6: Troubleshooting (0 screenshots)

*Terminal outputs shown as code blocks*

---

### Chapter 7: Advanced Topics (0 screenshots)

*Code examples only*

---

## 🛠️ Screenshot Tools

### Recommended Tools

**macOS**:
- Built-in: Cmd+Shift+4 (selection), Cmd+Shift+3 (full screen)
- Professional: [CleanShot X](https://cleanshot.com/) (annotations, scrolling capture)

**Windows**:
- Built-in: Windows+Shift+S (Snipping Tool)
- Professional: [ShareX](https://getsharex.com/) (free, feature-rich)

**Linux**:
- Built-in: Screenshot app (GNOME, KDE)
- Professional: [Flameshot](https://flameshot.org/) (annotations, upload)

**Cross-Platform**:
- [Greenshot](https://getgreenshot.org/) (free, annotations)
- Browser extensions: [Nimbus Screenshot](https://nimbusweb.me/)

---

## 📐 Screenshot Workflow

### 1. Setup Environment
```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy
sleep 60

# Access frontend
open http://localhost:3000
```

### 2. Prepare Browser
- Open Chrome in Incognito mode (clean state)
- Set window size: 1920x1080
- Hide browser toolbar (F11 for fullscreen)
- Zoom: 100% (Cmd+0 / Ctrl+0)

### 3. Load Sample Data
```bash
# Upload sample documents
# Classify documents
# Generate knowledge graph
# Create investigation boards
```

### 4. Capture Screenshots
- Use consistent timestamp across captures (morning, mid-week)
- Hide personal information (usernames, emails)
- Use placeholder data (e.g., "John Doe", "test@example.com")
- Capture multiple states if needed

### 5. Post-Processing
- Crop unnecessary UI (browser tabs, system notifications)
- Resize if needed (maintain aspect ratio)
- Add annotations with arrows/text (if helpful)
- Save as PNG with descriptive filename

### 6. Organize Files
```bash
# Create images directory
mkdir -p docs/images

# Save with clear naming convention
docs/images/01_login_screen.png
docs/images/02_dashboard_home.png
docs/images/03_document_upload.png
...
```

---

## 🔄 Integration into LaTeX

### Replace Placeholders

**Before:**
```latex
\begin{figure}[h]
\centering
\fbox{\textit{[SCREENSHOT PLACEHOLDER: Login Page]}}
\caption{Enterprise Login Screen}
\label{fig:login}
\end{figure}
```

**After:**
```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{images/01_login_screen.png}
\caption{Enterprise Login Screen}
\label{fig:login}
\end{figure}
```

### Sizing Guidelines
- **Full-page screenshots**: `width=1.0\textwidth`
- **Standard screenshots**: `width=0.8\textwidth`
- **Side-by-side**: `width=0.45\textwidth` each
- **Small UI elements**: `width=0.5\textwidth`

---

## ✅ Quality Checklist

Before adding screenshot to documentation:

- [ ] Resolution is 1920x1080 or higher
- [ ] Image is clear and readable
- [ ] No personal/sensitive information visible
- [ ] Consistent with other screenshots (colors, fonts)
- [ ] File size reasonable (<500 KB per PNG)
- [ ] Filename matches reference in LaTeX
- [ ] Screenshot shows intended feature clearly

---

## 🎨 Diagram Creation Tools

For non-UI screenshots (architecture diagrams, flowcharts):

1. **Draw.io** (free, online): https://app.diagrams.net/
2. **Lucidchart** (professional): https://www.lucidchart.com/
3. **Mermaid** (text-to-diagram): https://mermaid.js.org/
4. **LaTeX TikZ** (native LaTeX diagrams)

---

## 📊 Progress Tracking

Use this checklist to track screenshot completion:

```
Total: 20/20 screenshots
- [ ] Chapter 1: 0/2
- [ ] Chapter 2: 0/13
- [ ] Chapter 3: 0/4
- [ ] Chapter 5: 0/1
```

---

## 💡 Pro Tips

1. **Consistency is Key**: Capture all screenshots in one session for uniform look
2. **Use Sample Data**: Create realistic but non-sensitive test data
3. **Annotate Sparingly**: Only add arrows/text if absolutely necessary
4. **Test Compilation**: Add one screenshot and compile PDF to verify sizing
5. **Version Control**: Keep original high-res screenshots separate from compressed versions

---

**Estimated Time**: 2-3 hours for all 20 screenshots  
**Recommended Order**: Sequential (easier to maintain consistent data state)

---

**Good luck with screenshot capture! 📸**

