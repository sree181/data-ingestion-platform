#!/bin/bash

# RL Integration Deployment Script
# Deploys the complete RL-enhanced classification system

set -e

echo "🚀 RL Integration Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "services/pv-classification-service/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Starting RL Integration Deployment..."

# Step 1: Check Python environment
print_status "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_warning "No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    print_success "Virtual environment created and activated"
else
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    print_success "Virtual environment activated"
fi

# Step 2: Install dependencies
print_status "Installing dependencies..."
pip install -r services/pv-classification-service/requirements.txt
pip install -r rl_optimization/rl_training/requirements.txt

# Install additional RL dependencies
pip install matplotlib seaborn plotly prometheus_client psutil

print_success "Dependencies installed"

# Step 3: Check RL model availability
print_status "Checking RL model availability..."
if [ ! -f "rl_optimization/training_results/final_model.pt" ]; then
    print_warning "RL model not found. Training will be required on first run."
    print_status "Creating RL model directory..."
    mkdir -p rl_optimization/training_results
    mkdir -p rl_optimization/monitoring_output
else
    print_success "RL model found"
fi

# Step 4: Create monitoring directories
print_status "Setting up monitoring directories..."
mkdir -p rl_optimization/monitoring_output
mkdir -p rl_optimization/optimization_cache
mkdir -p rl_optimization/real_pubmed_data

print_success "Monitoring directories created"

# Step 5: Test RL integration
print_status "Testing RL integration..."
cd services/pv-classification-service

# Check if the service can start
print_status "Testing service startup..."
python -c "
import sys
import os
sys.path.append('/Users/sreehasgopinathan/Documents/Auburn/Project/Data_Ingestion')
sys.path.append('/Users/sreehasgopinathan/Documents/Auburn/Project/Data_Ingestion/services/pv-classification-service')
try:
    from rl_ensemble_controller import RLEnsembleController
    from rl_metrics_dashboard import RLMetricsDashboard
    print('RL components imported successfully')
except Exception as e:
    print(f'RL import failed: {e}')
    sys.exit(1)
" || {
    print_error "RL components import failed"
    exit 1
}

print_success "RL components imported successfully"

# Step 6: Start the service
print_status "Starting PV Classification Service with RL integration..."
print_status "Service will be available at: http://localhost:8000"
print_status "RL endpoints will be available at: http://localhost:8000/api/v1/rl/"
print_status ""
print_status "Available RL endpoints:"
print_status "  POST /api/v1/rl/classify - Single document RL classification"
print_status "  POST /api/v1/rl/classify/batch - Batch RL classification"
print_status "  GET  /api/v1/rl/metrics - Real-time metrics"
print_status "  GET  /api/v1/rl/health - RL system health"
print_status "  GET  /api/v1/rl/alerts - Performance alerts"
print_status "  GET  /api/v1/rl/performance-report - Performance report"
print_status ""

# Start the service
print_status "Starting service (Press Ctrl+C to stop)..."
python main.py

# If we get here, the service was stopped
print_warning "Service stopped"
