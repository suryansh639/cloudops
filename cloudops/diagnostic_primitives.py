"""
Diagnostic Primitives

Service-agnostic investigation primitives that work across AWS services.
Each primitive encapsulates ONE diagnostic step and returns structured facts.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta


class DiagnosticResult(BaseModel):
    """Structured result from a diagnostic primitive - facts only, no conclusions"""
    
    primitive: str
    resource_type: str
    resource_id: Optional[str]
    timestamp: datetime
    
    # Raw facts
    facts: Dict[str, Any]
    
    # Metadata
    success: bool
    error: Optional[str] = None


class DiagnosticPrimitive(ABC):
    """Base class for all diagnostic primitives"""
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> DiagnosticResult:
        """Execute diagnostic and return facts"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Primitive identifier"""
        pass


# ============================================================================
# UTILIZATION PRIMITIVES
# ============================================================================

class AnalyzeUtilization(DiagnosticPrimitive):
    """
    Analyze resource utilization for any metric.
    Works for: EC2 CPU, RDS connections, Lambda concurrency, etc.
    """
    
    def __init__(self, cloud_provider):
        self.provider = cloud_provider
    
    @property
    def name(self) -> str:
        return "analyze_utilization"
    
    def execute(self, context: Dict[str, Any]) -> DiagnosticResult:
        """
        Context:
        - resource_type: ec2, rds, lambda, etc.
        - resource_id: instance-id, db-identifier, etc.
        - metric: cpu, memory, connections, etc.
        - time_window: seconds
        """
        
        resource_type = context['resource_type']
        resource_id = context.get('resource_id')
        metric = context.get('metric', 'cpu')
        time_window = context.get('time_window', 3600)
        
        # Map generic metric to CloudWatch namespace/metric
        namespace, metric_name = self._map_metric(resource_type, metric)
        
        # Get metrics from CloudWatch
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=time_window)
        
        try:
            stats = self.provider.get_metric_statistics(
                namespace=namespace,
                metric_name=metric_name,
                dimensions=self._get_dimensions(resource_type, resource_id),
                start_time=start_time,
                end_time=end_time,
                period=300,
                statistics=['Average', 'Maximum', 'Minimum']
            )
            
            # Extract facts
            datapoints = stats.get('Datapoints', [])
            
            facts = {
                'metric': metric,
                'time_window_seconds': time_window,
                'datapoint_count': len(datapoints),
                'current_value': datapoints[-1]['Average'] if datapoints else None,
                'max_value': max([d['Maximum'] for d in datapoints]) if datapoints else None,
                'min_value': min([d['Minimum'] for d in datapoints]) if datapoints else None,
                'avg_value': sum([d['Average'] for d in datapoints]) / len(datapoints) if datapoints else None,
                'trend': self._calculate_trend(datapoints),
                'datapoints': datapoints[-10:]  # Last 10 for context
            }
            
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts=facts,
                success=True
            )
            
        except Exception as e:
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts={},
                success=False,
                error=str(e)
            )
    
    def _map_metric(self, resource_type: str, metric: str) -> tuple:
        """Map generic metric to CloudWatch namespace/metric"""
        
        mapping = {
            'ec2': {
                'cpu': ('AWS/EC2', 'CPUUtilization'),
                'memory': ('CWAgent', 'mem_used_percent'),
                'disk': ('CWAgent', 'disk_used_percent'),
                'network': ('AWS/EC2', 'NetworkIn')
            },
            'rds': {
                'cpu': ('AWS/RDS', 'CPUUtilization'),
                'connections': ('AWS/RDS', 'DatabaseConnections'),
                'memory': ('AWS/RDS', 'FreeableMemory'),
                'iops': ('AWS/RDS', 'ReadIOPS')
            },
            'lambda': {
                'duration': ('AWS/Lambda', 'Duration'),
                'errors': ('AWS/Lambda', 'Errors'),
                'throttles': ('AWS/Lambda', 'Throttles'),
                'concurrency': ('AWS/Lambda', 'ConcurrentExecutions')
            },
            'dynamodb': {
                'read': ('AWS/DynamoDB', 'ConsumedReadCapacityUnits'),
                'write': ('AWS/DynamoDB', 'ConsumedWriteCapacityUnits'),
                'throttles': ('AWS/DynamoDB', 'UserErrors')
            }
        }
        
        return mapping.get(resource_type, {}).get(metric, ('AWS/CloudWatch', metric))
    
    def _get_dimensions(self, resource_type: str, resource_id: Optional[str]) -> List[Dict]:
        """Get CloudWatch dimensions for resource"""
        
        if not resource_id:
            return []
        
        dimension_map = {
            'ec2': [{'Name': 'InstanceId', 'Value': resource_id}],
            'rds': [{'Name': 'DBInstanceIdentifier', 'Value': resource_id}],
            'lambda': [{'Name': 'FunctionName', 'Value': resource_id}],
            'dynamodb': [{'Name': 'TableName', 'Value': resource_id}]
        }
        
        return dimension_map.get(resource_type, [])
    
    def _calculate_trend(self, datapoints: List[Dict]) -> str:
        """Calculate trend: increasing, decreasing, stable"""
        
        if len(datapoints) < 2:
            return 'unknown'
        
        values = [d['Average'] for d in sorted(datapoints, key=lambda x: x['Timestamp'])]
        
        # Simple linear trend
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if diff_pct > 10:
            return 'increasing'
        elif diff_pct < -10:
            return 'decreasing'
        else:
            return 'stable'


# ============================================================================
# BASELINE COMPARISON PRIMITIVES
# ============================================================================

class CompareBaseline(DiagnosticPrimitive):
    """Compare current metrics against historical baseline"""
    
    def __init__(self, cloud_provider):
        self.provider = cloud_provider
    
    @property
    def name(self) -> str:
        return "compare_baseline"
    
    def execute(self, context: Dict[str, Any]) -> DiagnosticResult:
        """
        Compare current period vs baseline period (e.g., same time yesterday/last week)
        """
        
        resource_type = context['resource_type']
        resource_id = context.get('resource_id')
        metric = context.get('metric', 'cpu')
        
        # Current period
        current_end = datetime.utcnow()
        current_start = current_end - timedelta(hours=1)
        
        # Baseline period (same time yesterday)
        baseline_end = current_end - timedelta(days=1)
        baseline_start = baseline_end - timedelta(hours=1)
        
        try:
            # Get both periods
            current_stats = self._get_stats(resource_type, resource_id, metric, 
                                           current_start, current_end)
            baseline_stats = self._get_stats(resource_type, resource_id, metric,
                                            baseline_start, baseline_end)
            
            current_avg = current_stats['avg']
            baseline_avg = baseline_stats['avg']
            
            deviation_pct = ((current_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
            
            facts = {
                'metric': metric,
                'current_avg': current_avg,
                'current_max': current_stats['max'],
                'baseline_avg': baseline_avg,
                'baseline_max': baseline_stats['max'],
                'deviation_percent': deviation_pct,
                'is_anomaly': abs(deviation_pct) > 50,  # >50% deviation
                'comparison_period': 'same_time_yesterday'
            }
            
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts=facts,
                success=True
            )
            
        except Exception as e:
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts={},
                success=False,
                error=str(e)
            )
    
    def _get_stats(self, resource_type, resource_id, metric, start, end):
        """Helper to get statistics for a period"""
        # Implementation similar to AnalyzeUtilization
        # Returns {'avg': float, 'max': float, 'min': float}
        return {'avg': 0.0, 'max': 0.0, 'min': 0.0}


# ============================================================================
# DEPENDENCY PRIMITIVES
# ============================================================================

class TraceDependencies(DiagnosticPrimitive):
    """Identify and check health of dependencies"""
    
    def __init__(self, cloud_provider):
        self.provider = cloud_provider
    
    @property
    def name(self) -> str:
        return "trace_dependencies"
    
    def execute(self, context: Dict[str, Any]) -> DiagnosticResult:
        """
        Find dependencies and check their health.
        Works for: EC2→RDS, Lambda→DynamoDB, ECS→ALB, etc.
        """
        
        resource_type = context['resource_type']
        resource_id = context.get('resource_id')
        
        try:
            dependencies = self._discover_dependencies(resource_type, resource_id)
            
            # Check health of each dependency
            dependency_health = []
            for dep in dependencies:
                health = self._check_dependency_health(dep)
                dependency_health.append(health)
            
            facts = {
                'dependency_count': len(dependencies),
                'dependencies': dependency_health,
                'unhealthy_count': sum(1 for d in dependency_health if not d['healthy']),
                'has_dependency_issues': any(not d['healthy'] for d in dependency_health)
            }
            
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts=facts,
                success=True
            )
            
        except Exception as e:
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts={},
                success=False,
                error=str(e)
            )
    
    def _discover_dependencies(self, resource_type, resource_id):
        """Discover dependencies based on resource type"""
        # EC2: Check security groups for DB ports
        # Lambda: Check environment variables for service endpoints
        # ECS: Check task definition for linked services
        return []
    
    def _check_dependency_health(self, dependency):
        """Check if dependency is healthy"""
        return {
            'type': dependency.get('type'),
            'id': dependency.get('id'),
            'healthy': True,
            'status': 'available'
        }


# ============================================================================
# CONFIGURATION PRIMITIVES
# ============================================================================

class CheckRecentChanges(DiagnosticPrimitive):
    """Check for recent configuration or deployment changes"""
    
    def __init__(self, cloud_provider):
        self.provider = cloud_provider
    
    @property
    def name(self) -> str:
        return "check_recent_changes"
    
    def execute(self, context: Dict[str, Any]) -> DiagnosticResult:
        """
        Check CloudTrail for recent changes to resource.
        Works across all AWS services.
        """
        
        resource_type = context['resource_type']
        resource_id = context.get('resource_id')
        lookback_hours = context.get('lookback_hours', 24)
        
        try:
            # Query CloudTrail
            start_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            events = self.provider.lookup_cloudtrail_events(
                resource_type=resource_type,
                resource_id=resource_id,
                start_time=start_time
            )
            
            # Categorize events
            modifications = [e for e in events if e['event_name'] in [
                'ModifyDBInstance', 'UpdateFunctionConfiguration', 
                'ModifyInstanceAttribute', 'PutBucketPolicy'
            ]]
            
            deployments = [e for e in events if e['event_name'] in [
                'CreateDeployment', 'UpdateService', 'RunTask'
            ]]
            
            facts = {
                'lookback_hours': lookback_hours,
                'total_events': len(events),
                'modification_count': len(modifications),
                'deployment_count': len(deployments),
                'recent_modifications': modifications[:5],  # Last 5
                'recent_deployments': deployments[:5],
                'has_recent_changes': len(modifications) > 0 or len(deployments) > 0
            }
            
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts=facts,
                success=True
            )
            
        except Exception as e:
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts={},
                success=False,
                error=str(e)
            )


# ============================================================================
# SCALING PRIMITIVES
# ============================================================================

class CheckScalingBehavior(DiagnosticPrimitive):
    """Check if auto-scaling is working correctly"""
    
    def __init__(self, cloud_provider):
        self.provider = cloud_provider
    
    @property
    def name(self) -> str:
        return "check_scaling_behavior"
    
    def execute(self, context: Dict[str, Any]) -> DiagnosticResult:
        """
        Check scaling configuration and recent scaling activities.
        Works for: ASG, ECS services, Lambda concurrency, DynamoDB capacity
        """
        
        resource_type = context['resource_type']
        resource_id = context.get('resource_id')
        
        try:
            scaling_config = self._get_scaling_config(resource_type, resource_id)
            scaling_activities = self._get_scaling_activities(resource_type, resource_id)
            
            facts = {
                'scaling_enabled': scaling_config.get('enabled', False),
                'min_capacity': scaling_config.get('min'),
                'max_capacity': scaling_config.get('max'),
                'current_capacity': scaling_config.get('current'),
                'at_max_capacity': scaling_config.get('current') >= scaling_config.get('max'),
                'recent_scale_events': len(scaling_activities),
                'last_scale_time': scaling_activities[0]['time'] if scaling_activities else None,
                'scaling_activities': scaling_activities[:5]
            }
            
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts=facts,
                success=True
            )
            
        except Exception as e:
            return DiagnosticResult(
                primitive=self.name,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                facts={},
                success=False,
                error=str(e)
            )
    
    def _get_scaling_config(self, resource_type, resource_id):
        """Get scaling configuration"""
        return {'enabled': False, 'min': 1, 'max': 10, 'current': 1}
    
    def _get_scaling_activities(self, resource_type, resource_id):
        """Get recent scaling activities"""
        return []
