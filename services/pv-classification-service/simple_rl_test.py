#!/usr/bin/env python3
"""
Simple RL Test - Test RL components without complex dependencies
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "rl_optimization"))

def test_rl_imports():
    """Test RL component imports"""
    try:
        print("Testing basic imports...")
        
        # Test basic Python imports
        import numpy as np
        import torch
        import structlog
        print("✅ Basic dependencies imported")
        
        # Test if we can create basic RL components
        print("Testing RL component creation...")
        
        # Create a simple test
        from rl_ensemble_controller import RLEnsembleController
        print("✅ RLEnsembleController imported")
        
        from rl_metrics_dashboard import RLMetricsDashboard  
        print("✅ RLMetricsDashboard imported")
        
        print("✅ All RL components imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rl_imports()
    sys.exit(0 if success else 1)
