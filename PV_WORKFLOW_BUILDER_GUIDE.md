# 🧪 PV Workflow Builder - User Guide

## ✅ **YES! It's Ready in Your UI**

The PV Workflow Builder is now live and accessible in your application!

---

## 🚀 How to Access

### **Step 1: Open Your Browser**
Navigate to: **http://localhost:3000**

### **Step 2: Find the Workflow Builder Tab**
Look in the left sidebar for:
- **Icon**: 🌳 (Tree/Workflow icon)
- **Label**: "Workflow Builder"
- **Description**: "Visual pipeline automation"

### **Step 3: Click to Open**
Click on "Workflow Builder" and you'll see the PV Workflow Builder!

---

## 🎨 What You'll See

### **Left Panel: Node Palette**
Drag-and-drop nodes organized by category:

**SOURCE NODES** (Cyan/Blue)
- 📄 NCBI Source
- 📄 PubMed Source
- 📄 ChEMBL Source
- 📄 FDA Source

**PROCESSING** (Purple/Pink)
- ⚙️ Preprocessing (OCR, HTML cleaning, normalization)
- 🏷️ NER & Relations (Entity extraction)

**STORAGE** (Orange)
- 💾 Ingestion (Elasticsearch & Neo4j)

**ANALYSIS** (Green/Indigo)
- 📊 Classification (ML model classification)
- 👁️ Monitoring (Performance metrics)

### **Center: Canvas**
- Visual workflow area with grid background
- Drag nodes from palette here
- Connect nodes by dragging from output (right) to input (left) handles
- **Demo workflow pre-loaded** showing a complete PV pipeline

### **Top Bar: Controls**
- **Node count** chip
- **Reset** button (restore demo workflow)
- **Run Simulation** button (green, animated)

---

## 🎮 How to Use

### **1. Use the Demo Workflow (Easiest)**
The demo workflow is already set up:
```
PubMed → Preprocessing → NER → Ingestion → Classification
                                    ↓
                              Monitoring
```

**Just click "Run Simulation"** to see it in action!

### **2. Build Your Own Workflow**

#### **Add Nodes:**
1. Drag a node from the left palette
2. Drop it on the canvas
3. Repeat for all needed nodes

#### **Connect Nodes:**
1. Click and drag from a node's **right handle** (output)
2. Drag to another node's **left handle** (input)
3. Release to create connection
4. Connections are color-coded by source node type

#### **Run Workflow:**
1. Click **"Run Simulation"** button
2. Watch nodes light up and progress bars fill
3. See real-time metrics update
4. Edges animate during execution

### **3. Stop/Reset**
- **Stop**: Click "Stop" button during execution
- **Reset**: Click "Reset" to restore demo workflow

---

## 📊 What You'll See During Execution

### **Source Nodes (NCBI, PubMed, etc.)**
- Documents fetched counter
- Progress bar (0-100%)
- Duration timer
- Status: Pending → Running → Complete

### **Preprocessing Node**
- **3 sub-processes** with individual progress bars:
  - OCR (Optical Character Recognition)
  - HTML Cleaning
  - Normalization
- Overall progress
- Documents processed counter

### **NER Node**
- Entities extracted count
- Relationships extracted count
- Entity breakdown by type (drug, disease, adverse_event, gene)
- Top entities chips

### **Ingestion Node**
- **Dual progress bars**:
  - Elasticsearch: Documents ingested
  - Neo4j: Nodes & relationships created
- Both targets update independently

### **Classification Node**
- Documents classified counter
- Average confidence score
- Progress bar

### **Monitoring Node**
- Accuracy, Precision, Recall, F1 Score
- Latency (ms)
- Throughput (docs/sec)
- Real-time metric updates

---

## 🎨 Visual Features

### **Color Coding**
- **Cyan**: Source nodes
- **Purple**: Preprocessing
- **Pink**: NER
- **Orange**: Ingestion
- **Green**: Classification
- **Indigo**: Monitoring

### **Status Indicators**
- **Gray**: Pending (not started)
- **Blue**: Running (animated pulse effect)
- **Green**: Complete (checkmark)
- **Red**: Error (if any)

### **Animations**
- Pulsing borders on running nodes
- Animated edges during execution
- Smooth progress bar transitions
- Real-time metric updates

---

## 💡 Pro Tips

### **1. Realistic Simulation**
All simulations use realistic timing:
- Source fetch: ~15 seconds
- Preprocessing: ~20 seconds (staggered sub-processes)
- NER: ~25 seconds
- Ingestion: ~18 seconds (dual targets)
- Classification: ~22 seconds
- Monitoring: ~10 seconds

### **2. Topological Execution**
Workflow executes in correct order based on connections:
- Dependencies are automatically resolved
- Parallel branches execute sequentially
- No need to worry about execution order

### **3. Mini-Map**
- Bottom-right corner shows overview
- Color-coded nodes
- Click to navigate large workflows
- Zoom and pan controls

### **4. Canvas Controls**
- **Scroll**: Zoom in/out
- **Click + Drag**: Pan canvas
- **Ctrl + Scroll**: Fine zoom control

---

## 🧪 Example Use Cases

### **1. PubMed Literature Analysis**
```
PubMed → Preprocessing → NER → Ingestion → Classification
```

### **2. Multi-Source Integration**
```
NCBI ─┐
      ├─→ Preprocessing → NER → Ingestion
FDA ──┘
```

### **3. Full PV Pipeline with Monitoring**
```
PubMed → Preprocessing → NER → Ingestion → Classification
                                    ↓
                              Monitoring
```

---

## 🐛 Troubleshooting

### **Issue: Nodes not dragging**
- **Solution**: Make sure you're dragging from the node card in the left palette

### **Issue: Can't connect nodes**
- **Solution**: Drag from right handle (output) to left handle (input)
- Source nodes don't have input handles
- Monitoring nodes don't have output handles

### **Issue: Simulation not starting**
- **Solution**: Make sure you have at least one node on the canvas

### **Issue: Workflow stops mid-execution**
- **Solution**: This is expected if you click "Stop" button
- Click "Reset" and "Run Simulation" again

---

## 📸 Screenshots to Expect

### **Initial View**
- Left sidebar with node palette
- Center canvas with demo workflow
- Top bar with controls
- Mini-map in bottom-right

### **During Execution**
- Blue pulsing borders on running nodes
- Animated edges with flowing dots
- Progress bars filling up
- Real-time metrics updating
- Sub-processes progressing (preprocessing)
- Dual progress bars (ingestion)

### **After Completion**
- All nodes green with checkmarks
- 100% progress bars
- Final metrics displayed
- Success notification

---

## 🎯 Key Features Implemented

✅ **All 6 PV Node Types** - NCBI, PubMed, ChEMBL, FDA, Preprocessing, NER, Ingestion, Classification, Monitoring
✅ **Realistic Dummy Simulation** - No backend required, all client-side
✅ **Drag-and-Drop** - Intuitive node placement
✅ **Visual Connections** - Color-coded edges
✅ **Real-Time Progress** - Live updates during execution
✅ **Sub-Process Tracking** - Preprocessing shows OCR, HTML cleaning, normalization
✅ **Dual-Target Ingestion** - Elasticsearch & Neo4j progress
✅ **Professional UI** - Material-UI components with animations
✅ **Demo Workflow** - Pre-loaded example pipeline
✅ **Topological Execution** - Correct dependency order

---

## 🚀 Next Steps

1. **Try the Demo**: Click "Run Simulation" on the pre-loaded workflow
2. **Experiment**: Add your own nodes and connections
3. **Watch Metrics**: Observe realistic PV processing metrics
4. **Build Pipelines**: Create custom workflows for different use cases

---

## 📝 Technical Details

- **Framework**: React 18 + React Flow
- **UI Library**: Material-UI (MUI)
- **Simulation**: Custom JavaScript engine
- **No Backend Required**: All dummy data generated client-side
- **Execution**: Topological sort for correct order
- **Timing**: Realistic intervals (15-25 seconds per stage)

---

**Enjoy building PV workflows! 🧪🚀**

For questions or issues, check the browser console for debug logs.

