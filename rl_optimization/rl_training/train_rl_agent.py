#!/usr/bin/env python3
"""
Main RL Training Script
Trains the multi-objective RL agent on real PubMed data
"""

import sys
import os
import argparse
from pathlib import Path
import structlog

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from training_engine import RLTrainingEngine
from rl_agent import MultiObjectiveRLAgent
from rule_optimizer import RuleConfigurationGenerator

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Train RL agent for rule optimization")
    parser.add_argument("--data_path", 
                       default="rl_optimization/real_pubmed_data",
                       help="Path to training data")
    parser.add_argument("--output_dir", 
                       default="rl_optimization/training_results",
                       help="Output directory for results")
    parser.add_argument("--episodes", 
                       type=int, 
                       default=1000,
                       help="Number of training episodes")
    parser.add_argument("--max_steps", 
                       type=int, 
                       default=100,
                       help="Maximum steps per episode")
    parser.add_argument("--eval_freq", 
                       type=int, 
                       default=50,
                       help="Evaluation frequency")
    parser.add_argument("--save_freq", 
                       type=int, 
                       default=100,
                       help="Save frequency")
    parser.add_argument("--learning_rate", 
                       type=float, 
                       default=0.001,
                       help="Learning rate")
    parser.add_argument("--gamma", 
                       type=float, 
                       default=0.99,
                       help="Discount factor")
    parser.add_argument("--epsilon", 
                       type=float, 
                       default=0.1,
                       help="Initial epsilon for exploration")
    parser.add_argument("--batch_size", 
                       type=int, 
                       default=32,
                       help="Batch size for training")
    
    args = parser.parse_args()
    
    logger.info("Starting RL training", 
               data_path=args.data_path,
               output_dir=args.output_dir,
               episodes=args.episodes)
    
    try:
        # Initialize training engine
        training_engine = RLTrainingEngine(
            training_data_path=args.data_path,
            output_dir=args.output_dir,
            episodes=args.episodes,
            max_steps_per_episode=args.max_steps,
            evaluation_frequency=args.eval_freq,
            save_frequency=args.save_freq
        )
        
        # Start training
        training_engine.train()
        
        logger.info("RL training completed successfully")
        
    except Exception as e:
        logger.error("RL training failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
