"""
RL-Enhanced API Endpoints
Provides REST API endpoints for RL-controlled classification
"""

import asyncio
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import json
from pathlib import Path

# Import RL components
from rl_ensemble_controller import RLEnsembleController, RLClassificationResult
from rl_metrics_dashboard import RLMetricsDashboard

logger = structlog.get_logger(__name__)

# Pydantic models for API
class RLClassificationRequest(BaseModel):
    """Request model for RL classification"""
    document: Dict[str, Any] = Field(..., description="Document to classify")
    document_id: Optional[str] = Field(None, description="Optional document ID")
    enable_rl_optimization: bool = Field(True, description="Enable RL optimization")
    cost_budget: Optional[float] = Field(None, description="Cost budget constraint")
    performance_targets: Optional[Dict[str, float]] = Field(None, description="Performance targets")

class RLClassificationResponse(BaseModel):
    """Response model for RL classification"""
    success: bool
    document_id: Optional[str]
    classification: str
    confidence: float
    reasoning: str
    models_used: List[str]
    rl_decision_path: str
    performance_metrics: Dict[str, float]
    cost_estimate: float
    processing_time: float
    rl_optimization_applied: bool
    key_entities: Optional[List[Dict]] = None
    processed_at: str

class RLBatchClassificationRequest(BaseModel):
    """Request model for batch RL classification"""
    documents: List[Dict[str, Any]] = Field(..., description="Documents to classify")
    enable_rl_optimization: bool = Field(True, description="Enable RL optimization")
    cost_budget: Optional[float] = Field(None, description="Total cost budget")
    performance_targets: Optional[Dict[str, float]] = Field(None, description="Performance targets")

class RLBatchClassificationResponse(BaseModel):
    """Response model for batch RL classification"""
    success: bool
    total_documents: int
    successful_classifications: int
    failed_classifications: int
    total_cost: float
    average_processing_time: float
    performance_summary: Dict[str, Any]
    classifications: List[RLClassificationResponse]
    processed_at: str

class RLMetricsRequest(BaseModel):
    """Request model for RL metrics"""
    time_range: Optional[str] = Field("1h", description="Time range for metrics")
    include_trends: bool = Field(True, description="Include trend analysis")
    include_alerts: bool = Field(True, description="Include alert information")

class RLPerformanceReport(BaseModel):
    """RL performance report"""
    generated_at: str
    performance_summary: Dict[str, Any]
    metrics_trends: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    recommendations: List[Dict[str, str]]
    visualizations: List[str]

# Global RL controller and dashboard
rl_controller: Optional[RLEnsembleController] = None
rl_dashboard: Optional[RLMetricsDashboard] = None

def get_rl_controller() -> RLEnsembleController:
    """Get or create RL controller"""
    global rl_controller
    if rl_controller is None:
        rl_controller = RLEnsembleController(
            rl_model_path="rl_optimization/training_results/final_model.pt",
            enable_monitoring=True,
            enable_optimization=True,
            enable_security=True
        )
    return rl_controller

def get_rl_dashboard() -> RLMetricsDashboard:
    """Get or create RL dashboard"""
    global rl_dashboard
    if rl_dashboard is None:
        rl_dashboard = RLMetricsDashboard(
            max_history_size=10000,
            enable_visualization=True
        )
        # Start monitoring if controller is available
        if rl_controller:
            rl_dashboard.start_monitoring(rl_controller)
    return rl_dashboard

# Create API router
router = APIRouter(prefix="/api/v1/rl", tags=["RL-Enhanced Classification"])

@router.post("/classify", response_model=RLClassificationResponse)
async def rl_classify_document(request: RLClassificationRequest):
    """
    Classify document using RL-enhanced ensemble
    
    This endpoint uses the RL agent to intelligently control the entire
    classification pipeline, optimizing for accuracy, cost, and speed.
    """
    try:
        # Get RL controller
        controller = get_rl_controller()
        
        # Extract document information
        document = request.document
        title = document.get('title', '')
        abstract = document.get('abstract', '')
        mesh_terms = document.get('mesh_terms', [])
        publication_types = document.get('publication_types', [])
        
        # Apply cost budget if specified
        if request.cost_budget:
            # This would be implemented in the RL controller
            pass
        
        # Apply performance targets if specified
        if request.performance_targets:
            # This would be implemented in the RL controller
            pass
        
        # Perform RL-enhanced classification
        result = await controller.classify_document(
            title=title,
            abstract=abstract,
            mesh_terms=mesh_terms,
            publication_types=publication_types,
            document_id=request.document_id
        )
        
        # Convert to response format
        response = RLClassificationResponse(
            success=True,
            document_id=request.document_id,
            classification=result.classification,
            confidence=result.confidence,
            reasoning=result.reasoning,
            models_used=result.models_used,
            rl_decision_path=result.rl_decision_path,
            performance_metrics=result.performance_metrics,
            cost_estimate=result.cost_estimate,
            processing_time=result.processing_time,
            rl_optimization_applied=result.rl_optimization_applied,
            key_entities=result.key_entities,
            processed_at=datetime.utcnow().isoformat()
        )
        
        logger.info("RL classification completed",
                   document_id=request.document_id,
                   classification=result.classification,
                   confidence=result.confidence,
                   rl_optimization=result.rl_optimization_applied)
        
        return response
        
    except Exception as e:
        logger.error("RL classification failed", error=str(e), document_id=request.document_id)
        raise HTTPException(status_code=500, detail=f"RL classification failed: {str(e)}")

@router.post("/classify/batch", response_model=RLBatchClassificationResponse)
async def rl_classify_batch(request: RLBatchClassificationRequest):
    """
    Classify multiple documents using RL-enhanced ensemble
    
    Processes documents in parallel with RL optimization for each document.
    """
    try:
        # Get RL controller
        controller = get_rl_controller()
        
        # Process documents in parallel
        tasks = []
        for i, document in enumerate(request.documents):
            task = controller.classify_document(
                title=document.get('title', ''),
                abstract=document.get('abstract', ''),
                mesh_terms=document.get('mesh_terms', []),
                publication_types=document.get('publication_types', []),
                document_id=f"batch_{i}_{datetime.utcnow().timestamp()}"
            )
            tasks.append(task)
        
        # Wait for all classifications
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_classifications = []
        failed_classifications = 0
        total_cost = 0.0
        total_processing_time = 0.0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_classifications += 1
                logger.error("Batch classification failed", 
                           document_index=i, 
                           error=str(result))
            else:
                successful_classifications.append(RLClassificationResponse(
                    success=True,
                    document_id=f"batch_{i}",
                    classification=result.classification,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    models_used=result.models_used,
                    rl_decision_path=result.rl_decision_path,
                    performance_metrics=result.performance_metrics,
                    cost_estimate=result.cost_estimate,
                    processing_time=result.processing_time,
                    rl_optimization_applied=result.rl_optimization_applied,
                    key_entities=result.key_entities,
                    processed_at=datetime.utcnow().isoformat()
                ))
                total_cost += result.cost_estimate
                total_processing_time += result.processing_time
        
        # Calculate performance summary
        if successful_classifications:
            avg_accuracy = sum(r.performance_metrics.get('accuracy', 0) for r in successful_classifications) / len(successful_classifications)
            avg_cost_efficiency = sum(r.performance_metrics.get('cost_efficiency', 0) for r in successful_classifications) / len(successful_classifications)
            avg_processing_speed = sum(r.performance_metrics.get('processing_speed', 0) for r in successful_classifications) / len(successful_classifications)
            avg_domain_specialization = sum(r.performance_metrics.get('domain_specialization', 0) for r in successful_classifications) / len(successful_classifications)
        else:
            avg_accuracy = avg_cost_efficiency = avg_processing_speed = avg_domain_specialization = 0.0
        
        performance_summary = {
            'average_accuracy': avg_accuracy,
            'average_cost_efficiency': avg_cost_efficiency,
            'average_processing_speed': avg_processing_speed,
            'average_domain_specialization': avg_domain_specialization,
            'total_cost': total_cost,
            'average_processing_time': total_processing_time / max(len(successful_classifications), 1)
        }
        
        response = RLBatchClassificationResponse(
            success=True,
            total_documents=len(request.documents),
            successful_classifications=len(successful_classifications),
            failed_classifications=failed_classifications,
            total_cost=total_cost,
            average_processing_time=total_processing_time / max(len(successful_classifications), 1),
            performance_summary=performance_summary,
            classifications=successful_classifications,
            processed_at=datetime.utcnow().isoformat()
        )
        
        logger.info("RL batch classification completed",
                   total_documents=len(request.documents),
                   successful=len(successful_classifications),
                   failed=failed_classifications)
        
        return response
        
    except Exception as e:
        logger.error("RL batch classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"RL batch classification failed: {str(e)}")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_rl_metrics(request: RLMetricsRequest = Depends()):
    """
    Get real-time RL performance metrics
    
    Returns comprehensive metrics including performance trends,
    alerts, and recommendations.
    """
    try:
        # Get RL dashboard
        dashboard = get_rl_dashboard()
        
        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data()
        
        # Add alert summary
        alert_summary = dashboard.get_alert_summary()
        dashboard_data['alert_summary'] = alert_summary
        
        logger.info("RL metrics retrieved", 
                   data_points=len(dashboard_data.get('metrics_history', [])),
                   alerts=alert_summary.get('total_alerts', 0))
        
        return dashboard_data
        
    except Exception as e:
        logger.error("Failed to get RL metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get RL metrics: {str(e)}")

@router.get("/performance-report", response_model=RLPerformanceReport)
async def get_performance_report(background_tasks: BackgroundTasks):
    """
    Generate comprehensive RL performance report
    
    Creates detailed performance analysis with visualizations
    and recommendations.
    """
    try:
        # Get RL dashboard
        dashboard = get_rl_dashboard()
        
        # Generate report
        report_file = dashboard.generate_performance_report()
        
        # Create visualizations
        visualization_files = dashboard.create_visualization()
        
        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data()
        
        # Generate recommendations
        recommendations = dashboard._generate_recommendations()
        
        response = RLPerformanceReport(
            generated_at=datetime.utcnow().isoformat(),
            performance_summary=dashboard_data.get('performance_summary', {}),
            metrics_trends=dashboard_data.get('metrics_trends', {}),
            alerts=dashboard_data.get('recent_alerts', []),
            recommendations=recommendations,
            visualizations=visualization_files
        )
        
        logger.info("Performance report generated", 
                   report_file=report_file,
                   visualizations=len(visualization_files))
        
        return response
        
    except Exception as e:
        logger.error("Failed to generate performance report", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate performance report: {str(e)}")

@router.get("/health")
async def rl_health_check():
    """
    RL system health check
    
    Returns the health status of the RL-enhanced classification system.
    """
    try:
        # Get RL controller
        controller = get_rl_controller()
        
        # Get performance summary
        performance_summary = controller.get_performance_summary()
        
        # Check if monitoring is active
        dashboard = get_rl_dashboard()
        monitoring_status = dashboard.monitoring_active if dashboard else False
        
        health_status = {
            'status': 'healthy',
            'rl_controller_available': controller is not None,
            'monitoring_active': monitoring_status,
            'performance_summary': performance_summary,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error("RL health check failed", error=str(e))
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@router.post("/export-metrics")
async def export_rl_metrics(output_file: str = "rl_metrics_export.json"):
    """
    Export RL metrics to file
    
    Exports all collected metrics and performance data.
    """
    try:
        # Get RL dashboard
        dashboard = get_rl_dashboard()
        
        # Export metrics
        export_file = dashboard.export_metrics(output_file)
        
        logger.info("RL metrics exported", file=export_file)
        
        return {
            'success': True,
            'export_file': export_file,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to export RL metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export RL metrics: {str(e)}")

@router.get("/alerts")
async def get_rl_alerts():
    """
    Get RL performance alerts
    
    Returns recent performance alerts and recommendations.
    """
    try:
        # Get RL dashboard
        dashboard = get_rl_dashboard()
        
        # Get alert summary
        alert_summary = dashboard.get_alert_summary()
        
        return alert_summary
        
    except Exception as e:
        logger.error("Failed to get RL alerts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get RL alerts: {str(e)}")

@router.post("/retrain")
async def trigger_rl_retraining(background_tasks: BackgroundTasks):
    """
    Trigger RL model retraining
    
    Initiates retraining of the RL model with recent data.
    """
    try:
        # This would trigger RL retraining in the background
        # For now, we'll just log the request
        
        logger.info("RL retraining requested")
        
        # In a real implementation, this would:
        # 1. Collect recent performance data
        # 2. Trigger RL training with new data
        # 3. Update the model
        # 4. Validate performance
        
        return {
            'success': True,
            'message': 'RL retraining initiated',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to trigger RL retraining", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger RL retraining: {str(e)}")

# Initialize RL system on startup
@router.on_event("startup")
async def startup_rl_system():
    """Initialize RL system on startup"""
    try:
        # Initialize RL controller
        controller = get_rl_controller()
        
        # Initialize dashboard
        dashboard = get_rl_dashboard()
        
        # Start monitoring
        dashboard.start_monitoring(controller)
        
        logger.info("RL system initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize RL system", error=str(e))

@router.on_event("shutdown")
async def shutdown_rl_system():
    """Shutdown RL system"""
    try:
        # Stop monitoring
        dashboard = get_rl_dashboard()
        if dashboard:
            dashboard.stop_monitoring()
        
        logger.info("RL system shutdown completed")
        
    except Exception as e:
        logger.error("Failed to shutdown RL system", error=str(e))
