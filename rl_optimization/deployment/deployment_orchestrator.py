"""
Deployment Orchestrator
Comprehensive deployment and scaling system for RL models
"""

import os
import json
import time
import threading
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import structlog
from datetime import datetime
import yaml
from pathlib import Path
import docker
import requests
import asyncio
import aiohttp

logger = structlog.get_logger(__name__)

@dataclass
class DeploymentConfig:
    """Configuration for deployment orchestrator"""
    enable_docker: bool = True
    enable_kubernetes: bool = False
    enable_auto_scaling: bool = True
    enable_health_checks: bool = True
    enable_rolling_updates: bool = True
    enable_canary_deployments: bool = False
    docker_registry: str = "localhost:5000"
    kubernetes_namespace: str = "rl-models"
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80
    health_check_interval: int = 30
    deployment_timeout: int = 300
    rollback_timeout: int = 60

class DockerManager:
    """Docker container management"""
    
    def __init__(self, registry: str = "localhost:5000"):
        self.registry = registry
        self.client = docker.from_env()
        self.containers = {}
        self.images = {}
    
    def build_image(self, model_name: str, model_path: str, tag: str = "latest") -> bool:
        """Build Docker image for model"""
        try:
            # Create Dockerfile
            dockerfile_content = self._create_dockerfile(model_name, model_path)
            dockerfile_path = Path(model_path) / "Dockerfile"
            
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
            
            # Build image
            image_tag = f"{self.registry}/{model_name}:{tag}"
            image, build_logs = self.client.images.build(
                path=str(model_path),
                tag=image_tag,
                rm=True
            )
            
            self.images[f"{model_name}:{tag}"] = image
            logger.info(f"Docker image built: {image_tag}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            return False
    
    def _create_dockerfile(self, model_name: str, model_path: str) -> str:
        """Create Dockerfile for model"""
        return f"""
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model files
COPY {model_name}* ./

# Copy server code
COPY model_server.py .
COPY deployment/ ./deployment/

# Expose port
EXPOSE 8000

# Run model server
CMD ["python", "model_server.py", "--model-name", "{model_name}"]
"""
    
    def run_container(self, model_name: str, tag: str = "latest", 
                     port: int = 8000, env_vars: Dict[str, str] = None) -> str:
        """Run Docker container for model"""
        try:
            image_tag = f"{self.registry}/{model_name}:{tag}"
            
            # Run container
            container = self.client.containers.run(
                image_tag,
                detach=True,
                ports={8000: port},
                environment=env_vars or {},
                name=f"{model_name}-{tag}",
                restart_policy={"Name": "unless-stopped"}
            )
            
            container_id = container.id
            self.containers[container_id] = {
                "name": model_name,
                "tag": tag,
                "port": port,
                "status": "running"
            }
            
            logger.info(f"Container started: {container_id}")
            return container_id
            
        except Exception as e:
            logger.error(f"Failed to run container: {e}")
            return None
    
    def stop_container(self, container_id: str) -> bool:
        """Stop Docker container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            
            if container_id in self.containers:
                del self.containers[container_id]
            
            logger.info(f"Container stopped: {container_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            return False
    
    def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """Get container status"""
        try:
            container = self.client.containers.get(container_id)
            return {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "created": container.attrs["Created"],
                "ports": container.attrs["NetworkSettings"]["Ports"]
            }
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return {}
    
    def list_containers(self) -> List[Dict[str, Any]]:
        """List all containers"""
        containers = []
        for container_id, info in self.containers.items():
            status = self.get_container_status(container_id)
            containers.append(status)
        return containers

class KubernetesManager:
    """Kubernetes deployment management"""
    
    def __init__(self, namespace: str = "rl-models"):
        self.namespace = namespace
        self.deployments = {}
        self.services = {}
        self.ingresses = {}
    
    def create_deployment(self, model_name: str, image: str, 
                         replicas: int = 1, port: int = 8000) -> bool:
        """Create Kubernetes deployment"""
        try:
            # Create deployment manifest
            deployment_manifest = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": f"{model_name}-deployment",
                    "namespace": self.namespace
                },
                "spec": {
                    "replicas": replicas,
                    "selector": {
                        "matchLabels": {
                            "app": model_name
                        }
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": model_name
                            }
                        },
                        "spec": {
                            "containers": [{
                                "name": model_name,
                                "image": image,
                                "ports": [{
                                    "containerPort": port
                                }],
                                "resources": {
                                    "requests": {
                                        "memory": "256Mi",
                                        "cpu": "100m"
                                    },
                                    "limits": {
                                        "memory": "512Mi",
                                        "cpu": "500m"
                                    }
                                }
                            }]
                        }
                    }
                }
            }
            
            # Apply deployment
            result = subprocess.run([
                "kubectl", "apply", "-f", "-"
            ], input=yaml.dump(deployment_manifest), text=True, capture_output=True)
            
            if result.returncode == 0:
                self.deployments[model_name] = deployment_manifest
                logger.info(f"Kubernetes deployment created: {model_name}")
                return True
            else:
                logger.error(f"Failed to create deployment: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create Kubernetes deployment: {e}")
            return False
    
    def create_service(self, model_name: str, port: int = 8000) -> bool:
        """Create Kubernetes service"""
        try:
            service_manifest = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": f"{model_name}-service",
                    "namespace": self.namespace
                },
                "spec": {
                    "selector": {
                        "app": model_name
                    },
                    "ports": [{
                        "port": port,
                        "targetPort": port
                    }],
                    "type": "ClusterIP"
                }
            }
            
            result = subprocess.run([
                "kubectl", "apply", "-f", "-"
            ], input=yaml.dump(service_manifest), text=True, capture_output=True)
            
            if result.returncode == 0:
                self.services[model_name] = service_manifest
                logger.info(f"Kubernetes service created: {model_name}")
                return True
            else:
                logger.error(f"Failed to create service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create Kubernetes service: {e}")
            return False
    
    def scale_deployment(self, model_name: str, replicas: int) -> bool:
        """Scale deployment replicas"""
        try:
            result = subprocess.run([
                "kubectl", "scale", "deployment", f"{model_name}-deployment",
                f"--replicas={replicas}", f"-n={self.namespace}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Deployment scaled: {model_name} -> {replicas} replicas")
                return True
            else:
                logger.error(f"Failed to scale deployment: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to scale deployment: {e}")
            return False
    
    def get_deployment_status(self, model_name: str) -> Dict[str, Any]:
        """Get deployment status"""
        try:
            result = subprocess.run([
                "kubectl", "get", "deployment", f"{model_name}-deployment",
                f"-n={self.namespace}", "-o", "json"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get deployment status: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {}

class HealthChecker:
    """Health check and monitoring system"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_checks = {}
        self.health_status = {}
        self.check_thread = None
        self.is_running = False
    
    def add_health_check(self, name: str, url: str, timeout: int = 5):
        """Add health check endpoint"""
        self.health_checks[name] = {
            "url": url,
            "timeout": timeout,
            "last_check": None,
            "status": "unknown"
        }
        logger.info(f"Health check added: {name} -> {url}")
    
    def start_monitoring(self):
        """Start health monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.check_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.check_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Health monitoring loop"""
        while self.is_running:
            try:
                for name, check in self.health_checks.items():
                    self._check_endpoint(name, check)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(10)
    
    def _check_endpoint(self, name: str, check: Dict[str, Any]):
        """Check individual endpoint"""
        try:
            response = requests.get(
                check["url"],
                timeout=check["timeout"]
            )
            
            if response.status_code == 200:
                check["status"] = "healthy"
                check["last_check"] = datetime.utcnow().isoformat()
            else:
                check["status"] = "unhealthy"
                check["last_check"] = datetime.utcnow().isoformat()
                
        except Exception as e:
            check["status"] = "unhealthy"
            check["last_check"] = datetime.utcnow().isoformat()
            logger.warning(f"Health check failed for {name}: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        healthy_count = sum(1 for check in self.health_checks.values() if check["status"] == "healthy")
        total_count = len(self.health_checks)
        
        return {
            "overall_status": "healthy" if healthy_count == total_count else "unhealthy",
            "healthy_endpoints": healthy_count,
            "total_endpoints": total_count,
            "checks": self.health_checks
        }

class AutoScaler:
    """Automatic scaling based on metrics"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.scaling_history = []
        self.metrics_cache = {}
        self.scaling_thread = None
        self.is_running = False
    
    def start_scaling(self):
        """Start auto-scaling"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scaling_thread = threading.Thread(target=self._scaling_loop, daemon=True)
        self.scaling_thread.start()
        logger.info("Auto-scaling started")
    
    def stop_scaling(self):
        """Stop auto-scaling"""
        self.is_running = False
        if self.scaling_thread:
            self.scaling_thread.join(timeout=5)
        logger.info("Auto-scaling stopped")
    
    def _scaling_loop(self):
        """Auto-scaling loop"""
        while self.is_running:
            try:
                self._check_scaling_needs()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Auto-scaling error: {e}")
                time.sleep(30)
    
    def _check_scaling_needs(self):
        """Check if scaling is needed"""
        # This is a placeholder - actual implementation would:
        # 1. Collect metrics from deployed services
        # 2. Calculate current utilization
        # 3. Determine if scaling is needed
        # 4. Execute scaling actions
        
        logger.debug("Checking scaling needs...")
    
    def scale_service(self, service_name: str, target_replicas: int) -> bool:
        """Scale service to target replicas"""
        try:
            # This would integrate with the actual orchestration system
            logger.info(f"Scaling {service_name} to {target_replicas} replicas")
            
            # Record scaling action
            self.scaling_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "service": service_name,
                "target_replicas": target_replicas
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale service: {e}")
            return False

class DeploymentOrchestrator:
    """
    Main deployment orchestration system
    - Docker container management
    - Kubernetes deployment
    - Health monitoring
    - Auto-scaling
    - Rolling updates
    """
    
    def __init__(self, config: DeploymentConfig):
        """
        Initialize deployment orchestrator
        
        Args:
            config: Deployment configuration
        """
        self.config = config
        self.docker_manager = None
        self.kubernetes_manager = None
        self.health_checker = None
        self.auto_scaler = None
        
        # Deployment state
        self.deployments = {}
        self.services = {}
        self.deployment_history = []
        
        # Initialize components
        self._initialize_components()
        
        logger.info("DeploymentOrchestrator initialized", 
                   docker=config.enable_docker,
                   kubernetes=config.enable_kubernetes,
                   auto_scaling=config.enable_auto_scaling)
    
    def _initialize_components(self):
        """Initialize deployment components"""
        try:
            # Initialize Docker manager
            if self.config.enable_docker:
                self.docker_manager = DockerManager(self.config.docker_registry)
                logger.info("Docker manager initialized")
            
            # Initialize Kubernetes manager
            if self.config.enable_kubernetes:
                self.kubernetes_manager = KubernetesManager(self.config.kubernetes_namespace)
                logger.info("Kubernetes manager initialized")
            
            # Initialize health checker
            if self.config.enable_health_checks:
                self.health_checker = HealthChecker(self.config.health_check_interval)
                logger.info("Health checker initialized")
            
            # Initialize auto-scaler
            if self.config.enable_auto_scaling:
                self.auto_scaler = AutoScaler(self.config)
                logger.info("Auto-scaler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize deployment components: {e}")
            raise
    
    def deploy_model(self, model_name: str, model_path: str, 
                    deployment_type: str = "docker", replicas: int = 1) -> bool:
        """Deploy model using specified method"""
        try:
            if deployment_type == "docker":
                return self._deploy_docker(model_name, model_path, replicas)
            elif deployment_type == "kubernetes":
                return self._deploy_kubernetes(model_name, model_path, replicas)
            else:
                logger.error(f"Unsupported deployment type: {deployment_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deploy model: {e}")
            return False
    
    def _deploy_docker(self, model_name: str, model_path: str, replicas: int) -> bool:
        """Deploy model using Docker"""
        try:
            if not self.docker_manager:
                logger.error("Docker manager not initialized")
                return False
            
            # Build image
            if not self.docker_manager.build_image(model_name, model_path):
                return False
            
            # Run containers
            container_ids = []
            for i in range(replicas):
                port = 8000 + i
                container_id = self.docker_manager.run_container(
                    model_name, port=port
                )
                if container_id:
                    container_ids.append(container_id)
            
            # Record deployment
            self.deployments[model_name] = {
                "type": "docker",
                "replicas": len(container_ids),
                "container_ids": container_ids,
                "deployed_at": datetime.utcnow().isoformat()
            }
            
            # Add health checks
            if self.health_checker:
                for i, container_id in enumerate(container_ids):
                    port = 8000 + i
                    health_url = f"http://localhost:{port}/health"
                    self.health_checker.add_health_check(
                        f"{model_name}-{i}", health_url
                    )
            
            logger.info(f"Model deployed via Docker: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Docker deployment failed: {e}")
            return False
    
    def _deploy_kubernetes(self, model_name: str, model_path: str, replicas: int) -> bool:
        """Deploy model using Kubernetes"""
        try:
            if not self.kubernetes_manager:
                logger.error("Kubernetes manager not initialized")
                return False
            
            # Build Docker image first
            if self.docker_manager:
                if not self.docker_manager.build_image(model_name, model_path):
                    return False
                image = f"{self.config.docker_registry}/{model_name}:latest"
            else:
                image = f"{model_name}:latest"
            
            # Create deployment
            if not self.kubernetes_manager.create_deployment(
                model_name, image, replicas
            ):
                return False
            
            # Create service
            if not self.kubernetes_manager.create_service(model_name):
                return False
            
            # Record deployment
            self.deployments[model_name] = {
                "type": "kubernetes",
                "replicas": replicas,
                "deployed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Model deployed via Kubernetes: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Kubernetes deployment failed: {e}")
            return False
    
    def scale_model(self, model_name: str, replicas: int) -> bool:
        """Scale model replicas"""
        try:
            if model_name not in self.deployments:
                logger.error(f"Model not deployed: {model_name}")
                return False
            
            deployment = self.deployments[model_name]
            
            if deployment["type"] == "docker":
                # Docker scaling logic
                logger.info(f"Scaling Docker deployment: {model_name} -> {replicas}")
                return True
            elif deployment["type"] == "kubernetes":
                # Kubernetes scaling
                if self.kubernetes_manager:
                    return self.kubernetes_manager.scale_deployment(model_name, replicas)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to scale model: {e}")
            return False
    
    def start_monitoring(self):
        """Start monitoring and auto-scaling"""
        if self.health_checker:
            self.health_checker.start_monitoring()
        
        if self.auto_scaler:
            self.auto_scaler.start_scaling()
        
        logger.info("Deployment monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring and auto-scaling"""
        if self.health_checker:
            self.health_checker.stop_monitoring()
        
        if self.auto_scaler:
            self.auto_scaler.stop_scaling()
        
        logger.info("Deployment monitoring stopped")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status"""
        try:
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "deployments": self.deployments,
                "health_status": self.health_checker.get_health_status() if self.health_checker else {},
                "scaling_history": self.auto_scaler.scaling_history if self.auto_scaler else []
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup deployment resources"""
        try:
            self.stop_monitoring()
            
            # Stop all containers
            if self.docker_manager:
                for container_id in list(self.docker_manager.containers.keys()):
                    self.docker_manager.stop_container(container_id)
            
            logger.info("Deployment orchestrator cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup deployment orchestrator: {e}")

# Factory function for easy deployment orchestrator setup
def create_deployment_orchestrator(
    enable_docker: bool = True,
    enable_kubernetes: bool = False,
    enable_auto_scaling: bool = True,
    enable_health_checks: bool = True,
    **kwargs
) -> DeploymentOrchestrator:
    """
    Create deployment orchestrator with default configuration
    
    Args:
        enable_docker: Enable Docker deployment
        enable_kubernetes: Enable Kubernetes deployment
        enable_auto_scaling: Enable auto-scaling
        enable_health_checks: Enable health checks
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured DeploymentOrchestrator
    """
    config = DeploymentConfig(
        enable_docker=enable_docker,
        enable_kubernetes=enable_kubernetes,
        enable_auto_scaling=enable_auto_scaling,
        enable_health_checks=enable_health_checks,
        **kwargs
    )
    
    return DeploymentOrchestrator(config)
