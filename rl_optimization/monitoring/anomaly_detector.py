"""
Anomaly Detector for Training Monitoring
Detect training anomalies with statistical and ML-based methods
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
import threading
from collections import deque
import json
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings

logger = structlog.get_logger(__name__)

@dataclass
class AnomalyConfig:
    """Configuration for anomaly detection"""
    window_size: int = 100
    sensitivity: float = 0.1
    min_samples: int = 10
    contamination: float = 0.1
    enable_statistical_detection: bool = True
    enable_ml_detection: bool = True
    enable_clustering_detection: bool = True
    alert_threshold: float = 0.8
    cooldown_period: int = 300  # seconds

@dataclass
class AnomalyAlert:
    """Anomaly alert"""
    alert_id: str
    anomaly_type: str
    severity: str
    description: str
    timestamp: datetime
    metrics: Dict[str, Any]
    confidence: float
    recommendations: List[str]

@dataclass
class AnomalyStats:
    """Anomaly detection statistics"""
    total_anomalies: int
    anomalies_by_type: Dict[str, int]
    false_positive_rate: float
    detection_accuracy: float
    last_anomaly: Optional[datetime]
    alert_cooldown: Dict[str, datetime]

class AnomalyDetector:
    """
    Detect training anomalies
    - Reward divergence detection
    - Loss explosion detection
    - Memory leak detection
    - Performance degradation alerts
    """
    
    def __init__(self, config: AnomalyConfig):
        """
        Initialize anomaly detector
        
        Args:
            config: Anomaly detection configuration
        """
        self.config = config
        self.metrics_buffer = deque(maxlen=config.window_size)
        self.anomaly_history = deque(maxlen=1000)
        self.alert_cooldown = {}
        self.stats = AnomalyStats(
            total_anomalies=0,
            anomalies_by_type={},
            false_positive_rate=0.0,
            detection_accuracy=0.0,
            last_anomaly=None,
            alert_cooldown={}
        )
        
        # ML models
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.clustering_model = None
        
        # Statistical baselines
        self.baselines = {}
        self.baseline_lock = threading.Lock()
        
        logger.info("AnomalyDetector initialized", 
                   window_size=config.window_size,
                   sensitivity=config.sensitivity)
    
    def add_metrics(self, metrics: Dict[str, Any]):
        """
        Add metrics for anomaly detection
        
        Args:
            metrics: Training metrics
        """
        try:
            # Add timestamp
            metrics['timestamp'] = datetime.utcnow()
            
            # Add to buffer
            self.metrics_buffer.append(metrics)
            
            # Update baselines if we have enough data
            if len(self.metrics_buffer) >= self.config.min_samples:
                self._update_baselines()
            
            # Check for anomalies
            if len(self.metrics_buffer) >= self.config.min_samples:
                anomalies = self._detect_anomalies(metrics)
                
                for anomaly in anomalies:
                    self._handle_anomaly(anomaly)
            
        except Exception as e:
            logger.error(f"Failed to add metrics: {e}")
    
    def _update_baselines(self):
        """Update statistical baselines"""
        try:
            with self.baseline_lock:
                # Convert buffer to DataFrame
                df = pd.DataFrame(list(self.metrics_buffer))
                
                # Calculate baselines for numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                
                for column in numeric_columns:
                    if column != 'timestamp':
                        values = df[column].dropna()
                        if len(values) > 0:
                            self.baselines[column] = {
                                'mean': values.mean(),
                                'std': values.std(),
                                'median': values.median(),
                                'q25': values.quantile(0.25),
                                'q75': values.quantile(0.75),
                                'min': values.min(),
                                'max': values.max()
                            }
                
                logger.debug(f"Updated baselines for {len(self.baselines)} metrics")
                
        except Exception as e:
            logger.error(f"Failed to update baselines: {e}")
    
    def _detect_anomalies(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in current metrics"""
        anomalies = []
        
        try:
            # Statistical anomaly detection
            if self.config.enable_statistical_detection:
                stat_anomalies = self._detect_statistical_anomalies(current_metrics)
                anomalies.extend(stat_anomalies)
            
            # ML-based anomaly detection
            if self.config.enable_ml_detection:
                ml_anomalies = self._detect_ml_anomalies(current_metrics)
                anomalies.extend(ml_anomalies)
            
            # Clustering-based anomaly detection
            if self.config.enable_clustering_detection:
                cluster_anomalies = self._detect_clustering_anomalies(current_metrics)
                anomalies.extend(cluster_anomalies)
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
        
        return anomalies
    
    def _detect_statistical_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect statistical anomalies"""
        anomalies = []
        
        try:
            for metric_name, value in metrics.items():
                if metric_name == 'timestamp' or not isinstance(value, (int, float)):
                    continue
                
                if metric_name not in self.baselines:
                    continue
                
                baseline = self.baselines[metric_name]
                
                # Z-score anomaly detection
                z_score = abs((value - baseline['mean']) / max(baseline['std'], 1e-8))
                if z_score > 3.0:  # 3-sigma rule
                    anomalies.append({
                        'type': 'statistical_outlier',
                        'metric': metric_name,
                        'value': value,
                        'baseline_mean': baseline['mean'],
                        'baseline_std': baseline['std'],
                        'z_score': z_score,
                        'severity': 'high' if z_score > 5.0 else 'medium',
                        'confidence': min(z_score / 5.0, 1.0)
                    })
                
                # IQR anomaly detection
                iqr = baseline['q75'] - baseline['q25']
                lower_bound = baseline['q25'] - 1.5 * iqr
                upper_bound = baseline['q75'] + 1.5 * iqr
                
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        'type': 'iqr_outlier',
                        'metric': metric_name,
                        'value': value,
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound,
                        'severity': 'medium',
                        'confidence': 0.8
                    })
                
                # Trend anomaly detection
                if len(self.metrics_buffer) >= 10:
                    recent_values = [m.get(metric_name, 0) for m in list(self.metrics_buffer)[-10:]]
                    if len(recent_values) >= 5:
                        trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
                        if abs(trend) > baseline['std'] * 2:
                            anomalies.append({
                                'type': 'trend_anomaly',
                                'metric': metric_name,
                                'trend': trend,
                                'severity': 'medium',
                                'confidence': min(abs(trend) / baseline['std'], 1.0)
                            })
            
        except Exception as e:
            logger.error(f"Failed to detect statistical anomalies: {e}")
        
        return anomalies
    
    def _detect_ml_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect ML-based anomalies"""
        anomalies = []
        
        try:
            if len(self.metrics_buffer) < self.config.min_samples:
                return anomalies
            
            # Prepare features
            features = self._extract_features(metrics)
            if features is None:
                return anomalies
            
            # Train/update isolation forest
            if self.isolation_forest is None:
                self.isolation_forest = IsolationForest(
                    contamination=self.config.contamination,
                    random_state=42
                )
                
                # Train on historical data
                historical_features = []
                for metric in list(self.metrics_buffer)[:-1]:  # Exclude current metric
                    feature_vector = self._extract_features(metric)
                    if feature_vector is not None:
                        historical_features.append(feature_vector)
                
                if len(historical_features) >= self.config.min_samples:
                    historical_features = np.array(historical_features)
                    self.scaler.fit(historical_features)
                    scaled_features = self.scaler.transform(historical_features)
                    self.isolation_forest.fit(scaled_features)
            
            # Predict anomaly
            if self.isolation_forest is not None:
                scaled_features = self.scaler.transform([features])
                prediction = self.isolation_forest.predict(scaled_features)[0]
                score = self.isolation_forest.score_samples(scaled_features)[0]
                
                if prediction == -1:  # Anomaly detected
                    anomalies.append({
                        'type': 'ml_anomaly',
                        'metric': 'composite',
                        'anomaly_score': score,
                        'severity': 'high' if score < -0.5 else 'medium',
                        'confidence': abs(score)
                    })
            
        except Exception as e:
            logger.error(f"Failed to detect ML anomalies: {e}")
        
        return anomalies
    
    def _detect_clustering_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect clustering-based anomalies"""
        anomalies = []
        
        try:
            if len(self.metrics_buffer) < self.config.min_samples:
                return anomalies
            
            # Prepare features
            features = self._extract_features(metrics)
            if features is None:
                return anomalies
            
            # Get historical features
            historical_features = []
            for metric in list(self.metrics_buffer)[:-1]:
                feature_vector = self._extract_features(metric)
                if feature_vector is not None:
                    historical_features.append(feature_vector)
            
            if len(historical_features) < self.config.min_samples:
                return anomalies
            
            # Perform clustering
            historical_features = np.array(historical_features)
            self.scaler.fit(historical_features)
            scaled_features = self.scaler.transform(historical_features)
            
            # DBSCAN clustering
            clustering = DBSCAN(eps=0.5, min_samples=3)
            cluster_labels = clustering.fit_predict(scaled_features)
            
            # Check if current point is an outlier
            current_scaled = self.scaler.transform([features])
            current_label = clustering.fit_predict(current_scaled)[0]
            
            if current_label == -1:  # Noise/outlier
                # Calculate distance to nearest cluster
                min_distance = float('inf')
                for i, label in enumerate(cluster_labels):
                    if label != -1:
                        distance = np.linalg.norm(current_scaled[0] - scaled_features[i])
                        min_distance = min(min_distance, distance)
                
                anomalies.append({
                    'type': 'clustering_anomaly',
                    'metric': 'composite',
                    'distance_to_nearest_cluster': min_distance,
                    'severity': 'high' if min_distance > 2.0 else 'medium',
                    'confidence': min(min_distance / 2.0, 1.0)
                })
            
        except Exception as e:
            logger.error(f"Failed to detect clustering anomalies: {e}")
        
        return anomalies
    
    def _extract_features(self, metrics: Dict[str, Any]) -> Optional[np.ndarray]:
        """Extract features from metrics"""
        try:
            features = []
            
            # Extract numeric features
            numeric_metrics = ['episode_reward', 'episode_length', 'training_loss', 
                             'epsilon', 'memory_size', 'accuracy', 'cost_efficiency']
            
            for metric in numeric_metrics:
                value = metrics.get(metric, 0.0)
                if isinstance(value, (int, float)):
                    features.append(float(value))
                else:
                    features.append(0.0)
            
            # Add derived features
            if 'episode_reward' in metrics and 'episode_length' in metrics:
                reward = metrics.get('episode_reward', 0.0)
                length = metrics.get('episode_length', 1.0)
                features.append(reward / max(length, 1.0))  # Reward per step
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Failed to extract features: {e}")
            return None
    
    def _handle_anomaly(self, anomaly: Dict[str, Any]):
        """Handle detected anomaly"""
        try:
            # Check cooldown
            anomaly_type = anomaly['type']
            if anomaly_type in self.alert_cooldown:
                last_alert = self.alert_cooldown[anomaly_type]
                if datetime.utcnow() - last_alert < timedelta(seconds=self.config.cooldown_period):
                    return  # Still in cooldown
            
            # Create alert
            alert = AnomalyAlert(
                alert_id=str(uuid.uuid4()),
                anomaly_type=anomaly_type,
                severity=anomaly.get('severity', 'medium'),
                description=self._generate_anomaly_description(anomaly),
                timestamp=datetime.utcnow(),
                metrics=anomaly,
                confidence=anomaly.get('confidence', 0.5),
                recommendations=self._generate_recommendations(anomaly)
            )
            
            # Store anomaly
            self.anomaly_history.append(alert)
            
            # Update statistics
            self.stats.total_anomalies += 1
            self.stats.anomalies_by_type[anomaly_type] = self.stats.anomalies_by_type.get(anomaly_type, 0) + 1
            self.stats.last_anomaly = datetime.utcnow()
            self.alert_cooldown[anomaly_type] = datetime.utcnow()
            
            # Log anomaly
            logger.warning(f"Anomaly detected: {anomaly_type}",
                          severity=alert.severity,
                          confidence=alert.confidence,
                          description=alert.description)
            
        except Exception as e:
            logger.error(f"Failed to handle anomaly: {e}")
    
    def _generate_anomaly_description(self, anomaly: Dict[str, Any]) -> str:
        """Generate human-readable anomaly description"""
        anomaly_type = anomaly['type']
        metric = anomaly.get('metric', 'unknown')
        value = anomaly.get('value', 0.0)
        
        if anomaly_type == 'statistical_outlier':
            z_score = anomaly.get('z_score', 0.0)
            return f"Statistical outlier detected in {metric}: value={value:.3f}, z-score={z_score:.2f}"
        
        elif anomaly_type == 'iqr_outlier':
            return f"IQR outlier detected in {metric}: value={value:.3f}"
        
        elif anomaly_type == 'trend_anomaly':
            trend = anomaly.get('trend', 0.0)
            return f"Trend anomaly detected in {metric}: trend={trend:.3f}"
        
        elif anomaly_type == 'ml_anomaly':
            score = anomaly.get('anomaly_score', 0.0)
            return f"ML anomaly detected: score={score:.3f}"
        
        elif anomaly_type == 'clustering_anomaly':
            distance = anomaly.get('distance_to_nearest_cluster', 0.0)
            return f"Clustering anomaly detected: distance={distance:.3f}"
        
        else:
            return f"Unknown anomaly type: {anomaly_type}"
    
    def _generate_recommendations(self, anomaly: Dict[str, Any]) -> List[str]:
        """Generate recommendations for anomaly"""
        recommendations = []
        
        anomaly_type = anomaly['type']
        metric = anomaly.get('metric', 'unknown')
        
        if anomaly_type == 'statistical_outlier':
            recommendations.extend([
                f"Check if {metric} values are within expected range",
                "Consider adjusting model hyperparameters",
                "Verify data quality and preprocessing"
            ])
        
        elif anomaly_type == 'trend_anomaly':
            recommendations.extend([
                f"Monitor {metric} trend closely",
                "Consider early stopping if trend continues",
                "Check for overfitting or underfitting"
            ])
        
        elif anomaly_type in ['ml_anomaly', 'clustering_anomaly']:
            recommendations.extend([
                "Review recent model changes",
                "Check for data distribution shifts",
                "Consider retraining the model"
            ])
        
        return recommendations
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get anomaly detection summary"""
        return {
            'total_anomalies': self.stats.total_anomalies,
            'anomalies_by_type': dict(self.stats.anomalies_by_type),
            'last_anomaly': self.stats.last_anomaly.isoformat() if self.stats.last_anomaly else None,
            'recent_anomalies': [
                {
                    'type': alert.anomaly_type,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.isoformat(),
                    'description': alert.description
                }
                for alert in list(self.anomaly_history)[-10:]
            ],
            'config': self.config.__dict__
        }
    
    def export_anomalies_to_file(self, filepath: str):
        """Export anomalies to file"""
        try:
            anomalies_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'summary': self.get_anomaly_summary(),
                'anomaly_history': [
                    {
                        'alert_id': alert.alert_id,
                        'anomaly_type': alert.anomaly_type,
                        'severity': alert.severity,
                        'description': alert.description,
                        'timestamp': alert.timestamp.isoformat(),
                        'metrics': alert.metrics,
                        'confidence': alert.confidence,
                        'recommendations': alert.recommendations
                    }
                    for alert in self.anomaly_history
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(anomalies_data, f, indent=2, default=str)
            
            logger.info(f"Anomalies exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export anomalies: {e}")

# Factory function for easy anomaly detection setup
def create_anomaly_detector(
    window_size: int = 100,
    sensitivity: float = 0.1,
    contamination: float = 0.1,
    **kwargs
) -> AnomalyDetector:
    """
    Create anomaly detector with default configuration
    
    Args:
        window_size: Window size for anomaly detection
        sensitivity: Detection sensitivity
        contamination: Contamination rate for ML models
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured AnomalyDetector
    """
    config = AnomalyConfig(
        window_size=window_size,
        sensitivity=sensitivity,
        contamination=contamination,
        **kwargs
    )
    
    return AnomalyDetector(config)
