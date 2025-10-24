"""
Model Optimizer
Advanced neural network optimization for RL training
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingLR, StepLR
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import structlog
from datetime import datetime
import json
from pathlib import Path

logger = structlog.get_logger(__name__)

@dataclass
class ModelOptimizationConfig:
    """Configuration for model optimization"""
    enable_mixed_precision: bool = True
    enable_gradient_clipping: bool = True
    gradient_clip_norm: float = 1.0
    enable_weight_decay: bool = True
    weight_decay: float = 1e-4
    enable_batch_norm: bool = True
    enable_dropout: bool = True
    dropout_rate: float = 0.1
    enable_learning_rate_scheduling: bool = True
    scheduler_type: str = "reduce_on_plateau"  # reduce_on_plateau, cosine, step
    enable_early_stopping: bool = True
    early_stopping_patience: int = 10
    enable_model_compression: bool = False
    compression_ratio: float = 0.5

class LearningRateScheduler:
    """Advanced learning rate scheduling"""
    
    def __init__(self, optimizer: optim.Optimizer, config: ModelOptimizationConfig):
        self.optimizer = optimizer
        self.config = config
        self.scheduler = None
        self.best_loss = float('inf')
        self.patience_counter = 0
        self.learning_rate_history = []
        
        self._initialize_scheduler()
    
    def _initialize_scheduler(self):
        """Initialize learning rate scheduler"""
        if not self.config.enable_learning_rate_scheduling:
            return
        
        if self.config.scheduler_type == "reduce_on_plateau":
            self.scheduler = ReduceLROnPlateau(
                self.optimizer,
                mode='min',
                factor=0.5,
                patience=5,
                verbose=True
            )
        elif self.config.scheduler_type == "cosine":
            self.scheduler = CosineAnnealingLR(
                self.optimizer,
                T_max=1000,
                eta_min=1e-6
            )
        elif self.config.scheduler_type == "step":
            self.scheduler = StepLR(
                self.optimizer,
                step_size=100,
                gamma=0.1
            )
        else:
            logger.warning(f"Unknown scheduler type: {self.config.scheduler_type}")
    
    def step(self, loss: float = None):
        """Step the learning rate scheduler"""
        if self.scheduler is None:
            return
        
        if isinstance(self.scheduler, ReduceLROnPlateau):
            if loss is not None:
                self.scheduler.step(loss)
        else:
            self.scheduler.step()
        
        # Record learning rate
        current_lr = self.optimizer.param_groups[0]['lr']
        self.learning_rate_history.append({
            'lr': current_lr,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def should_stop_early(self, loss: float) -> bool:
        """Check if training should stop early"""
        if not self.config.enable_early_stopping:
            return False
        
        if loss < self.best_loss:
            self.best_loss = loss
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            return self.patience_counter >= self.config.early_stopping_patience
    
    def get_current_lr(self) -> float:
        """Get current learning rate"""
        return self.optimizer.param_groups[0]['lr']
    
    def get_lr_history(self) -> List[Dict[str, Any]]:
        """Get learning rate history"""
        return self.learning_rate_history

class GradientOptimizer:
    """Gradient optimization utilities"""
    
    def __init__(self, config: ModelOptimizationConfig):
        self.config = config
        self.gradient_norms = []
        self.clipping_count = 0
    
    def clip_gradients(self, model: nn.Module) -> float:
        """Clip gradients to prevent exploding gradients"""
        if not self.config.enable_gradient_clipping:
            return 0.0
        
        total_norm = 0.0
        param_count = 0
        
        for param in model.parameters():
            if param.grad is not None:
                param_norm = param.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
                param_count += 1
        
        total_norm = total_norm ** (1. / 2)
        
        # Record gradient norm
        self.gradient_norms.append({
            'norm': total_norm,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Clip gradients if necessary
        if total_norm > self.config.gradient_clip_norm:
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                self.config.gradient_clip_norm
            )
            self.clipping_count += 1
            logger.debug(f"Gradients clipped, norm: {total_norm:.4f}")
        
        return total_norm
    
    def get_gradient_stats(self) -> Dict[str, Any]:
        """Get gradient statistics"""
        if not self.gradient_norms:
            return {}
        
        norms = [entry['norm'] for entry in self.gradient_norms]
        return {
            'mean_norm': np.mean(norms),
            'max_norm': np.max(norms),
            'min_norm': np.min(norms),
            'clipping_count': self.clipping_count,
            'clipping_rate': self.clipping_count / len(norms) if norms else 0.0
        }

class ModelCompressor:
    """Model compression utilities"""
    
    def __init__(self, config: ModelOptimizationConfig):
        self.config = config
        self.compression_history = []
    
    def compress_model(self, model: nn.Module) -> nn.Module:
        """Compress model using various techniques"""
        if not self.config.enable_model_compression:
            return model
        
        try:
            # Prune model
            compressed_model = self._prune_model(model)
            
            # Quantize model
            compressed_model = self._quantize_model(compressed_model)
            
            # Record compression
            original_params = sum(p.numel() for p in model.parameters())
            compressed_params = sum(p.numel() for p in compressed_model.parameters())
            compression_ratio = compressed_params / original_params
            
            self.compression_history.append({
                'original_params': original_params,
                'compressed_params': compressed_params,
                'compression_ratio': compression_ratio,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Model compressed", 
                       original_params=original_params,
                       compressed_params=compressed_params,
                       compression_ratio=compression_ratio)
            
            return compressed_model
            
        except Exception as e:
            logger.error(f"Model compression failed: {e}")
            return model
    
    def _prune_model(self, model: nn.Module) -> nn.Module:
        """Prune model by removing less important weights"""
        # Simple magnitude-based pruning
        for module in model.modules():
            if isinstance(module, nn.Linear):
                # Prune weights with small magnitudes
                threshold = torch.quantile(torch.abs(module.weight), self.config.compression_ratio)
                mask = torch.abs(module.weight) > threshold
                module.weight.data *= mask.float()
        
        return model
    
    def _quantize_model(self, model: nn.Module) -> nn.Module:
        """Quantize model to reduce precision"""
        # Simple quantization to 8-bit
        model = model.half()  # Convert to half precision
        return model

class ModelOptimizer:
    """
    Main model optimization system
    - Learning rate scheduling
    - Gradient optimization
    - Model compression
    - Mixed precision training
    - Early stopping
    """
    
    def __init__(self, config: ModelOptimizationConfig):
        """
        Initialize model optimizer
        
        Args:
            config: Model optimization configuration
        """
        self.config = config
        self.lr_scheduler = None
        self.gradient_optimizer = None
        self.model_compressor = None
        self.scaler = None
        
        # Initialize components
        self._initialize_components()
        
        # Optimization history
        self.optimization_history = []
        
        logger.info("ModelOptimizer initialized", 
                   mixed_precision=config.enable_mixed_precision,
                   gradient_clipping=config.enable_gradient_clipping,
                   lr_scheduling=config.enable_learning_rate_scheduling,
                   early_stopping=config.enable_early_stopping)
    
    def _initialize_components(self):
        """Initialize optimization components"""
        try:
            # Initialize gradient optimizer
            self.gradient_optimizer = GradientOptimizer(self.config)
            
            # Initialize model compressor
            self.model_compressor = ModelCompressor(self.config)
            
            # Initialize mixed precision scaler
            if self.config.enable_mixed_precision and torch.cuda.is_available():
                self.scaler = torch.cuda.amp.GradScaler()
                logger.info("Mixed precision scaler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize model optimizer components: {e}")
            raise
    
    def setup_optimizer(self, model: nn.Module, learning_rate: float = 1e-3) -> optim.Optimizer:
        """Setup optimized optimizer for model"""
        try:
            # Get optimizer parameters
            optimizer_params = {
                'lr': learning_rate,
                'weight_decay': self.config.weight_decay if self.config.enable_weight_decay else 0.0
            }
            
            # Create optimizer
            optimizer = optim.AdamW(model.parameters(), **optimizer_params)
            
            # Setup learning rate scheduler
            self.lr_scheduler = LearningRateScheduler(optimizer, self.config)
            
            logger.info("Optimizer setup completed", 
                       learning_rate=learning_rate,
                       weight_decay=optimizer_params['weight_decay'])
            
            return optimizer
            
        except Exception as e:
            logger.error(f"Failed to setup optimizer: {e}")
            raise
    
    def optimize_training_step(
        self,
        model: nn.Module,
        optimizer: optim.Optimizer,
        loss_fn: callable,
        inputs: torch.Tensor,
        targets: torch.Tensor
    ) -> Dict[str, Any]:
        """Optimize a single training step"""
        try:
            # Clear gradients
            optimizer.zero_grad()
            
            # Forward pass with mixed precision if enabled
            if self.scaler is not None:
                with torch.cuda.amp.autocast():
                    outputs = model(inputs)
                    loss = loss_fn(outputs, targets)
            else:
                outputs = model(inputs)
                loss = loss_fn(outputs, targets)
            
            # Backward pass
            if self.scaler is not None:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
            
            # Clip gradients
            gradient_norm = self.gradient_optimizer.clip_gradients(model)
            
            # Optimizer step
            if self.scaler is not None:
                self.scaler.step(optimizer)
                self.scaler.update()
            else:
                optimizer.step()
            
            # Update learning rate
            if self.lr_scheduler:
                self.lr_scheduler.step(loss.item())
            
            # Record optimization metrics
            metrics = {
                'loss': loss.item(),
                'gradient_norm': gradient_norm,
                'learning_rate': self.lr_scheduler.get_current_lr() if self.lr_scheduler else optimizer.param_groups[0]['lr'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.optimization_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Training step optimization failed: {e}")
            raise
    
    def should_stop_training(self, loss: float) -> bool:
        """Check if training should stop"""
        if not self.lr_scheduler:
            return False
        
        return self.lr_scheduler.should_stop_early(loss)
    
    def compress_model(self, model: nn.Module) -> nn.Module:
        """Compress model for deployment"""
        if not self.model_compressor:
            return model
        
        return self.model_compressor.compress_model(model)
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary"""
        try:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'config': {
                    'mixed_precision': self.config.enable_mixed_precision,
                    'gradient_clipping': self.config.enable_gradient_clipping,
                    'weight_decay': self.config.enable_weight_decay,
                    'lr_scheduling': self.config.enable_learning_rate_scheduling,
                    'early_stopping': self.config.enable_early_stopping,
                    'model_compression': self.config.enable_model_compression
                },
                'gradient_stats': self.gradient_optimizer.get_gradient_stats() if self.gradient_optimizer else {},
                'lr_history': self.lr_scheduler.get_lr_history() if self.lr_scheduler else [],
                'compression_history': self.model_compressor.compression_history if self.model_compressor else [],
                'optimization_history_length': len(self.optimization_history)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get optimization summary: {e}")
            return {}
    
    def save_optimization_report(self, filepath: str):
        """Save optimization report"""
        try:
            report = {
                'summary': self.get_optimization_summary(),
                'optimization_history': self.optimization_history[-100:],  # Last 100 entries
                'gradient_norms': self.gradient_optimizer.gradient_norms[-100:] if self.gradient_optimizer else [],
                'lr_history': self.lr_scheduler.get_lr_history() if self.lr_scheduler else [],
                'compression_history': self.model_compressor.compression_history if self.model_compressor else []
            }
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Optimization report saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save optimization report: {e}")

# Factory function for easy model optimizer setup
def create_model_optimizer(
    enable_mixed_precision: bool = True,
    enable_gradient_clipping: bool = True,
    enable_lr_scheduling: bool = True,
    enable_early_stopping: bool = True,
    **kwargs
) -> ModelOptimizer:
    """
    Create model optimizer with default configuration
    
    Args:
        enable_mixed_precision: Enable mixed precision training
        enable_gradient_clipping: Enable gradient clipping
        enable_lr_scheduling: Enable learning rate scheduling
        enable_early_stopping: Enable early stopping
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured ModelOptimizer
    """
    config = ModelOptimizationConfig(
        enable_mixed_precision=enable_mixed_precision,
        enable_gradient_clipping=enable_gradient_clipping,
        enable_learning_rate_scheduling=enable_lr_scheduling,
        enable_early_stopping=enable_early_stopping,
        **kwargs
    )
    
    return ModelOptimizer(config)
