"""
Reasoning-Based Planner

Maps incident classes to diagnostic primitives dynamically.
NO service-specific logic - only incident class → primitive mappings.
"""
from typing import List, Dict, Any
from cloudops.incident_classification import IncidentClass, IncidentClassification
from cloudops.diagnostic_primitives import DiagnosticPrimitive


class DiagnosticPlan(BaseModel):
    """Execution plan composed of diagnostic primitives"""
    
    plan_id: str
    incident_class: IncidentClass
    primitives: List[str]  # Ordered list of primitive names
    context: Dict[str, Any]  # Shared context for all primitives
    estimated_duration_seconds: int


class ReasoningPlanner:
    """
    Maps incident classes to diagnostic primitives.
    
    Key principle: Encode WHAT to investigate (incident class),
    not HOW for each service (playbook).
    """
    
    def __init__(self, primitives: Dict[str, DiagnosticPrimitive]):
        self.primitives = primitives
        self._incident_strategies = self._define_strategies()
    
    def create_plan(self, classification: IncidentClassification) -> DiagnosticPlan:
        """
        Create diagnostic plan based on incident class.
        
        This is the ONLY place where incident classes map to primitives.
        NO service-specific logic here.
        """
        
        # Get strategy for primary incident class
        strategy = self._incident_strategies.get(classification.primary_class)
        
        if not strategy:
            raise ValueError(f"No strategy for incident class: {classification.primary_class}")
        
        # Build context from classification
        context = {
            'resource_type': classification.resource_type,
            'resource_id': classification.resource_id,
            'metric': classification.metric,
            'scope': classification.scope,
            'time_window': classification.time_window
        }
        
        # Select primitives based on strategy
        primitives = strategy['primitives']
        
        # Add secondary class primitives if applicable
        for secondary in classification.secondary_classes:
            secondary_strategy = self._incident_strategies.get(secondary)
            if secondary_strategy:
                # Add unique primitives from secondary strategies
                for p in secondary_strategy['primitives']:
                    if p not in primitives:
                        primitives.append(p)
        
        return DiagnosticPlan(
            plan_id=self._generate_plan_id(),
            incident_class=classification.primary_class,
            primitives=primitives,
            context=context,
            estimated_duration_seconds=len(primitives) * 3  # ~3s per primitive
        )
    
    def _define_strategies(self) -> Dict[IncidentClass, Dict]:
        """
        Define diagnostic strategies for each incident class.
        
        This is the CORE SCALING MECHANISM:
        - 12 incident classes
        - Each maps to 3-6 primitives
        - Primitives work across ALL services
        - NO service-specific logic
        """
        
        return {
            # Resource exhaustion: check utilization, compare baseline, check scaling
            IncidentClass.RESOURCE_SATURATION: {
                'primitives': [
                    'analyze_utilization',      # What's the current usage?
                    'compare_baseline',         # Is this normal?
                    'find_top_consumers',       # What's consuming resources?
                    'check_scaling_behavior',   # Is scaling working?
                    'check_recent_changes'      # Did something change?
                ],
                'description': 'Resource exhaustion investigation'
            },
            
            # Sudden traffic increase: check load patterns, scaling, dependencies
            IncidentClass.LOAD_SPIKE: {
                'primitives': [
                    'analyze_utilization',      # Confirm spike
                    'compare_baseline',         # How abnormal?
                    'check_scaling_behavior',   # Did we scale?
                    'find_top_consumers',       # What's driving load?
                    'trace_dependencies'        # Are dependencies handling it?
                ],
                'description': 'Load spike investigation'
            },
            
            # Configuration changed: check recent changes, compare config
            IncidentClass.CONFIGURATION_DRIFT: {
                'primitives': [
                    'check_recent_changes',     # What changed?
                    'diff_configuration',       # What's different?
                    'validate_configuration',   # Is config valid?
                    'check_deployment_status'   # Was there a deployment?
                ],
                'description': 'Configuration drift investigation'
            },
            
            # Dependency down: trace dependencies, check connectivity
            IncidentClass.DEPENDENCY_FAILURE: {
                'primitives': [
                    'trace_dependencies',       # What are dependencies?
                    'check_connectivity',       # Can we reach them?
                    'check_dependency_health',  # Are they healthy?
                    'check_recent_changes',     # Did dependency change?
                    'evaluate_throttling'       # Are we being throttled?
                ],
                'description': 'Dependency failure investigation'
            },
            
            # Scaling not working: check scaling config and activities
            IncidentClass.SCALING_FAILURE: {
                'primitives': [
                    'check_scaling_behavior',   # Is scaling configured?
                    'analyze_utilization',      # What's the load?
                    'check_scaling_limits',     # Hit any limits?
                    'check_recent_changes',     # Did config change?
                    'check_permissions'         # Can we scale?
                ],
                'description': 'Scaling failure investigation'
            },
            
            # Network broken: check connectivity, security groups, routes
            IncidentClass.NETWORK_CONNECTIVITY: {
                'primitives': [
                    'check_connectivity',       # Can we connect?
                    'check_security_groups',    # Are ports open?
                    'check_network_acls',       # Any network blocks?
                    'check_route_tables',       # Are routes correct?
                    'trace_dependencies'        # What are we trying to reach?
                ],
                'description': 'Network connectivity investigation'
            },
            
            # Permission denied: check IAM policies, resource policies
            IncidentClass.PERMISSION_FAILURE: {
                'primitives': [
                    'check_permissions',        # What permissions exist?
                    'check_resource_policy',    # Resource-level policy?
                    'check_recent_changes',     # Did permissions change?
                    'validate_credentials'      # Are credentials valid?
                ],
                'description': 'Permission failure investigation'
            },
            
            # Cost spike: analyze spend, find top consumers
            IncidentClass.COST_ANOMALY: {
                'primitives': [
                    'analyze_cost_trend',       # What's the spend?
                    'compare_baseline',         # Is this abnormal?
                    'find_top_consumers',       # What's expensive?
                    'check_recent_changes',     # Did something change?
                    'analyze_utilization'       # Are we over-provisioned?
                ],
                'description': 'Cost anomaly investigation'
            },
            
            # New deployment causing issues: check deployment, compare versions
            IncidentClass.DEPLOYMENT_REGRESSION: {
                'primitives': [
                    'check_deployment_status',  # What was deployed?
                    'compare_versions',         # What changed?
                    'analyze_error_rate',       # Are errors up?
                    'check_recent_changes',     # When did it deploy?
                    'analyze_utilization'       # Resource usage different?
                ],
                'description': 'Deployment regression investigation'
            },
            
            # Service down: check availability, health checks, dependencies
            IncidentClass.AVAILABILITY_LOSS: {
                'primitives': [
                    'check_resource_status',    # Is it running?
                    'check_health_checks',      # Are health checks passing?
                    'trace_dependencies',       # Are dependencies up?
                    'check_recent_changes',     # Did something break it?
                    'analyze_error_rate'        # What errors are occurring?
                ],
                'description': 'Availability loss investigation'
            },
            
            # Slow but not saturated: check latency, dependencies, queries
            IncidentClass.PERFORMANCE_DEGRADATION: {
                'primitives': [
                    'analyze_latency',          # How slow?
                    'compare_baseline',         # Is this abnormal?
                    'trace_dependencies',       # Are dependencies slow?
                    'analyze_query_performance', # Slow queries?
                    'check_recent_changes'      # Did something change?
                ],
                'description': 'Performance degradation investigation'
            },
            
            # Data issues: check replication, consistency
            IncidentClass.DATA_INCONSISTENCY: {
                'primitives': [
                    'check_replication_lag',    # Is replication behind?
                    'check_data_integrity',     # Is data corrupted?
                    'check_recent_changes',     # Did schema change?
                    'analyze_error_rate'        # Are there errors?
                ],
                'description': 'Data inconsistency investigation'
            }
        }
    
    def _generate_plan_id(self) -> str:
        """Generate unique plan ID"""
        import uuid
        return f"plan-{uuid.uuid4().hex[:8]}"


# ============================================================================
# PRIMITIVE REGISTRY
# ============================================================================

class PrimitiveRegistry:
    """
    Registry of all available diagnostic primitives.
    Primitives are registered once and reused across all investigations.
    """
    
    def __init__(self, cloud_provider):
        self.provider = cloud_provider
        self._primitives = {}
        self._register_primitives()
    
    def _register_primitives(self):
        """Register all available primitives"""
        from cloudops.diagnostic_primitives import (
            AnalyzeUtilization,
            CompareBaseline,
            TraceDependencies,
            CheckRecentChanges,
            CheckScalingBehavior
        )
        
        # Instantiate and register
        self._primitives = {
            'analyze_utilization': AnalyzeUtilization(self.provider),
            'compare_baseline': CompareBaseline(self.provider),
            'trace_dependencies': TraceDependencies(self.provider),
            'check_recent_changes': CheckRecentChanges(self.provider),
            'check_scaling_behavior': CheckScalingBehavior(self.provider),
            
            # Placeholders for other primitives
            # These would be implemented similarly
            'find_top_consumers': None,
            'diff_configuration': None,
            'validate_configuration': None,
            'check_deployment_status': None,
            'check_connectivity': None,
            'check_dependency_health': None,
            'evaluate_throttling': None,
            'check_scaling_limits': None,
            'check_permissions': None,
            'check_security_groups': None,
            'check_network_acls': None,
            'check_route_tables': None,
            'check_resource_policy': None,
            'validate_credentials': None,
            'analyze_cost_trend': None,
            'compare_versions': None,
            'analyze_error_rate': None,
            'check_resource_status': None,
            'check_health_checks': None,
            'analyze_latency': None,
            'analyze_query_performance': None,
            'check_replication_lag': None,
            'check_data_integrity': None
        }
    
    def get(self, name: str) -> DiagnosticPrimitive:
        """Get primitive by name"""
        primitive = self._primitives.get(name)
        if primitive is None:
            raise ValueError(f"Primitive not implemented: {name}")
        return primitive
    
    def list_available(self) -> List[str]:
        """List all available primitive names"""
        return [k for k, v in self._primitives.items() if v is not None]
