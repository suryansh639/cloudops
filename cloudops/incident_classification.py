"""
Incident Classification System

Defines universal incident classes that apply across all cloud services.
Each incident class represents a fundamental failure mode, not a service-specific problem.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class IncidentClass(str, Enum):
    """Universal incident classes - finite set of fundamental failure modes"""
    
    RESOURCE_SATURATION = "resource_saturation"      # CPU, memory, disk, connections exhausted
    LOAD_SPIKE = "load_spike"                        # Sudden traffic/request increase
    CONFIGURATION_DRIFT = "configuration_drift"      # Settings changed from baseline
    DEPENDENCY_FAILURE = "dependency_failure"        # Upstream/downstream service unavailable
    SCALING_FAILURE = "scaling_failure"              # Auto-scaling not working
    NETWORK_CONNECTIVITY = "network_connectivity"    # Network path broken
    PERMISSION_FAILURE = "permission_failure"        # IAM/RBAC denying access
    COST_ANOMALY = "cost_anomaly"                   # Unexpected spend increase
    DEPLOYMENT_REGRESSION = "deployment_regression"  # New version causing issues
    AVAILABILITY_LOSS = "availability_loss"          # Service/resource down
    PERFORMANCE_DEGRADATION = "performance_degradation"  # Slow but not saturated
    DATA_INCONSISTENCY = "data_inconsistency"       # Replication lag, corruption


class IncidentClassification(BaseModel):
    """Result of classifying a user query into incident classes"""
    
    primary_class: IncidentClass
    secondary_classes: List[IncidentClass] = []
    confidence: float  # 0.0 to 1.0
    
    # Extracted context from query
    resource_type: Optional[str] = None  # e.g., "ec2", "rds", "pod"
    resource_id: Optional[str] = None
    metric: Optional[str] = None  # e.g., "cpu", "memory", "latency"
    scope: str = "production"
    time_window: int = 3600  # seconds


class IncidentClassifier:
    """
    Classifies natural language queries into incident classes.
    Uses LLM but constrains output to defined incident classes.
    """
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
    
    def classify(self, query: str) -> IncidentClassification:
        """
        Classify user query into incident class(es).
        
        Examples:
        - "high CPU on RDS" → RESOURCE_SATURATION
        - "pod crashing" → AVAILABILITY_LOSS + DEPENDENCY_FAILURE
        - "Lambda timing out" → RESOURCE_SATURATION or DEPENDENCY_FAILURE
        - "sudden cost spike" → COST_ANOMALY + LOAD_SPIKE
        """
        
        prompt = f"""
Classify this cloud operations incident into one or more incident classes.

Query: "{query}"

Available incident classes:
- resource_saturation: CPU, memory, disk, connections exhausted
- load_spike: Sudden traffic/request increase
- configuration_drift: Settings changed from baseline
- dependency_failure: Upstream/downstream service unavailable
- scaling_failure: Auto-scaling not working
- network_connectivity: Network path broken
- permission_failure: IAM/RBAC denying access
- cost_anomaly: Unexpected spend increase
- deployment_regression: New version causing issues
- availability_loss: Service/resource down
- performance_degradation: Slow but not saturated
- data_inconsistency: Replication lag, corruption

Extract:
- primary_class: Most likely incident class
- secondary_classes: Other possible classes (if any)
- confidence: 0.0 to 1.0
- resource_type: Type of resource (ec2, rds, lambda, pod, etc.)
- resource_id: Specific resource identifier (if mentioned)
- metric: Specific metric (cpu, memory, latency, etc.)
- scope: Environment (production, staging, dev)

Return JSON only.
"""
        
        response = self.ai_provider.generate(
            prompt=prompt,
            temperature=0.0,
            max_tokens=500
        )
        
        # Parse and validate
        import json
        data = json.loads(response)
        
        return IncidentClassification(
            primary_class=IncidentClass(data['primary_class']),
            secondary_classes=[IncidentClass(c) for c in data.get('secondary_classes', [])],
            confidence=data.get('confidence', 0.8),
            resource_type=data.get('resource_type'),
            resource_id=data.get('resource_id'),
            metric=data.get('metric'),
            scope=data.get('scope', 'production'),
            time_window=data.get('time_window', 3600)
        )
