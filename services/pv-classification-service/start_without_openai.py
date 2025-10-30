#!/usr/bin/env python3
"""
Start PV Classification Service without OpenAI dependency
Uses only Rule-based + BERT classifiers for testing
"""

import os
import sys
from pathlib import Path

# Set environment variable to disable OpenAI
os.environ['DISABLE_OPENAI'] = 'true'
os.environ['USE_SIMPLIFIED_LLM'] = 'true'

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import and start the service
if __name__ == "__main__":
    print("🚀 Starting PV Classification Service (Rule-based + BERT only)")
    print("=" * 60)
    print("📊 Models Available:")
    print("   ✅ Rule-based Classifier (Free, Fast)")
    print("   ✅ BERT Classifier (facebook/bart-large-mnli)")
    print("   ⚠️  LLM Classifier (Disabled - No OpenAI API key)")
    print("=" * 60)
    
    # Import and run the main service
    from main import app
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
